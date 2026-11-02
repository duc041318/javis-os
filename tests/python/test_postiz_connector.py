"""Connector Postiz (lên lịch / đăng bài mạng xã hội). Chạy tay / CI:

    python tests/python/test_postiz_connector.py

Không cần pytest, không chạm mạng.

Vì sao có file này: Postiz là connector ĐĂNG BÀI THẬT ra mạng xã hội. Một tool duy nhất
(integrationSchedulePostTool) vừa tạo nháp, vừa lên lịch, vừa đăng ngay, phân biệt bằng tham số
LỒNG socialPost[].type. Nên catalog có thêm `draft_rules`. Ba thứ phải giữ:

  1. Mức Ghi nháp tạo được bài NHÁP (để người dùng duyệt trong Postiz) nhưng TUYỆT ĐỐI không lên
     lịch hay đăng ngay. Chỉ một bài trong lô không phải nháp là cả lời gọi bị coi là nguy hiểm.
  2. Thiếu tham số, sai kiểu, danh sách rỗng → nguy hiểm (fail-closed), không bao giờ là ghi thường.
  3. Hai kiểu địa chỉ: Postiz Cloud (bỏ trống ô địa chỉ → url tĩnh) và Postiz tự cài
     (<địa chỉ>/api/mcp).
"""
from _paths import ROOT, SERVER  # noqa: E402,F401  - nạp server/ vào sys.path
import sys

import mcp_catalog as mc

loi = []


def check(ten, dieu_kien, them=""):
    print(("ok   " if dieu_kien else "FAIL ") + ten + (("  [" + str(them) + "]") if them and not dieu_kien else ""))
    if not dieu_kien:
        loi.append(ten)


con = mc.get("postiz")
check("catalog có connector postiz", bool(con))
if not con:
    print("\nFAIL - test_postiz_connector: thiếu hẳn connector")
    sys.exit(1)

# ---- 1. Khai báo cơ bản ----
check("transport http", con.get("transport") == "http")
check("mặc định CHỈ ĐỌC", con.get("default_perm") == "readonly")
check("rủi ro nói rõ đăng thật không hoàn tác được",
      "ĐĂNG" in con.get("risk", "") and "hoàn tác" in con.get("risk", ""))
check("logo có file thật", (ROOT / "dashboard" / "logos" / "postiz.svg").is_file())

fields = {f["key"]: f for f in ((con.get("auth") or {}).get("fields") or [])}
check("API key đi bằng Authorization: Bearer",
      fields.get("api_key", {}).get("header") == "Authorization: Bearer {api_key}")
check("ô địa chỉ là tuỳ chọn (Cloud thì bỏ trống)", bool(fields.get("postiz_url", {}).get("optional")))
check("ô địa chỉ KHÔNG bị nhét thành header", "header" not in fields.get("postiz_url", {}))
check("ô API key KHÔNG được tuỳ chọn", not fields.get("api_key", {}).get("optional"))

pub = [c for c in mc.public_catalog() if c["id"] == "postiz"]
check("UI thấy connector", len(pub) == 1)
check("UI không lộ draft_rules", pub and "draft_rules" not in pub[0])

# ---- 2. Địa chỉ ----
check("Cloud: bỏ trống địa chỉ → build_url rỗng để rơi về url tĩnh",
      mc.build_url(con, {"api_key": "k"}) == "" and con.get("url") == "https://api.postiz.com/mcp")
for raw, mong in [
    ("https://postiz.cty.vn", "https://postiz.cty.vn/api/mcp"),
    ("postiz.cty.vn/", "https://postiz.cty.vn/api/mcp"),
    # Dán nguyên URL đang mở (kể cả đã có /api) vẫn ra đúng, không bị /api/api.
    ("https://postiz.cty.vn/api", "https://postiz.cty.vn/api/mcp"),
    ("https://postiz.cty.vn/launches?x=1", "https://postiz.cty.vn/api/mcp"),
    ("http://localhost:4007", "http://localhost:4007/api/mcp"),
]:
    got = mc.build_url(con, {"api_key": "k", "postiz_url": raw})
    check("tự cài " + repr(raw) + " → đúng", got == mong, got)
check("CANARY: địa chỉ rác → rỗng", mc.build_url(con, {"api_key": "k", "postiz_url": "không phải url"}) == "")
check("header dựng đúng", mc.build_headers(con, {"api_key": "KEY"}) == {"Authorization": "Bearer KEY"})

# ---- 3. Phân loại tool thường ----
LOAI = {
    "integrationList": "read", "groupList": "read", "integrationSchema": "read",
    "postsListTool": "read", "mediaListTool": "read",
    "uploadFromUrlTool": "write", "generateImageTool": "write", "triggerTool": "write",
    "deletePostTool": "danger", "postSettingsTool": "danger",
}
for tool, mong in LOAI.items():
    got = mc.classify(con, tool)
    check("phân loại " + tool + " → " + mong, got == mong, got)


# ---- 4. Luật nháp của tool tạo bài ----
def bai(*types):
    return {"socialPost": [{"integrationId": "x", "type": t, "date": "2026-11-03T02:00:00Z",
                            "postsAndComments": [{"content": "<p>hi</p>", "attachments": []}]}
                           for t in types]}


T = "integrationSchedulePostTool"
check("lúc LIST tool tạo bài hiện ở mức Ghi nháp", mc.classify(con, T, None) == "write")
check("toàn nháp → ghi thường", mc.classify(con, T, bai("draft", "draft")) == "write")
check("tên id cũ schedulePostTool cũng theo luật nháp", mc.classify(con, "schedulePostTool", bai("draft")) == "write")
check("lên lịch → nguy hiểm", mc.classify(con, T, bai("schedule")) == "danger")
check("đăng ngay → nguy hiểm", mc.classify(con, T, bai("now")) == "danger")
check("CANARY: lô trộn 1 bài lên lịch → nguy hiểm", mc.classify(con, T, bai("draft", "draft", "schedule")) == "danger")
for ten, args in [("thiếu socialPost", {}), ("socialPost rỗng", {"socialPost": []}),
                  ("socialPost sai kiểu", {"socialPost": "draft"}),
                  ("phần tử không phải dict", {"socialPost": ["draft"]}),
                  ("thiếu type", {"socialPost": [{"integrationId": "x"}]}),
                  ("type lạ", bai("DRAFT ")), ("args không phải dict", "draft")]:
    got = mc.classify(con, T, args)
    check("CANARY fail-closed: " + ten + " → nguy hiểm", got == "danger", got)
check("type viết hoa vẫn là nháp", mc.classify(con, T, bai("Draft")) == "write")

# Luật an toàn quan trọng nhất của connector này.
check("Ghi nháp tạo được bài nháp", mc.allowed(con, "safe", "full", T, bai("draft"))[0])
check("CANARY: Ghi nháp KHÔNG lên lịch được", not mc.allowed(con, "safe", "full", T, bai("schedule"))[0])
check("CANARY: Ghi nháp KHÔNG đăng ngay được", not mc.allowed(con, "safe", "full", T, bai("now"))[0])
check("CANARY: Chỉ đọc không tạo được cả bài nháp", not mc.allowed(con, "readonly", "full", T, bai("draft"))[0])
check("Toàn quyền mới đăng được", mc.allowed(con, "full", "full", T, bai("now"))[0])
check("CANARY: loop auto không đăng được dù kết nối Toàn quyền",
      not mc.allowed(con, "full", "auto", T, bai("now"))[0])
check("loop auto vẫn tạo nháp được", mc.allowed(con, "full", "auto", T, bai("draft"))[0])
check("CANARY: loop suggest không tạo cả nháp", not mc.allowed(con, "full", "suggest", T, bai("draft"))[0])

# Connector khác không khai draft_rules phải không bị ảnh hưởng.
check("connector khác không dính luật nháp",
      mc.classify(mc.get("n8n"), "execute_workflow", {"socialPost": [{"type": "draft"}]}) == "danger")

if loi:
    print(f"\nFAIL - test_postiz_connector: {len(loi)} lỗi")
    sys.exit(1)
print("\nOK - test_postiz_connector")
