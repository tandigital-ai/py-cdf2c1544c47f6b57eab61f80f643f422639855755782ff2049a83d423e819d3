# Báo cáo rà soát TAX INVOICE PRO và lộ trình thương mại hóa

**Kết luận chính: dự án có nền tảng hữu ích cho ứng dụng quản lý hóa đơn ngoại tuyến, nhưng chưa nên phát hành thương mại ở trạng thái hiện tại.** Việc cần ưu tiên không phải là tạo file `.exe`, mà là sửa các lỗi có thể làm mất chứng từ, sai số liệu và đưa ra cảnh báo thuế thiếu căn cứ.

Tôi khuyến nghị **giữ lại phần chức năng có giá trị, tái cấu trúc từng bước, không viết lại toàn bộ ngay từ đầu**.

## 1. Phạm vi và mức độ xác minh

Tôi đã thực hiện:

- Đọc bản mã nguồn công khai trên nhánh `main`, commit **`11820a8c3a897564799667a5c0f107e658e4e2d8`**.
- Kiểm tra cú pháp **42 file Python, khoảng 17.190 dòng**, không tính các file `.bak`.
- Rà soát các luồng chính: XML, ZIP, SQLite, Excel, báo cáo, tra cứu MST, email, khởi động và đóng gói.
- Chạy **14 kiểm tra tái hiện độc lập** bằng dữ liệu giả và CSDL tạm.
- Đối chiếu một số căn cứ pháp lý, kỹ thuật với nguồn chính thức.

**Chưa thực hiện:** chạy đầy đủ giao diện trên Windows, đăng nhập tài khoản thuế, kiểm thử tải trực tiếp, build và nghiệm thu `.exe`, hoặc chứng nhận tuân thủ pháp luật toàn diện. Tôi cũng **chưa sửa mã nguồn hay push thay đổi vào repository của bạn**.

Các vị trí `file.py:dòng` dưới đây thuộc thư mục `TaxInvoicePro` tại commit trên.

---

## 2. Bảng đánh giá tổng thể

| Hạng mục | Điểm đã làm được | Thiếu hoặc chưa đạt | Đánh giá |
|---|---|---|---|
| Ứng dụng desktop | Có Tkinter/CustomTkinter, nhiều màn hình, bộ lọc, bảng dữ liệu | Nhiều lớp tương thích và bản vá làm luồng chạy khó kiểm soát | Có thể tiếp tục phát triển |
| Đọc XML | Đọc thông tin người bán/mua, dòng hàng, thuế suất, mã CQT, quan hệ hóa đơn | Mất độ chính xác tiền; xử lý lỗi từng hóa đơn chưa đầy đủ; chưa thấy kiểm chứng XSD theo phiên bản | Cần sửa lõi |
| Nhập ZIP | Nhập ZIP, có xử lý ZIP lồng trong một luồng nhập | Có tình huống mất XML sau khi xóa thư mục tạm; thiếu hạn mức giải nén | Chưa an toàn để thương mại |
| Lưu trữ SQLite | Có bảng hóa đơn, dòng hàng, chỉ mục, nhật ký và WAL | Sao lưu sai cách với WAL; thiếu giao dịch nguyên tử; khóa hóa đơn chưa đủ | Ưu tiên rất cao |
| Đối chiếu Excel | Có đọc bảng kê, dò tiêu đề, tìm hóa đơn thiếu/thừa | Đối chiếu “khớp” chủ yếu dựa tổng tiền, chưa so sánh đầy đủ thuế và trạng thái | Mới đáp ứng một phần |
| Xuất Excel | Có bảng kê và báo cáo chi tiết | Có formula injection; chưa bảo toàn số tiền thập phân xuyên suốt | Cần gia cố |
| Xem/in hóa đơn | Có HTML, QR, mẫu tự dựng và XSLT | Chưa xuất PDF trực tiếp; XSLT chưa được cô lập an toàn | Có giá trị nhưng còn rủi ro |
| Tải từ cơ quan thuế | Có hướng dẫn người dùng tải bằng trình duyệt rồi nhập | **Chưa có connector đăng nhập, truy vấn, tải ZIP/Excel trực tiếp** | Chưa triển khai theo mục tiêu |
| Nhận hóa đơn email | Có IMAP; dùng Windows Credential Manager | Cần hoàn thiện TLS, timeout, UIDVALIDITY, chống trùng, retry và kiểm thử Windows | Nền tảng tốt |
| Tra cứu người nộp thuế | Có API, cache, danh sách rủi ro | Có suy diễn “đang hoạt động” chỉ từ tên doanh nghiệp; dữ liệu giữa module chưa thống nhất | Chưa đủ tin cậy |
| Cảnh báo thuế | Có nhiều nhóm cảnh báo hữu ích | Cần phiên bản hóa quy tắc, thời điểm hiệu lực, bằng chứng và chuyên gia nghiệp vụ duyệt | Chỉ nên coi là hỗ trợ rà soát |
| Chữ ký số | Đọc được thông tin và sự hiện diện chữ ký | **Chưa xác thực mật mã, chuỗi chứng thư và tình trạng chứng thư** | Không được gọi là đã xác thực |
| Kiểm thử | Có công cụ kiểm tra cú pháp, import, UI, SQLite, Excel | Thiếu bộ dữ liệu chuẩn và kiểm thử hồi quy; một số kiểm tra có thể báo đạt dù chưa kiểm tra thực chất | Chưa đủ làm cổng phát hành |
| Đóng gói `.exe` | Có script PyInstaller, `onedir`/`onefile`, icon | Đường dẫn chưa thống nhất; chép dữ liệu hiện có vào bản phát hành; thiếu quy trình ký và cập nhật | Chưa sẵn sàng phát hành |
| License thương mại | Chưa thấy cơ chế tương ứng trong mã đã rà soát | Thiếu activation, thời hạn, giới hạn thiết bị, quản trị, thu hồi, gia hạn | Phải thiết kế mới |

**Định vị đúng hiện tại:** công cụ desktop nhập–xem–đối chiếu–lưu trữ hóa đơn có sẵn; chưa phải sản phẩm hoàn chỉnh “tự động tải hóa đơn thuế + xác minh + quản trị license”.

---

## 3. Các lỗi đã tái hiện bằng kiểm tra độc lập

Quy ước ưu tiên:

- **P0:** cần chặn phát hành vì nguy cơ mất dữ liệu hoặc lộ dữ liệu nghiêm trọng.
- **P1:** phải xử lý trước khi bán vì ảnh hưởng tính đúng đắn hoặc an toàn.
- Đây là kiểm tra ở cấp hàm/module, không phải kiểm thử toàn bộ giao diện.

| # | Ưu tiên | Vấn đề và vị trí | Kết quả đã tái hiện | Hướng sửa |
|---|---|---|---|---|
| 1 | **P0** | Sao lưu bằng `shutil.copy2()` khi SQLite bật WAL — `kho.py:669–688` | Bản sao lưu thử nghiệm báo **`no such table: hoa_don`**, trong khi DB đang chạy có dữ liệu | Dùng SQLite Backup API; kiểm tra khôi phục và tính toàn vẹn |
| 2 | **P0** | XML trong thư mục tạm bị xóa sau nhập ZIP — `importer.py:149–167` | Khi `tu_chep_xml=False`, nhập thành công, `da_tai=1`, nhưng XML không còn tồn tại | Bắt buộc lưu bền vững chứng từ từ ZIP trước khi hoàn tất nhập |
| 3 | **P0** | XSLT không hạn chế quyền đọc file — `xslt_nhung.py:194–201` | Khi có `lxml`, mẫu thử đọc được một file XML giả bên ngoài hóa đơn | Chặn truy cập file/mạng của XSLT; cô lập xử lý, giới hạn tài nguyên |
| 4 | **P1** | Khóa chống trùng thiếu mẫu số — `xml_parser.py:452–458`, `kho.py:214–219` | Hai bản ghi khác mẫu số nhưng cùng MST/ký hiệu/số bị coi là trùng | Chuẩn hóa định danh đầy đủ; migration có kiểm soát xung đột |
| 5 | **P1** | Không bảo toàn tiền thập phân — `xml_parser.py:406–413`, `kho.py:144–146, 499–508` | Tổng tiền gốc **110,25** lưu và đọc lại thành **110** | Dùng `Decimal`; lưu chính xác, chỉ làm tròn ở bước nghiệp vụ xác định |
| 6 | **P1** | Chuẩn hóa MST không thống nhất | MST chi nhánh có và không có dấu `-` sinh hai khóa khác nhau | Một hàm chuẩn hóa duy nhất; giữ cả giá trị gốc và chuẩn hóa |
| 7 | **P1** | Chấp nhận ngày không tồn tại — `xml_parser.py:133–146` | `2026-02-31` được chấp nhận | Không dùng regex làm đường thoát bỏ qua xác thực lịch |
| 8 | **P1** | Bỏ mất lỗi trong file nhiều hóa đơn — `xml_parser.py:547–562` | File có một hóa đơn đúng và một hóa đơn lỗi chỉ trả về bản đúng, không trả lỗi của bản còn lại | Trả kết quả gồm bản thành công và lỗi từng hóa đơn |
| 9 | **P1** | Dùng kích thước file để kết luận đã có bản gốc — `importer.py:74–77` | Hai file cùng kích thước nhưng khác nội dung bị gộp vào file cũ | So sánh SHA-256; lưu phiên bản khác nội dung |
| 10 | **P1** | Kiểm tra phạm vi xóa bằng `startswith()` — `kho.py:554–559` | Thư mục `archive-other` bị nhận là nằm trong `archive` | Kiểm tra đường dẫn đã resolve và quan hệ cha–con thực sự |
| 11 | **P1** | Tự suy ra trạng thái hoạt động — `mst_tra_cuu.py:441–450` | API chỉ trả tên công ty, hệ thống tạo trạng thái **`00 / an_toan`** | Không có trạng thái từ nguồn thì phải là “Chưa xác định” |
| 12 | **P1** | Excel formula injection — `exporter.py:89–99` | Tên người bán `=1+1` được ghi thành ô công thức | Ép kiểu text cho dữ liệu văn bản không tin cậy; tách công thức do app tạo |
| 13 | **P1** | Đối chiếu báo “khớp” sai — `doi_chieu.py:564–577` | Hai hóa đơn cùng tổng tiền nhưng khác tiền hàng, thuế và trạng thái vẫn báo khớp | So sánh từng trường và xuất loại chênh lệch |
| 14 | **P1** | Ghi hóa đơn không nguyên tử — `kho.py:372–402` | Lỗi ở dòng hàng nhưng phần đầu hóa đơn vẫn tồn tại sau commit tiếp theo | Transaction/savepoint theo hóa đơn; rollback toàn bộ khi lỗi |

### Ba điểm cần hiểu đúng

**Sao lưu hiện tại không thể được coi là bảo hiểm dữ liệu.** `commit()` không đồng nghĩa toàn bộ dữ liệu WAL đã nằm trong file `.db` để sao chép bằng thao tác file thông thường.

**Đọc được XML không đồng nghĩa hóa đơn hợp lệ.** Parser đang đặt mặc định `trang_thai = "Hợp lệ"` tại `xml_parser.py:347`, trong khi chữ ký mới được kiểm tra sự hiện diện. Nên tách thành:

- Đọc được cấu trúc.
- Đạt kiểm tra dữ liệu.
- Kết quả xác thực chữ ký.
- Trạng thái từ nguồn cơ quan thuế.
- Kết quả rà soát nghiệp vụ.

**XSLT cần coi là đầu vào có khả năng thực thi xử lý**, không chỉ là mẫu trang trí. Kiểm tra của tôi chỉ dùng file giả, không đọc dữ liệu riêng tư và không thử đưa dữ liệu ra ngoài.

Mã tham chiếu: [lõi lưu trữ `kho.py`](https://github.com/tandigital-ai/py-cdf2c1544c47f6b57eab61f80f643f422639855755782ff2049a83d423e819d3/blob/11820a8c3a897564799667a5c0f107e658e4e2d8/TaxInvoicePro/kho.py), [bộ đọc XML](https://github.com/tandigital-ai/py-cdf2c1544c47f6b57eab61f80f643f422639855755782ff2049a83d423e819d3/blob/11820a8c3a897564799667a5c0f107e658e4e2d8/TaxInvoicePro/xml_parser.py), [bộ nhập ZIP/XML](https://github.com/tandigital-ai/py-cdf2c1544c47f6b57eab61f80f643f422639855755782ff2049a83d423e819d3/blob/11820a8c3a897564799667a5c0f107e658e4e2d8/TaxInvoicePro/importer.py).

---

## 4. Các rủi ro khác phát hiện qua đọc mã

Các mục sau **không nên đánh đồng với lỗi đã kiểm thử đầy đủ trên Windows**.

### 4.1. Repository công khai chứa dữ liệu vận hành

Trong `data/` có:

- `taxinvoice.db`, `taxinvoice.db-wal`, `taxinvoice.db-shm`.
- Cache tra cứu MST.
- File dữ liệu đã chuyển đổi.
- Cấu hình người dùng.

Tôi chưa xác nhận đây là toàn bộ dữ liệu mẫu hay có dữ liệu khách hàng thật. Tuy nhiên, **đưa các file này vào repository công khai là rủi ro phải kiểm tra ngay**.

Đặc biệt, `dong_goi.py:69–82, 130–132` chép cả thư mục `data` và `config.json` sang bản phát hành `onedir`.

**Hành động:** phát hành từ môi trường build sạch; chỉ đưa cấu hình mặc định và schema. Nếu xác định đã có dữ liệu nhạy cảm công khai, cần xử lý cả lịch sử Git và đánh giá phạm vi lộ, không chỉ xóa file ở commit mới.

### 4.2. Đường dẫn không thống nhất sau khi đóng gói

- `kho.py` nhận biết chế độ frozen và dùng thư mục chứa `.exe`.
- Nhiều module khác dùng trực tiếp thư mục của `__file__`.

Với PyInstaller, đặc biệt `onefile`, các vị trí này có thể khác nhau. Hậu quả có thể gồm đọc nhầm DB, mất cache sau thoát, log rơi vào thư mục giải nén tạm hoặc lỗi quyền ghi.

**Cần một dịch vụ đường dẫn duy nhất cho toàn bộ ứng dụng.**

### 4.3. UI vẫn có tác vụ nặng chạy đồng bộ

`app.py:1084–1114` gọi nhập ZIP/XML trực tiếp trong callback giao diện. Bộ theo dõi thư mục cũng đưa khâu nhập dữ liệu về luồng UI.

Bộ giám sát treo giúp chẩn đoán, **không thay thế kiến trúc xử lý nền**.

Nên dùng worker, hàng đợi kết quả, tiến độ và hủy tác vụ; chỉ cập nhật widget trên luồng UI.

### 4.4. “Cho phép dùng SQLite đa luồng” chưa phải quản lý đồng thời an toàn

`giam_sat.py` thay thế toàn cục `sqlite3.connect`, đặt `check_same_thread=False`.

Cách này không tự bảo đảm các giao dịch không xen kẽ. Nên dùng:

- Một worker ghi DB có thứ tự; hoặc
- Connection riêng theo tác vụ, transaction rõ ràng, timeout và retry có giới hạn.

### 4.5. Bộ kiểm thử hiện tại có thể tạo cảm giác an toàn sai

Ví dụ:

- `kiem_tra_toan_dien.py:426–429`: không có file Excel để kiểm tra vẫn ghi kết quả đạt.
- Phần kiểm tra DB tạo/xóa bảng ngay trong DB tại thư mục dữ liệu ứng dụng.
- Chưa có bộ fixture nghiệp vụ đủ mạnh để phát hiện các lỗi đã tái hiện ở trên.

Kiểm thử phát hành phải dùng DB tạm; phân biệt **PASS / FAIL / SKIP**, không coi “không kiểm tra được” là “đạt”.

### 4.6. Quá nhiều xử lý lỗi im lặng

Qua phân tích cú pháp, có **153 khối bắt `Exception` hoặc bắt trống rồi chỉ `pass`**.

Không phải tất cả đều sai, nhưng với nhập chứng từ và tính toán thuế, cách này làm mất dấu nguyên nhân và có thể biến thất bại thành dữ liệu thiếu mà người dùng không biết.

### 4.7. Các điểm cần kiểm tra tiếp

- Giới hạn số file, dung lượng giải nén, tỷ lệ nén và độ sâu ZIP.
- Luồng theo dõi đang đánh dấu file đã quét kể cả sau một số kết quả lỗi, có nguy cơ không thử lại.
- IMAP không SSL hiện không có bước STARTTLS trước đăng nhập.
- Gói lưu trữ đặt tên theo mẫu số/ký hiệu/số hóa đơn nhưng thiếu MST người bán, có nguy cơ ghi đè giữa các nhà cung cấp.
- Dependency chỉ khai báo cận dưới `>=`, chưa có môi trường build tái lập.
- README hướng dẫn chạy `app.py`, trong khi bản khởi động mới là `khoi_dong.py`; số phiên bản giữa các module không đồng nhất.

---

## 5. Thiết kế đúng cho nghiệp vụ hóa đơn và cảnh báo thuế

### 5.1. Không sửa dữ liệu gốc để “làm cho khớp”

Nên có ba lớp dữ liệu:

| Lớp | Nội dung | Nguyên tắc |
|---|---|---|
| Chứng từ gốc | XML/ZIP/Excel nguyên bản, hash, nguồn, thời điểm nhận | Bất biến; không tự chỉnh sửa |
| Dữ liệu chuẩn hóa | Thông tin hóa đơn, dòng hàng, tiền, quan hệ | Có phiên bản parser; truy ngược được về chứng từ |
| Kết quả kiểm tra | Sai lệch, chữ ký, trạng thái, cảnh báo | Có quy tắc, bằng chứng, thời điểm và phiên bản |

Các giá trị suy ra khi XML thiếu trường phải có cờ như **“suy tính”**, không được trộn với giá trị thực sự có trong XML.

Đối với tiền:

- Dùng `Decimal`, không dùng `float` làm nguồn chân lý.
- Bảo toàn số tiền nguyên tệ và tỷ giá.
- Không cộng chung VND, USD, EUR trước khi có quy tắc quy đổi.
- Phân biệt không chịu thuế, không kê khai tính nộp và thuế suất 0%.
- Kiểm thử riêng hóa đơn điều chỉnh âm, chiết khấu, nhiều thuế suất và làm tròn.

### 5.2. Tình trạng người nộp thuế phải có nguồn và thời điểm

Một bản ghi tra cứu tối thiểu cần:

```text
MST
Mã trạng thái / nội dung nguyên bản
Nguồn tra cứu
Thời điểm tra cứu
Ngày hiệu lực của trạng thái, nếu nguồn cung cấp
Bằng chứng hoặc mã tham chiếu
Kết quả xác định / chưa xác định
```

**Không được suy luận:**

- Có tên doanh nghiệp ⇒ đang hoạt động.
- Đang hoạt động ⇒ mọi hóa đơn đều hợp pháp.
- Hiện đã ngừng hoạt động ⇒ mọi hóa đơn quá khứ đều không hợp lệ.
- Có trong danh sách rủi ro ⇒ tự động loại toàn bộ chi phí và thuế đầu vào.

Các nội dung liên quan khấu trừ/chi phí phải là cảnh báo cần xác minh, có chuyên gia nghiệp vụ duyệt; không tự biến thành quyết định pháp lý chỉ từ cache trạng thái.

### 5.3. Phiên bản hóa căn cứ pháp lý và định dạng XML

Tại thời điểm rà soát **17/10/2026**, nguồn chính thức xác nhận:

- [Nghị định 254/2026/NĐ-CP](https://vanban.chinhphu.vn/?pageid=27160&docid=218689): hiệu lực 01/07/2026.
- [Thông tư 91/2026/TT-BTC](https://vanban.chinhphu.vn/?pageid=27160&docid=219006&classid=1&orggroupid=4): hiệu lực 01/07/2026.
- [Quyết định 1233/QĐ-CT](https://vbpq.mof.gov.vn/Detail?contentType=LegalDocument_VBDH&id=611897&tab=0): ban hành và có hiệu lực 27/08/2026, về thành phần dữ liệu và phương thức truyền nhận.

Mã nguồn đang nhắc cấu trúc kế thừa các quyết định cũ; tôi chưa thấy bộ schema/test thể hiện việc đối chiếu Quyết định 1233.

**Không thể kết luận parser sai toàn bộ chỉ vì thiếu tên văn bản mới.** Nhưng trước thương mại hóa phải lập ma trận tương thích theo phiên bản XML, loại chứng từ, ngày phát sinh và các điều khoản chuyển tiếp.

Nên lưu quy tắc theo cấu trúc:

```text
rule_id · version · effective_from · effective_to
document_reference · applicability · severity · evidence_required
```

Như vậy, cập nhật quy định mới không làm đánh giá sai dữ liệu lịch sử.

---

## 6. Lộ trình bổ sung tải ZIP/Excel từ cơ quan thuế

### Hiện trạng thực tế

- `app.py:795–808`: “tải XML” là **chép file đã có**.
- `app.py:810–825`: “tải PDF” là **xuất HTML rồi hướng dẫn in PDF**.
- `importer.py` ghi rõ không kết nối máy chủ.
- IMAP là kênh lấy email, không phải tải từ cơ quan thuế.

### Phương án đề xuất

| Phương án | Vai trò | Khuyến nghị |
|---|---|---|
| Người dùng tải bằng trình duyệt; app tự nhận file | Dễ ổn định, ít phụ thuộc thay đổi cổng | Hoàn thiện trước để có sản phẩm sử dụng được |
| Tự động hóa trình duyệt có người dùng xác nhận | Hỗ trợ quy trình tải trên tài khoản được ủy quyền | Chỉ triển khai sau kiểm tra điều kiện sử dụng và thử nghiệm thực tế |
| API/tích hợp được cấp quyền | Tích hợp bền vững khi có hợp đồng, tài liệu và quyền truy cập | Ưu tiên nếu thực sự có kênh được phép |

**Không nên giả định có API công khai ổn định chỉ vì tài khoản truy cập được trên trình duyệt.** Không thiết kế vượt CAPTCHA/MFA hoặc né giới hạn của cổng.

Connector nên tách riêng khỏi parser và có:

1. Quản lý từng đơn vị/MST và phạm vi ủy quyền.
2. Phiên đăng nhập bảo vệ bằng cơ chế Windows; không ghi cookie/token vào log.
3. Chia kỳ truy vấn, phân trang, checkpoint và tiếp tục sau gián đoạn.
4. Giới hạn tốc độ, retry có backoff; xử lý hết phiên.
5. Chờ tải hoàn tất, kiểm tra định dạng và hash trước nhập.
6. Nhật ký số bản ghi tìm thấy, số file tải được, số bản nhập thành công và số lỗi.
7. Cách nhập thủ công dự phòng khi cổng thay đổi.

Không gửi tài khoản thuế lên máy chủ license; hai hệ thống này phải độc lập.

---

## 7. Kiến trúc mục tiêu: giữ Python, giảm rủi ro nâng cấp

Tôi đề xuất kiến trúc sau:

```text
Giao diện desktop
        │
Dịch vụ nghiệp vụ / điều phối tác vụ
        ├── Nhập XML / ZIP / Excel / Email / Connector thuế
        ├── Chuẩn hóa và kiểm tra hóa đơn
        ├── Đối chiếu, báo cáo, cảnh báo
        └── Kiểm tra quyền sử dụng
        │
Kho dữ liệu và chứng từ
        ├── SQLite + migration
        ├── File gốc bất biến + SHA-256
        ├── Nhật ký xử lý
        └── Sao lưu / khôi phục
```

### Các quyết định quan trọng

- **Giữ CustomTkinter trong giai đoạn sửa lõi.** Không đổi UI framework cùng lúc với sửa dữ liệu, connector và license.
- Tách UI khỏi SQL, parser và HTTP.
- Thay các bản vá động bằng API nội bộ rõ ràng.
- Đưa chuẩn hóa MST, số tiền, ngày, định danh hóa đơn về một nơi.
- Thêm migration có phiên bản, backup trước migration và đường lui.
- Cấu trúc dữ liệu có `workspace_id` hoặc đơn vị quản lý rõ ràng nếu phục vụ đại lý kế toán nhiều khách hàng.
- Lưu quan hệ hóa đơn gốc/điều chỉnh/thay thế thành dữ liệu có cấu trúc, không chỉ suy lại từ file mỗi lần.

**SQLite vẫn phù hợp cho desktop độc lập.** Nếu cần nhiều máy cùng sửa chung dữ liệu, không nên đơn giản đặt file SQLite trên thư mục mạng; cần kiến trúc dịch vụ dữ liệu riêng.

---

## 8. Kế hoạch đóng gói `.exe` dùng thương mại

### 8.1. Khuyến nghị bản đầu: `onedir` + bộ cài

| Lựa chọn | Ưu điểm | Hạn chế |
|---|---|---|
| PyInstaller `onedir` | Dễ kiểm tra dependency, chẩn đoán, khởi động và cập nhật | Nhiều file, cần bộ cài |
| PyInstaller `onefile` | Dễ gửi một file | Giải nén tạm, khó quản lý đường dẫn, khởi động và chẩn đoán hơn |
| Nuitka | Có thể cân nhắc để tăng chi phí phân tích mã | Build phức tạp hơn; không bảo vệ license tuyệt đối |

**Đề xuất:** PyInstaller `onedir` kết hợp Inno Setup hoặc công cụ installer tương đương. Sau khi ổn định mới cân nhắc `onefile`.

### 8.2. Phân tách chương trình và dữ liệu

```text
Program Files\Vendor\TaxInvoicePro\
    Chương trình và tài nguyên chỉ đọc

%LOCALAPPDATA%\Vendor\TaxInvoicePro\
    CSDL, cấu hình, cache, log, trạng thái license

Thư mục lưu trữ do khách hàng chọn\
    XML/ZIP gốc, chứng từ xuất, bản sao lưu
```

Nếu dùng chung giữa nhiều tài khoản Windows, cần thiết kế `%PROGRAMDATA%` và quyền truy cập riêng, không tự áp dụng mặc định.

### 8.3. Quy trình phát hành bắt buộc

1. Chốt một phiên bản Python được hỗ trợ và lock dependency.
2. Build trên Windows sạch hoặc Windows CI.
3. Chạy test trước build và smoke test trên bản đã đóng gói.
4. Không đóng gói DB/cache/cấu hình thật.
5. Kiểm tra máy không cài Python, đường dẫn tiếng Việt, tài khoản không có quyền admin và nhiều mức DPI.
6. Ký số executable và installer; ký số không bảo đảm tuyệt đối không bị SmartScreen/antivirus cảnh báo.
7. Cập nhật bằng manifest có chữ ký, kiểm tra hash, hỗ trợ rollback.
8. Gỡ cài đặt mặc định không xóa chứng từ khách hàng.

**Không yêu cầu khách hàng tự `pip install` sau khi mua `.exe`.** Chức năng cần `lxml` hoặc thư viện khác phải được đưa vào bản build và kiểm thử từ trước.

---

## 9. Thiết kế license theo thời hạn, thiết bị và số lượng

### 9.1. Tách rõ ba khái niệm

| Khái niệm | Ý nghĩa |
|---|---|
| Thời hạn | 3, 6, 12 hoặc 36 tháng |
| Số thiết bị được kích hoạt | Một license cho 1/3/5… máy |
| Số license được phát hành | Ví dụ đại lý được cấp 100 mã để bán |

**Số thiết bị** khác **số người dùng đồng thời**. Nếu muốn floating license dùng theo số phiên đồng thời, phải thiết kế lease và chính sách mạng khác.

### 9.2. Gói đề xuất

| Gói | Thời hạn | Thiết bị | Quyền chức năng |
|---|---:|---:|---|
| 3 tháng | 3 tháng lịch | Theo đơn hàng | Theo phiên bản |
| 6 tháng | 6 tháng lịch | Theo đơn hàng | Theo phiên bản |
| 1 năm | 12 tháng lịch | Theo đơn hàng | Theo phiên bản |
| 3 năm | 36 tháng lịch | Theo đơn hàng | Theo phiên bản |

Phải quy định rõ:

- Tính hạn từ thanh toán, phát hành hay kích hoạt đầu tiên.
- Gia hạn trước hạn cộng từ ngày hết hạn hiện tại.
- Gia hạn sau hạn tính theo chính sách hợp đồng.
- Mua thêm máy có đồng thời hạn với license chính không.
- “Một tháng” là tháng lịch, không mặc định 30 ngày.
- Gói 3 năm bao gồm cập nhật nghiệp vụ, hỗ trợ và connector trong phạm vi nào.

### 9.3. Kiến trúc cấp phép

```text
Ứng dụng Windows
    ├── Mã license
    ├── Định danh và khóa thiết bị
    └── Chứng nhận quyền sử dụng có chữ ký
                 │ HTTPS
Máy chủ license
    ├── Khách hàng / đơn hàng
    ├── Gói và quyền chức năng
    ├── Kích hoạt thiết bị
    ├── Gia hạn / thu hồi / chuyển máy
    └── Nhật ký quản trị
```

Backend có thể là dịch vụ Python trên hạ tầng phù hợp hoặc một dịch vụ HTTPS nhẹ khác; không cần đưa dữ liệu hóa đơn lên backend chỉ để kiểm tra license.

**Nguyên tắc bảo mật:**

- Chữ ký bất đối xứng, chẳng hạn Ed25519.
- Khóa riêng chỉ nằm trên hệ thống phát hành; `.exe` chỉ có khóa công khai để xác minh.
- Không dùng “ngày hết hạn trong JSON + mã hóa đơn giản” làm cơ chế chính.
- Không chứa một khóa HMAC dùng chung cho toàn bộ khách hàng trong `.exe`.
- Bảo vệ dữ liệu kích hoạt bằng DPAPI/Credential Manager.
- Kiểm tra quyền ở tầng dịch vụ nghiệp vụ, không chỉ ẩn nút giao diện.

### 9.4. Gắn license với thiết bị

Không nên chỉ dùng MAC address: dễ thay đổi, nhiều card mạng, VPN và có thể giả mạo.

Nên kết hợp:

- Khóa riêng của lần cài đặt, được bảo vệ trên Windows.
- Dấu vân tay thiết bị được băm, giảm thu thập thông tin phần cứng thô.
- Chính sách xử lý thay ổ cứng, cài lại Windows, đổi mainboard.
- Luồng deactivate/chuyển máy có nhật ký.

**Không có cơ chế client-side chống sao chép tuyệt đối**, nhất là khi người dùng có quyền quản trị hoặc clone máy ảo. Mục tiêu thực tế là kiểm soát thương mại tốt, hạn chế chia sẻ trái phép và tránh khóa nhầm khách hàng hợp lệ.

### 9.5. Hoạt động offline

Phương án cân bằng ban đầu:

- Kích hoạt online.
- Cấp chứng nhận sử dụng ngắn hạn có chữ ký, ví dụ 7 ngày.
- Kiểm tra lại định kỳ khi có mạng.
- Thời hạn chứng nhận không vượt ngày hết hạn gói.
- Khi offline quá hạn: chuyển sang chế độ hạn chế theo hợp đồng.

Với khách hàng cần offline dài ngày, dùng quy trình challenge–response ký số và chấp nhận rằng thu hồi license không thể có hiệu lực tức thì.

**Nên giữ quyền xem, sao lưu và xuất dữ liệu đã có khi hết hạn**, còn tính năng nhập/tải mới tùy chính sách. Không dùng dữ liệu kế toán của khách hàng làm công cụ ép gia hạn.

### 9.6. Quản lý số lượng license và thiết bị

Các bảng chính:

| Bảng | Nội dung |
|---|---|
| `customers` | Khách hàng, thông tin liên hệ |
| `plans` | Thời hạn và quyền chức năng |
| `licenses` | Trạng thái, thời hạn, giới hạn thiết bị |
| `activations` | Thiết bị đã kích hoạt |
| `license_events` | Gia hạn, chuyển máy, thu hồi |
| `reseller_allocations` | Hạn mức cấp mã cho đại lý, nếu có |
| `audit_logs` | Ai thực hiện thay đổi, khi nào, lý do |

**Điểm kỹ thuật bắt buộc:** kiểm tra và chiếm một suất thiết bị phải là thao tác nguyên tử phía server. Hai máy kích hoạt đồng thời không được cùng vượt qua kiểm tra khi chỉ còn một suất.

Trang quản trị cần MFA, phân quyền, cấp mã theo lô, tìm kiếm theo khách hàng, xem số máy đã dùng, thu hồi/chuyển máy và lịch sử không sửa tùy tiện.

---

## 10. Kế hoạch hành động và điều kiện nghiệm thu

Ước lượng dưới đây giả định **2 lập trình viên có kinh nghiệm, 1 QA tham gia thường xuyên và chuyên gia kế toán–thuế duyệt nghiệp vụ**. Đây là ước lượng lập kế hoạch, chưa phải cam kết tiến độ.

| Giai đoạn | Công việc chính | Điều kiện nghiệm thu | Ước lượng |
|---|---|---|---|
| **0. Bảo vệ dữ liệu** | Rà soát repo công khai; sửa backup; ngăn đóng gói dữ liệu thật; tạm chặn XSLT không an toàn | Khôi phục được DB và chứng từ; bản phát hành sạch | 3–5 ngày |
| **1. Sửa lõi dữ liệu** | Decimal, định danh, transaction, nhập ZIP bền vững, lỗi từng hóa đơn | 14 tình huống đã nêu có test hồi quy và kết quả đúng | 2–3 tuần |
| **2. Chuẩn hóa kiến trúc** | Đường dẫn, worker, migration, loại bỏ logic trùng, log có ngữ cảnh | Không treo UI ở bộ dữ liệu mục tiêu; không ghi dữ liệu dở dang | 1–2 tuần |
| **3. Nghiệp vụ và nguồn dữ liệu** | Đối chiếu đầy đủ; trạng thái NNT; schema; connector được phép | Test bằng dữ liệu đại diện và tài khoản thử nghiệm được ủy quyền | 2–4 tuần |
| **4. License** | Backend, kích hoạt, hạn dùng, giới hạn máy, quản trị, offline | Không vượt suất khi kích hoạt đồng thời; xử lý đổi máy/mất mạng đúng | 2–3 tuần |
| **5. Đóng gói và pilot** | Installer, ký số, cập nhật, rollback, hỗ trợ | Chạy trên máy sạch và qua pilot khách hàng | 1–2 tuần |

Một số việc có thể làm song song. **Khung dự kiến khoảng 10–14 tuần cho bản thương mại đầu tiên có kiểm soát**, với rủi ro tiến độ lớn nhất nằm ở connector cơ quan thuế và phạm vi quy tắc nghiệp vụ.

### Bộ kiểm thử tối thiểu trước khi bán

- XML nhiều nhà cung cấp, namespace, encoding và phiên bản.
- Hóa đơn nhiều thuế suất, ngoại tệ, chiết khấu, điều chỉnh âm, thay thế.
- Nhập lặp không nhân đôi; cùng định danh khác nội dung phải cảnh báo.
- ZIP lồng, ZIP lỗi, file lớn, thiếu dung lượng và lỗi quyền ghi.
- Sao lưu–khôi phục khi WAL hoạt động; crash giữa lúc nhập/migration.
- Excel không biến dữ liệu văn bản thành công thức.
- Kết quả tra cứu thiếu dữ liệu hoặc timeout không trở thành “an toàn”.
- License hết hạn, sai chữ ký, đổi máy, mất mạng, chỉnh giờ, server gián đoạn, kích hoạt đồng thời.
- Cài mới, nâng cấp, rollback, gỡ cài đặt không mất dữ liệu.

Ngoài kỹ thuật, cần rà soát quyền sở hữu mã nguồn, giấy phép dependency, EULA, chính sách dữ liệu, hỗ trợ và trách nhiệm dịch vụ. **Repository public không đồng nghĩa tự động có quyền thương mại hóa mọi thành phần bên trong.**

---

## 11. Đề xuất quyết định ngay

Tôi đề xuất chia sản phẩm thành hai mốc:

### Mốc A — Sản phẩm ngoại tuyến đáng tin cậy

Nhập XML/ZIP/Excel/email, lưu trữ an toàn, đối chiếu đúng, báo cáo, backup/restore, `.exe` và license.

Đây là nền tảng nên hoàn thiện trước.

### Mốc B — Tự động hóa có kiểm soát

Connector thuế, cập nhật trạng thái NNT, xác thực chữ ký nâng cao và các quy tắc nghiệp vụ đã được duyệt.

**Không nên quảng bá trước các chức năng “tải trực tiếp”, “xác thực hóa đơn hợp pháp” hoặc “cảnh báo thuế chính xác” khi chưa có bằng chứng kiểm thử và phạm vi trách nhiệm rõ ràng.**

Để chuyển sang sửa mã, cần chốt thêm bốn đầu vào:

1. Bộ XML/ZIP/Excel đã ẩn thông tin nhạy cảm nhưng giữ nguyên cấu trúc, gồm cả trường hợp đang lỗi.
2. Log lỗi, phiên bản Windows/Python và các bước tái hiện lỗi giao diện.
3. Mô hình sử dụng: một doanh nghiệp hay đại lý kế toán nhiều MST; dữ liệu riêng từng máy hay dùng chung.
4. Chính sách license: số máy cố định hay đồng thời, thời gian offline cho phép, cách chuyển máy và thời điểm bắt đầu tính hạn.

**Ưu tiên đầu tiên của tôi sẽ là một đợt sửa “an toàn dữ liệu và tính đúng đắn”, không phải đóng gói ngay bản hiện tại thành `.exe`.**