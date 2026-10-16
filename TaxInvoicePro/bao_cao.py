# -*- coding: utf-8 -*-
"""
bao_cao.py - TAX INVOICE PRO v1.3.0 - Giai doan 6
Bang ke Excel nhieu sheet, goi luu tru theo ky, so sanh hai hoa don.
Tac gia: TDA - 0986509106
"""
import os
import re
import html
import shutil
import datetime

import doi_chieu as dc

TIEU_DE_DS = ["STT", "Ngày lập", "Mẫu số", "Ký hiệu", "Số hóa đơn",
              "MST người bán", "Tên người bán", "MST người mua",
              "Tiền hàng", "Thuế GTGT", "Tổng thanh toán",
              "Trạng thái", "Loại hóa đơn", "Tệp XML"]


def _ten_an_toan(s):
    return re.sub(r"[^0-9A-Za-z_\-\.]", "_", str(s or ""))[:60]


def _nhan_ky(tu_ngay, den_ngay):
    if tu_ngay and den_ngay:
        return "%s_%s" % (dc.ngay_chuan(tu_ngay).replace("-", ""),
                          dc.ngay_chuan(den_ngay).replace("-", ""))
    return datetime.datetime.now().strftime("%Y%m%d")


# ------------------------------------------------------------ Excel
def xuat_bao_cao(ds, duong_dan, canh_bao=None, tu_ngay=None, den_ngay=None):
    """Xuat bang ke Excel 5 sheet. Tra ve duong dan tep da ghi."""
    from openpyxl import Workbook
    from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
    from openpyxl.utils import get_column_letter

    canh_bao = canh_bao or []
    bang_dong = dc.doc_dong_hang()

    dam = Font(bold=True, color="FFFFFF")
    nen = PatternFill("solid", fgColor="1565C0")
    nen_tong = PatternFill("solid", fgColor="E3F0FD")
    vien = Border(*[Side(style="thin", color="B8C6D6")] * 4)
    giua = Alignment(horizontal="center", vertical="center", wrap_text=True)
    tien = '#,##0'

    wb = Workbook()

    def tao_sheet(ten, tieu_de, rong):
        ws = wb.create_sheet(ten) if wb.sheetnames != ["Sheet"] else wb.active
        ws.title = ten
        ws.append(tieu_de)
        for i, _ in enumerate(tieu_de, 1):
            o = ws.cell(row=1, column=i)
            o.font, o.fill, o.alignment, o.border = dam, nen, giua, vien
            ws.column_dimensions[get_column_letter(i)].width = rong[i - 1]
        ws.freeze_panes = "A2"
        ws.auto_filter.ref = None
        try:
            ws.page_setup.orientation = "landscape"
            ws.page_setup.fitToWidth = 1
            ws.page_setup.fitToHeight = 0
            ws.sheet_properties.pageSetUpPr.fitToPage = True
            ws.print_title_rows = "1:1"
        except Exception:
            pass
        return ws

    # --- Sheet 1: danh sach hoa don
    ws = tao_sheet("Danh sách", TIEU_DE_DS,
                   [5, 12, 7, 10, 12, 15, 38, 15, 14, 13, 15, 12, 18, 40])
    for i, h in enumerate(ds, 1):
        ws.append([i, dc.ngay_vn(h["ngay_lap"]), h["ky_hieu_mau_so"],
                   h["ky_hieu_hoa_don"], h["so_hoa_don"], h["mst_nguoi_ban"],
                   h["ten_nguoi_ban"], h["mst_nguoi_mua"], h["tien_hang"],
                   h["thue_gtgt"], h["tong_tien"], h["trang_thai"],
                   h["loai_hoa_don"] or "", h["duong_dan_xml"]])
    n = len(ds)
    for r in range(2, n + 2):
        for c in (9, 10, 11):
            ws.cell(row=r, column=c).number_format = tien
    if n:
        d = n + 2
        ws.cell(row=d, column=7, value="TỔNG CỘNG").font = Font(bold=True)
        for c in (9, 10, 11):
            col = get_column_letter(c)
            o = ws.cell(row=d, column=c,
                        value="=SUM(%s2:%s%d)" % (col, col, n + 1))
            o.number_format, o.font, o.fill = tien, Font(bold=True), nen_tong
        ws.auto_filter.ref = "A1:N%d" % (n + 1)

    # --- Sheet 2: chi tiet dong hang
    ws2 = tao_sheet("Dòng hàng",
                    ["Ngày lập", "Ký hiệu", "Số HĐ", "Người bán", "STT",
                     "Tên hàng hóa, dịch vụ", "ĐVT", "Số lượng", "Đơn giá",
                     "Thành tiền", "Thuế suất", "Tiền thuế"],
                    [12, 10, 10, 30, 5, 44, 8, 11, 14, 15, 10, 14])
    dong_r = 1
    for h in ds:
        for j, d in enumerate(dc.dong_cua(h, bang_dong), 1):
            ws2.append([dc.ngay_vn(h["ngay_lap"]), h["ky_hieu_hoa_don"],
                        h["so_hoa_don"], h["ten_nguoi_ban"],
                        d.get("stt") or j, d.get("ten", ""), d.get("dvt", ""),
                        d.get("so_luong", 0), d.get("don_gia", 0),
                        d.get("thanh_tien", 0), d.get("thue_suat", ""),
                        d.get("tien_thue", 0)])
            dong_r += 1
    for r in range(2, dong_r + 1):
        for c in (8, 9, 10, 12):
            ws2.cell(row=r, column=c).number_format = '#,##0.###'
    if dong_r > 1:
        ws2.cell(row=dong_r + 1, column=6, value="TỔNG").font = Font(bold=True)
        for c in (10, 12):
            col = get_column_letter(c)
            o = ws2.cell(row=dong_r + 1, column=c,
                         value="=SUM(%s2:%s%d)" % (col, col, dong_r))
            o.number_format, o.font, o.fill = tien, Font(bold=True), nen_tong

    # --- Sheet 3: tong hop theo nha cung cap
    ncc = {}
    for h in ds:
        k = (h["mst_nguoi_ban"], h["ten_nguoi_ban"])
        g = ncc.setdefault(k, [0, 0, 0, 0])
        g[0] += 1
        g[1] += h["tien_hang"]
        g[2] += h["thue_gtgt"]
        g[3] += h["tong_tien"]
    ws3 = tao_sheet("Theo nhà cung cấp",
                    ["STT", "MST người bán", "Tên người bán", "Số hóa đơn",
                     "Tiền hàng", "Thuế GTGT", "Tổng thanh toán"],
                    [5, 16, 46, 12, 16, 15, 17])
    for i, ((mst, ten), g) in enumerate(
            sorted(ncc.items(), key=lambda x: -x[1][3]), 1):
        ws3.append([i, mst, ten, g[0], g[1], g[2], g[3]])
    for r in range(2, len(ncc) + 2):
        for c in (5, 6, 7):
            ws3.cell(row=r, column=c).number_format = tien
    if ncc:
        d = len(ncc) + 2
        ws3.cell(row=d, column=3, value="TỔNG CỘNG").font = Font(bold=True)
        for c in (4, 5, 6, 7):
            col = get_column_letter(c)
            o = ws3.cell(row=d, column=c,
                         value="=SUM(%s2:%s%d)" % (col, col, d - 1))
            o.number_format, o.font, o.fill = tien, Font(bold=True), nen_tong

    # --- Sheet 4: tong hop theo thue suat
    ts = {}
    for h in ds:
        dongs = dc.dong_cua(h, bang_dong)
        if dongs:
            for d in dongs:
                k = str(d.get("thue_suat") or "KHÔNG GHI").strip() or "KHÔNG GHI"
                g = ts.setdefault(k, [0, 0.0, 0.0])
                g[0] += 1
                g[1] += d.get("thanh_tien", 0)
                g[2] += d.get("tien_thue", 0)
        else:
            if h["tien_hang"] > 0 and h["thue_gtgt"] > 0:
                k = "%d%%" % round(h["thue_gtgt"] * 100.0 / h["tien_hang"])
            elif h["thue_gtgt"] == 0:
                k = "KCT / 0%"
            else:
                k = "KHÔNG GHI"
            g = ts.setdefault(k, [0, 0.0, 0.0])
            g[0] += 1
            g[1] += h["tien_hang"]
            g[2] += h["thue_gtgt"]
    ws4 = tao_sheet("Theo thuế suất",
                    ["Thuế suất", "Số dòng/hóa đơn", "Tiền hàng", "Tiền thuế"],
                    [18, 18, 20, 20])
    for k, g in sorted(ts.items()):
        ws4.append([k, g[0], round(g[1]), round(g[2])])
    for r in range(2, len(ts) + 2):
        for c in (3, 4):
            ws4.cell(row=r, column=c).number_format = tien
    if ts:
        d = len(ts) + 2
        ws4.cell(row=d, column=1, value="TỔNG").font = Font(bold=True)
        for c in (2, 3, 4):
            col = get_column_letter(c)
            o = ws4.cell(row=d, column=c,
                         value="=SUM(%s2:%s%d)" % (col, col, d - 1))
            o.number_format, o.font, o.fill = tien, Font(bold=True), nen_tong

    # --- Sheet 5: canh bao
    ws5 = tao_sheet("Cảnh báo",
                    ["Mức", "Loại", "Hóa đơn", "Nội dung cần xử lý"],
                    [9, 18, 28, 90])
    mau_muc = {"Nặng": "FFCDD2", "Vừa": "FFE0B2", "Nhẹ": "E8F5E9"}
    for c in canh_bao:
        ws5.append([c["muc"], c["loai"], c["hoa_don"], c["mo_ta"]])
        o = ws5.cell(row=ws5.max_row, column=1)
        o.fill = PatternFill("solid", fgColor=mau_muc.get(c["muc"], "FFFFFF"))
    if not canh_bao:
        ws5.append(["", "", "", "Không có cảnh báo nào — dữ liệu sạch."])

    # --- trang bia thong tin
    ws0 = wb.create_sheet("Thông tin", 0)
    ws0.column_dimensions["A"].width = 28
    ws0.column_dimensions["B"].width = 62
    thong_tin = [
        ("BẢNG KÊ HÓA ĐƠN ĐIỆN TỬ", ""),
        ("Phần mềm", "TAX INVOICE PRO v1.3.0"),
        ("Tác giả", "TDA - 0986509106"),
        ("Ngày lập báo cáo",
         datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")),
        ("Kỳ dữ liệu", "%s - %s" % (dc.ngay_vn(tu_ngay) or "đầu kỳ",
                                    dc.ngay_vn(den_ngay) or "cuối kỳ")),
        ("Số hóa đơn", len(ds)),
        ("Tổng tiền hàng", sum(h["tien_hang"] for h in ds)),
        ("Tổng thuế GTGT", sum(h["thue_gtgt"] for h in ds)),
        ("Tổng thanh toán", sum(h["tong_tien"] for h in ds)),
        ("Số cảnh báo", len(canh_bao)),
        ("Chuẩn dữ liệu",
         "Nghị định 254/2026/NĐ-CP và Thông tư 91/2026/TT-BTC"),
        ("Ghi chú", "Dữ liệu lấy từ tệp XML do người dùng tải hợp pháp về máy. "
                    "Tệp XML là bản gốc có giá trị pháp lý."),
    ]
    for ten, gt in thong_tin:
        ws0.append([ten, gt])
    ws0["A1"].font = Font(bold=True, size=15, color="1565C0")
    for r in range(2, len(thong_tin) + 1):
        ws0.cell(row=r, column=1).font = Font(bold=True)
    for r in (7, 8, 9):
        ws0.cell(row=r, column=2).number_format = tien

    thu_muc = os.path.dirname(os.path.abspath(duong_dan))
    if thu_muc and not os.path.isdir(thu_muc):
        os.makedirs(thu_muc, exist_ok=True)
    wb.save(duong_dan)
    return duong_dan


# ------------------------------------------------------ goi luu tru
def _html_don_gian(hd, dongs):
    r = ["<!DOCTYPE html><html lang='vi'><head><meta charset='utf-8'>",
         "<title>Hóa đơn %s</title><style>"
         "body{font-family:'Times New Roman',serif;max-width:820px;margin:24px auto;}"
         "h1{font-size:19px;text-align:center;color:#1565C0;}"
         "table{width:100%%;border-collapse:collapse;margin-top:10px;}"
         "th,td{border:1px solid #7a8794;padding:5px 7px;font-size:13px;}"
         "th{background:#E3F0FD;}td.r{text-align:right;}"
         ".th{border:none;padding:2px 0;font-size:13px;}"
         "</style></head><body>" % html.escape(hd["so_hoa_don"]),
         "<h1>HÓA ĐƠN ĐIỆN TỬ</h1>",
         "<table><tr><td class='th'>Mẫu số: <b>%s</b> &nbsp; Ký hiệu: <b>%s</b>"
         " &nbsp; Số: <b>%s</b></td><td class=' th' style='text-align:right;"
         "border:none'>Ngày lập: <b>%s</b></td></tr></table>"
         % (html.escape(hd["ky_hieu_mau_so"]), html.escape(hd["ky_hieu_hoa_don"]),
            html.escape(hd["so_hoa_don"]), dc.ngay_vn(hd["ngay_lap"])),
         "<table><tr><th style='width:50%%'>Người bán</th>"
         "<th>Người mua</th></tr><tr><td>%s<br>MST: %s</td>"
         "<td>%s<br>MST: %s</td></tr></table>"
         % (html.escape(hd["ten_nguoi_ban"]), html.escape(hd["mst_nguoi_ban"]),
            html.escape(hd["ten_nguoi_mua"] or ""),
            html.escape(hd["mst_nguoi_mua"] or ""))]
    r.append("<table><tr><th>STT</th><th>Tên hàng hóa, dịch vụ</th><th>ĐVT</th>"
             "<th>Số lượng</th><th>Đơn giá</th><th>Thành tiền</th></tr>")
    if dongs:
        for i, d in enumerate(dongs, 1):
            r.append("<tr><td>%d</td><td>%s</td><td>%s</td><td class='r'>%s</td>"
                     "<td class='r'>%s</td><td class='r'>%s</td></tr>"
                     % (i, html.escape(d.get("ten", "")),
                        html.escape(d.get("dvt", "")),
                        ("%g" % d.get("so_luong", 0)),
                        dc.fmt_tien(d.get("don_gia", 0)),
                        dc.fmt_tien(d.get("thanh_tien", 0))))
    else:
        r.append("<tr><td colspan='6' style='text-align:center'>"
                 "(không có chi tiết dòng hàng trong kho)</td></tr>")
    r.append("</table><table>"
             "<tr><td style='width:70%%'>Cộng tiền hàng</td><td class='r'>%s</td></tr>"
             "<tr><td>Tiền thuế GTGT</td><td class='r'>%s</td></tr>"
             "<tr><td><b>Tổng tiền thanh toán</b></td><td class='r'><b>%s</b></td></tr>"
             "</table>" % (dc.fmt_tien(hd["tien_hang"]),
                           dc.fmt_tien(hd["thue_gtgt"]),
                           dc.fmt_tien(hd["tong_tien"])))
    r.append("<p style='font-size:11px;color:#667'>Bản thể hiện do TAX INVOICE "
             "PRO lập để xem và lưu nội bộ. Tệp XML mới là bản gốc có giá trị "
             "pháp lý. Tác giả: TDA - 0986509106.</p></body></html>")
    return "".join(r)


def xuat_goi_luu_tru(ds, thu_muc_dich, tu_ngay=None, den_ngay=None,
                     bao_tien_do=None):
    """Tao thu muc goi luu tru: XML goc + ban the hien HTML + danh muc Excel."""
    ky = _nhan_ky(tu_ngay, den_ngay)
    goc = os.path.join(thu_muc_dich, "GoiLuuTru_%s_%s"
                       % (ky, datetime.datetime.now().strftime("%H%M%S")))
    t_xml = os.path.join(goc, "XML_goc")
    t_html = os.path.join(goc, "Ban_the_hien")
    for t in (goc, t_xml, t_html):
        os.makedirs(t, exist_ok=True)

    bang_dong = dc.doc_dong_hang()
    chep, thieu, html_ok = 0, 0, 0
    for i, h in enumerate(ds, 1):
        ten = "HoaDon_%s%s_%s" % (_ten_an_toan(h["ky_hieu_mau_so"]),
                                  _ten_an_toan(h["ky_hieu_hoa_don"]),
                                  _ten_an_toan(h["so_hoa_don"]))
        nguon = h.get("duong_dan_xml") or ""
        if nguon and os.path.exists(nguon):
            try:
                shutil.copyfile(nguon, os.path.join(t_xml, ten + ".xml"))
                chep += 1
            except Exception:
                thieu += 1
        else:
            thieu += 1
        try:
            noi_dung = None
            try:
                import invoice_render
                import xml_parser
                if nguon and os.path.exists(nguon):
                    kq = xml_parser.doc_file_an_toan(nguon)
                    inv = kq[0] if isinstance(kq, tuple) else kq
                    if inv:
                        noi_dung = invoice_render.tao_html(inv) \
                            if hasattr(invoice_render, "tao_html") else None
            except Exception:
                noi_dung = None
            if not noi_dung:
                noi_dung = _html_don_gian(h, dc.dong_cua(h, bang_dong))
            with open(os.path.join(t_html, ten + ".html"), "w",
                      encoding="utf-8") as f:
                f.write(noi_dung)
            html_ok += 1
        except Exception:
            pass
        if bao_tien_do and i % 5 == 0:
            bao_tien_do(i, len(ds))

    danh_muc = os.path.join(goc, "DanhMuc_HoaDon.xlsx")
    xuat_bao_cao(ds, danh_muc, dc.tong_hop_canh_bao(ds), tu_ngay, den_ngay)

    with open(os.path.join(goc, "DOC_TRUOC_KHI_LUU_TRU.txt"), "w",
              encoding="utf-8") as f:
        f.write(
            "GÓI LƯU TRỮ HÓA ĐƠN ĐIỆN TỬ\r\n"
            "Phần mềm: TAX INVOICE PRO v1.3.0 - Tác giả TDA - 0986509106\r\n"
            "Ngày tạo: %s\r\n"
            "Kỳ dữ liệu: %s đến %s\r\n"
            "Số hóa đơn: %d | Chép được XML gốc: %d | Thiếu tệp XML: %d | "
            "Bản thể hiện HTML: %d\r\n\r\n"
            "Thư mục XML_goc chứa tệp gốc có giá trị pháp lý. Thư mục "
            "Ban_the_hien chỉ để xem và in. Tệp DanhMuc_HoaDon.xlsx là bảng kê "
            "tổng hợp kèm danh sách cảnh báo cần xử lý.\r\n"
            % (datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
               dc.ngay_vn(tu_ngay) or "đầu kỳ",
               dc.ngay_vn(den_ngay) or "cuối kỳ",
               len(ds), chep, thieu, html_ok))
    return {"thu_muc": goc, "xml": chep, "thieu_xml": thieu,
            "html": html_ok, "danh_muc": danh_muc}


# -------------------------------------------------- so sanh 2 hoa don
def so_sanh_hai_hoa_don(a, b, duong_dan):
    """Tao tep HTML so sanh hai hoa don canh nhau, to dam cho khac biet."""
    bang_dong = dc.doc_dong_hang()
    truong = [("Ngày lập", "ngay_lap"), ("Mẫu số", "ky_hieu_mau_so"),
              ("Ký hiệu", "ky_hieu_hoa_don"), ("Số hóa đơn", "so_hoa_don"),
              ("MST người bán", "mst_nguoi_ban"),
              ("Tên người bán", "ten_nguoi_ban"),
              ("MST người mua", "mst_nguoi_mua"),
              ("Tiền hàng", "tien_hang"), ("Thuế GTGT", "thue_gtgt"),
              ("Tổng thanh toán", "tong_tien"), ("Trạng thái", "trang_thai"),
              ("Loại hóa đơn", "loai_hoa_don")]
    r = ["<!DOCTYPE html><html lang='vi'><head><meta charset='utf-8'>",
         "<title>So sánh hai hóa đơn</title><style>"
         "body{font-family:Segoe UI,Arial,sans-serif;max-width:1100px;"
         "margin:22px auto;color:#1b2733;}"
         "h1{color:#1565C0;font-size:21px;}"
         "table{width:100%;border-collapse:collapse;margin-bottom:18px;}"
         "th,td{border:1px solid #c7d3e0;padding:6px 9px;font-size:13px;"
         "vertical-align:top;}"
         "th{background:#1565C0;color:#fff;}"
         "td.k{background:#F4F7FB;font-weight:600;width:20%;}"
         "tr.khac td{background:#FFF3CD;font-weight:600;}"
         ".r{text-align:right;}"
         ".ghi{font-size:11px;color:#667;}"
         "</style></head><body><h1>So sánh hai hóa đơn</h1>"]
    r.append("<table><tr><th>Trường dữ liệu</th><th>Hóa đơn A</th>"
             "<th>Hóa đơn B</th></tr>")
    for nhan, khoa in truong:
        va, vb = a.get(khoa, ""), b.get(khoa, "")
        if khoa == "ngay_lap":
            va, vb = dc.ngay_vn(va), dc.ngay_vn(vb)
        elif khoa in ("tien_hang", "thue_gtgt", "tong_tien"):
            va, vb = dc.fmt_tien(va), dc.fmt_tien(vb)
        lop = " class='khac'" if str(va) != str(vb) else ""
        r.append("<tr%s><td class='k'>%s</td><td>%s</td><td>%s</td></tr>"
                 % (lop, nhan, html.escape(str(va)), html.escape(str(vb))))
    chenh = b.get("tong_tien", 0) - a.get("tong_tien", 0)
    r.append("<tr><td class='k'>Chênh lệch B − A</td><td colspan='2' "
             "class='r'><b>%s đ</b></td></tr></table>" % dc.fmt_tien(chenh))

    for ten_hd, hd in (("Hóa đơn A", a), ("Hóa đơn B", b)):
        r.append("<h3 style='color:#0D47A1;font-size:15px'>%s — %s%s số %s</h3>"
                 % (ten_hd, html.escape(hd["ky_hieu_mau_so"]),
                    html.escape(hd["ky_hieu_hoa_don"]),
                    html.escape(hd["so_hoa_don"])))
        r.append("<table><tr><th>STT</th><th>Tên hàng hóa, dịch vụ</th>"
                 "<th>ĐVT</th><th>Số lượng</th><th>Đơn giá</th>"
                 "<th>Thành tiền</th><th>Thuế suất</th></tr>")
        dongs = dc.dong_cua(hd, bang_dong)
        if dongs:
            for i, d in enumerate(dongs, 1):
                r.append("<tr><td>%d</td><td>%s</td><td>%s</td>"
                         "<td class='r'>%g</td><td class='r'>%s</td>"
                         "<td class='r'>%s</td><td>%s</td></tr>"
                         % (i, html.escape(d.get("ten", "")),
                            html.escape(d.get("dvt", "")),
                            d.get("so_luong", 0),
                            dc.fmt_tien(d.get("don_gia", 0)),
                            dc.fmt_tien(d.get("thanh_tien", 0)),
                            html.escape(str(d.get("thue_suat", "")))))
        else:
            r.append("<tr><td colspan='7' style='text-align:center'>"
                     "(không có chi tiết dòng hàng)</td></tr>")
        r.append("</table>")

    r.append("<p class='ghi'>Dòng tô vàng là trường có giá trị khác nhau giữa "
             "hai hóa đơn. Tạo bởi TAX INVOICE PRO v1.3.0 — TDA 0986509106 — "
             "%s.</p></body></html>"
             % datetime.datetime.now().strftime("%d/%m/%Y %H:%M"))
    with open(duong_dan, "w", encoding="utf-8") as f:
        f.write("".join(r))
    return duong_dan
