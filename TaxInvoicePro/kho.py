# -*- coding: utf-8 -*-
"""
kho.py - TAX INVOICE PRO v1.2.0
Tang du lieu: hang so giao dien, cau hinh, kho SQLite, loc - sap xep - xoa,
nhat ky nap, lich su tra cuu, sao luu. Hoan toan ngoai tuyen.
Tac gia: TDA - 0986509106
"""

import json
import logging
import os
import re
import shutil
import sqlite3
import sys
from datetime import datetime
from logging.handlers import RotatingFileHandler

import tt91

# ----------------------------------------------------------------------
# Hang so chung
# ----------------------------------------------------------------------
APP_NAME = "TAX INVOICE PRO"
APP_VERSION = "v1.2.0"
TAC_GIA = "TDA"
DIEN_THOAI = "0986509106"
NGAY_CAP_NHAT = "10/10/2026"
OFFLINE_TEXT = "Chế độ ngoại tuyến — đọc dữ liệu đã lưu trên máy"
SLOGAN = "Nhanh chóng  •  Chính xác  •  Tiết kiệm thời gian"

MAU_XANH_DAM = "#0D47A1"
MAU_XANH = "#1565C0"
MAU_XANH_NHAT = "#E8F1FC"
MAU_NEN = "#F4F7FB"
MAU_TRANG = "#FFFFFF"
MAU_VIEN = "#D7DEE8"
MAU_CHU = "#1A2430"
MAU_XAM = "#5B6B7C"
MAU_LUC = "#1B7F3B"
MAU_LUC_DAM = "#15692F"
MAU_CAM = "#E07C00"
MAU_TIM = "#7B3FA0"
MAU_DO = "#C62828"
MAU_DO_DAM = "#A51B1B"

MAU_TRANG_THAI = {
    "Hợp lệ": MAU_LUC,
    "Điều chỉnh": MAU_CAM,
    "Thay thế": MAU_TIM,
    "Hủy": MAU_DO,
}

MENU_TRAI = [
    ("trang_chu", "Trang chủ"),
    ("tra_cuu", "Tra cứu - Tải hóa đơn"),
    ("quan_ly_tep", "Quản lý tệp đã tải"),
    ("lich_su", "Lịch sử tra cứu"),
    ("thiet_lap", "Thiết lập"),
    ("huong_dan", "Hướng dẫn sử dụng"),
    ("lien_he", "Liên hệ hỗ trợ"),
]

DS_TRANG_THAI = ["Tất cả", "Hợp lệ", "Điều chỉnh", "Thay thế", "Hủy"]
DS_LOAI_HOA_DON = ["Tất cả"] + sorted(
    {tt91.loai_ngan(m) for m in tt91.MAU_SO})
DS_SO_DONG = ["20", "50", "100", "200", "Tất cả"]

COT_BANG = [
    ("sel", "", 36, "center"),
    ("stt", "STT", 46, "center"),
    ("ngay_lap", "Ngày lập", 92, "center"),
    ("so_hoa_don", "Số hóa đơn", 92, "center"),
    ("ky_hieu_mau_so", "Mẫu số", 58, "center"),
    ("ky_hieu_hoa_don", "Ký hiệu", 80, "center"),
    ("mst_nguoi_ban", "MST người bán", 112, "center"),
    ("ten_nguoi_ban", "Tên người bán", 260, "w"),
    ("tien_hang", "Tiền hàng", 105, "e"),
    ("thue_gtgt", "Thuế GTGT", 95, "e"),
    ("tong_tien", "Tổng tiền", 110, "e"),
    ("trang_thai", "Trạng thái", 92, "center"),
    ("thao_tac", "Thao tác", 186, "center"),
]
COT_SAP_XEP = ("ngay_lap", "so_hoa_don", "ten_nguoi_ban", "tien_hang",
               "thue_gtgt", "tong_tien", "trang_thai", "mst_nguoi_ban")
THAO_TAC_NHAN = ["XEM", "XML", "IN", "XÓA"]
THAO_TAC_TEXT = "  ".join("[%s]" % t for t in THAO_TAC_NHAN)


# ----------------------------------------------------------------------
# Duong dan
# ----------------------------------------------------------------------
def _goc():
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


THU_MUC_GOC = _goc()
THU_MUC_DATA = os.path.join(THU_MUC_GOC, "data")
THU_MUC_LOG = os.path.join(THU_MUC_GOC, "logs")
THU_MUC_BACKUP = os.path.join(THU_MUC_DATA, "backup")
DUONG_DAN_DB = os.path.join(THU_MUC_DATA, "taxinvoice.db")
DUONG_DAN_CAU_HINH = os.path.join(THU_MUC_GOC, "config.json")
DUONG_DAN_JSON_CU = os.path.join(THU_MUC_DATA, "invoices.json")

log = logging.getLogger("taxinvoicepro")


def _mac_dinh_luu_tru():
    if os.name == "nt" and os.path.isdir("D:\\"):
        return "D:\\HoaDon_TCT"
    return os.path.join(os.path.expanduser("~"), "Documents", "HoaDon_TCT")


CAU_HINH_MAC_DINH = {
    "thu_muc_luu_tru": _mac_dinh_luu_tru(),
    "thu_muc_xuat": "",
    "thu_muc_nap_gan_nhat": "",
    "so_ban_ghi_moi_trang": "50",
    "mst_mac_dinh": "",
    "tu_ngay_mac_dinh": "",
    "den_ngay_mac_dinh": "",
    "nguoi_dung": "Kế toán Info",
    "tu_chep_xml": True,
    "mo_sau_khi_xuat": True,
    "xac_nhan_truoc_khi_xoa": True,
}

# ----------------------------------------------------------------------
# Cau truc bang
# ----------------------------------------------------------------------
_COT_TEXT = [
    "khoa", "id", "so_hoa_don", "ky_hieu_mau_so", "ky_hieu_hoa_don",
    "ky_hieu_day_du", "ngay_lap", "ten_hoa_don", "loai_hoa_don",
    "ten_loai_day_du", "trang_thai", "mst_nguoi_ban", "ten_nguoi_ban",
    "dia_chi_nguoi_ban", "sdt_nguoi_ban", "email_nguoi_ban", "stk_nguoi_ban",
    "ngan_hang_nguoi_ban", "mst_nguoi_mua", "ten_nguoi_mua",
    "dia_chi_nguoi_mua", "cccd_nguoi_mua", "nguoi_mua_hang", "email_nguoi_mua",
    "tong_tien_chu", "don_vi_tien_te", "hinh_thuc_tt", "mst_tcgp",
    "phien_ban_xml", "ma_cqt", "ma_qr", "duong_dan_xml", "ten_tep", "sha256",
    "nguon", "ngay_nap", "ghi_chu",
]
_COT_INT = ["tien_hang", "thue_gtgt", "tong_tien", "chiet_khau", "phi_khac",
            "da_tai", "tu_may_tinh_tien"]
_COT_REAL = ["ty_gia"]
_COT_JSON = ["hoa_don_lien_quan", "thue_theo_suat", "chu_ky",
             "thong_tin_khac", "canh_bao", "giai_ma_ky_hieu"]
_COT_HD = _COT_TEXT + _COT_INT + _COT_REAL + _COT_JSON

_SQL_HD = ("CREATE TABLE IF NOT EXISTS hoa_don (khoa TEXT PRIMARY KEY, "
           + ", ".join(
               ["%s TEXT" % c for c in _COT_TEXT if c != "khoa"]
               + ["%s INTEGER DEFAULT 0" % c for c in _COT_INT]
               + ["%s REAL DEFAULT 1" % c for c in _COT_REAL]
               + ["%s TEXT" % c for c in _COT_JSON])
           + ")")

_SQL_DONG = """CREATE TABLE IF NOT EXISTS dong_hang (
 ma INTEGER PRIMARY KEY AUTOINCREMENT, khoa TEXT, stt INTEGER,
 tinh_chat TEXT, ten_tinh_chat TEXT, ma_hang TEXT, ten_hang TEXT, dvt TEXT,
 so_luong REAL, don_gia REAL, ty_le_ck REAL, tien_ck REAL, thanh_tien REAL,
 thue_suat TEXT, ty_le_thue REAL, tien_thue REAL)"""

_SQL_NHAT_KY = """CREATE TABLE IF NOT EXISTS nhat_ky_nap (
 ma INTEGER PRIMARY KEY AUTOINCREMENT, thoi_diem TEXT, nguon TEXT,
 duong_dan TEXT, tong_tep INTEGER, hoa_don INTEGER, them INTEGER,
 trung INTEGER, loi INTEGER, chi_tiet TEXT)"""

_SQL_LICH_SU = """CREATE TABLE IF NOT EXISTS lich_su_tra_cuu (
 ma INTEGER PRIMARY KEY AUTOINCREMENT, thoi_diem TEXT, mo_ta TEXT,
 dieu_kien TEXT, so_ket_qua INTEGER)"""

_conn = None


# ----------------------------------------------------------------------
# Tien ich dinh dang
# ----------------------------------------------------------------------
def to_int(x, md=0):
    try:
        return int(round(float(str(x).replace(".", "").replace(",", ".")
                              if isinstance(x, str) else x)))
    except (TypeError, ValueError):
        return md


def fmt_tien(x):
    try:
        return "{:,.0f}".format(float(x or 0)).replace(",", ".")
    except (TypeError, ValueError):
        return str(x)


def fmt_ngay(s):
    m = re.match(r"(\d{4})-(\d{2})-(\d{2})", (s or "").strip())
    return "%s/%s/%s" % (m.group(3), m.group(2), m.group(1)) if m else (s or "")


def parse_ngay(s):
    """Chuyen chuoi nguoi dung nhap thanh yyyy-mm-dd, khong hop le tra ve ''."""
    s = (s or "").strip()
    if not s:
        return ""
    s = s.replace(".", "/").replace("-", "/")
    for f in ("%d/%m/%Y", "%Y/%m/%d", "%d/%m/%y"):
        try:
            return datetime.strptime(s, f).strftime("%Y-%m-%d")
        except ValueError:
            continue
    return ""


def khoa_trung(inv):
    return "%s|%s|%s" % (
        (inv.get("mst_nguoi_ban") or "").strip().upper(),
        (inv.get("ky_hieu_hoa_don") or "").strip().upper(),
        (str(inv.get("so_hoa_don") or "").strip().lstrip("0") or "0"),
    )


def chuan_hoa_ky_hieu(inv):
    """Dua du lieu kieu cu (mau so 7 ky tu, ky hieu 'AA/26E') ve chuan TT91."""
    ms = str(inv.get("ky_hieu_mau_so") or "").strip().upper()
    kh = str(inv.get("ky_hieu_hoa_don") or "").strip().upper()
    if len(ms) == 7 and (len(kh) != 6 or "/" in kh):
        inv["ky_hieu_mau_so"] = ms[0]
        inv["ky_hieu_hoa_don"] = ms[1:7]
    elif len(ms) > 1:
        inv["ky_hieu_mau_so"] = ms[0]
    inv["ky_hieu_day_du"] = (str(inv.get("ky_hieu_mau_so") or "")
                             + str(inv.get("ky_hieu_hoa_don") or ""))
    if not inv.get("loai_hoa_don"):
        inv["loai_hoa_don"] = tt91.loai_ngan(inv.get("ky_hieu_mau_so"),
                                             inv.get("ten_hoa_don"))
    return inv


# ----------------------------------------------------------------------
# Khoi tao
# ----------------------------------------------------------------------
def _khoi_tao_log():
    if log.handlers:
        return
    os.makedirs(THU_MUC_LOG, exist_ok=True)
    h = RotatingFileHandler(os.path.join(THU_MUC_LOG, "app.log"),
                            maxBytes=1048576, backupCount=5, encoding="utf-8")
    h.setFormatter(logging.Formatter(
        "%(asctime)s [%(levelname)s] %(message)s", "%d/%m/%Y %H:%M:%S"))
    log.addHandler(h)
    log.setLevel(logging.INFO)


def ket_noi():
    global _conn
    if _conn is None:
        os.makedirs(THU_MUC_DATA, exist_ok=True)
        _conn = sqlite3.connect(DUONG_DAN_DB, check_same_thread=False)
        _conn.row_factory = sqlite3.Row
        _conn.execute("PRAGMA journal_mode=WAL")
    return _conn


def khoi_tao():
    _khoi_tao_log()
    c = ket_noi()
    c.execute(_SQL_HD)
    c.execute(_SQL_DONG)
    c.execute(_SQL_NHAT_KY)
    c.execute(_SQL_LICH_SU)
    c.execute("CREATE INDEX IF NOT EXISTS ix_ngay ON hoa_don(ngay_lap)")
    c.execute("CREATE INDEX IF NOT EXISTS ix_ban ON hoa_don(mst_nguoi_ban)")
    c.execute("CREATE INDEX IF NOT EXISTS ix_dong ON dong_hang(khoa)")
    c.commit()
    _bo_sung_cot()
    so = di_tru()
    log.info("Khởi động %s %s — %d hóa đơn trong kho (vừa chuyển đổi %d).",
             APP_NAME, APP_VERSION, dem(), so)
    return c


def _bo_sung_cot():
    """Them cot con thieu khi nang cap tu ban truoc."""
    c = ket_noi()
    co = {r["name"] for r in c.execute("PRAGMA table_info(hoa_don)")}
    for cot in _COT_HD:
        if cot in co:
            continue
        kieu = ("INTEGER DEFAULT 0" if cot in _COT_INT
                else "REAL DEFAULT 1" if cot in _COT_REAL else "TEXT")
        c.execute("ALTER TABLE hoa_don ADD COLUMN %s %s" % (cot, kieu))
    c.commit()


def dong_ket_noi():
    global _conn
    if _conn is not None:
        try:
            _conn.commit()
            _conn.close()
        except sqlite3.Error:
            pass
        _conn = None


# ----------------------------------------------------------------------
# Cau hinh
# ----------------------------------------------------------------------
def doc_cau_hinh():
    ch = dict(CAU_HINH_MAC_DINH)
    try:
        with open(DUONG_DAN_CAU_HINH, "r", encoding="utf-8") as f:
            ch.update(json.load(f) or {})
    except (OSError, ValueError):
        pass
    if not ch.get("thu_muc_xuat"):
        ch["thu_muc_xuat"] = ch.get("thu_muc_luu_tru") or _mac_dinh_luu_tru()
    return ch


def ghi_cau_hinh(ch):
    try:
        with open(DUONG_DAN_CAU_HINH, "w", encoding="utf-8") as f:
            json.dump(ch, f, ensure_ascii=False, indent=2)
        return True
    except OSError as e:
        log.error("Không ghi được config.json: %s", e)
        return False


# ----------------------------------------------------------------------
# Ghi / doc hoa don
# ----------------------------------------------------------------------
def _hang_tu_inv(inv):
    inv = chuan_hoa_ky_hieu(dict(inv))
    kh = inv.get("khoa") or khoa_trung(inv)
    hang = {"khoa": kh}
    for cot in _COT_HD:
        if cot == "khoa":
            continue
        v = inv.get(cot)
        if cot in _COT_JSON:
            hang[cot] = json.dumps(v if v is not None else
                                   ({} if cot in ("hoa_don_lien_quan",
                                                  "giai_ma_ky_hieu") else []),
                                   ensure_ascii=False)
        elif cot in _COT_INT:
            hang[cot] = to_int(v)
        elif cot in _COT_REAL:
            try:
                hang[cot] = float(v or 1)
            except (TypeError, ValueError):
                hang[cot] = 1.0
        else:
            hang[cot] = "" if v is None else str(v)
    if not hang.get("ngay_nap"):
        hang["ngay_nap"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    if not hang.get("nguon"):
        hang["nguon"] = "XML"
    if not hang.get("trang_thai"):
        hang["trang_thai"] = "Hợp lệ"
    if not hang.get("id"):
        hang["id"] = "HD" + str(abs(hash(kh)))[:12]
    return hang


def co_hoa_don(kh):
    r = ket_noi().execute("SELECT 1 FROM hoa_don WHERE khoa=?", (kh,)).fetchone()
    return r is not None


def them_hoa_don(inv, ghi_de=False, luu_ngay=True):
    """Tra ve 'them' | 'cap_nhat' | 'trung'."""
    c = ket_noi()
    hang = _hang_tu_inv(inv)
    kh = hang["khoa"]
    da_co = co_hoa_don(kh)
    if da_co and not ghi_de:
        return "trung"
    cot = list(hang.keys())
    c.execute("INSERT OR REPLACE INTO hoa_don (%s) VALUES (%s)"
              % (", ".join(cot), ", ".join("?" * len(cot))),
              [hang[k] for k in cot])
    c.execute("DELETE FROM dong_hang WHERE khoa=?", (kh,))
    for d in (inv.get("dong_hang") or []):
        c.execute("""INSERT INTO dong_hang (khoa, stt, tinh_chat, ten_tinh_chat,
                     ma_hang, ten_hang, dvt, so_luong, don_gia, ty_le_ck,
                     tien_ck, thanh_tien, thue_suat, ty_le_thue, tien_thue)
                     VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                  (kh, to_int(d.get("stt")), str(d.get("tinh_chat") or "1"),
                   d.get("ten_tinh_chat") or "", d.get("ma_hang") or "",
                   d.get("ten_hang") or "", d.get("dvt") or "",
                   float(d.get("so_luong") or 0), float(d.get("don_gia") or 0),
                   float(d.get("ty_le_ck") or 0), float(d.get("tien_ck") or 0),
                   float(d.get("thanh_tien") or 0), d.get("thue_suat") or "",
                   (None if d.get("ty_le_thue") is None
                    else float(d.get("ty_le_thue"))),
                   (None if d.get("tien_thue") is None
                    else float(d.get("tien_thue")))))
    if luu_ngay:
        c.commit()
    return "cap_nhat" if da_co else "them"


def them_nhieu(danh_sach, ghi_de=False):
    them = trung = loi = 0
    for inv in danh_sach:
        try:
            kq = them_hoa_don(inv, ghi_de, luu_ngay=False)
            if kq == "trung":
                trung += 1
            else:
                them += 1
        except sqlite3.Error as e:
            loi += 1
            log.error("Lỗi ghi hóa đơn: %s", e)
    ket_noi().commit()
    return them, trung, loi


def _ra_dict(r):
    d = dict(r)
    for cot in _COT_JSON:
        if cot in d:
            try:
                d[cot] = json.loads(d[cot]) if d[cot] else (
                    {} if cot in ("hoa_don_lien_quan", "giai_ma_ky_hieu") else [])
            except (ValueError, TypeError):
                d[cot] = {} if cot in ("hoa_don_lien_quan",
                                       "giai_ma_ky_hieu") else []
    return d


def _menh_de(dk):
    dk = dk or {}
    w, p = [], []

    def like(cot, gt):
        if gt:
            w.append("LOWER(%s) LIKE ?" % cot)
            p.append("%" + str(gt).strip().lower() + "%")

    like("mst_nguoi_mua", dk.get("mst_nguoi_mua"))
    like("cccd_nguoi_mua", dk.get("cccd_nguoi_mua"))
    like("ky_hieu_hoa_don", dk.get("ky_hieu_hoa_don"))
    like("so_hoa_don", dk.get("so_hoa_don"))
    like("ten_nguoi_ban", dk.get("ten_nguoi_ban"))
    like("mst_nguoi_ban", dk.get("mst_nguoi_ban"))
    ms = (dk.get("ky_hieu_mau_so") or "").strip()
    if ms:
        w.append("ky_hieu_mau_so = ?")
        p.append(ms[0])
    tt = (dk.get("trang_thai") or "").strip()
    if tt and tt != "Tất cả":
        w.append("trang_thai = ?")
        p.append(tt)
    lo = (dk.get("loai_hoa_don") or "").strip()
    if lo and lo != "Tất cả":
        w.append("loai_hoa_don = ?")
        p.append(lo)
    if dk.get("tu_ngay"):
        w.append("ngay_lap >= ?")
        p.append(dk["tu_ngay"])
    if dk.get("den_ngay"):
        w.append("ngay_lap <= ?")
        p.append(dk["den_ngay"])
    if dk.get("tong_tu"):
        w.append("tong_tien >= ?")
        p.append(to_int(dk["tong_tu"]))
    if dk.get("tong_den"):
        w.append("tong_tien <= ?")
        p.append(to_int(dk["tong_den"]))
    tk = (dk.get("tu_khoa") or "").strip().lower()
    if tk:
        w.append("(LOWER(ten_nguoi_ban) LIKE ? OR LOWER(ten_nguoi_mua) LIKE ? "
                 "OR LOWER(so_hoa_don) LIKE ? OR LOWER(ma_cqt) LIKE ?)")
        p += ["%" + tk + "%"] * 4
    if dk.get("chi_chua_tai"):
        w.append("da_tai = 0")
    return (" WHERE " + " AND ".join(w)) if w else "", p


def lay_danh_sach(dieu_kien=None, sap_xep="ngay_lap", giam=True, gioi_han=0):
    if sap_xep not in COT_SAP_XEP + ("ngay_nap",):
        sap_xep = "ngay_lap"
    md, p = _menh_de(dieu_kien)
    sql = ("SELECT * FROM hoa_don" + md + " ORDER BY %s %s, ngay_nap DESC"
           % (sap_xep, "DESC" if giam else "ASC"))
    if gioi_han:
        sql += " LIMIT %d" % int(gioi_han)
    return [_ra_dict(r) for r in ket_noi().execute(sql, p)]


def dem(dieu_kien=None):
    md, p = _menh_de(dieu_kien)
    return ket_noi().execute("SELECT COUNT(*) FROM hoa_don" + md, p).fetchone()[0]


def lay_chi_tiet(khoa):
    r = ket_noi().execute("SELECT * FROM hoa_don WHERE khoa=?", (khoa,)).fetchone()
    if r is None:
        return None
    inv = _ra_dict(r)
    inv["dong_hang"] = [dict(x) for x in ket_noi().execute(
        "SELECT * FROM dong_hang WHERE khoa=? ORDER BY stt, ma", (khoa,))]
    inv["tien_hang_goc"] = inv.get("tien_hang")
    inv["thue_goc"] = inv.get("thue_gtgt")
    inv["tong_tien_goc"] = inv.get("tong_tien")
    return inv


def cap_nhat_truong(khoa, **truong):
    cot = [k for k in truong if k in _COT_HD]
    if not cot:
        return 0
    c = ket_noi()
    c.execute("UPDATE hoa_don SET %s WHERE khoa=?"
              % ", ".join("%s=?" % k for k in cot),
              [truong[k] for k in cot] + [khoa])
    c.commit()
    return c.total_changes


# ----------------------------------------------------------------------
# Xoa
# ----------------------------------------------------------------------
def xoa(danh_sach_khoa, xoa_tep=False):
    """Xoa hoa don khoi kho. Tra ve (so_hoa_don_xoa, so_tep_xoa)."""
    khoas = [k for k in (danh_sach_khoa or []) if k]
    if not khoas:
        return (0, 0)
    sao_luu("truoc_khi_xoa")
    c = ket_noi()
    so_tep = 0
    if xoa_tep:
        for k in khoas:
            r = c.execute("SELECT duong_dan_xml FROM hoa_don WHERE khoa=?",
                          (k,)).fetchone()
            d = (r["duong_dan_xml"] if r else "") or ""
            if d and os.path.isfile(d) and _trong_kho(d):
                try:
                    os.remove(d)
                    so_tep += 1
                except OSError as e:
                    log.warning("Không xóa được tệp %s: %s", d, e)
    goi = ",".join("?" * len(khoas))
    c.execute("DELETE FROM dong_hang WHERE khoa IN (%s)" % goi, khoas)
    cur = c.execute("DELETE FROM hoa_don WHERE khoa IN (%s)" % goi, khoas)
    c.commit()
    log.info("Đã xóa %d hóa đơn (%d tệp XML).", cur.rowcount, so_tep)
    return (cur.rowcount, so_tep)


def _trong_kho(duong_dan):
    goc = os.path.abspath(doc_cau_hinh().get("thu_muc_luu_tru") or "")
    try:
        return bool(goc) and os.path.abspath(duong_dan).startswith(goc)
    except (OSError, ValueError):
        return False


def xoa_theo_dieu_kien(dieu_kien, xoa_tep=False):
    return xoa([r["khoa"] for r in lay_danh_sach(dieu_kien)], xoa_tep)


def xoa_tat_ca(xoa_tep=False):
    return xoa([r["khoa"] for r in lay_danh_sach()], xoa_tep)


# ----------------------------------------------------------------------
# Thong ke
# ----------------------------------------------------------------------
def thong_ke(dieu_kien=None):
    md, p = _menh_de(dieu_kien)
    r = ket_noi().execute(
        "SELECT COUNT(*) n, COALESCE(SUM(da_tai),0) t, "
        "COALESCE(SUM(tien_hang),0) th, COALESCE(SUM(thue_gtgt),0) tg, "
        "COALESCE(SUM(tong_tien),0) tt FROM hoa_don" + md, p).fetchone()
    tk = {"tong": r["n"], "da_tai": r["t"], "chua_tai": r["n"] - r["t"],
          "tien_hang": r["th"], "thue": r["tg"], "tong_tien": r["tt"],
          "theo_trang_thai": {}, "theo_loai": {}}
    for row in ket_noi().execute(
            "SELECT trang_thai, COUNT(*) n FROM hoa_don" + md
            + " GROUP BY trang_thai", p):
        tk["theo_trang_thai"][row["trang_thai"] or "Khác"] = row["n"]
    for row in ket_noi().execute(
            "SELECT loai_hoa_don, COUNT(*) n FROM hoa_don" + md
            + " GROUP BY loai_hoa_don", p):
        tk["theo_loai"][row["loai_hoa_don"] or "Khác"] = row["n"]
    return tk


def khoang_thoi_gian():
    r = ket_noi().execute("SELECT MIN(ngay_lap) a, MAX(ngay_lap) b "
                          "FROM hoa_don WHERE ngay_lap <> ''").fetchone()
    return ((r["a"] or ""), (r["b"] or ""))


# ----------------------------------------------------------------------
# Nhat ky nap / lich su tra cuu
# ----------------------------------------------------------------------
def ghi_nhat_ky_nap(bc):
    c = ket_noi()
    c.execute("""INSERT INTO nhat_ky_nap (thoi_diem, nguon, duong_dan, tong_tep,
                 hoa_don, them, trung, loi, chi_tiet)
                 VALUES (?,?,?,?,?,?,?,?,?)""",
              (datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
               bc.get("nguon", ""), bc.get("duong_dan", ""),
               to_int(bc.get("tong_tep")), to_int(bc.get("hoa_don")),
               to_int(bc.get("them")), to_int(bc.get("trung")),
               to_int(bc.get("loi")),
               json.dumps(bc.get("chi_tiet") or [], ensure_ascii=False)))
    c.commit()


def lay_nhat_ky_nap(gioi_han=200):
    ds = []
    for r in ket_noi().execute("SELECT * FROM nhat_ky_nap ORDER BY ma DESC "
                               "LIMIT ?", (gioi_han,)):
        d = dict(r)
        try:
            d["chi_tiet"] = json.loads(d["chi_tiet"] or "[]")
        except ValueError:
            d["chi_tiet"] = []
        ds.append(d)
    return ds


def xoa_nhat_ky_nap():
    c = ket_noi()
    c.execute("DELETE FROM nhat_ky_nap")
    c.commit()


def ghi_lich_su(mo_ta, dieu_kien, so_ket_qua):
    c = ket_noi()
    c.execute("INSERT INTO lich_su_tra_cuu (thoi_diem, mo_ta, dieu_kien, "
              "so_ket_qua) VALUES (?,?,?,?)",
              (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), mo_ta,
               json.dumps(dieu_kien or {}, ensure_ascii=False),
               to_int(so_ket_qua)))
    c.execute("DELETE FROM lich_su_tra_cuu WHERE ma NOT IN "
              "(SELECT ma FROM lich_su_tra_cuu ORDER BY ma DESC LIMIT 300)")
    c.commit()


def lay_lich_su(gioi_han=200):
    ds = []
    for r in ket_noi().execute("SELECT * FROM lich_su_tra_cuu ORDER BY ma DESC "
                               "LIMIT ?", (gioi_han,)):
        d = dict(r)
        try:
            d["dieu_kien"] = json.loads(d["dieu_kien"] or "{}")
        except ValueError:
            d["dieu_kien"] = {}
        ds.append(d)
    return ds


def xoa_lich_su():
    c = ket_noi()
    c.execute("DELETE FROM lich_su_tra_cuu")
    c.commit()


# ----------------------------------------------------------------------
# Sao luu
# ----------------------------------------------------------------------
def sao_luu(nhan="auto", giu=10):
    if not os.path.isfile(DUONG_DAN_DB):
        return ""
    try:
        os.makedirs(THU_MUC_BACKUP, exist_ok=True)
        ket_noi().commit()
        ten = "taxinvoice_%s_%s.db" % (datetime.now().strftime("%Y%m%d_%H%M%S"),
                                       nhan)
        dich = os.path.join(THU_MUC_BACKUP, ten)
        shutil.copy2(DUONG_DAN_DB, dich)
        ds = sorted((f for f in os.listdir(THU_MUC_BACKUP)
                     if f.lower().endswith(".db")), reverse=True)
        for f in ds[giu:]:
            try:
                os.remove(os.path.join(THU_MUC_BACKUP, f))
            except OSError:
                pass
        return dich
    except (OSError, sqlite3.Error) as e:
        log.warning("Không sao lưu được: %s", e)
        return ""


# ----------------------------------------------------------------------
# Chuyen doi du lieu cu
# ----------------------------------------------------------------------
def di_tru():
    so = 0
    c = ket_noi()
    bang = {r["name"] for r in c.execute(
        "SELECT name FROM sqlite_master WHERE type='table'")}
    if "invoices" in bang:
        cot = [r["name"] for r in c.execute("PRAGMA table_info(invoices)")]
        chung = [x for x in cot if x in _COT_HD]
        if chung:
            for r in c.execute("SELECT * FROM invoices"):
                inv = {k: r[k] for k in chung}
                inv.pop("khoa", None)
                if not inv.get("so_hoa_don"):
                    continue
                inv["nguon"] = inv.get("nguon") or "Chuyển từ bản cũ"
                if them_hoa_don(inv, ghi_de=False, luu_ngay=False) == "them":
                    so += 1
            c.commit()
        c.execute("DROP TABLE invoices")
        try:
            c.execute("DROP TABLE IF EXISTS invoice_lines")
        except sqlite3.Error:
            pass
        c.commit()
        log.info("Đã chuyển %d hóa đơn từ bảng cũ.", so)
    if os.path.isfile(DUONG_DAN_JSON_CU):
        try:
            with open(DUONG_DAN_JSON_CU, "r", encoding="utf-8") as f:
                ds = json.load(f)
            if isinstance(ds, dict):
                ds = ds.get("invoices") or ds.get("hoa_don") or []
            for inv in ds or []:
                if isinstance(inv, dict) and inv.get("so_hoa_don"):
                    inv["nguon"] = inv.get("nguon") or "Chuyển từ invoices.json"
                    if them_hoa_don(inv, False, luu_ngay=False) == "them":
                        so += 1
            c.commit()
            os.rename(DUONG_DAN_JSON_CU, DUONG_DAN_JSON_CU + ".daChuyen")
        except (OSError, ValueError) as e:
            log.warning("Không đọc được invoices.json: %s", e)
    # chuan hoa ky hieu kieu cu con sot lai
    sua = 0
    for r in c.execute("SELECT khoa, ky_hieu_mau_so, ky_hieu_hoa_don, "
                       "ten_hoa_don FROM hoa_don").fetchall():
        inv = dict(r)
        cu = (inv["ky_hieu_mau_so"], inv["ky_hieu_hoa_don"])
        chuan_hoa_ky_hieu(inv)
        if (inv["ky_hieu_mau_so"], inv["ky_hieu_hoa_don"]) != cu:
            c.execute("UPDATE hoa_don SET ky_hieu_mau_so=?, ky_hieu_hoa_don=?, "
                      "ky_hieu_day_du=?, loai_hoa_don=? WHERE khoa=?",
                      (inv["ky_hieu_mau_so"], inv["ky_hieu_hoa_don"],
                       inv["ky_hieu_day_du"], inv["loai_hoa_don"], inv["khoa"]))
            sua += 1
    if sua:
        c.commit()
        log.info("Đã chuẩn hóa ký hiệu cho %d hóa đơn theo Thông tư 91/2026.", sua)
    return so


def nap_du_lieu_mau():
    """Nap 12 hoa don mau (chi dung de xem thu giao dien)."""
    try:
        import sample_data
    except ImportError:
        return 0
    ham = None
    for ten in ("tao_du_lieu_mau", "du_lieu_mau", "tao_mau", "DU_LIEU_MAU"):
        ham = getattr(sample_data, ten, None)
        if ham is not None:
            break
    if ham is None:
        return 0
    ds = ham() if callable(ham) else ham
    them = 0
    for inv in ds or []:
        inv = dict(inv)
        inv["nguon"] = "Dữ liệu mẫu"
        inv["ghi_chu"] = "Dữ liệu mẫu minh họa, không phải hóa đơn thật"
        if them_hoa_don(inv, False, luu_ngay=False) == "them":
            them += 1
    ket_noi().commit()
    return them


def xoa_du_lieu_mau():
    ds = [r["khoa"] for r in ket_noi().execute(
        "SELECT khoa FROM hoa_don WHERE nguon='Dữ liệu mẫu'")]
    return xoa(ds)[0]
