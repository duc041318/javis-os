---
name: Soi repo GitHub
description: Clone một repo GitHub, chạy test, chạy thử lệnh trong README, đối chiếu tài liệu với code thật, kết luận nên dùng hay không.
group: AI
---

# Soi repo GitHub

Biến một link GitHub thành kết luận dùng được: nó là cái gì, có chạy thật không,
tài liệu có khớp code không, có nên cài vào máy mình không.

Nguyên tắc xuyên suốt: **chỉ khẳng định thứ đã chạy thật và thấy tận mắt**. Đọc code
mà chưa chạy thì phải nói rõ là chưa kiểm chứng. Không được suy ra "chắc là chạy được"
từ việc README viết đẹp.

## Khi nào dùng

Kích hoạt khi người dùng dán một link `github.com/<owner>/<repo>` kèm những câu như
"xem github này", "repo này thế nào", "cái này dùng được không", "review giúp",
"có nên cài không", "đánh giá plugin/thư viện này". Cũng dùng khi người dùng hỏi so
sánh vài repo cùng chức năng, hoặc muốn kiểm chứng một con số mà README quảng cáo.

KHÔNG dùng khi người dùng chỉ hỏi kiến thức chung về một dự án nổi tiếng mà không cần
kiểm chứng, hoặc khi họ muốn danh sách repo trending (việc đó của skill khác).

## Chuẩn bị

- Chuẩn hoá link trước: cắt sạch query string (`?fbclid=...`, `?utm_...`), lấy đúng
  `owner/repo`. Link Facebook hay rút gọn thì mở ra lấy link gốc.
- Chọn một thư mục tạm để clone. Không clone vào brain, không clone vào thư mục dự án
  đang làm việc.

## Cách chạy

Clone nông, một lần, đừng chạy song song với việc nặng khác:

```bash
GIT_LFS_SKIP_SMUDGE=1 git clone --depth 1 https://github.com/<owner>/<repo> <thu-muc-tam>
```

Không clone được (repo riêng tư, mạng chặn, môi trường không có git) thì chuyển sang đọc
qua GitHub API hoặc WebFetch, và **nói rõ trong báo cáo là chưa chạy thử được**, mọi nhận
xét lúc đó chỉ là đọc code.

## Quy trình

**Bước 1 - Trinh sát 60 giây.** Lấy các số đo khách quan trước khi đọc chữ:
cây thư mục, tổng dung lượng, số dòng code từng file, ngôn ngữ, giấy phép, commit cuối,
tổng số commit, có `.github/workflows` không, có thư mục test không.
Repo một commit duy nhất và không có CI là tín hiệu prototype, ghi nhận ngay.

**Bước 2 - Đọc README như một danh sách kiểm chứng.** Trích ra hai thứ:
mọi CÂU LỆNH mà README bảo người dùng gõ, và mọi CON SỐ mà README khẳng định
(phần trăm cải thiện, số test, tốc độ, dung lượng). Đây chính là danh sách việc phải
xác minh ở các bước sau, không phải để đọc cho biết.

**Bước 3 - Chạy test đúng cách tài liệu nói.** Đối chiếu số test thực tế với số ghi
trên badge hoặc trong README. Chú ý test phủ tới đâu: nhiều repo chỉ test lớp lõi mà
bỏ trắng lớp CLI hoặc entrypoint, nên lỗi nằm đúng chỗ người dùng chạm vào đầu tiên.

**Bước 4 - Gõ lại y nguyên từng lệnh trong Quick Start và CLI reference.** Không tự sửa
cú pháp cho nó chạy. Lệnh nào lỗi thì ghi lại nguyên văn thông báo lỗi, rồi mới thử tìm
cách gõ đúng để biết là tài liệu sai hay code sai. Đây là bước tìm ra nhiều lỗi nhất.

**Bước 5 - Truy nguồn mọi con số quảng cáo.** Tìm trong code chỗ tính ra con số đó.
Bẫy hay gặp là baseline hằng số cứng (kiểu `baseline = max(x * 15, 30000)`), khiến kết quả
luôn đẹp bất kể đầu vào. Cách kiểm nhanh: chạy công cụ trên một thư mục gần như trống,
nếu vẫn báo cải thiện 99% thì đó là hằng số chứ không phải đo đạc.

**Bước 6 - Sáu phép thử độ bền.** Chạy đủ, cái nào không áp dụng thì bỏ:
- Chạy cùng một lệnh ba lần trên cùng dữ liệu, so kết quả. Khác nhau là công cụ không
  tái lập được, thường do duyệt `set`/`dict` chưa sắp xếp.
- Tạo thư mục thử có `node_modules`, `.venv`, `.git` rồi chạy. Công cụ quét dự án mà không
  lọc thư mục vendor thì trên dự án thật sẽ mô tả thư viện của người khác.
- Chạy với đường dẫn có dấu cách và đường dẫn tiếng Việt có dấu.
- `grep` tìm `os.popen`, `os.system`, `shell=True`, `eval(`, `exec(` và xem có ghép chuỗi
  do người dùng nhập vào không. Có thì đó là lỗ chèn lệnh, nêu thành mục riêng trong báo cáo.
- Thử thiếu dependency tuỳ chọn: nhiều repo quảng cáo "có fallback khi thiếu thư viện X"
  nhưng fallback lại hỏng âm thầm và rơi về giá trị mặc định mà không báo gì.
- Kiểm badge: badge "tests passing" không có `.github/workflows` chỉ là ảnh tĩnh tự gắn.

**Bước 7 - Chốt kết luận theo một trong bốn mức**, nói thẳng, không vòng vo:
- *Nên dùng*: chạy đúng như tài liệu, có CI, có người dùng thật.
- *Dùng được nhưng có điều kiện*: nêu rõ điều kiện và những chỗ phải tự sửa.
- *Chỉ nên tham khảo ý tưởng*: clone về đọc, đừng cài vào quy trình thật.
- *Không nên dùng*: nêu lý do nặng nhất trước.

## Bẫy

- **Đừng đánh giá qua độ đẹp của README.** README chỉn chu, có sơ đồ SVG, có badge là tín
  hiệu marketing chứ không phải tín hiệu chất lượng. Nhiều repo đẹp nhất lại là repo lệch
  tài liệu nhiều nhất.
- **Không chạy script cài đặt của repo lạ.** Cấm chạy `install.sh`, `setup.py install`,
  `npm install` với postinstall, hay bất cứ thứ gì sửa ngoài thư mục tạm. Chỉ chạy test và
  các lệnh đọc dữ liệu. Nếu buộc phải cài mới đánh giá được thì dừng lại, báo người dùng
  và hỏi trước.
- **Cẩn thận với lệnh nhận đường dẫn.** Trước khi truyền đường dẫn vào công cụ của repo,
  xem code có ghép thẳng vào shell không. Có thì chỉ thử bằng đường dẫn vô hại.
- **Sai lệch im lặng nguy hơn crash.** Công cụ nhận sai tham số rồi vẫn trả JSON đẹp là
  lỗi nặng hơn công cụ báo lỗi, vì người dùng sẽ tin vào số sai. Luôn kiểm xem kết quả có
  đúng là của dữ liệu mình đưa vào không.
- **Đừng nói repo hỏng khi mới chỉ đọc code.** Phải chạy ra lỗi mới được kết luận hỏng.

## Định dạng báo cáo

Văn nói tiếng Việt, xưng hô như đang nói chuyện. Không dùng bảng markdown, không dùng ký
tự em dash. Bốn phần theo thứ tự:

1. *Đã kiểm những gì*: một dòng nêu commit, ngày, dung lượng, số dòng code, đã chạy test
   và chạy thử lệnh nào. Để người đọc biết kết luận dựa trên cái gì.
2. *Nó là cái gì*: hai đến bốn câu, kèm một câu công tâm về điểm mạnh thật sự.
3. *Vấn đề tìm được*: mỗi vấn đề một đoạn, mở đầu bằng câu chốt in đậm, sau đó là bằng
   chứng cụ thể (lệnh đã gõ, thông báo lỗi nguyên văn, con số thật). Xếp nặng trước nhẹ sau.
   Không có vấn đề nào thì nói thẳng là không có, đừng bịa cho đủ.
4. *Kết luận và đề xuất*: một trong bốn mức ở bước 7, rồi hai hoặc ba việc cụ thể có thể
   làm tiếp.

## Kiểm chứng

Trước khi gửi báo cáo, tự soát bốn câu:
- Mọi khẳng định "cái này hỏng" có kèm lệnh đã chạy và lỗi thật chưa?
- Con số nào trong README đã đối chiếu, con số nào chưa, đã nói rõ chưa?
- Có nhầm lỗi tài liệu thành lỗi code, hoặc ngược lại không?
- Đã xoá thư mục tạm và mọi file rác tạo ra trong lúc thử chưa?
