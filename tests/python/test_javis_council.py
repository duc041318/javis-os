"""Phòng họp `javis-council` (0.439.0): Javis làm đầu não, Hermes và Muse là thành viên gắn qua MCP.

    python tests/run.py javis_council      (KHÔNG mạng)

Khoá đúng những điều chủ cần tin:
1. Cổng MCP thành viên công khai nhưng tự xác thực: không khoá / khoá sai -> 401; khoá qua header hay `?key=` đều được.
2. Thành viên chỉ thấy việc của mình và cuộc họp có mình.
3. Họp phản biện: ý kiến vòng đang mở độc lập (không thấy của người kia), đủ người thì chờ đầu não, vòng sau mọi người
   thấy toàn bộ ý kiến cũ, hết vòng thì phải chốt.
4. Kho chỉ giữ BĂM của khoá; thu hồi khoá là khoá cũ hết vào được.
5. `javis_council` chỉ chủ dùng.
"""
from _paths import ROOT, SERVER  # noqa: E402,F401
import json
import os
import tempfile

os.environ["JAVIS_STATE_DIR"] = tempfile.mkdtemp(prefix="javis-council-")
os.environ["JAVIS_REQUIRE_LOGIN"] = "1"

from fastapi.testclient import TestClient   # noqa: E402
import config as cfg   # noqa: E402
import main            # noqa: E402
import mcp_hub         # noqa: E402
import plugins_host    # noqa: E402

_fails = []


def check(name, cond, them=""):
    print(("ok   " if cond else "FAIL ") + name + (f"  [{them}]" if them and not cond else ""))
    if not cond:
        _fails.append(name)


_s = cfg.read_settings()
_s["auth"] = {"username": "admin", **dict(zip(("password_hash", "salt"), cfg.hash_password("matkhau123")))}
cfg.write_settings(_s)
plugins_host.invalidate()

# ---- tool của đầu não, lấy từ plugin đã nạp ----
lp = next((p for p in plugins_host._load_all(None)["plugins"] if p.slug == "javis-council"), None)
check("plugin javis-council nạp được", lp is not None, str(plugins_host._load_all(None).get("errors")))
tool = next(t for t in lp.ctx._tools if t["name"] == "javis_council")
brain = lambda **a: tool["handler"](a, lp.ctx)   # noqa: E731
check("javis_council chỉ chủ dùng", "javis_council" in mcp_hub.OWNER_ONLY_TOOLS)
check("status/read/log chỉ cần quyền đọc", tool["op_modes"].get("status") == "readonly"
      and tool["min_mode"] == "safe")


def lay_khoa(txt):
    return next(dong.strip() for dong in txt.splitlines() if dong.strip().startswith("jc_"))


out_h = brain(op="add_member", name="hermes", role="làm việc trên máy tính của chủ")
out_m = brain(op="add_member", name="muse", role="trợ lý Meta trên đám mây")
k_h, k_m = lay_khoa(out_h), lay_khoa(out_m)
check("cấp khoá kèm lệnh gắn Hermes", "hermes mcp add" in out_h)
check("cấp khoá kèm cách gắn Muse", "custom connector" in out_m)
check("tên 'javis' bị từ chối", brain(op="add_member", name="javis").startswith("ERROR"))
kho = json.loads((lp.ctx.data_dir / "council.json").read_text(encoding="utf-8"))
check("kho KHÔNG giữ khoá thô", k_h not in json.dumps(kho) and k_m not in json.dumps(kho))

la = TestClient(main.app)
URL = "/ext/javis-council/mcp"


def rpc(method, params=None, key=None, qs=False, rid=1):
    h = {} if (key is None or qs) else {"authorization": f"Bearer {key}"}
    u = URL + (f"?key={key}" if qs and key else "")
    return la.post(u, json={"jsonrpc": "2.0", "id": rid, "method": method, "params": params or {}}, headers=h)


def call(key, name, **args):
    r = rpc("tools/call", {"name": name, "arguments": args}, key)
    res = r.json()["result"]
    return res["content"][0]["text"], res["isError"]


# ---- 1. xác thực ----
check("không khoá -> 401", rpc("initialize").status_code == 401)
check("khoá sai -> 401", rpc("initialize", key="jc_sai").status_code == 401)
r = rpc("initialize", {"protocolVersion": "2025-06-18"}, key=k_h)
check("initialize bằng header", r.status_code == 200 and r.json()["result"]["serverInfo"]["name"] == "javis-council")
check("initialize kèm hướng dẫn cho thành viên", "council_inbox" in r.json()["result"]["instructions"])
r = rpc("tools/list", key=k_m, qs=True)
check("khoá qua ?key= (cho Muse chỉ nhận URL)", r.status_code == 200
      and {t["name"] for t in r.json()["result"]["tools"]} >= {"council_inbox", "council_meeting_reply"})
check("notification -> 202", la.post(URL, json={"jsonrpc": "2.0", "method": "notifications/initialized"},
                                     headers={"authorization": f"Bearer {k_h}"}).status_code == 202)
check("GET -> 405 (không SSE)", la.get(URL, headers={"authorization": f"Bearer {k_h}"}).status_code == 405)
check("trang nhật ký đòi đăng nhập", la.get("/ext/javis-council/").status_code == 401)

# ---- 2. giao việc ----
out = brain(op="assign", to="hermes", title="Tóm tắt 3 dự án đất nền Sóc Sơn",
            detail="Đọc file trên máy, trả về bảng giá và pháp lý.")
check("giao việc T..", "T" in out and "Hermes" in out)
tid = next(w for w in out.replace(".", " ").split() if w.startswith("T") and w[1:].isdigit())
txt, _ = call(k_h, "council_inbox")
check("Hermes thấy việc", tid in txt and "Sóc Sơn" in txt)
txt, _ = call(k_m, "council_inbox")
check("Muse KHÔNG thấy việc của Hermes", tid not in txt)
txt, err = call(k_m, "council_task_update", id=tid, status="xong", text="mạo danh")
check("Muse không cập nhật được việc của Hermes", err)
call(k_h, "council_task_update", id=tid, status="dang_lam", text="đang đọc file")
call(k_h, "council_task_update", id=tid, status="xong", text="Dự án A 12tr/m2, sổ đỏ từng lô.")
st = brain(op="status")
check("đầu não thấy việc chờ mình", "VIỆC CHỜ ĐẦU NÃO" in st and tid in st)
check("đầu não đọc kết quả, có rào 'là dữ liệu'", "12tr/m2" in brain(op="read", id=tid)
      and "DỮ LIỆU" in brain(op="read", id=tid))
check("đọc rồi thì hết chờ", tid not in brain(op="status").split("VIỆC CHỜ")[-1].split("Nhật ký")[0]
      if "VIỆC CHỜ" in brain(op="status") else True)

# ---- 3. họp phản biện ----
out = brain(op="meet", topic="Kênh bán đất nền quý tới", goal="Chọn 1 kênh chính",
            proposal="Dồn ngân sách vào Facebook Ads.", max_rounds=2)
mid = next(w for w in out.replace(",", " ").split() if w.startswith("H") and w[1:].isdigit())
txt, _ = call(k_h, "council_inbox")
check("Hermes được mời họp", mid in txt and "Facebook Ads" in txt)
call(k_h, "council_meeting_reply", id=mid, stance="phan_doi", reasoning="CPL Facebook đang tăng.",
     alternative="Zalo OA + môi giới")
txt, _ = call(k_m, "council_read", id=mid)
check("Muse KHÔNG thấy ý kiến của Hermes ở vòng đang mở", "CPL Facebook" not in txt)
txt, err = call(k_m, "council_meeting_reply", id=mid, stance="ok", reasoning="x")
check("stance lạ bị từ chối", err)
txt, _ = call(k_m, "council_meeting_reply", id=mid, stance="dong_y_mot_phan", reasoning="Facebook vẫn rẻ ở Hà Nội.")
check("đủ người -> chờ đầu não", "chờ đầu não" in txt)
check("status báo họp chờ đầu não", mid in brain(op="status"))
brain(op="next_round", id=mid, proposal="Facebook 60%, Zalo OA 40%.", note="Tiếp thu ý CPL của Hermes.")
txt, _ = call(k_m, "council_read", id=mid)
check("vòng 2: thấy toàn bộ ý kiến vòng 1", "CPL Facebook" in txt and "Vòng 2" in txt)
call(k_h, "council_meeting_reply", id=mid, stance="dong_y", reasoning="Hợp lý.")
call(k_m, "council_meeting_reply", id=mid, stance="dong_y", reasoning="Đồng ý.")
check("mọi người đồng ý -> gợi ý chốt", "nên chốt" in brain(op="status"))
check("hết vòng thì không mở thêm", brain(op="next_round", id=mid, proposal="x").startswith("ERROR"))
out = brain(op="conclude", id=mid, decision="Facebook 60%, Zalo OA 40%, xem lại sau 4 tuần.")
check("chốt có kết luận", "KẾT LUẬN" in out)
txt, err = call(k_h, "council_meeting_reply", id=mid, stance="phan_doi", reasoning="muộn")
check("chốt rồi không nhận góp ý", err)

# ---- 4. nhắn đầu não, nhật ký, thu hồi khoá ----
call(k_m, "council_message", text="Đối thủ vừa giảm giá 5%.")
log = brain(op="log")
check("nhật ký bằng chữ đủ các bên", "Javis" in log and "Hermes" in log and "Muse" in log and "giảm giá" in log)
brain(op="remove_member", name="muse")
check("thu hồi khoá -> 401", rpc("tools/list", key=k_m).status_code == 401)

chu = TestClient(main.app)
chu.post("/auth/login", data={"username": "admin", "password": "matkhau123"})
r = chu.get("/ext/javis-council/")
check("chủ đọc trang nhật ký", r.status_code == 200 and "PHÒNG HỌP" in r.text)

print(f"\n{'FAIL' if _fails else 'PASS'}: {len(_fails)} lỗi")
raise SystemExit(1 if _fails else 0)
