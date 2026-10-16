# -*- coding: utf-8 -*-
"""
xml_parser.py - TAX INVOICE PRO v1.2.0
Bo doc XML hoa don dien tu Viet Nam, hoan toan ngoai tuyen.

Chuan ap dung: Nghi dinh 254/2026/ND-CP va Thong tu 91/2026/TT-BTC
(hieu luc 01/07/2026); cau truc the du lieu ke thua QD 1450/QD-TCT
va QD 1510/QD-TCT (PBan 2.x).

Dac diem:
  - Bo qua moi namespace, khong phan biet hoa thuong ten the.
  - Doc duoc tep chua NHIEU the <HDon> noi tiep nhau.
  - Hoa don tu may tinh tien thieu TgTCThue/TgTThue/TSuat van doc duoc.
  - So thap phan, MST 10/12/13 chu so, DLQRCode, MCCQT, chu ky so.
Tac gia: TDA - 0986509106
"""

import hashlib
import os
import re
import xml.etree.ElementTree as ET
from datetime import datetime

import tt91

PHIEN_BAN_BO_DOC = "1.2.0"
TRUONG_BAT_BUOC = ("so_hoa_don", "ky_hieu_hoa_don", "ngay_lap", "mst_nguoi_ban")
_DUNG_SAI = 1.0  # dong VND


# ----------------------------------------------------------------------
# Tien ich XML
# ----------------------------------------------------------------------
def _ten(e):
    t = getattr(e, "tag", "")
    if not isinstance(t, str):
        return ""
    if "}" in t:
        t = t.split("}", 1)[1]
    return t.strip()


def _txt(n):
    if n is None:
        return ""
    s = "".join(n.itertext())
    s = s.replace("\r", " ").replace("\n", " ").replace("\t", " ")
    return re.sub(r" {2,}", " ", s).strip()


def _con(e, ten):
    if e is None:
        return []
    tl = ten.lower()
    return [c for c in list(e) if _ten(c).lower() == tl]


def _c1(e, *tens):
    for ten in tens:
        ds = _con(e, ten)
        if ds:
            return ds[0]
    return None


def _sau(e, *tens):
    if e is None:
        return None
    tl = {t.lower() for t in tens}
    for node in e.iter():
        if node is e:
            continue
        if _ten(node).lower() in tl:
            return node
    return None


def _nut(e, *tens):
    n = _c1(e, *tens)
    if n is None:
        n = _sau(e, *tens)
    return n


def _t(e, *tens):
    return _txt(_nut(e, *tens))


def _so(s, mac_dinh=0.0):
    """Doc so tu chuoi. XML chuan dung dau cham thap phan, khong nhom nghin."""
    if s is None:
        return mac_dinh
    if isinstance(s, (int, float)):
        return float(s)
    s = str(s).strip().replace("\u00a0", "").replace(" ", "")
    if not s:
        return mac_dinh
    am = s.startswith("-") or (s.startswith("(") and s.endswith(")"))
    s = s.strip("()").lstrip("+-")
    s = re.sub(r"[^0-9.,]", "", s)
    if not s:
        return mac_dinh
    if "," in s and "." in s:
        if s.rfind(",") > s.rfind("."):
            s = s.replace(".", "").replace(",", ".")
        else:
            s = s.replace(",", "")
    elif "," in s:
        if re.fullmatch(r"\d{1,3}(,\d{3})+", s):
            s = s.replace(",", "")
        else:
            s = s.replace(",", ".")
    elif s.count(".") > 1:
        s = s.replace(".", "")
    try:
        v = float(s)
    except ValueError:
        return mac_dinh
    return -v if am else v


def _so_co(e, *tens):
    """Tra ve (gia_tri, co_mat_trong_xml)."""
    n = _nut(e, *tens)
    if n is None:
        return (0.0, False)
    s = _txt(n)
    if s == "":
        return (0.0, False)
    return (_so(s), True)


def _ngay(s):
    s = (s or "").strip()
    if not s:
        return ""
    s = s.replace("T", " ").split(" ")[0].strip()
    for f in ("%Y-%m-%d", "%d/%m/%Y", "%Y/%m/%d", "%d-%m-%Y", "%Y%m%d", "%d.%m.%Y"):
        try:
            return datetime.strptime(s, f).strftime("%Y-%m-%d")
        except ValueError:
            continue
    m = re.search(r"(\d{4})[-/](\d{1,2})[-/](\d{1,2})", s)
    if m:
        return "%s-%02d-%02d" % (m.group(1), int(m.group(2)), int(m.group(3)))
    return ""


def _nguyen(x):
    try:
        return int(round(float(x)))
    except (TypeError, ValueError):
        return 0


def _ttkhac(e):
    """Doc khoi TTKhac/TTin -> danh sach {ten, kieu, gia_tri}."""
    ds = []
    khoi = _c1(e, "TTKhac")
    if khoi is None:
        return ds
    for ttin in _con(khoi, "TTin"):
        ten = _t(ttin, "TTruong")
        gt = _t(ttin, "DLieu")
        if ten or gt:
            ds.append({"ten": ten, "kieu": _t(ttin, "KDLieu"), "gia_tri": gt})
    return ds


# ----------------------------------------------------------------------
# Tach cac the <HDon> trong noi dung tep
# ----------------------------------------------------------------------
def _giai_ma(du_lieu):
    if isinstance(du_lieu, bytes):
        for enc in ("utf-8-sig", "utf-8", "utf-16", "cp1258", "latin-1"):
            try:
                du_lieu = du_lieu.decode(enc)
                break
            except (UnicodeDecodeError, LookupError):
                continue
        if isinstance(du_lieu, bytes):
            du_lieu = du_lieu.decode("utf-8", "ignore")
    return du_lieu.lstrip("\ufeff").strip()


def tach_hoa_don(noi_dung):
    """Tra ve danh sach phan tu <HDon>. Ho tro tep co nhieu hoa don noi nhau."""
    text = _giai_ma(noi_dung)
    if not text:
        raise ValueError("Tệp rỗng, không có nội dung XML.")
    goc = None
    try:
        goc = ET.fromstring(text)
    except ET.ParseError:
        rong = re.sub(r"<\?xml[^>]*\?>", "", text)
        try:
            goc = ET.fromstring("<TaxInvoiceProGoi>" + rong + "</TaxInvoiceProGoi>")
        except ET.ParseError as e:
            raise ValueError("Tệp XML không hợp lệ: %s" % e)
    if _ten(goc).lower() == "hdon":
        return [goc]
    ds = [e for e in goc.iter() if _ten(e).lower() == "hdon"]
    if ds:
        return ds
    if _sau(goc, "DLHDon") is not None or _sau(goc, "TTChung") is not None:
        return [goc]
    raise ValueError("Không tìm thấy thẻ <HDon> trong tệp XML.")


# ----------------------------------------------------------------------
# Doc mot hoa don
# ----------------------------------------------------------------------
def _doc_chu_ky(hd):
    ds = []
    cks = _c1(hd, "DSCKS") or _sau(hd, "DSCKS")
    if cks is None:
        return ds
    nhan = {"nban": "Người bán", "nmua": "Người mua",
            "ccksikhac": "Khác", "cckskhac": "Khác"}
    for khoi in list(cks):
        vai = nhan.get(_ten(khoi).lower(), _ten(khoi))
        for sig in [n for n in khoi.iter() if _ten(n).lower() == "signature"]:
            subj = _txt(_sau(sig, "X509SubjectName"))
            cn = re.search(r"CN=([^,]+)", subj)
            uid = re.search(r"UID=(?:MST:)?([^,]+)", subj)
            tg = _txt(_sau(sig, "SigningTime"))
            ds.append({
                "vai_tro": vai,
                "ten": (cn.group(1).strip() if cn else subj),
                "mst": (uid.group(1).strip() if uid else ""),
                "thoi_diem": tg.replace("T", " ") if tg else "",
                "co_chu_ky": bool(_txt(_sau(sig, "SignatureValue"))),
            })
    return ds


def _doc_dong_hang(nd):
    dong = []
    ds = _c1(nd, "DSHHDVu")
    items = _con(ds, "HHDVu") if ds is not None else []
    if not items:
        items = [n for n in nd.iter() if _ten(n).lower() == "hhdvu"]
    for i, hh in enumerate(items, 1):
        tchat = (_t(hh, "TChat") or "1").strip()
        sl, co_sl = _so_co(hh, "SLuong")
        dg, co_dg = _so_co(hh, "DGia")
        stck, _ = _so_co(hh, "STCKhau")
        tlck, _ = _so_co(hh, "TLCKhau")
        tt, co_tt = _so_co(hh, "ThTien")
        if not co_tt and co_sl and co_dg:
            tt = sl * dg - stck
        ty_le, nhan_ts, ma_ts = tt91.chuan_hoa_tsuat(_t(hh, "TSuat"))
        thue_dong, co_thue_dong = _so_co(hh, "TThue")
        dong.append({
            "stt": _nguyen(_t(hh, "STT")) or i,
            "tinh_chat": tchat,
            "ten_tinh_chat": tt91.ten_tinh_chat(tchat),
            "ma_hang": _t(hh, "MHHDVu"),
            "ten_hang": _t(hh, "THHDVu"),
            "dvt": _t(hh, "DVTinh"),
            "so_luong": sl,
            "don_gia": dg,
            "ty_le_ck": tlck,
            "tien_ck": stck,
            "thanh_tien": tt,
            "thue_suat": nhan_ts,
            "ty_le_thue": ty_le,
            "ma_thue_suat": ma_ts,
            "tien_thue": thue_dong if co_thue_dong else None,
            "thong_tin_khac": _ttkhac(hh),
        })
    return dong


def _tong_tu_dong(dong):
    tong = 0.0
    for d in dong:
        tc = d["tinh_chat"]
        if tc == "4":
            continue
        if tc == "3":
            tong -= abs(d["thanh_tien"])
        else:
            tong += d["thanh_tien"]
    return tong


def _doc_mot_hdon(hd, duong_dan="", sha=""):
    dl = _c1(hd, "DLHDon") or hd
    ttc = _c1(dl, "TTChung") or _sau(dl, "TTChung") or dl
    nd = _c1(dl, "NDHDon") or _sau(dl, "NDHDon") or dl
    nban = _c1(nd, "NBan") or _sau(nd, "NBan")
    nmua = _c1(nd, "NMua") or _sau(nd, "NMua")
    tt = _c1(nd, "TToan") or _sau(nd, "TToan")

    ma_mau_so = (_t(ttc, "KHMSHDon") or "").strip()
    ky_hieu = (_t(ttc, "KHHDon") or "").strip().upper()
    so_hd = (_t(ttc, "SHDon") or "").strip()
    ngay_lap = _ngay(_t(ttc, "NLap"))
    ten_hd = _t(ttc, "THDon")

    # ---- dong hang ----
    dong = _doc_dong_hang(nd)

    # ---- bang tong hop theo thue suat ----
    bang_ts = []
    th = _c1(tt, "THTTLTSuat") if tt is not None else None
    for lt in (_con(th, "LTSuat") if th is not None else []):
        ty_le, nhan, ma = tt91.chuan_hoa_tsuat(_t(lt, "TSuat"))
        bang_ts.append({
            "thue_suat": nhan,
            "ty_le": ty_le,
            "ma": ma,
            "tien_hang": _so(_t(lt, "ThTien")),
            "tien_thue": _so(_t(lt, "TThue")),
        })

    # ---- cac chi tieu tong ----
    tien_hang, co_th = _so_co(tt, "TgTCThue")
    thue, co_thue = _so_co(tt, "TgTThue")
    tong, co_tong = _so_co(tt, "TgTTTBSo")
    ck, _ = _so_co(tt, "TTCKTMai")
    phi, _ = _so_co(tt, "TgTPhi")

    if not co_th:
        if bang_ts:
            tien_hang = sum(b["tien_hang"] for b in bang_ts)
        elif dong:
            tien_hang = _tong_tu_dong(dong)
        elif co_tong:
            tien_hang = tong - (thue if co_thue else 0.0)
    if not co_thue:
        if bang_ts:
            thue = sum(b["tien_thue"] for b in bang_ts)
        elif any(d["tien_thue"] is not None for d in dong):
            thue = sum(d["tien_thue"] or 0.0 for d in dong)
        elif co_tong:
            thue = max(0.0, tong - tien_hang)
        else:
            thue = 0.0
    if not co_tong:
        tong = tien_hang + thue + phi

    # ---- hoa don lien quan ----
    lq = _c1(ttc, "TTHDLQuan")
    hd_lq = {}
    trang_thai = "Hợp lệ"
    if lq is not None and len(list(lq)):
        tc = (_t(lq, "TCHDon") or "").strip()
        hd_lq = {
            "tinh_chat": tt91.TC_HOA_DON.get(tc, ""),
            "ma_mau_so": _t(lq, "KHMSHDon"),
            "ky_hieu": _t(lq, "KHHDon"),
            "so_hoa_don": _t(lq, "SHDon"),
            "ngay_lap": _ngay(_t(lq, "NLap")),
            "ly_do": _t(lq, "LDo"),
            "co_quan_thue": _t(lq, "CQTCapMa"),
        }
        if hd_lq["tinh_chat"]:
            trang_thai = hd_lq["tinh_chat"]

    # ---- nguoi ban / nguoi mua ----
    khac_ban = _ttkhac(nban) if nban is not None else []
    khac_chung = _ttkhac(ttc)
    khac_nd = _ttkhac(nd)

    def _tim_khac(ds, *tu_khoa):
        for m in ds:
            ten = (m.get("ten") or "").lower()
            for k in tu_khoa:
                if k in ten:
                    return m.get("gia_tri", "")
        return ""

    inv = {
        "id": "",
        "phien_ban_xml": _t(ttc, "PBan"),
        "ten_hoa_don": ten_hd,
        "ky_hieu_mau_so": ma_mau_so,
        "ky_hieu_hoa_don": ky_hieu,
        "ky_hieu_day_du": (ma_mau_so + ky_hieu) if ma_mau_so else ky_hieu,
        "so_hoa_don": so_hd,
        "ngay_lap": ngay_lap,
        "don_vi_tien_te": _t(ttc, "DVTTe") or "VND",
        "ty_gia": _so(_t(ttc, "TGia"), 1.0) or 1.0,
        "hinh_thuc_tt": _t(ttc, "HTTToan") or _tim_khac(khac_chung, "thanh toán"),
        "mst_tcgp": _t(ttc, "MSTTCGP"),

        "mst_nguoi_ban": tt91.chuan_hoa_mst(_t(nban, "MST")) if nban is not None else "",
        "ten_nguoi_ban": _t(nban, "Ten") if nban is not None else "",
        "dia_chi_nguoi_ban": _t(nban, "DChi") if nban is not None else "",
        "sdt_nguoi_ban": _t(nban, "SDThoai") if nban is not None else "",
        "email_nguoi_ban": _t(nban, "DCTDTu") if nban is not None else "",
        "stk_nguoi_ban": (_t(nban, "STKNHang") if nban is not None else "")
                         or _tim_khac(khac_chung + khac_ban, "stk", "số tài khoản"),
        "ngan_hang_nguoi_ban": (_t(nban, "TNHang") if nban is not None else "")
                               or _tim_khac(khac_chung + khac_ban, "ngân hàng"),

        "mst_nguoi_mua": tt91.chuan_hoa_mst(_t(nmua, "MST")) if nmua is not None else "",
        "ten_nguoi_mua": _t(nmua, "Ten") if nmua is not None else "",
        "dia_chi_nguoi_mua": _t(nmua, "DChi") if nmua is not None else "",
        "cccd_nguoi_mua": (_t(nmua, "CCCDan") if nmua is not None else ""),
        "nguoi_mua_hang": _t(nmua, "HVTNMHang") if nmua is not None else "",
        "email_nguoi_mua": _t(nmua, "DCTDTu") if nmua is not None else "",

        "tien_hang": _nguyen(tien_hang),
        "thue_gtgt": _nguyen(thue),
        "tong_tien": _nguyen(tong),
        "chiet_khau": _nguyen(ck),
        "phi_khac": _nguyen(phi),
        "tien_hang_goc": tien_hang,
        "thue_goc": thue,
        "tong_tien_goc": tong,
        "tong_tien_chu": _t(tt, "TgTTTBChu") if tt is not None else "",

        "trang_thai": trang_thai,
        "loai_hoa_don": tt91.loai_ngan(ma_mau_so, ten_hd),
        "ten_loai_day_du": tt91.ten_mau_so(ma_mau_so)[0] or ten_hd,

        "ma_cqt": _t(hd, "MCCQT"),
        "ma_qr": _t(hd, "DLQRCode"),
        "duong_dan_xml": duong_dan,
        "ten_tep": os.path.basename(duong_dan) if duong_dan else "",
        "sha256": sha,
        "da_tai": 1 if duong_dan else 0,
        "nguon": "XML",
        "ngay_nap": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),

        "dong_hang": dong,
        "thue_theo_suat": bang_ts,
        "hoa_don_lien_quan": hd_lq,
        "chu_ky": _doc_chu_ky(hd),
        "thong_tin_khac": khac_chung + khac_nd,
        "canh_bao": [],
    }

    gm = tt91.giai_ma_ky_hieu(ma_mau_so, ky_hieu,
                              ngay_lap[:4] if len(ngay_lap) >= 4 else None)
    inv["giai_ma_ky_hieu"] = gm
    inv["tu_may_tinh_tien"] = gm.get("tu_may_tinh_tien", False)

    thieu = [t for t in TRUONG_BAT_BUOC if not str(inv.get(t) or "").strip()]
    if thieu:
        raise ValueError("Thiếu trường bắt buộc: " + ", ".join(thieu))

    inv["khoa"] = khoa_trung(inv)
    inv["id"] = "XML" + hashlib.sha1(inv["khoa"].encode("utf-8")).hexdigest()[:13].upper()
    inv["canh_bao"] = kiem_tra(inv)
    return inv


def khoa_trung(inv):
    """Khoa chong trung: MST nguoi ban | ky hieu | so hoa don."""
    return "%s|%s|%s" % (
        (inv.get("mst_nguoi_ban") or "").strip().upper(),
        (inv.get("ky_hieu_hoa_don") or "").strip().upper(),
        (inv.get("so_hoa_don") or "").strip().lstrip("0") or "0",
    )


# ----------------------------------------------------------------------
# Kiem tra nhat quan (chi canh bao, KHONG sua so lieu)
# ----------------------------------------------------------------------
def kiem_tra(inv):
    cb = list(inv.get("giai_ma_ky_hieu", {}).get("canh_bao", []))
    th = float(inv.get("tien_hang_goc", inv.get("tien_hang", 0)) or 0)
    thue = float(inv.get("thue_goc", inv.get("thue_gtgt", 0)) or 0)
    tong = float(inv.get("tong_tien_goc", inv.get("tong_tien", 0)) or 0)
    phi = float(inv.get("phi_khac", 0) or 0)

    if abs(th + thue + phi - tong) > _DUNG_SAI:
        cb.append("Tổng tiền thanh toán (%s) khác tiền hàng + tiền thuế (%s)."
                  % (_dinh_dang(tong), _dinh_dang(th + thue + phi)))

    dong = inv.get("dong_hang") or []
    if dong:
        tong_dong = _tong_tu_dong(dong)
        if abs(tong_dong - th) > _DUNG_SAI:
            cb.append("Cộng thành tiền các dòng hàng (%s) khác tiền hàng chưa thuế (%s)."
                      % (_dinh_dang(tong_dong), _dinh_dang(th)))
        for d in dong:
            if d["tinh_chat"] in ("2", "4"):
                continue
            if d["so_luong"] and d["don_gia"]:
                du = d["so_luong"] * d["don_gia"] - d["tien_ck"]
                if abs(du - d["thanh_tien"]) > _DUNG_SAI:
                    cb.append("Dòng %s (%s): số lượng x đơn giá = %s, thành tiền ghi %s."
                              % (d["stt"], (d["ten_hang"] or "")[:40],
                                 _dinh_dang(du), _dinh_dang(d["thanh_tien"])))

    bang = inv.get("thue_theo_suat") or []
    if bang:
        if abs(sum(b["tien_hang"] for b in bang) - th) > _DUNG_SAI:
            cb.append("Bảng tổng hợp theo thuế suất có tiền hàng khác chỉ tiêu "
                      "tổng tiền chưa thuế.")
        if abs(sum(b["tien_thue"] for b in bang) - thue) > _DUNG_SAI:
            cb.append("Bảng tổng hợp theo thuế suất có tiền thuế khác chỉ tiêu "
                      "tổng tiền thuế.")
        for b in bang:
            if b["ty_le"] is not None and b["tien_hang"]:
                du = b["tien_hang"] * b["ty_le"] / 100.0
                if abs(du - b["tien_thue"]) > max(_DUNG_SAI, b["tien_hang"] * 0.0001):
                    cb.append("Thuế suất %s: %s x %s%% = %s, hóa đơn ghi %s."
                              % (b["thue_suat"], _dinh_dang(b["tien_hang"]),
                                 ("%g" % b["ty_le"]), _dinh_dang(du),
                                 _dinh_dang(b["tien_thue"])))

    ok, tb = tt91.kiem_tra_mst(inv.get("mst_nguoi_ban"), True)
    if not ok:
        cb.append("Người bán: " + tb)
    if inv.get("mst_nguoi_mua"):
        ok2, tb2 = tt91.kiem_tra_mst(inv.get("mst_nguoi_mua"), False)
        if not ok2:
            cb.append("Người mua: " + tb2)
    if not inv.get("mst_nguoi_mua") and not inv.get("cccd_nguoi_mua"):
        cb.append("Hóa đơn không có mã số thuế và không có CCCD người mua.")
    if not inv.get("chu_ky"):
        cb.append("Không tìm thấy chữ ký số trong tệp XML (chỉ kiểm tra sự hiện diện, "
                  "không xác thực giá trị chữ ký).")
    if inv.get("ngay_lap", "") >= "2026-07-01" and not inv.get("ma_cqt") \
            and inv.get("giai_ma_ky_hieu", {}).get("co_ma") == "C":
        cb.append("Hóa đơn thuộc loại có mã cơ quan thuế nhưng thiếu mã (MCCQT).")
    return cb


def _dinh_dang(x):
    try:
        v = float(x)
    except (TypeError, ValueError):
        return str(x)
    if abs(v - round(v)) < 0.005:
        return "{:,.0f}".format(round(v)).replace(",", ".")
    return "{:,.2f}".format(v).replace(",", "X").replace(".", ",").replace("X", ".")


# ----------------------------------------------------------------------
# API cong khai
# ----------------------------------------------------------------------
def bam_file(duong_dan):
    h = hashlib.sha256()
    with open(duong_dan, "rb") as f:
        for khoi in iter(lambda: f.read(65536), b""):
            h.update(khoi)
    return h.hexdigest()


def doc_nhieu_tu_file(duong_dan):
    """Doc tat ca hoa don trong mot tep XML. Tra ve danh sach dict."""
    with open(duong_dan, "rb") as f:
        du_lieu = f.read()
    sha = hashlib.sha256(du_lieu).hexdigest()
    ds = tach_hoa_don(du_lieu)
    kq = []
    loi = []
    for hd in ds:
        try:
            kq.append(_doc_mot_hdon(hd, duong_dan, sha))
        except ValueError as e:
            loi.append(str(e))
    if not kq:
        raise ValueError(loi[0] if loi else "Không đọc được hóa đơn nào trong tệp.")
    return kq


def doc_file(duong_dan):
    """Doc hoa don dau tien trong tep. Nem ValueError neu khong hop le."""
    return doc_nhieu_tu_file(duong_dan)[0]


def doc_file_an_toan(duong_dan):
    """Tra ve (inv hoac None, thong_bao_loi)."""
    try:
        return (doc_file(duong_dan), "")
    except (ValueError, OSError, ET.ParseError) as e:
        return (None, str(e))


def doc_mot_file(duong_dan):
    """Tuong thich ban cu: tra ve (inv hoac None, danh sach truong thieu/loi)."""
    inv, loi = doc_file_an_toan(duong_dan)
    if inv is None:
        tt = [p.strip() for p in loi.replace("Thiếu trường bắt buộc:", "").split(",")]
        return (None, [p for p in tt if p])
    return (inv, [])


def doc_chuoi(noi_dung, duong_dan=""):
    """Doc tu chuoi/bytes XML co san."""
    ds = tach_hoa_don(noi_dung)
    return [_doc_mot_hdon(hd, duong_dan, "") for hd in ds]


# Cac ten goi tuong thich voi phien ban truoc
doc_xml = doc_file
doc_file_xml = doc_file
doc_hoa_don = doc_file
parse_file = doc_file
sha256_file = bam_file
bam_sha256 = bam_file
kiem_tra_hoa_don = kiem_tra
khoa_hoa_don = khoa_trung
