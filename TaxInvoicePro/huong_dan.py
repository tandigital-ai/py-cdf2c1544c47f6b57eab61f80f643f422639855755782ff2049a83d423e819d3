# -*- coding: utf-8 -*-
"""
huong_dan.py - TAX INVOICE PRO v1.7.1
Huong dan su dung day du: man hinh trong ung dung + xuat ban HTML de in.
Tac gia: TDA - 0986509106
"""

import os
import html
import webbrowser
import datetime as dt
import tkinter as tk
from tkinter import ttk, messagebox

try:
    import va_ttk
except Exception:
    pass

import customtkinter as ctk

PHIEN_BAN = "v1.7.1"
TAC_GIA = "TDA"
DIEN_THOAI = "0986509106"
THU_MUC = os.path.dirname(os.path.abspath(__file__))

XANH = "#1565C0"
XANH_DAM = "#0D47A1"
NEN = "#F4F7FB"
TRANG = "#FFFFFF"
XAM = "#64748B"

MUC = [

("Giới thiệu và phạm vi sử dụng", """
TAX INVOICE PRO là phần mềm chạy trên máy tính Windows, dùng để lưu trữ, tra cứu, đối chiếu và kết
xuất báo cáo từ các tệp hóa đơn điện tử định dạng XML mà bạn đã tải về máy.

Phần mềm làm việc ở chế độ ngoại tuyến. Phần mềm không đăng nhập thay bạn vào Cổng Hóa đơn điện tử
của cơ quan thuế, không vượt mã xác nhận, không ký số và không gửi hóa đơn đi đâu. Việc đăng nhập và
tải hóa đơn là thao tác bạn tự làm trên trình duyệt bằng tài khoản thuế của mình; phần mềm nhận các
tệp đã tải về và xử lý chúng.

Dữ liệu chuẩn theo Nghị định 254/2026/NĐ-CP và Thông tư 91/2026/TT-BTC, hiệu lực từ ngày 01/07/2026,
hỗ trợ đủ chín loại mẫu số hóa đơn, trong đó có hóa đơn khởi tạo từ máy tính tiền và hóa đơn của hộ
kinh doanh có mã số thuế mười hai chữ số.

Tệp XML gốc mới là chứng từ có giá trị pháp lý. Bản thể hiện do phần mềm dựng ra, cũng như mọi báo
cáo kết xuất, chỉ phục vụ việc đọc và đối chiếu nội bộ.
"""),

("Cài đặt lần đầu trên máy mới", """
Bước một, cài Python. Tải bộ cài Python bản 64-bit cho Windows từ trang python.org, khi chạy bộ cài
nhớ đánh dấu ô "Add python.exe to PATH" ở màn hình đầu tiên rồi mới bấm Install Now.

Bước hai, chép nguyên thư mục dự án sang máy mới, ví dụ vào D:\\TaxInvoicePro. Thư mục này chứa toàn
bộ tệp .py, thư mục data và thư mục logs.

Bước ba, mở Command Prompt tại thư mục đó. Cách nhanh nhất là mở File Explorer tới thư mục, bấm vào
thanh địa chỉ, gõ chữ cmd rồi nhấn Enter.

Bước bốn, tạo môi trường ảo và cài thư viện bằng ba lệnh sau, chạy lần lượt:

    python -m venv .venv
    .venv\\Scripts\\activate
    pip install customtkinter openpyxl

Nếu muốn xem hóa đơn theo đúng mẫu của nhà cung cấp thì cài thêm lxml bằng lệnh pip install lxml.
Nếu máy không có Internet, bạn chép thư mục .venv từ máy cũ sang là dùng được ngay.

Bước năm, nháy đúp tệp ChayAppMoi.bat. Lần chạy đầu phần mềm tự tạo cơ sở dữ liệu trong thư mục data
và nạp mười hai hóa đơn mẫu để bạn làm quen; xóa chúng đi lúc nào cũng được.
"""),

("Màn hình chính và cách chỉnh cỡ chữ", """
Cửa sổ chia làm ba phần. Thanh trên cùng màu xanh hiển thị tên phần mềm, phiên bản và nhắc rằng phần
mềm đang chạy ngoại tuyến. Cột xanh đậm bên trái là chín mục chức năng. Vùng giữa là nội dung của mục
đang chọn.

Trên laptop màn hình 4K, lần chạy đầu phần mềm tự đo độ phân giải của Windows để chọn mức phóng. Nếu
chữ vẫn chưa vừa mắt, giữ phím Ctrl và bấm dấu bằng để phóng to, Ctrl và dấu trừ để thu nhỏ, Ctrl và
số 0 để trả về mức tự động. Mức bạn chọn cùng kích thước cửa sổ được ghi nhớ cho lần mở sau.

Mọi bảng dữ liệu đều tự giãn cột cho kín bề ngang. Bảng nào nằm trong khung cố định sẽ có một thanh
xám mỏng ngay bên dưới: rê chuột vào đó, con trỏ đổi thành mũi tên hai đầu, giữ chuột trái kéo lên
xuống để chỉnh chiều cao bảng, nháy đúp vào thanh đó để bảng tự vừa đúng số dòng đang có.

Nháy chuột vào tiêu đề cột để sắp xếp tăng dần, nháy lần nữa để đảo chiều.
"""),

("Lấy hóa đơn từ Cổng Thuế về máy", """
Phần việc này bạn làm trên trình duyệt, phần mềm không làm thay.

Mở trang hoadondientu.gdt.gov.vn, đăng nhập bằng tài khoản thuế của đơn vị, nhập mã xác nhận. Vào mục
Tra cứu, chọn Tra cứu hóa đơn điện tử mua vào hoặc bán ra, đặt khoảng thời gian cần lấy, bấm Tìm kiếm.

Khi danh sách hiện ra, bấm Kết xuất XML để tải về một tệp nén chứa các hóa đơn, và bấm Kết xuất Excel
để tải bảng kê của cổng. Trình duyệt thường lưu cả hai vào thư mục Downloads.

Giữ lại tệp Excel của cổng, vì ở mục Đối chiếu và Kiểm tra bạn sẽ dùng nó để so xem cổng có bao nhiêu
hóa đơn còn máy mình đang có bao nhiêu.

Mỗi lần tra cứu, cổng giới hạn khoảng thời gian, nên với cả năm bạn nên tải theo từng tháng hoặc từng
quý, đặt tên tệp rõ ràng rồi nạp lần lượt. Hóa đơn phải lưu trữ mười năm, vì vậy hãy giữ nguyên các
tệp XML gốc, đừng chỉ giữ bản PDF.
"""),

("Nạp hóa đơn vào kho", """
Vào mục Tra cứu và Tải hóa đơn, bấm nút TẢI HÓA ĐƠN. Phần mềm cho bạn chọn một trong các cách: chọn
từng tệp XML, chọn cả thư mục chứa XML, hoặc chọn thẳng tệp ZIP tải từ cổng mà không cần giải nén
trước. Tệp nén lồng nhau tối đa ba lớp đều đọc được.

Sau khi nạp, phần mềm báo số hóa đơn thêm mới, số bị trùng và số lỗi kèm lý do từng tệp. Hóa đơn được
coi là trùng khi giống nhau cả ba yếu tố: mã số thuế người bán, ký hiệu hóa đơn và số hóa đơn. Nạp
cùng một tệp nhiều lần cũng không làm dữ liệu bị nhân đôi.

Bản gốc XML được chép vào kho lưu trữ, sắp theo mã số thuế người bán và theo năm, nên sau này cần xuất
trình cho cơ quan thuế là có ngay.

Nếu muốn khỏi phải nạp tay, vào mục Đối chiếu và Kiểm tra, thẻ Nạp tự động. Ở đó bạn bật bộ quét thư
mục: phần mềm theo dõi thư mục Downloads theo chu kỳ bạn đặt, hễ thấy tệp XML hoặc ZIP mới là tự nạp.
Tệp đã xử lý được nhận diện bằng mã băm nội dung nên đổi tên tệp cũng không bị nạp lại.

Cũng tại thẻ đó có phần hộp thư điện tử. Bạn khai máy chủ IMAP, cổng, địa chỉ hộp thư và chọn khoảng
ngày, phần mềm tải các tệp XML và ZIP đính kèm trong thư về rồi nạp vào kho. Với Gmail và Outlook bạn
phải dùng mật khẩu ứng dụng chứ không phải mật khẩu đăng nhập thường. Mật khẩu được cất trong Windows
Credential Manager của máy bạn, không ghi vào tệp cấu hình.
"""),

("Tra cứu, lọc và xóa dữ liệu", """
Khung THÔNG TIN TRA CỨU có chín ô lọc: mã số thuế người mua, số định danh người mua, ký hiệu hóa đơn,
trạng thái, từ ngày, đến ngày, số hóa đơn, ký hiệu mẫu số và loại hóa đơn. Ô nào để trống thì bỏ qua
điều kiện đó. Khoảng ngày lấy cả ngày đầu và ngày cuối. Tìm theo tên không phân biệt chữ hoa chữ thường.

Nếu bấm TRA CỨU mà không ra kết quả, trước tiên hãy bấm Xóa điều kiện rồi tra lại: thường là do ô mã số
thuế người mua còn giữ giá trị mặc định của đơn vị khác.

Thanh công cụ phía trên bảng cho phép chọn tất cả dòng đang hiển thị, bỏ chọn, tải tệp XML gốc của các
dòng đã chọn ra một thư mục, lưu bản thể hiện, xuất Excel, xóa các dòng đã chọn hoặc xóa toàn bộ kết
quả đang lọc. Bạn cũng có thể chọn dòng rồi nhấn phím Delete, hoặc bấm chuột phải để mở thực đơn nhanh.

Mỗi lần xóa, phần mềm tự sao lưu cơ sở dữ liệu vào thư mục data\\backup và giữ lại mười bản gần nhất.
Lịch sử tra cứu lưu ba trăm lần gần nhất, xem ở mục Lịch sử tra cứu.
"""),

("Xem bản thể hiện hóa đơn", """
Nháy đúp một dòng bất kỳ trong bảng để mở cửa sổ hóa đơn. Cửa sổ trình bày thông tin người bán, người
mua, bảng chi tiết hàng hóa dịch vụ, cộng tiền hàng, tiền thuế giá trị gia tăng, tổng tiền thanh toán,
số tiền bằng chữ, khối chữ ký số của người bán và của cơ quan thuế, cùng phần thông tin kỹ thuật.

Bảng chi tiết hàng hóa kéo cao thấp được bằng thanh xám ngay bên dưới, hóa đơn nhiều dòng vẫn xem thoải
mái. Bốn nút ở đáy cửa sổ lần lượt dùng để in hoặc lưu PDF, lưu bản thể hiện ra tệp HTML, mở tệp XML
gốc và đóng cửa sổ.

Muốn có tệp PDF thì bấm In, trong hộp thoại in chọn máy in tên là Microsoft Print to PDF rồi chọn nơi
lưu. Phần mềm cố ý không tự sinh PDF để bản in luôn đúng với những gì bạn nhìn thấy.

Nếu nhà cung cấp có nhúng mẫu hiển thị riêng vào tệp XML, bạn mở ChayXemMau.bat để xem hóa đơn đúng
theo mẫu của họ, và dùng chế độ so sánh hai hóa đơn cạnh nhau khi cần đối chiếu hóa đơn gốc với hóa
đơn điều chỉnh hoặc thay thế. Chế độ này cần thư viện lxml.
"""),

("Đối chiếu và kiểm tra", """
Thẻ Kiểm tra dữ liệu rà soát toàn kho và liệt kê các điểm cần xử lý: hóa đơn trùng, hóa đơn có tổng
tiền không khớp với tiền hàng cộng thuế, mã số thuế sai định dạng, hóa đơn đã bị thay thế hoặc bị hủy
mà vẫn đang nằm trong số liệu hạch toán, hóa đơn thiếu tệp XML gốc, và hóa đơn mua vào từ năm triệu
đồng trở lên chưa có chứng từ thanh toán không dùng tiền mặt.

Điểm cuối cùng đáng lưu ý nhất vì liên quan trực tiếp đến quyền khấu trừ thuế đầu vào theo Luật Thuế
giá trị gia tăng số 48/2024/QH15 và Điều 26 Nghị định 181/2025/NĐ-CP. Phần mềm chỉ cảnh báo để bạn đi
tìm chứng từ thanh toán, không tự kết luận.

Thẻ Đối chiếu bảng kê Cổng Thuế nhận tệp Excel bạn đã kết xuất từ cổng, tự dò dòng tiêu đề, ánh xạ cột
rồi chỉ ra hóa đơn nào cổng có mà máy chưa có, hóa đơn nào máy có mà cổng không có.

Phần mềm không kiểm tra tính liên tục số hóa đơn mua vào, vì mỗi nhà cung cấp phát hành cho rất nhiều
khách nên số hóa đơn bạn nhận được đứt quãng là chuyện bình thường. Quy tắc này chỉ có ý nghĩa với hóa
đơn bán ra của chính đơn vị bạn.
"""),

("Báo cáo và kê khai, tệp Excel chín sheet", """
Vào mục Báo cáo và Kê khai, chọn kỳ rồi bấm xuất. Tệp Excel kết xuất gồm chín sheet.

Sheet Thông tin ghi lại điều kiện lọc, thời điểm xuất và số liệu tổng quát, dùng để biết tệp này được
tạo từ dữ liệu nào.

Sheet Chi tiết mặt hàng là bảng phẳng, mỗi mặt hàng một dòng với đủ ba mươi tư cột, lặp lại toàn bộ
thông tin đầu hóa đơn ở từng dòng con. Không ô nào bị bỏ trống: chỗ nào hóa đơn gốc không ghi thì điền
quy ước KHÔNG CÓ, số không, hoặc KHÔNG GHI. Nhờ vậy bạn kéo thẳng sang PivotTable hoặc nạp vào phần
mềm kho, phần mềm kế toán mà không phải dọn dữ liệu. Hóa đơn máy tính tiền không ghi chi tiết dòng thì
phần mềm tạo một dòng suy ra từ tổng và ghi rõ ở cột nguồn dòng.

Hai sheet Bảng kê mua vào và Bảng kê bán ra xếp hóa đơn theo từng nhóm thuế suất, mỗi nhóm có dòng cộng
riêng và cuối bảng có dòng tổng cộng. Đây là phần phục vụ kê khai thuế giá trị gia tăng.

Bốn sheet thống kê gồm theo tháng, theo đối tác, theo mặt hàng và theo thuế suất, dùng để nhìn nhanh
biến động và tìm khoản bất thường.

Sheet Tổng hợp kê khai gom số liệu vào đúng các chỉ tiêu trên tờ khai: chỉ tiêu 23 và 24 cho giá trị và
thuế giá trị gia tăng của hàng hóa dịch vụ mua vào, chỉ tiêu 32 và 33 cho hàng hóa dịch vụ bán ra chịu
thuế. Bạn vẫn phải tự đối chiếu với sổ sách trước khi điền tờ khai.

Mọi dòng cộng trong tệp đều là công thức SUM sống, nên khi bạn xóa bớt hay sửa một dòng thì tổng tự cập
nhật. Nếu nghi ngờ công thức sai phạm vi, đóng tệp Excel lại rồi chạy lệnh python va_excel.py kèm đường
dẫn tệp, phần mềm sẽ tính lại toàn bộ phạm vi cộng nhóm và báo đã sửa bao nhiêu ô.

Ngoài Excel còn có bản CSV phẳng cho ai muốn nạp vào hệ thống khác, và gói lưu trữ gồm tệp XML gốc kèm
bảng kê, dùng khi cần nộp hoặc bàn giao hồ sơ.
"""),

("Nhà cung cấp và rủi ro", """
Mục này gom toàn bộ người bán trong kho hóa đơn kèm số hóa đơn và tổng tiền giao dịch. Phần tổng hợp
chạy hoàn toàn ngoại tuyến.

Việc tra cứu tình trạng hoạt động của mã số thuế qua mạng mặc định tắt. Muốn dùng, bạn mở thẻ Hướng dẫn
và Cấu hình, đánh dấu cho phép tra cứu trực tuyến, bấm lưu, rồi quay lại chọn dòng và bấm tra cứu. Kết
quả lưu lại trong số ngày bạn đặt, trong thời gian đó phần mềm không gọi mạng nữa.

Nguồn tra cứu mặc định là một dịch vụ công khai theo mã số thuế. Nhà cung cấp dịch vụ này thông báo
dừng từ ngày 01/03/2027; khi đó bạn chỉ cần sửa ô mẫu địa chỉ sang nguồn thay thế, phần còn lại giữ
nguyên. Mẫu địa chỉ bắt buộc chứa chuỗi {mst}.

Danh sách doanh nghiệp rủi ro thì phần mềm không tự tải. Bạn bấm nút mở trang của cơ quan thuế, tải tệp
Excel về máy rồi nạp vào. Mã số thuế nào vừa nằm trong danh sách vừa là nhà cung cấp của bạn sẽ được tô
đỏ. Kết quả tra cứu chỉ để tham khảo khi rà soát nội bộ; căn cứ chính thức vẫn là tra cứu trực tiếp trên
hệ thống của cơ quan thuế.
"""),

("Thiết lập, sao lưu và chuyển máy", """
Mục Thiết lập cho bạn đổi thư mục lưu trữ hóa đơn, mã số thuế đơn vị, số bản ghi mỗi trang và tên người
dùng hiển thị ở góc trên.

Toàn bộ dữ liệu nằm trong thư mục data: cơ sở dữ liệu taxinvoice.db, các tệp cấu hình dạng json, thư mục
backup và thư mục kho chứa XML gốc. Muốn sao lưu, chỉ cần đóng phần mềm rồi chép nguyên thư mục data
sang ổ cứng ngoài hoặc ổ đĩa mạng. Muốn chuyển sang máy khác, chép cả thư mục dự án kèm thư mục data.

Nên sao lưu định kỳ hằng tháng, và luôn sao lưu trước khi xóa dữ liệu hàng loạt. Hóa đơn điện tử phải
lưu trữ mười năm, nên giữ ít nhất hai bản ở hai nơi khác nhau là cách làm an toàn.
"""),

("Xử lý sự cố thường gặp", """
Cửa sổ vừa hiện lên đã tắt ngay: mở tệp logs\\app.log bằng Notepad và đọc mấy dòng cuối, ở đó ghi rõ lỗi.

Một mục trong cột trái mở ra màn hình trắng hoặc báo lỗi: chạy lệnh python thu_man_hinh.py trong môi
trường ảo, công cụ này kiểm tra từng tệp và từng màn hình rồi ghi kết quả vào logs\\thu_man_hinh.txt.

Nạp XML nhưng hóa đơn không hiện trong bảng: bấm Xóa điều kiện rồi tra cứu lại, vì nhiều khả năng ô mã
số thuế người mua hoặc khoảng ngày đang lọc mất.

Tệp XML báo thiếu trường: mở tệp bằng Notepad xem có phải hóa đơn thật không. Một số tệp tải về chỉ là
bản thể hiện PDF đổi đuôi, không phải XML.

Không xuất được Excel: đóng tệp Excel cùng tên đang mở rồi xuất lại, vì Windows khóa tệp đang mở.

Chữ quá nhỏ hoặc quá to: dùng Ctrl với dấu bằng, dấu trừ và số 0 như đã nói ở phần màn hình chính.

Lỗi liên quan đến tkinter trên Python phiên bản mới: dự án đã có sẵn tệp va_ttk.py xử lý việc này, chỉ
cần giữ nguyên tệp đó trong thư mục.
"""),

("Đóng gói thành tệp chạy trực tiếp", """
Nếu muốn đem phần mềm sang máy không cài Python, bạn đóng gói thành tệp exe. Trong môi trường ảo, cài
công cụ bằng lệnh pip install pyinstaller, sau đó chạy lệnh đóng gói với tham số nhập cửa sổ chính là
khoi_dong.py, bật chế độ không hiện cửa sổ dòng lệnh, và kèm theo các tệp dữ liệu trong thư mục data.

Kết quả nằm trong thư mục dist. Chép cả thư mục đó sang máy đích là chạy được. Lần đầu chạy trên máy
mới, phần mềm tự tạo lại thư mục data nếu chưa có.

Lưu ý một số phần mềm diệt virus hay cảnh báo nhầm với tệp exe tự đóng gói; nếu gặp, bạn thêm ngoại lệ
cho thư mục chứa phần mềm.
"""),

("Tác giả và miễn trừ trách nhiệm", """
Phần mềm TAX INVOICE PRO do TDA phát triển, điện thoại 0986509106.

Phần mềm hỗ trợ tra cứu và lưu trữ hóa đơn điện tử đã có trên máy, dùng cho mục đích công việc hợp pháp.
Người dùng chịu trách nhiệm về tính chính xác của số liệu kê khai với cơ quan thuế. Mọi kết quả kiểm tra,
cảnh báo và báo cáo của phần mềm chỉ mang tính hỗ trợ rà soát, không thay thế ý kiến của người làm kế
toán hay của cơ quan quản lý thuế.

Căn cứ pháp lý được tham chiếu gồm Nghị định 254/2026/NĐ-CP, Thông tư 91/2026/TT-BTC, Luật Thuế giá trị
gia tăng số 48/2024/QH15 và Nghị định 181/2025/NĐ-CP. Khi văn bản thay đổi, bạn nên kiểm tra lại các quy
tắc cảnh báo trước khi dùng số liệu để kê khai.
"""),
]


# ------------------------------------------------------------------ xuat HTML
def tao_html():
    nay = dt.datetime.now().strftime("%d/%m/%Y %H:%M")
    p = []
    p.append("<!DOCTYPE html><html lang='vi'><head><meta charset='utf-8'>")
    p.append("<title>Hướng dẫn sử dụng TAX INVOICE PRO %s</title>" % PHIEN_BAN)
    p.append("""<style>
body{font-family:'Segoe UI',Arial,sans-serif;margin:0;background:#F4F7FB;color:#1F2937;}
.giay{max-width:960px;margin:0 auto;background:#fff;padding:36px 48px;}
h1{color:#0D47A1;margin:0 0 4px;font-size:26px;}
.phu{color:#64748B;margin-bottom:24px;}
h2{color:#1565C0;font-size:18px;margin:28px 0 8px;border-bottom:2px solid #E3F0FD;padding-bottom:6px;}
p{line-height:1.75;margin:10px 0;text-align:justify;}
.ml{background:#E3F0FD;padding:14px 20px;border-radius:8px;margin-bottom:10px;}
.ml a{color:#0D47A1;text-decoration:none;display:block;padding:3px 0;}
.chan{margin-top:34px;border-top:1px solid #CBD5E1;padding-top:12px;color:#64748B;font-size:13px;}
code{background:#F1F5F9;padding:2px 6px;border-radius:4px;font-family:Consolas,monospace;}
@media print{body{background:#fff}.giay{padding:0}}
</style></head><body><div class='giay'>""")
    p.append("<h1>HƯỚNG DẪN SỬ DỤNG TAX INVOICE PRO %s</h1>" % PHIEN_BAN)
    p.append("<div class='phu'>Tác giả: %s &nbsp;•&nbsp; Điện thoại: %s &nbsp;•&nbsp; Bản in ngày %s</div>"
             % (TAC_GIA, DIEN_THOAI, nay))
    p.append("<div class='ml'><b>Mục lục</b>")
    for i, (ten, _) in enumerate(MUC, 1):
        p.append("<a href='#m%d'>%d. %s</a>" % (i, i, html.escape(ten)))
    p.append("</div>")
    for i, (ten, noi_dung) in enumerate(MUC, 1):
        p.append("<h2 id='m%d'>%d. %s</h2>" % (i, i, html.escape(ten)))
        for doan in noi_dung.strip().split("\n\n"):
            p.append("<p>%s</p>" % html.escape(" ".join(doan.split())))
    p.append("<div class='chan'>TAX INVOICE PRO %s — Tác giả: %s — Điện thoại: %s<br>"
             "Phần mềm hỗ trợ tra cứu và lưu trữ hóa đơn điện tử đã có trên máy, "
             "sử dụng cho mục đích công việc hợp pháp.</div>" % (PHIEN_BAN, TAC_GIA, DIEN_THOAI))
    p.append("</div></body></html>")
    return "\n".join(p)


def xuat_html(duong_dan=None, mo=True):
    dd = duong_dan or os.path.join(THU_MUC, "HuongDanSuDung.html")
    with open(dd, "w", encoding="utf-8") as f:
        f.write(tao_html())
    if mo:
        try:
            webbrowser.open("file:///" + dd.replace("\\", "/"))
        except Exception:
            pass
    return dd


# ------------------------------------------------------------------ man hinh
class ManHinhHuongDan(ctk.CTkFrame):

    def __init__(self, master, app=None, **kw):
        super().__init__(master, fg_color=NEN, **kw)
        self.app = app

        dau = ctk.CTkFrame(self, fg_color="transparent")
        dau.pack(fill="x", padx=14, pady=(12, 6))
        ctk.CTkLabel(dau, text="HƯỚNG DẪN SỬ DỤNG",
                     font=("Segoe UI", 18, "bold"), text_color=XANH_DAM).pack(side="left")
        ctk.CTkButton(dau, text="Xuất bản HTML để in", width=170, fg_color=XANH,
                      hover_color=XANH_DAM, command=self.xuat).pack(side="right")
        ctk.CTkButton(dau, text="Mở thư mục phần mềm", width=170, fg_color="#455A64",
                      hover_color="#263238", command=self.mo_thu_muc).pack(side="right", padx=8)

        tim = ctk.CTkFrame(self, fg_color="transparent")
        tim.pack(fill="x", padx=14, pady=(0, 8))
        ctk.CTkLabel(tim, text="Tìm trong hướng dẫn:", font=("Segoe UI", 12)).pack(side="left")
        self.o_tim = ctk.CTkEntry(tim, width=300, placeholder_text="ví dụ: kê khai, IMAP, sao lưu")
        self.o_tim.pack(side="left", padx=8)
        self.o_tim.bind("<Return>", lambda e: self.tim())
        ctk.CTkButton(tim, text="Tìm", width=70, fg_color=XANH_DAM,
                      hover_color=XANH, command=self.tim).pack(side="left")
        self.nhan_tim = ctk.CTkLabel(tim, text="", font=("Segoe UI", 11), text_color=XAM)
        self.nhan_tim.pack(side="left", padx=10)

        chia = ttk.PanedWindow(self, orient="horizontal")
        chia.pack(fill="both", expand=True, padx=14, pady=(0, 6))

        trai = tk.Frame(chia, bg=TRANG, highlightthickness=1, highlightbackground="#CBD5E1")
        phai = tk.Frame(chia, bg=TRANG, highlightthickness=1, highlightbackground="#CBD5E1")
        chia.add(trai, weight=1)
        chia.add(phai, weight=3)

        tk.Label(trai, text="  NỘI DUNG", bg="#E3F0FD", fg=XANH_DAM,
                 anchor="w", font=("Segoe UI", 10, "bold")).pack(fill="x")
        self.ds = tk.Listbox(trai, activestyle="none", borderwidth=0,
                             highlightthickness=0, selectmode="browse")
        cuon_t = ttk.Scrollbar(trai, orient="vertical", command=self.ds.yview)
        self.ds.configure(yscrollcommand=cuon_t.set)
        cuon_t.pack(side="right", fill="y")
        self.ds.pack(fill="both", expand=True, padx=4, pady=4)
        for i, (ten, _) in enumerate(MUC, 1):
            self.ds.insert("end", " %d. %s" % (i, ten))
        self.ds.bind("<<ListboxSelect>>", self.chon)

        self.tb = ctk.CTkTextbox(phai, wrap="word", font=("Segoe UI", 13),
                                 fg_color=TRANG, text_color="#1F2937")
        self.tb.pack(fill="both", expand=True, padx=10, pady=10)

        ctk.CTkLabel(self, text="TAX INVOICE PRO %s  •  Tác giả: %s  •  Điện thoại: %s"
                     % (PHIEN_BAN, TAC_GIA, DIEN_THOAI),
                     font=("Segoe UI", 11), text_color=XAM).pack(pady=(0, 8))

        self.ds.selection_set(0)
        self.hien(0)

    def hien(self, i):
        ten, noi_dung = MUC[i]
        self.tb.configure(state="normal")
        self.tb.delete("1.0", "end")
        than = "\n\n".join(" ".join(d.split()) for d in noi_dung.strip().split("\n\n"))
        self.tb.insert("1.0", "%d. %s\n\n%s\n" % (i + 1, ten.upper(), than))
        self.tb.configure(state="disabled")

    def chon(self, _e=None):
        s = self.ds.curselection()
        if s:
            self.hien(int(s[0]))

    def tim(self):
        tu = (self.o_tim.get() or "").strip().lower()
        if not tu:
            return
        for i, (ten, noi_dung) in enumerate(MUC):
            if tu in ten.lower() or tu in noi_dung.lower():
                self.ds.selection_clear(0, "end")
                self.ds.selection_set(i)
                self.ds.see(i)
                self.hien(i)
                self.nhan_tim.configure(text="Thấy ở mục %d." % (i + 1))
                return
        self.nhan_tim.configure(text="Không thấy từ khóa này.")

    def xuat(self):
        try:
            dd = xuat_html()
            messagebox.showinfo("Đã xuất",
                                "Đã lưu và mở bằng trình duyệt:\n%s\n\n"
                                "Trong trình duyệt bấm Ctrl+P, chọn máy in "
                                "Microsoft Print to PDF để có bản PDF." % dd)
        except Exception as e:
            messagebox.showerror("Lỗi", str(e))

    def mo_thu_muc(self):
        try:
            os.startfile(THU_MUC)
        except Exception:
            messagebox.showinfo("Đường dẫn", THU_MUC)


ManHinh = ManHinhHuongDan
LOP_MAN_HINH = {"huong_dan": ManHinhHuongDan, "huong_dan_su_dung": ManHinhHuongDan}


if __name__ == "__main__":
    ctk.set_appearance_mode("light")
    root = ctk.CTk()
    root.title("TAX INVOICE PRO — Hướng dẫn sử dụng")
    root.geometry("1200x780")
    ManHinhHuongDan(root).pack(fill="both", expand=True)
    root.mainloop()


TEP_DAY_DU = True  # dau hieu tep da duoc dan day du - dung xoa dong nay
