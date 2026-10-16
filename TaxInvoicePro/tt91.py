# -*- coding: utf-8 -*-
"""
tt91.py - TAX INVOICE PRO
Danh muc mau so / ky hieu / thue suat hoa don dien tu theo:
  - Nghi dinh 254/2026/ND-CP (30/06/2026)
  - Thong tu 91/2026/TT-BTC (30/06/2026), hieu luc 01/07/2026
Tac gia: TDA - 0986509106
"""

import re

VAN_BAN_AP_DUNG = (
    "Nghị định 254/2026/NĐ-CP và Thông tư 91/2026/TT-BTC "
    "(hiệu lực từ 01/07/2026)"
)

# Ky hieu mau so hoa don: 1 chu so tu nhien 1..9 (Dieu 4 Thong tu 91/2026/TT-BTC)
MAU_SO = {
    "1": ("Hóa đơn giá trị gia tăng", "Hóa đơn GTGT"),
    "2": ("Hóa đơn bán hàng", "Hóa đơn bán hàng"),
    "3": ("Hóa đơn bán tài sản công", "Bán tài sản công"),
    "4": ("Hóa đơn bán hàng dự trữ quốc gia", "Hàng dự trữ quốc gia"),
    "5": ("Tem, vé, thẻ, phiếu thu điện tử và chứng từ điện tử khác "
          "có nội dung của hóa đơn", "Tem, vé, thẻ điện tử"),
    "6": ("Phiếu xuất kho kiêm vận chuyển nội bộ điện tử, "
          "phiếu xuất kho hàng gửi bán đại lý điện tử", "Phiếu xuất kho"),
    "7": ("Hóa đơn thương mại điện tử", "Hóa đơn thương mại"),
    "8": ("Hóa đơn giá trị gia tăng tích hợp biên lai thu thuế, phí, lệ phí",
          "HĐ GTGT kiêm biên lai"),
    "9": ("Hóa đơn bán hàng tích hợp biên lai thu thuế, phí, lệ phí",
          "HĐ bán hàng kiêm biên lai"),
}

# Ky tu dau tien cua ky hieu hoa don
CO_MA = {
    "C": "Có mã của cơ quan thuế",
    "K": "Không có mã của cơ quan thuế",
}

# Ky tu thu 4 cua ky hieu hoa don
LOAI_CHU = {
    "T": "Doanh nghiệp, tổ chức, hộ kinh doanh, cá nhân kinh doanh "
         "đăng ký sử dụng với cơ quan thuế",
    "D": "Hóa đơn bán tài sản công, hàng dự trữ quốc gia hoặc hóa đơn đặc thù "
         "không nhất thiết có một số tiêu thức",
    "L": "Hóa đơn của cơ quan thuế cấp theo từng lần phát sinh",
    "M": "Hóa đơn điện tử được khởi tạo từ máy tính tiền",
    "N": "Phiếu xuất kho kiêm vận chuyển nội bộ điện tử",
    "B": "Phiếu xuất kho hàng gửi bán đại lý điện tử",
    "G": "Tem, vé, thẻ điện tử là hóa đơn giá trị gia tăng",
    "H": "Tem, vé, thẻ điện tử là hóa đơn bán hàng",
    "X": "Hóa đơn thương mại điện tử",
    "F": "Hóa đơn giá trị gia tăng kiêm tờ khai hoàn thuế",
}

# Thue suat dac biet (khong phai con so)
THUE_SUAT_CHU = {
    "KCT": "Không chịu thuế GTGT",
    "KKKNT": "Không kê khai, tính nộp thuế GTGT",
    "KHAC": "Thuế suất khác",
    "\\": "Không áp dụng thuế suất",
}

# Tinh chat dong hang (truong TChat)
TINH_CHAT = {
    "1": "Hàng hóa, dịch vụ",
    "2": "Khuyến mại",
    "3": "Chiết khấu thương mại",
    "4": "Ghi chú, diễn giải",
    "5": "Hàng hóa, dịch vụ (phụ)",
}

# Tinh chat hoa don lien quan (truong TCHDon trong TTHDLQuan)
TC_HOA_DON = {"1": "Thay thế", "2": "Điều chỉnh"}


def ten_mau_so(ma):
    """Tra ve (ten day du, ten ngan) cua mot ma mau so."""
    ma = (str(ma or "").strip())[:1]
    return MAU_SO.get(ma, ("Loại hóa đơn khác", "Loại khác"))


def loai_ngan(ma_mau_so, ten_hoa_don=""):
    """Nhan loai hoa don dung cho bang danh sach va bo loc cua ung dung."""
    ma = (str(ma_mau_so or "").strip())[:1]
    if ma in ("1", "8"):
        return "Hóa đơn GTGT"
    if ma in ("2", "9"):
        return "Hóa đơn bán hàng"
    if ma in MAU_SO:
        return MAU_SO[ma][1]
    t = (ten_hoa_don or "").lower()
    if "giá trị gia tăng" in t:
        return "Hóa đơn GTGT"
    if "bán hàng" in t:
        return "Hóa đơn bán hàng"
    return "Loại khác"


def giai_ma_ky_hieu(ma_mau_so, ky_hieu, nam_lap=None):
    """Giai ma cap (mau so, ky hieu) theo Dieu 4 Thong tu 91/2026/TT-BTC.

    Tra ve dict mo ta + danh sach canh bao (khong tu sua du lieu).
    """
    ms = (str(ma_mau_so or "").strip())[:1]
    kh = (str(ky_hieu or "").strip()).upper()
    cb = []
    kq = {
        "mau_so": ms,
        "ky_hieu": kh,
        "day_du": (ms + kh) if ms else kh,
        "ten_loai": ten_mau_so(ms)[0],
        "ten_loai_ngan": ten_mau_so(ms)[1],
        "co_ma": "",
        "mo_ta_co_ma": "",
        "nam": "",
        "chu_loai": "",
        "mo_ta_loai": "",
        "hau_to": "",
        "tu_may_tinh_tien": False,
        "mo_ta": "",
        "canh_bao": cb,
    }
    if ms and ms not in MAU_SO:
        cb.append("Ký hiệu mẫu số hóa đơn '%s' không thuộc 9 loại quy định "
                  "tại Thông tư 91/2026/TT-BTC." % ms)
    if not kh:
        cb.append("Hóa đơn không có ký hiệu hóa đơn.")
        return kq
    if len(kh) != 6:
        cb.append("Ký hiệu hóa đơn '%s' có %d ký tự, quy định là 6 ký tự."
                  % (kh, len(kh)))
    if len(kh) >= 1:
        kq["co_ma"] = kh[0]
        kq["mo_ta_co_ma"] = CO_MA.get(kh[0], "")
        if kh[0] not in CO_MA:
            cb.append("Ký tự đầu của ký hiệu phải là C hoặc K, đang là '%s'." % kh[0])
    if len(kh) >= 3:
        kq["nam"] = kh[1:3]
        if not kh[1:3].isdigit():
            cb.append("Ký tự thứ 2-3 phải là 2 chữ số của năm lập hóa đơn.")
        elif nam_lap:
            try:
                if kh[1:3] != str(int(nam_lap))[-2:]:
                    cb.append("Năm trong ký hiệu (%s) khác năm lập hóa đơn (%s)."
                              % (kh[1:3], nam_lap))
            except (TypeError, ValueError):
                pass
    if len(kh) >= 4:
        c = kh[3]
        kq["chu_loai"] = c
        kq["mo_ta_loai"] = LOAI_CHU.get(c, "")
        kq["tu_may_tinh_tien"] = (c == "M")
        if c not in LOAI_CHU:
            cb.append("Ký tự thứ 4 '%s' không thuộc nhóm T, D, L, M, N, B, G, H, X, F."
                      % c)
    if len(kh) >= 6:
        kq["hau_to"] = kh[4:6]
    phan = [kq["ten_loai"]]
    if kq["mo_ta_co_ma"]:
        phan.append(kq["mo_ta_co_ma"].lower())
    if kq["nam"]:
        phan.append("lập năm 20" + kq["nam"])
    if kq["mo_ta_loai"]:
        phan.append(kq["mo_ta_loai"].lower())
    kq["mo_ta"] = ", ".join(phan)
    return kq


def chuan_hoa_tsuat(raw):
    """Chuan hoa truong TSuat.

    Tra ve (ty_le float hoac None, nhan hien thi, ma: SO/KCT/KKKNT/KHAC/KHONG).
    """
    s = (str(raw or "")).strip()
    if s in ("", "\\", "/", "-"):
        return (None, "\\", "KHONG")
    hoa = s.upper().replace(" ", "")
    if hoa in ("KCT", "KHONGCHIUTHUE"):
        return (None, "KCT", "KCT")
    if hoa in ("KKKNT", "KHONGKEKHAI"):
        return (None, "KKKNT", "KKKNT")
    if hoa in ("KHAC", "KHAC:", "OTHER"):
        return (None, "KHÁC", "KHAC")
    m = re.search(r"-?\d+(?:[.,]\d+)?", s)
    if not m:
        return (None, s, "KHAC")
    try:
        v = float(m.group(0).replace(",", "."))
    except ValueError:
        return (None, s, "KHAC")
    if 0 < v < 1 and "%" not in s:
        v = v * 100.0
    nhan = ("%g%%" % v)
    return (v, nhan, "SO")


def chuan_hoa_mst(mst):
    return re.sub(r"[^0-9\-]", "", str(mst or "").strip())


def kiem_tra_mst(mst, bat_buoc=True):
    """Tra ve (hop_le, thong_bao). Chap nhan 10, 12, 13 chu so va dang 10-3."""
    s = chuan_hoa_mst(mst)
    if not s:
        return (not bat_buoc, "" if not bat_buoc else "Thiếu mã số thuế.")
    chuoi = s.replace("-", "")
    if not chuoi.isdigit():
        return (False, "Mã số thuế '%s' chứa ký tự không hợp lệ." % mst)
    if len(chuoi) not in (10, 12, 13, 14):
        return (False, "Mã số thuế '%s' có %d chữ số, không đúng định dạng "
                       "10 hoặc 13 chữ số." % (mst, len(chuoi)))
    return (True, "")


def ten_tinh_chat(ma):
    return TINH_CHAT.get(str(ma or "1").strip(), "Hàng hóa, dịch vụ")
