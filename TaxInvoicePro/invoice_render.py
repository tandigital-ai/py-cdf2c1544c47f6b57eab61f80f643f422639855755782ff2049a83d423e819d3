# -*- coding: utf-8 -*-
"""
invoice_render.py - TAX INVOICE PRO v1.2.0
Tao ban the hien hoa don dien tu dang HTML (de xem va tu in ra PDF bang
chuc nang Ctrl+P cua trinh duyet). Khong tao PDF truc tiep, khong ket noi mang.
Trinh bay theo Nghi dinh 254/2026/ND-CP va Thong tu 91/2026/TT-BTC.
Tac gia: TDA - 0986509106
"""

import html
import os
import re
from datetime import datetime

import tt91

try:
    import qr_mini
except ImportError:
    qr_mini = None

TAC_GIA = "TDA"
DIEN_THOAI = "0986509106"
_CHU_SO = ["không", "một", "hai", "ba", "bốn", "năm", "sáu", "bảy", "tám", "chín"]
_BAC = ["", " nghìn", " triệu", " tỷ", " nghìn tỷ", " triệu tỷ"]


# ----------------------------------------------------------------------
# Dinh dang
# ----------------------------------------------------------------------
def fmt_tien(x, le=0):
    try:
        v = float(x or 0)
    except (TypeError, ValueError):
        return str(x)
    if le == 0 and abs(v - round(v)) < 0.005:
        return "{:,.0f}".format(round(v)).replace(",", ".")
    s = "{:,.{p}f}".format(v, p=max(le, 2)).replace(",", "X").replace(".", ",")
    s = s.replace("X", ".")
    if "," in s:
        s = s.rstrip("0").rstrip(",")
    return s


def fmt_sl(x):
    try:
        v = float(x or 0)
    except (TypeError, ValueError):
        return str(x)
    if abs(v - round(v)) < 1e-9:
        return "{:,.0f}".format(round(v)).replace(",", ".")
    return fmt_tien(v, 2)


def fmt_ngay(s):
    s = (s or "").strip()
    m = re.match(r"(\d{4})-(\d{2})-(\d{2})", s)
    if m:
        return "%s/%s/%s" % (m.group(3), m.group(2), m.group(1))
    return s


def _ngay_chu(s):
    m = re.match(r"(\d{4})-(\d{2})-(\d{2})", (s or "").strip())
    if not m:
        return ""
    return "Ngày %s tháng %s năm %s" % (m.group(3), m.group(2), m.group(1))


def _doc_ba(n, day_du):
    tram, du = divmod(n, 100)
    chuc, dv = divmod(du, 10)
    kq = []
    if tram > 0 or day_du:
        kq.append(_CHU_SO[tram] + " trăm")
    if chuc == 0:
        if dv > 0:
            if tram > 0 or day_du:
                kq.append("lẻ")
            kq.append(_CHU_SO[dv])
    elif chuc == 1:
        kq.append("mười")
        if dv == 1:
            kq.append("một")
        elif dv == 5:
            kq.append("lăm")
        elif dv > 0:
            kq.append(_CHU_SO[dv])
    else:
        kq.append(_CHU_SO[chuc] + " mươi")
        if dv == 1:
            kq.append("mốt")
        elif dv == 4:
            kq.append("tư")
        elif dv == 5:
            kq.append("lăm")
        elif dv > 0:
            kq.append(_CHU_SO[dv])
    return " ".join(kq)


def so_tien_bang_chu(so, don_vi="đồng"):
    try:
        n = int(round(float(so or 0)))
    except (TypeError, ValueError):
        return ""
    am = n < 0
    n = abs(n)
    if n == 0:
        return "Không " + don_vi + " chẵn./."
    nhom = []
    while n > 0:
        n, d = divmod(n, 1000)
        nhom.append(d)
    phan = []
    dau_tien = True
    for i in range(len(nhom) - 1, -1, -1):
        if nhom[i] == 0:
            continue
        phan.append(_doc_ba(nhom[i], not dau_tien) + (_BAC[i] if i < len(_BAC) else ""))
        dau_tien = False
    chu = " ".join(phan).strip()
    chu = re.sub(r"\s{2,}", " ", chu)
    chu = ("Âm " if am else "") + chu[:1].upper() + chu[1:]
    return chu + " " + don_vi + " chẵn./."


# ----------------------------------------------------------------------
# Ma QR
# ----------------------------------------------------------------------
def _svg_tu_ma_tran(m, o=4, vien=4):
    n = len(m)
    canh = (n + vien * 2) * o
    o_den = []
    for y in range(n):
        for x in range(n):
            if m[y][x]:
                o_den.append('<rect x="%d" y="%d" width="%d" height="%d"/>'
                             % ((x + vien) * o, (y + vien) * o, o, o))
    return ('<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" '
            'viewBox="0 0 %d %d"><rect width="%d" height="%d" fill="#fff"/>'
            '<g fill="#000">%s</g></svg>'
            % (canh, canh, canh, canh, canh, canh, "".join(o_den)))


def _qr_svg(du_lieu):
    if not du_lieu or qr_mini is None:
        return ""
    for ten in ("tao_ma_tran", "ma_tran", "tao_qr"):
        ham = getattr(qr_mini, ten, None)
        if callable(ham):
            try:
                return _svg_tu_ma_tran(ham(du_lieu))
            except Exception:
                pass
    ham = getattr(qr_mini, "ve_svg", None)
    if callable(ham):
        try:
            return ham(du_lieu)
        except Exception:
            return ""
    return ""


# ----------------------------------------------------------------------
# Ban the hien HTML
# ----------------------------------------------------------------------
_CSS = """
*{box-sizing:border-box}
body{font-family:"Times New Roman",Times,serif;font-size:13.5px;color:#111;
     margin:0;padding:18px;background:#eef2f7}
.to{max-width:850px;margin:0 auto;background:#fff;padding:26px 30px 18px;
    border:1px solid #d7dee8;box-shadow:0 2px 10px rgba(0,0,0,.08)}
.dau{display:flex;justify-content:space-between;align-items:flex-start;gap:16px}
.dau .trai{font-size:12px;color:#444;line-height:1.5}
.ma-so{border:1px solid #1565c0;border-radius:6px;padding:8px 12px;font-size:12px;
       min-width:235px;line-height:1.7;color:#0d47a1}
.ma-so b{font-size:13px}
h1{font-size:19px;text-align:center;margin:14px 0 2px;letter-spacing:.5px;
   text-transform:uppercase;color:#0d47a1}
.phu{text-align:center;font-size:12px;font-style:italic;color:#555;margin-bottom:2px}
.ngay{text-align:center;font-size:12.5px;font-style:italic;margin-bottom:12px}
.khoi{border:1px solid #cfd8e3;border-radius:6px;padding:9px 12px;margin-bottom:9px}
.khoi .tieu{font-weight:bold;color:#0d47a1;font-size:12px;text-transform:uppercase;
            border-bottom:1px solid #e3e9f2;padding-bottom:3px;margin-bottom:5px}
.hang{display:flex;gap:8px;margin:2px 0}
.hang .nhan{min-width:150px;color:#555}
.hang .gt{flex:1;font-weight:600}
table.ct{width:100%;border-collapse:collapse;margin-top:6px;font-size:12.5px}
table.ct th{background:#1565c0;color:#fff;border:1px solid #0d47a1;padding:5px 4px;
            font-weight:600;text-align:center}
table.ct td{border:1px solid #c6d0dc;padding:4px 5px;vertical-align:top}
.r{text-align:right}.c{text-align:center}
.km{font-style:italic;color:#8a6d00;background:#fffbe9}
.ck{font-style:italic;color:#a33;background:#fff4f4}
.gc{font-style:italic;color:#555;background:#fafafa}
table.tong{width:58%;margin-left:42%;border-collapse:collapse;margin-top:8px;font-size:13px}
table.tong td{padding:3px 6px;border-bottom:1px dotted #c6d0dc}
table.tong td.r{text-align:right;font-weight:600}
.tt{background:#e8f1fc;font-size:14.5px}
.tt td{color:#0d47a1;font-weight:bold;border-bottom:none}
.chu{margin-top:6px;font-style:italic}
table.ts{width:100%;border-collapse:collapse;margin-top:8px;font-size:12px}
table.ts th,table.ts td{border:1px solid #c6d0dc;padding:3px 5px}
table.ts th{background:#f0f4fa;color:#0d47a1}
.ky{display:flex;gap:18px;margin-top:16px}
.ky>div{flex:1;text-align:center;border:1px dashed #a8c0e0;border-radius:6px;
        padding:10px;min-height:92px}
.ky .nhan{font-weight:bold;font-size:12px;color:#0d47a1}
.ky .ok{color:#1b7f3b;font-weight:bold;margin-top:6px;font-size:12px}
.ky .tg{font-size:11.5px;color:#555}
.qr{text-align:center;margin-top:10px}
.qr svg{width:124px;height:124px}
.cb{border:1px solid #f0b400;background:#fff8e1;border-radius:6px;padding:8px 12px;
    margin:10px 0;font-size:12px;color:#7a5600}
.cb b{color:#9a4b00}
.cb ul{margin:5px 0 0 18px;padding:0}
.lq{border:1px solid #9b59b6;background:#f8f1fb;border-radius:6px;padding:8px 12px;
    margin:10px 0;font-size:12.5px;color:#6a2d80}
.chan{margin-top:14px;border-top:1px solid #d7dee8;padding-top:8px;font-size:11.5px;
      color:#555;display:flex;justify-content:space-between;gap:10px;flex-wrap:wrap}
.chan .tg{font-weight:bold;color:#0d47a1}
.in{max-width:850px;margin:10px auto 0;font-size:12px;color:#44607f;text-align:center}
@media print{body{background:#fff;padding:0}.to{border:none;box-shadow:none;
  max-width:100%;padding:0}.in{display:none}}
"""


def _e(x):
    return html.escape(str(x if x is not None else ""))


def _dong_hang(inv):
    for k in ("dong_hang", "lines", "chi_tiet", "hang_hoa"):
        ds = inv.get(k)
        if ds:
            return ds
    return []


def tao_html(inv, tieu_de=None, hien_qr=True, **_bo_qua):
    """Tra ve chuoi HTML ban the hien cua mot hoa don (dict tu xml_parser)."""
    gm = inv.get("giai_ma_ky_hieu") or tt91.giai_ma_ky_hieu(
        inv.get("ky_hieu_mau_so"), inv.get("ky_hieu_hoa_don"),
        (inv.get("ngay_lap") or "")[:4])
    dvt_tien = inv.get("don_vi_tien_te") or "VND"
    ten = tieu_de or inv.get("ten_loai_day_du") or inv.get("ten_hoa_don") \
        or tt91.ten_mau_so(inv.get("ky_hieu_mau_so"))[0]

    dong = _dong_hang(inv)
    co_ck = any(float(d.get("tien_ck") or 0) for d in dong)
    co_ts = any((d.get("thue_suat") or "") not in ("", "\\") for d in dong)
    cot = 6 + (1 if co_ck else 0) + (1 if co_ts else 0)

    hang_html = []
    for d in dong:
        tc = str(d.get("tinh_chat") or "1")
        lop = {"2": " class='km'", "3": " class='ck'", "4": " class='gc'"}.get(tc, "")
        o = ["<td class='c'>%s</td>" % _e(d.get("stt") or "")]
        ten_hang = _e(d.get("ten_hang") or "")
        if tc == "2":
            ten_hang += " <i>(khuyến mại)</i>"
        elif tc == "3":
            ten_hang += " <i>(chiết khấu thương mại)</i>"
        if d.get("ma_hang"):
            ten_hang += "<br><span style='font-size:11px;color:#666'>Mã: %s</span>" \
                        % _e(d.get("ma_hang"))
        o.append("<td>%s</td>" % ten_hang)
        o.append("<td class='c'>%s</td>" % _e(d.get("dvt") or ""))
        if tc == "4":
            o.append("<td colspan='%d'></td>" % (cot - 3))
        else:
            o.append("<td class='r'>%s</td>" % fmt_sl(d.get("so_luong")))
            o.append("<td class='r'>%s</td>" % fmt_tien(d.get("don_gia"), 2))
            if co_ck:
                o.append("<td class='r'>%s</td>" % fmt_tien(d.get("tien_ck")))
            o.append("<td class='r'>%s</td>" % fmt_tien(d.get("thanh_tien")))
            if co_ts:
                o.append("<td class='c'>%s</td>" % _e(d.get("thue_suat") or "\\"))
        hang_html.append("<tr%s>%s</tr>" % (lop, "".join(o)))
    if not hang_html:
        hang_html.append("<tr><td colspan='%d' class='c' style='padding:14px;"
                         "color:#777'><i>Hóa đơn này được nạp từ bảng kê, "
                         "không có chi tiết dòng hàng.</i></td></tr>" % cot)

    th_cot = ["STT", "Tên hàng hóa, dịch vụ", "ĐVT", "Số lượng", "Đơn giá"]
    if co_ck:
        th_cot.append("Chiết khấu")
    th_cot.append("Thành tiền")
    if co_ts:
        th_cot.append("Thuế suất")

    bang_ts = inv.get("thue_theo_suat") or []
    ts_html = ""
    if bang_ts:
        r = ["<tr><th style='width:28%'>Thuế suất</th>"
             "<th>Tiền hàng chưa thuế</th><th>Tiền thuế GTGT</th></tr>"]
        for b in bang_ts:
            r.append("<tr><td class='c'>%s</td><td class='r'>%s</td>"
                     "<td class='r'>%s</td></tr>"
                     % (_e(b.get("thue_suat")), fmt_tien(b.get("tien_hang")),
                        fmt_tien(b.get("tien_thue"))))
        ts_html = ("<table class='ts'><caption style='text-align:left;font-size:12px;"
                   "color:#0d47a1;font-weight:bold;padding:4px 0'>"
                   "Tổng hợp theo từng loại thuế suất</caption>%s</table>"
                   % "".join(r))

    chu = inv.get("tong_tien_chu") or so_tien_bang_chu(
        inv.get("tong_tien"), "đồng" if dvt_tien == "VND" else dvt_tien)

    ky_html = []
    for k in (inv.get("chu_ky") or []):
        ky_html.append(
            "<div><div class='nhan'>Chữ ký số %s</div>"
            "<div class='ok'>%s</div><div>%s</div>"
            "<div class='tg'>%s</div></div>"
            % (_e(k.get("vai_tro")),
               "Đã ký điện tử" if k.get("co_chu_ky") else "(không có giá trị chữ ký)",
               _e(k.get("ten")),
               ("Thời điểm ký: " + _e(k.get("thoi_diem"))) if k.get("thoi_diem") else ""))
    if not ky_html:
        ky_html.append("<div><div class='nhan'>Chữ ký số người bán</div>"
                       "<div class='tg'>Không tìm thấy chữ ký số trong tệp XML</div></div>")

    cb = inv.get("canh_bao") or []
    cb_html = ""
    if cb:
        cb_html = ("<div class='cb'><b>Cảnh báo kiểm tra dữ liệu "
                   "(phần mềm không tự sửa số liệu trên hóa đơn):</b><ul>%s</ul></div>"
                   % "".join("<li>%s</li>" % _e(c) for c in cb))

    lq = inv.get("hoa_don_lien_quan") or {}
    lq_html = ""
    if lq and (lq.get("so_hoa_don") or lq.get("ly_do")):
        lq_html = ("<div class='lq'><b>Hóa đơn %s cho:</b> số %s, ký hiệu %s%s, "
                   "ngày %s%s</div>"
                   % (_e(lq.get("tinh_chat") or "liên quan"),
                      _e(lq.get("so_hoa_don")), _e(lq.get("ma_mau_so") or ""),
                      _e(lq.get("ky_hieu")), fmt_ngay(lq.get("ngay_lap")),
                      (" — Lý do: " + _e(lq.get("ly_do"))) if lq.get("ly_do") else ""))

    qr_html = ""
    if hien_qr and inv.get("ma_qr"):
        svg = _qr_svg(inv.get("ma_qr"))
        if svg:
            qr_html = ("<div class='qr'>%s<div style='font-size:11px;color:#666'>"
                       "Mã QR tra cứu hóa đơn</div></div>" % svg)

    tt_khac = [m for m in (inv.get("thong_tin_khac") or [])
               if (m.get("gia_tri") or "").strip()]
    khac_html = ""
    if tt_khac:
        khac_html = ("<div class='khoi'><div class='tieu'>Thông tin khác</div>%s</div>"
                     % "".join("<div class='hang'><div class='nhan'>%s</div>"
                               "<div class='gt'>%s</div></div>"
                               % (_e(m.get("ten")), _e(m.get("gia_tri")))
                               for m in tt_khac))

    def _h(nhan, gt):
        return ("<div class='hang'><div class='nhan'>%s</div>"
                "<div class='gt'>%s</div></div>" % (nhan, _e(gt))) if gt else ""

    body = """<!DOCTYPE html>
<html lang="vi"><head><meta charset="utf-8">
<title>%(tieu_de)s</title><style>%(css)s</style></head><body>
<div class="to">
 <div class="dau">
  <div class="trai">
   <div><b style="color:#0d47a1;font-size:14px">%(ten_ban)s</b></div>
   <div>Mã số thuế: <b>%(mst_ban)s</b></div>
   <div>%(dc_ban)s</div>
   %(lien_he_ban)s
  </div>
  <div class="ma-so">
   <div>Ký hiệu mẫu số: <b>%(mau_so)s</b></div>
   <div>Ký hiệu hóa đơn: <b>%(ky_hieu)s</b></div>
   <div>Số hóa đơn: <b>%(so_hd)s</b></div>
   %(ma_cqt)s
  </div>
 </div>
 <h1>%(ten_hd)s</h1>
 <div class="phu">(Bản thể hiện của hóa đơn điện tử — không thay thế tệp XML gốc)</div>
 <div class="ngay">%(ngay_chu)s</div>
 %(lq)s
 <div class="khoi">
  <div class="tieu">Người mua hàng</div>
  %(nguoi_mua)s
  %(ten_mua)s%(mst_mua)s%(cccd_mua)s%(dc_mua)s%(ht_tt)s
 </div>
 <table class="ct"><thead><tr>%(th)s</tr></thead><tbody>%(rows)s</tbody></table>
 %(bang_ts)s
 <table class="tong">
  <tr><td>Cộng tiền hàng chưa thuế</td><td class="r">%(tien_hang)s</td></tr>
  %(dong_ck)s
  <tr><td>Tiền thuế giá trị gia tăng</td><td class="r">%(thue)s</td></tr>
  %(dong_phi)s
  <tr class="tt"><td>TỔNG TIỀN THANH TOÁN</td><td class="r">%(tong)s</td></tr>
 </table>
 <div class="chu">Số tiền viết bằng chữ: <b>%(chu)s</b>%(ngoai_te)s</div>
 %(cb)s
 %(khac)s
 <div class="ky">%(ky)s</div>
 %(qr)s
 <div class="chan">
  <div>Hóa đơn điện tử lập theo %(van_ban)s.<br>
   %(giai_ma)s<br>
   Tệp gốc: %(ten_tep)s</div>
  <div style="text-align:right">
   <span class="tg">TAX INVOICE PRO</span><br>
   Tác giả: %(tac_gia)s — Điện thoại: %(dt)s<br>
   Kết xuất lúc %(luc)s</div>
 </div>
</div>
<div class="in">Để lưu thành PDF: nhấn <b>Ctrl + P</b> → chọn máy in
 <b>Microsoft Print to PDF</b> hoặc <b>Save as PDF</b> → Lưu.</div>
</body></html>""" % {
        "css": _CSS,
        "tieu_de": _e("Hoa don %s - %s" % (inv.get("ky_hieu_hoa_don"),
                                           inv.get("so_hoa_don"))),
        "ten_ban": _e(inv.get("ten_nguoi_ban")),
        "mst_ban": _e(inv.get("mst_nguoi_ban")),
        "dc_ban": _e(inv.get("dia_chi_nguoi_ban")),
        "lien_he_ban": "".join(filter(None, [
            ("<div>Điện thoại: %s</div>" % _e(inv.get("sdt_nguoi_ban")))
            if inv.get("sdt_nguoi_ban") else "",
            ("<div>Số tài khoản: %s%s</div>"
             % (_e(inv.get("stk_nguoi_ban")),
                (" — " + _e(inv.get("ngan_hang_nguoi_ban")))
                if inv.get("ngan_hang_nguoi_ban") else ""))
            if inv.get("stk_nguoi_ban") else "",
        ])),
        "mau_so": _e(inv.get("ky_hieu_mau_so")),
        "ky_hieu": _e(inv.get("ky_hieu_hoa_don")),
        "so_hd": _e(inv.get("so_hoa_don")),
        "ma_cqt": ("<div>Mã của cơ quan thuế:<br><b>%s</b></div>"
                   % _e(inv.get("ma_cqt"))) if inv.get("ma_cqt") else "",
        "ten_hd": _e(ten),
        "ngay_chu": _e(_ngay_chu(inv.get("ngay_lap")) or fmt_ngay(inv.get("ngay_lap"))),
        "lq": lq_html,
        "nguoi_mua": _h("Họ tên người mua hàng", inv.get("nguoi_mua_hang")),
        "ten_mua": _h("Tên đơn vị", inv.get("ten_nguoi_mua")),
        "mst_mua": _h("Mã số thuế", inv.get("mst_nguoi_mua")),
        "cccd_mua": _h("Số CCCD", inv.get("cccd_nguoi_mua")),
        "dc_mua": _h("Địa chỉ", inv.get("dia_chi_nguoi_mua")),
        "ht_tt": _h("Hình thức thanh toán", inv.get("hinh_thuc_tt")),
        "th": "".join("<th>%s</th>" % c for c in th_cot),
        "rows": "".join(hang_html),
        "bang_ts": ts_html,
        "tien_hang": fmt_tien(inv.get("tien_hang")),
        "dong_ck": ("<tr><td>Tổng tiền chiết khấu thương mại</td>"
                    "<td class='r'>%s</td></tr>" % fmt_tien(inv.get("chiet_khau")))
                   if float(inv.get("chiet_khau") or 0) else "",
        "dong_phi": ("<tr><td>Tổng tiền phí khác</td><td class='r'>%s</td></tr>"
                     % fmt_tien(inv.get("phi_khac")))
                    if float(inv.get("phi_khac") or 0) else "",
        "thue": fmt_tien(inv.get("thue_gtgt")),
        "tong": fmt_tien(inv.get("tong_tien")) + " " + _e(dvt_tien),
        "chu": _e(chu),
        "ngoai_te": ("" if dvt_tien == "VND"
                     else " <i>(Tỷ giá: %s)</i>" % fmt_tien(inv.get("ty_gia"), 2)),
        "cb": cb_html,
        "khac": khac_html,
        "ky": "".join(ky_html),
        "qr": qr_html,
        "van_ban": _e(tt91.VAN_BAN_AP_DUNG),
        "giai_ma": _e(gm.get("mo_ta") or ""),
        "ten_tep": _e(inv.get("ten_tep") or inv.get("duong_dan_xml") or "(không rõ)"),
        "tac_gia": TAC_GIA,
        "dt": DIEN_THOAI,
        "luc": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
    }
    return body


def ten_tep_html(inv):
    kh = re.sub(r"[^0-9A-Za-z]", "", (inv.get("ky_hieu_day_du")
                                      or inv.get("ky_hieu_hoa_don") or "HD"))
    so = re.sub(r"[^0-9A-Za-z]", "", str(inv.get("so_hoa_don") or "0"))
    return "HoaDon_%s_%s.html" % (kh, so)


def luu_html(inv, thu_muc=None, duong_dan=None, **_bo_qua):
    """Ghi ban the hien ra tep .html, tra ve duong dan tep."""
    if not duong_dan:
        thu_muc = thu_muc or os.getcwd()
        if not os.path.isdir(thu_muc):
            os.makedirs(thu_muc, exist_ok=True)
        duong_dan = os.path.join(thu_muc, ten_tep_html(inv))
        goc, duoi = os.path.splitext(duong_dan)
        i = 1
        while os.path.exists(duong_dan):
            duong_dan = "%s_%d%s" % (goc, i, duoi)
            i += 1
    with open(duong_dan, "w", encoding="utf-8") as f:
        f.write(tao_html(inv))
    return duong_dan


def luu_nhieu_html(danh_sach, thu_muc):
    kq = []
    for inv in danh_sach:
        try:
            kq.append(luu_html(inv, thu_muc))
        except OSError:
            continue
    return kq


# Cac ten goi tuong thich voi phien ban truoc
ban_the_hien_html = tao_html
tao_ban_the_hien = tao_html
tao_html_hoa_don = tao_html
render_html = tao_html
html_hoa_don = tao_html
xuat_html = luu_html
ghi_html = luu_html
xuat_nhieu_html = luu_nhieu_html
doc_so_tien_bang_chu = so_tien_bang_chu
so_thanh_chu = so_tien_bang_chu
dinh_dang_tien = fmt_tien
