# -*- coding: utf-8 -*-
"""
doi_chieu.py - TAX INVOICE PRO v1.3.0 - Giai doan 4
Nghiep vu doi chieu: trung hoa don, chuoi goc/dieu chinh/thay the/huy,
lien tuc so hoa don, kiem tra MST, doi chieu bang ke Excel tu Cong Thue.
Module tu doc data\\taxinvoice.db va tu do cau truc bang nen khong
phu thuoc chu ky ham cua kho.py (an toan voi ban v1.2.0 dang chay).
Tac gia: TDA - 0986509106
"""
import os
import re
import sqlite3
import datetime
import unicodedata
import xml.etree.ElementTree as ET

THU_MUC_GOC = os.path.dirname(os.path.abspath(__file__))
DUONG_DAN_DB = os.path.join(THU_MUC_GOC, "data", "taxinvoice.db")

TEN_BANG_HD = ("hoa_don", "invoices", "hoadon")
TEN_BANG_DONG = ("dong_hang", "invoice_lines", "chi_tiet_hang")

DUNG_SAI = 1.0  # VND

BI_DANH = {
    "khoa": ("khoa", "khoa_trung", "key"),
    "id": ("id", "ma"),
    "so_hoa_don": ("so_hoa_don", "shdon", "so_hd", "sohoadon"),
    "ky_hieu_hoa_don": ("ky_hieu_hoa_don", "khhdon", "ky_hieu"),
    "ky_hieu_mau_so": ("ky_hieu_mau_so", "khmshdon", "mau_so"),
    "ngay_lap": ("ngay_lap", "nlap", "ngay"),
    "mst_nguoi_ban": ("mst_nguoi_ban", "mst_ban", "mstnban"),
    "ten_nguoi_ban": ("ten_nguoi_ban", "ten_ban", "tennban"),
    "mst_nguoi_mua": ("mst_nguoi_mua", "mst_mua", "mstnmua"),
    "ten_nguoi_mua": ("ten_nguoi_mua", "ten_mua", "tennmua"),
    "cccd_nguoi_mua": ("cccd_nguoi_mua", "cccd"),
    "tien_hang": ("tien_hang", "tgtcthue", "tong_tien_chua_thue"),
    "thue_gtgt": ("thue_gtgt", "tgtthue", "tien_thue"),
    "tong_tien": ("tong_tien", "tgttttbso", "tong_thanh_toan"),
    "trang_thai": ("trang_thai", "tthai"),
    "loai_hoa_don": ("loai_hoa_don", "loai"),
    "duong_dan_xml": ("duong_dan_xml", "duong_dan", "file_xml", "path"),
    "da_tai": ("da_tai", "datai"),
}

BI_DANH_DONG = {
    "khoa": ("khoa", "khoa_hd", "hoa_don_khoa", "invoice_key"),
    "hd_id": ("hd_id", "invoice_id", "id_hoa_don"),
    "stt": ("stt", "so_tt", "stt_dong"),
    "ten": ("ten", "ten_hang", "thhdvu", "ten_hang_hoa", "mo_ta"),
    "dvt": ("dvt", "don_vi_tinh", "dvtinh"),
    "so_luong": ("so_luong", "sluong"),
    "don_gia": ("don_gia", "dgia"),
    "thanh_tien": ("thanh_tien", "thtien"),
    "thue_suat": ("thue_suat", "tsuat", "ltsuat"),
    "tien_thue": ("tien_thue", "tthue"),
}


# ---------------------------------------------------------------- tien ich
def khong_dau(s):
    s = unicodedata.normalize("NFD", str(s or ""))
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    s = s.replace("\u0111", "d").replace("\u0110", "D")
    return re.sub(r"\s+", " ", s).strip().lower()


def so(v):
    if v is None:
        return 0.0
    if isinstance(v, (int, float)):
        return float(v)
    t = str(v).strip().replace(" ", "")
    if not t:
        return 0.0
    if "," in t and "." in t:
        t = t.replace(".", "").replace(",", ".") if t.rfind(",") > t.rfind(".") \
            else t.replace(",", "")
    elif "," in t:
        phan = t.split(",")[-1]
        t = t.replace(",", ".") if len(phan) in (1, 2, 3) and len(t.split(",")) == 2 \
            and len(phan) < 3 else t.replace(",", "")
    elif t.count(".") > 1:
        t = t.replace(".", "")
    elif "." in t and len(t.split(".")[-1]) == 3:
        t = t.replace(".", "")
    try:
        return float(re.sub(r"[^0-9.\-]", "", t) or 0)
    except ValueError:
        return 0.0


def fmt_tien(v):
    try:
        n = int(round(so(v)))
    except Exception:
        return "0"
    return "{:,.0f}".format(n).replace(",", ".")


def ngay_chuan(v):
    """Tra ve chuoi yyyy-mm-dd hoac '' neu khong doc duoc."""
    if v is None:
        return ""
    if isinstance(v, (datetime.datetime, datetime.date)):
        return v.strftime("%Y-%m-%d")
    t = str(v).strip()
    if not t:
        return ""
    t = t.split("T")[0].split(" ")[0]
    for m in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%Y/%m/%d", "%d.%m.%Y"):
        try:
            return datetime.datetime.strptime(t, m).strftime("%Y-%m-%d")
        except ValueError:
            continue
    g = re.search(r"(\d{4})-(\d{2})-(\d{2})", t)
    return "%s-%s-%s" % g.groups() if g else ""


def ngay_vn(v):
    c = ngay_chuan(v)
    return "%s/%s/%s" % (c[8:10], c[5:7], c[0:4]) if c else ""


def tach_ky_hieu(mau_so, ky_hieu):
    """Dua ve chuan TT91: mau so 1 chu so + ky hieu 6 ky tu."""
    m = re.sub(r"[^0-9A-Za-z]", "", str(mau_so or "")).upper()
    k = re.sub(r"[^0-9A-Za-z]", "", str(ky_hieu or "")).upper()
    if len(k) == 7 and k[0].isdigit():
        m, k = k[0], k[1:]
    elif len(m) == 7 and m[0].isdigit() and not k:
        m, k = m[0], m[1:]
    return m, k


def khoa_hd(mst_ban, mau_so, ky_hieu, so_hd):
    mst = re.sub(r"[^0-9]", "", str(mst_ban or ""))
    _, k = tach_ky_hieu(mau_so, ky_hieu)
    s = re.sub(r"[^0-9]", "", str(so_hd or "")).lstrip("0") or "0"
    return "%s|%s|%s" % (mst, k, s)


# -------------------------------------------------------------- doc CSDL
def _mo():
    if not os.path.exists(DUONG_DAN_DB):
        raise FileNotFoundError("Khong thay tep CSDL: %s" % DUONG_DAN_DB)
    conn = sqlite3.connect(DUONG_DAN_DB)
    conn.row_factory = sqlite3.Row
    return conn


def _tim_bang(conn, ung_vien):
    co = [r[0] for r in conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
    thap = {t.lower(): t for t in co}
    for t in ung_vien:
        if t.lower() in thap:
            return thap[t.lower()]
    return None


def _anh_xa(cot_thuc, bi_danh):
    thap = {c.lower(): c for c in cot_thuc}
    kq = {}
    for logic, ds in bi_danh.items():
        for ten in ds:
            if ten.lower() in thap:
                kq[logic] = thap[ten.lower()]
                break
    return kq


def _chuan_hoa(row, ax):
    d = {}
    for logic in BI_DANH:
        c = ax.get(logic)
        d[logic] = row[c] if c is not None and c in row.keys() else None
    for t in ("tien_hang", "thue_gtgt", "tong_tien"):
        d[t] = int(round(so(d.get(t))))
    d["ngay_lap"] = ngay_chuan(d.get("ngay_lap"))
    ms, kh = tach_ky_hieu(d.get("ky_hieu_mau_so"), d.get("ky_hieu_hoa_don"))
    d["ky_hieu_mau_so"], d["ky_hieu_hoa_don"] = ms, kh
    for t in ("so_hoa_don", "mst_nguoi_ban", "ten_nguoi_ban", "mst_nguoi_mua",
              "ten_nguoi_mua", "trang_thai", "loai_hoa_don", "duong_dan_xml",
              "cccd_nguoi_mua"):
        d[t] = "" if d.get(t) is None else str(d[t]).strip()
    d["khoa_chuan"] = khoa_hd(d["mst_nguoi_ban"], ms, kh, d["so_hoa_don"])
    if not d.get("khoa"):
        d["khoa"] = d["khoa_chuan"]
    return d


def doc_hoa_don(tu_ngay=None, den_ngay=None):
    """Doc toan bo hoa don trong kho, loc theo khoang ngay (yyyy-mm-dd)."""
    conn = _mo()
    try:
        bang = _tim_bang(conn, TEN_BANG_HD)
        if not bang:
            return []
        cot = [r[1] for r in conn.execute("PRAGMA table_info(%s)" % bang)]
        ax = _anh_xa(cot, BI_DANH)
        ds = [_chuan_hoa(r, ax)
              for r in conn.execute("SELECT * FROM %s" % bang).fetchall()]
    finally:
        conn.close()
    t1, t2 = ngay_chuan(tu_ngay), ngay_chuan(den_ngay)
    if t1:
        ds = [h for h in ds if h["ngay_lap"] and h["ngay_lap"] >= t1]
    if t2:
        ds = [h for h in ds if h["ngay_lap"] and h["ngay_lap"] <= t2]
    ds.sort(key=lambda h: (h["ngay_lap"], h["ten_nguoi_ban"], h["so_hoa_don"]))
    return ds


def doc_dong_hang():
    """Tra ve dict: khoa hoac id hoa don -> danh sach dong hang."""
    kq = {}
    try:
        conn = _mo()
    except Exception:
        return kq
    try:
        bang = _tim_bang(conn, TEN_BANG_DONG)
        if not bang:
            return kq
        cot = [r[1] for r in conn.execute("PRAGMA table_info(%s)" % bang)]
        ax = _anh_xa(cot, BI_DANH_DONG)
        for r in conn.execute("SELECT * FROM %s" % bang).fetchall():
            d = {}
            for logic in BI_DANH_DONG:
                c = ax.get(logic)
                d[logic] = r[c] if c is not None and c in r.keys() else None
            for t in ("so_luong", "don_gia", "thanh_tien", "tien_thue"):
                d[t] = so(d.get(t))
            d["ten"] = "" if d.get("ten") is None else str(d["ten"])
            d["dvt"] = "" if d.get("dvt") is None else str(d["dvt"])
            d["thue_suat"] = "" if d.get("thue_suat") is None else str(d["thue_suat"])
            for k in (d.get("khoa"), d.get("hd_id")):
                if k is None or k == "":
                    continue
                kq.setdefault(str(k), []).append(d)
    except Exception:
        pass
    finally:
        conn.close()
    return kq


def dong_cua(hd, bang_dong):
    for k in (hd.get("khoa"), hd.get("khoa_chuan"), hd.get("id")):
        if k is None:
            continue
        v = bang_dong.get(str(k))
        if v:
            return v
    return []


# ------------------------------------------------------- kiem tra MST
def kiem_tra_mst(mst):
    s = re.sub(r"[^0-9\-]", "", str(mst or "")).strip()
    if not s:
        return False, "thiếu mã số thuế"
    if re.fullmatch(r"\d{10}", s):
        return True, "MST doanh nghiệp/tổ chức (10 số)"
    if re.fullmatch(r"\d{10}-\d{3}", s):
        return True, "MST đơn vị phụ thuộc (10-3 số)"
    if re.fullmatch(r"\d{13}", s):
        return True, "MST đơn vị phụ thuộc (13 số viết liền)"
    if re.fullmatch(r"\d{12}", s):
        return True, "số định danh cá nhân / hộ kinh doanh (12 số)"
    return False, "không đúng định dạng 10, 10-3, 12 hoặc 13 số"


# --------------------------------------------- hoa don lien quan tu XML
_BO_NHO_LQ = {}


def lien_quan_tu_xml(duong_dan):
    """Doc khoi TTHDLQuan trong tep XML goc: tra ve danh sach hoa don bi
    dieu chinh / thay the. Khong phu thuoc xml_parser."""
    if not duong_dan or not os.path.exists(duong_dan):
        return []
    if duong_dan in _BO_NHO_LQ:
        return _BO_NHO_LQ[duong_dan]
    kq = []
    try:
        cay = ET.parse(duong_dan).getroot()
        for nut in cay.iter():
            ten = nut.tag.split("}")[-1]
            if ten not in ("TTHDLQuan", "HDLQuan", "HDon_LQuan"):
                continue
            m = {}
            for con in nut.iter():
                t = con.tag.split("}")[-1]
                v = (con.text or "").strip()
                if not v:
                    continue
                if t in ("SHDon", "ShDon"):
                    m["so_hoa_don"] = v
                elif t in ("KHHDon",):
                    m["ky_hieu_hoa_don"] = v
                elif t in ("KHMSHDon",):
                    m["ky_hieu_mau_so"] = v
                elif t in ("Nlap", "NLap"):
                    m["ngay_lap"] = ngay_chuan(v)
                elif t in ("TCHDon", "TChat"):
                    m["tinh_chat"] = v
                elif t in ("MSTNBan", "MST"):
                    m.setdefault("mst_nguoi_ban", v)
            if m.get("so_hoa_don"):
                kq.append(m)
    except Exception:
        kq = []
    _BO_NHO_LQ[duong_dan] = kq
    return kq


# ------------------------------------------------------------ canh bao
def _nhan(hd):
    return "%s%s - %s" % (hd["ky_hieu_mau_so"], hd["ky_hieu_hoa_don"],
                          hd["so_hoa_don"])


def canh_bao_trung(ds):
    nhom = {}
    for h in ds:
        nhom.setdefault(h["khoa_chuan"], []).append(h)
    cb = []
    for k, v in nhom.items():
        if len(v) > 1:
            cb.append({
                "loai": "Trùng hóa đơn", "muc": "Nặng", "hoa_don": _nhan(v[0]),
                "mo_ta": "Có %d bản ghi cùng MST người bán + ký hiệu + số "
                         "hóa đơn (%s). Giữ lại một bản, xóa các bản còn lại."
                         % (len(v), v[0]["ten_nguoi_ban"] or k)})
    return cb


def canh_bao_mst(ds):
    cb = []
    for h in ds:
        ok, mo_ta = kiem_tra_mst(h["mst_nguoi_ban"])
        if not ok:
            cb.append({"loai": "Sai MST", "muc": "Vừa", "hoa_don": _nhan(h),
                       "mo_ta": "MST người bán '%s' %s (%s)."
                                % (h["mst_nguoi_ban"], mo_ta,
                                   h["ten_nguoi_ban"])})
        if h["mst_nguoi_mua"]:
            ok2, mo_ta2 = kiem_tra_mst(h["mst_nguoi_mua"])
            if not ok2:
                cb.append({"loai": "Sai MST", "muc": "Nhẹ", "hoa_don": _nhan(h),
                           "mo_ta": "MST người mua '%s' %s."
                                    % (h["mst_nguoi_mua"], mo_ta2)})
    return cb


def canh_bao_so_lieu(ds):
    cb = []
    for h in ds:
        lech = h["tong_tien"] - (h["tien_hang"] + h["thue_gtgt"])
        if abs(lech) > DUNG_SAI:
            cb.append({
                "loai": "Lệch số liệu", "muc": "Vừa", "hoa_don": _nhan(h),
                "mo_ta": "Tổng thanh toán %s ≠ tiền hàng %s + thuế %s "
                         "(lệch %s đ). Phần mềm không tự sửa số."
                         % (fmt_tien(h["tong_tien"]), fmt_tien(h["tien_hang"]),
                            fmt_tien(h["thue_gtgt"]), fmt_tien(lech))})
    return cb


def chuoi_hoa_don(ds):
    """Tra ve dict khoa_chuan -> {'bi': [...], 'tham_chieu': [...]}"""
    ban_do = {h["khoa_chuan"]: h for h in ds}
    chuoi = {k: {"bi": [], "tham_chieu": [], "thieu": []} for k in ban_do}
    for h in ds:
        tt = khong_dau(h["trang_thai"])
        if not any(x in tt for x in ("thay the", "dieu chinh")):
            continue
        for lq in lien_quan_tu_xml(h["duong_dan_xml"]):
            k = khoa_hd(lq.get("mst_nguoi_ban") or h["mst_nguoi_ban"],
                        lq.get("ky_hieu_mau_so"), lq.get("ky_hieu_hoa_don"),
                        lq.get("so_hoa_don"))
            chuoi[h["khoa_chuan"]]["tham_chieu"].append(k)
            if k in ban_do:
                chuoi[k]["bi"].append((h["trang_thai"], h["khoa_chuan"]))
            else:
                chuoi[h["khoa_chuan"]]["thieu"].append(lq)
    return chuoi, ban_do


def canh_bao_chuoi(ds):
    cb = []
    try:
        chuoi, ban_do = chuoi_hoa_don(ds)
    except Exception:
        return cb
    for k, v in chuoi.items():
        hd = ban_do[k]
        for trang_thai, khoa_moi in v["bi"]:
            goc_tt = khong_dau(hd["trang_thai"])
            if "hop le" in goc_tt:
                cb.append({
                    "loai": "Chuỗi hóa đơn", "muc": "Nặng", "hoa_don": _nhan(hd),
                    "mo_ta": "Hóa đơn này đã bị %s bởi %s nhưng vẫn đang ở "
                             "trạng thái Hợp lệ — kiểm tra lại hạch toán."
                             % (trang_thai.lower(),
                                _nhan(ban_do[khoa_moi]))})
        for lq in v["thieu"]:
            cb.append({
                "loai": "Chuỗi hóa đơn", "muc": "Vừa", "hoa_don": _nhan(hd),
                "mo_ta": "Hóa đơn %s cho hóa đơn gốc ký hiệu %s số %s ngày %s "
                         "nhưng kho chưa có hóa đơn gốc đó."
                         % (hd["trang_thai"].lower(),
                            lq.get("ky_hieu_hoa_don", "?"),
                            lq.get("so_hoa_don", "?"),
                            ngay_vn(lq.get("ngay_lap")) or "?")})
    return cb


def canh_bao_lien_tuc(ds, nguong=200):
    """Bao khoang so hoa don bi thieu theo tung nguoi ban + ky hieu."""
    nhom = {}
    for h in ds:
        if not h["so_hoa_don"].strip():
            continue
        s = re.sub(r"[^0-9]", "", h["so_hoa_don"])
        if not s:
            continue
        key = (h["mst_nguoi_ban"], h["ky_hieu_mau_so"] + h["ky_hieu_hoa_don"],
               h["ten_nguoi_ban"])
        nhom.setdefault(key, set()).add(int(s))
    cb = []
    for (mst, kh, ten), tap in nhom.items():
        if len(tap) < 2:
            continue
        ds_so = sorted(tap)
        for a, b in zip(ds_so, ds_so[1:]):
            thieu = b - a - 1
            if thieu <= 0:
                continue
            if thieu > nguong:
                mo_ta = ("Thiếu %d số giữa %d và %d — nhiều khả năng do kỳ "
                         "tải dữ liệu không liền mạch, không phải mất hóa đơn."
                         % (thieu, a, b))
                muc = "Nhẹ"
            else:
                mo_ta = ("Thiếu %d số hóa đơn: từ %d đến %d."
                         % (thieu, a + 1, b - 1))
                muc = "Vừa"
            cb.append({"loai": "Liên tục số", "muc": muc,
                       "hoa_don": "%s - %s" % (kh, ten or mst),
                       "mo_ta": mo_ta})
    return cb


def tong_hop_canh_bao(ds=None):
    if ds is None:
        ds = doc_hoa_don()
    cb = []
    cb += canh_bao_trung(ds)
    cb += canh_bao_chuoi(ds)
    cb += canh_bao_so_lieu(ds)
    cb += canh_bao_mst(ds)
    cb += canh_bao_lien_tuc(ds)
    uu_tien = {"Nặng": 0, "Vừa": 1, "Nhẹ": 2}
    cb.sort(key=lambda x: (uu_tien.get(x["muc"], 3), x["loai"], x["hoa_don"]))
    return cb


# ------------------------------------------- doc bang ke Excel Cong Thue
TU_KHOA_COT = {
    "so_hoa_don": ("so hoa don", "so hd", "shdon", "so"),
    "ky_hieu_hoa_don": ("ky hieu hoa don", "ky hieu", "khhdon"),
    "ky_hieu_mau_so": ("ky hieu mau so", "mau so", "khmshdon"),
    "ngay_lap": ("ngay lap", "ngay hoa don", "ngay ky"),
    "mst_nguoi_ban": ("mst nguoi ban", "ma so thue nguoi ban", "mst ben ban"),
    "ten_nguoi_ban": ("ten nguoi ban", "ten ben ban", "don vi ban"),
    "tien_hang": ("tong tien chua thue", "tien chua thue", "thanh tien chua thue",
                  "tong tien chua thue gtgt"),
    "thue_gtgt": ("tong tien thue", "tien thue", "thue gtgt"),
    "tong_tien": ("tong tien thanh toan", "tong tien co thue", "tong thanh toan",
                  "tong tien"),
    "trang_thai": ("trang thai hoa don", "trang thai"),
}


def _nhan_dien_cot(hang):
    ban_do = {}
    for i, o in enumerate(hang):
        nhan = khong_dau(o)
        if not nhan:
            continue
        for logic, tu_khoa in TU_KHOA_COT.items():
            if logic in ban_do:
                continue
            for tk in tu_khoa:
                if nhan == tk or nhan.startswith(tk + " ") or tk in nhan:
                    ban_do[logic] = i
                    break
    return ban_do


def doc_bang_ke(duong_dan, so_dong_do=40):
    """Doc tep Excel/CSV bang ke xuat tu Cong Thue, tu do dong tieu de."""
    hang_tho = []
    if duong_dan.lower().endswith(".csv"):
        import csv
        for ma in ("utf-8-sig", "cp1258", "latin-1"):
            try:
                with open(duong_dan, "r", encoding=ma, newline="") as f:
                    hang_tho = [r for r in csv.reader(f)]
                break
            except UnicodeDecodeError:
                continue
    else:
        from openpyxl import load_workbook
        wb = load_workbook(duong_dan, read_only=True, data_only=True)
        ws = wb[wb.sheetnames[0]]
        for r in ws.iter_rows(values_only=True):
            hang_tho.append(list(r))
        wb.close()
    if not hang_tho:
        raise ValueError("Tệp rỗng hoặc không đọc được.")

    dong_td, ban_do = -1, {}
    for i, h in enumerate(hang_tho[:so_dong_do]):
        bd = _nhan_dien_cot(h)
        if len(bd) >= 3 and "so_hoa_don" in bd:
            dong_td, ban_do = i, bd
            break
    if dong_td < 0:
        raise ValueError("Không tìm thấy dòng tiêu đề có cột 'Số hóa đơn'. "
                         "Hãy xuất lại bảng kê từ Cổng Thuế ở dạng Excel.")

    kq = []
    for h in hang_tho[dong_td + 1:]:
        if not any(str(x or "").strip() for x in h):
            continue
        d = {}
        for logic, i in ban_do.items():
            d[logic] = h[i] if i < len(h) else None
        shd = re.sub(r"[^0-9]", "", str(d.get("so_hoa_don") or ""))
        if not shd:
            continue
        ms, kh = tach_ky_hieu(d.get("ky_hieu_mau_so"), d.get("ky_hieu_hoa_don"))
        kq.append({
            "so_hoa_don": str(d.get("so_hoa_don")).strip(),
            "ky_hieu_mau_so": ms, "ky_hieu_hoa_don": kh,
            "ngay_lap": ngay_chuan(d.get("ngay_lap")),
            "mst_nguoi_ban": re.sub(r"[^0-9\-]", "",
                                    str(d.get("mst_nguoi_ban") or "")),
            "ten_nguoi_ban": str(d.get("ten_nguoi_ban") or "").strip(),
            "tien_hang": int(round(so(d.get("tien_hang")))),
            "thue_gtgt": int(round(so(d.get("thue_gtgt")))),
            "tong_tien": int(round(so(d.get("tong_tien")))),
            "trang_thai": str(d.get("trang_thai") or "").strip(),
            "khoa_chuan": khoa_hd(d.get("mst_nguoi_ban"), ms, kh, shd),
        })
    return kq, {"dong_tieu_de": dong_td + 1, "cot": sorted(ban_do),
                "so_dong": len(kq)}


def doi_chieu_bang_ke(ds_may, ds_cong):
    may = {h["khoa_chuan"]: h for h in ds_may}
    cong = {h["khoa_chuan"]: h for h in ds_cong}
    chi_co_cong = [cong[k] for k in cong if k not in may]
    chi_co_may = [may[k] for k in may if k not in cong]
    lech = []
    for k in set(may) & set(cong):
        a, b = may[k], cong[k]
        if abs(a["tong_tien"] - b["tong_tien"]) > DUNG_SAI:
            lech.append({"khoa": k, "may": a, "cong": b})
    sap = lambda d: sorted(d, key=lambda x: (x.get("ngay_lap", ""),
                                             x.get("so_hoa_don", "")))
    return {"chi_co_cong": sap(chi_co_cong), "chi_co_may": sap(chi_co_may),
            "lech_tien": lech, "khop": len(set(may) & set(cong)) - len(lech)}


if __name__ == "__main__":
    danh_sach = doc_hoa_don()
    print("Trong kho: %d hóa đơn" % len(danh_sach))
    for c in tong_hop_canh_bao(danh_sach):
        print(" [%s] %-16s %-24s %s"
              % (c["muc"], c["loai"], c["hoa_don"], c["mo_ta"]))
