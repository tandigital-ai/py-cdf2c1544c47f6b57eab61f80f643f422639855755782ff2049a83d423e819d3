# -*- coding: utf-8 -*-
"""
theo_doi.py - TAX INVOICE PRO v1.5.0 - Giai doan 3 (kenh C)
Bo quet thu muc chay nen, nhan dien tep da nap theo ma bam SHA-256.
Khong ket noi may chu thue; chi doc tep co san tren may.
Tac gia: TDA - 0986509106
"""
import os
import sys
import json
import time
import shutil
import inspect
import hashlib
import sqlite3
import zipfile
import tempfile
import datetime
import threading

THU_MUC = os.path.dirname(os.path.abspath(__file__))
TEP_CAU_HINH = os.path.join(THU_MUC, "data", "tu_dong.json")
DUONG_DAN_DB = os.path.join(THU_MUC, "data", "taxinvoice.db")
TEP_LOG = os.path.join(THU_MUC, "logs", "tu_dong.log")

DUOI_NHAN = (".xml", ".zip")
LOAI_TRU = ("data", "logs", "backup", "ban_the_hien", "__pycache__", ".venv",
            "build", "dist")


def thu_muc_tai_ve():
    for t in (os.path.join(os.path.expanduser("~"), "Downloads"),
              os.path.join(os.path.expanduser("~"), "Tải xuống")):
        if os.path.isdir(t):
            return t
    return os.path.expanduser("~")


CAU_HINH_MAC_DINH = {
    "bat_theo_doi": False,
    "thu_muc": [thu_muc_tai_ve()],
    "chu_ky_giay": 30,
    "de_quy": True,
    "so_ngay_gan_day": 30,
    "imap": {"may_chu": "imap.gmail.com", "cong": 993, "ssl": True,
             "tai_khoan": "", "hop_thu": "INBOX", "so_ngay": 30,
             "bat": False},
}


# ------------------------------------------------------------ cau hinh
def doc_cau_hinh():
    c = json.loads(json.dumps(CAU_HINH_MAC_DINH))
    try:
        with open(TEP_CAU_HINH, "r", encoding="utf-8") as f:
            luu = json.load(f)
        for k, v in luu.items():
            if k == "imap" and isinstance(v, dict):
                c["imap"].update(v)
            else:
                c[k] = v
    except Exception:
        pass
    return c


def ghi_cau_hinh(c):
    os.makedirs(os.path.dirname(TEP_CAU_HINH), exist_ok=True)
    tam = TEP_CAU_HINH + ".tmp"
    with open(tam, "w", encoding="utf-8") as f:
        json.dump(c, f, ensure_ascii=False, indent=2)
    os.replace(tam, TEP_CAU_HINH)
    return TEP_CAU_HINH


def ghi_log(dong):
    try:
        os.makedirs(os.path.dirname(TEP_LOG), exist_ok=True)
        with open(TEP_LOG, "a", encoding="utf-8") as f:
            f.write("%s  %s\n"
                    % (datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
                       dong))
    except Exception:
        pass


# -------------------------------------------------------------- ma bam
def bam_sha256(duong_dan):
    h = hashlib.sha256()
    with open(duong_dan, "rb") as f:
        while True:
            k = f.read(262144)
            if not k:
                break
            h.update(k)
    return h.hexdigest()


def _bang_bam():
    os.makedirs(os.path.dirname(DUONG_DAN_DB), exist_ok=True)
    conn = sqlite3.connect(DUONG_DAN_DB, timeout=15)
    conn.execute("CREATE TABLE IF NOT EXISTS tep_da_quet ("
                 "sha256 TEXT PRIMARY KEY, duong_dan TEXT, ten_tep TEXT,"
                 "thoi_diem TEXT, ket_qua TEXT, so_them INTEGER)")
    conn.commit()
    return conn


def da_quet(sha):
    try:
        conn = _bang_bam()
        r = conn.execute("SELECT 1 FROM tep_da_quet WHERE sha256=?",
                         (sha,)).fetchone()
        conn.close()
        return r is not None
    except Exception:
        return False


def ghi_nhan(sha, duong_dan, ket_qua, so_them=0):
    try:
        conn = _bang_bam()
        conn.execute("INSERT OR REPLACE INTO tep_da_quet VALUES (?,?,?,?,?,?)",
                     (sha, duong_dan, os.path.basename(duong_dan),
                      datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                      ket_qua, int(so_them)))
        conn.commit()
        conn.close()
    except Exception:
        pass


def danh_sach_da_quet(gioi_han=300):
    try:
        conn = _bang_bam()
        r = conn.execute("SELECT ten_tep, duong_dan, thoi_diem, ket_qua,"
                         " so_them FROM tep_da_quet ORDER BY thoi_diem DESC"
                         " LIMIT ?", (gioi_han,)).fetchall()
        conn.close()
        return r
    except Exception:
        return []


def xoa_lich_su_bam():
    try:
        conn = _bang_bam()
        conn.execute("DELETE FROM tep_da_quet")
        conn.commit()
        conn.close()
        return True
    except Exception:
        return False


# ----------------------------------------------------- nap tep vao kho
def _goi_nap_thu_muc(thu_muc):
    import importer
    loi_cuoi = None
    for ten in ("nap_thu_muc", "nap_tu_thu_muc", "nap_xml_thu_muc",
                "nap_thu_muc_xml"):
        ham = getattr(importer, ten, None)
        if not callable(ham):
            continue
        for doi_so in ((thu_muc,), (thu_muc, False), (thu_muc, True)):
            try:
                return ham(*doi_so)
            except TypeError as e:
                loi_cuoi = e
                continue
    raise RuntimeError("Không gọi được hàm nạp thư mục trong importer.py (%s)"
                       % loi_cuoi)


def _doc_bao_cao(kq):
    """Tim so hoa don them moi / trung / loi trong ket qua tra ve."""
    bc = None
    if isinstance(kq, dict):
        bc = kq
    elif isinstance(kq, (list, tuple)):
        for p in kq:
            if isinstance(p, dict):
                bc = p
                break
        if bc is None and kq and isinstance(kq[0], (list, tuple)):
            return len(kq[0]), 0, 0
    if not isinstance(bc, dict):
        return 0, 0, 0
    def lay(*ten):
        for t in ten:
            if t in bc:
                try:
                    return int(bc[t])
                except Exception:
                    pass
        return 0
    return (lay("them", "them_moi", "moi", "so_them"),
            lay("trung", "da_co", "bo_qua_trung"),
            lay("loi", "that_bai", "thieu_truong"))


def nap_mot_tep(duong_dan):
    """Nap mot tep .xml hoac .zip vao kho. Tra ve (them, trung, loi, mo_ta)."""
    tam = tempfile.mkdtemp(prefix="tip_")
    try:
        duoi = os.path.splitext(duong_dan)[1].lower()
        if duoi == ".zip":
            try:
                with zipfile.ZipFile(duong_dan) as z:
                    z.extractall(tam)
            except Exception as e:
                return 0, 0, 1, "Không giải nén được: %s" % e
        else:
            shutil.copy2(duong_dan, os.path.join(tam,
                                                 os.path.basename(duong_dan)))
        co_xml = False
        for goc, _, tep in os.walk(tam):
            if any(t.lower().endswith(".xml") for t in tep):
                co_xml = True
                break
        if not co_xml:
            return 0, 0, 0, "Không có tệp XML bên trong"
        kq = _goi_nap_thu_muc(tam)
        them, trung, loi = _doc_bao_cao(kq)
        return them, trung, loi, ("thêm %d, trùng %d, lỗi %d"
                                  % (them, trung, loi))
    except Exception as e:
        return 0, 0, 1, "Lỗi: %s" % e
    finally:
        shutil.rmtree(tam, ignore_errors=True)


def nap_nhieu_tep(ds_tep, bao=None):
    tong = {"tep": 0, "them": 0, "trung": 0, "loi": 0, "chi_tiet": []}
    for d in ds_tep:
        if not os.path.exists(d):
            continue
        try:
            sha = bam_sha256(d)
        except Exception as e:
            tong["loi"] += 1
            tong["chi_tiet"].append((os.path.basename(d), "không đọc được: %s" % e))
            continue
        if da_quet(sha):
            tong["chi_tiet"].append((os.path.basename(d), "đã nạp trước đó"))
            continue
        a, b, c, mo_ta = nap_mot_tep(d)
        tong["tep"] += 1
        tong["them"] += a
        tong["trung"] += b
        tong["loi"] += c
        ghi_nhan(sha, d, mo_ta, a)
        ghi_log("%s -> %s" % (os.path.basename(d), mo_ta))
        tong["chi_tiet"].append((os.path.basename(d), mo_ta))
        if bao:
            bao("%s: %s" % (os.path.basename(d), mo_ta))
    return tong


# ------------------------------------------------------------- quet
def tim_tep_moi(cau_hinh):
    gioi_han = time.time() - cau_hinh.get("so_ngay_gan_day", 30) * 86400
    ra = []
    for t in cau_hinh.get("thu_muc", []):
        if not t or not os.path.isdir(t):
            continue
        if cau_hinh.get("de_quy", True):
            di = os.walk(t)
        else:
            di = [(t, [], [x for x in os.listdir(t)
                           if os.path.isfile(os.path.join(t, x))])]
        for goc, thu_muc_con, tep in di:
            thu_muc_con[:] = [d for d in thu_muc_con
                              if d.lower() not in LOAI_TRU
                              and not d.startswith(".")]
            for ten in tep:
                if not ten.lower().endswith(DUOI_NHAN):
                    continue
                d = os.path.join(goc, ten)
                try:
                    if os.path.getmtime(d) < gioi_han:
                        continue
                    if os.path.getsize(d) <= 0:
                        continue
                except OSError:
                    continue
                ra.append(d)
    return ra


def loc_tep_chua_nap(ds_tep):
    ra = []
    for d in ds_tep:
        try:
            if not da_quet(bam_sha256(d)):
                ra.append(d)
        except Exception:
            continue
    return ra


class DichVuTheoDoi(object):
    """Quet thu muc chay nen. Viec ghi vao CSDL duoc day ve luong giao dien
    qua ham goi_ui (thuong la widget.after) de tranh xung dot SQLite."""

    def __init__(self, goi_ui=None, khi_xong=None, bao=None):
        self.goi_ui = goi_ui
        self.khi_xong = khi_xong
        self.bao = bao
        self._dung = threading.Event()
        self._luong = None
        self._hang_doi = []
        self._khoa = threading.Lock()
        self.lan_quet_cuoi = None
        self.tong_them = 0

    def dang_chay(self):
        return self._luong is not None and self._luong.is_alive()

    def bat(self):
        if self.dang_chay():
            return False
        self._dung.clear()
        self._luong = threading.Thread(target=self._vong_lap, daemon=True)
        self._luong.start()
        ghi_log("Bật bộ theo dõi thư mục.")
        return True

    def tat(self):
        self._dung.set()
        ghi_log("Tắt bộ theo dõi thư mục.")
        return True

    def quet_ngay(self):
        threading.Thread(target=self._quet, daemon=True).start()

    def _vong_lap(self):
        c = doc_cau_hinh()
        chu_ky = max(5, int(c.get("chu_ky_giay", 30)))
        while not self._dung.is_set():
            self._quet()
            if self._dung.wait(chu_ky):
                break

    def _quet(self):
        try:
            c = doc_cau_hinh()
            moi = loc_tep_chua_nap(tim_tep_moi(c))
            self.lan_quet_cuoi = datetime.datetime.now()
            if not moi:
                if self.bao:
                    self._tren_ui(lambda: self.bao(
                        "Quét lúc %s — không có tệp mới."
                        % self.lan_quet_cuoi.strftime("%H:%M:%S")))
                return
            with self._khoa:
                self._hang_doi.extend(moi)
            self._tren_ui(self._xu_ly_hang_doi)
        except Exception as e:
            ghi_log("Lỗi quét: %s" % e)

    def _tren_ui(self, ham):
        if self.goi_ui:
            try:
                self.goi_ui(ham)
                return
            except Exception:
                pass
        ham()

    def _xu_ly_hang_doi(self):
        with self._khoa:
            ds, self._hang_doi = self._hang_doi, []
        if not ds:
            return
        kq = nap_nhieu_tep(ds, bao=self.bao)
        self.tong_them += kq["them"]
        if self.bao:
            self.bao("Tự động nạp %d tệp: thêm %d hóa đơn, trùng %d, lỗi %d."
                     % (kq["tep"], kq["them"], kq["trung"], kq["loi"]))
        if self.khi_xong and kq["them"]:
            try:
                self.khi_xong(kq)
            except Exception:
                pass


DICH_VU = None


def lay_dich_vu(goi_ui=None, khi_xong=None, bao=None):
    global DICH_VU
    if DICH_VU is None:
        DICH_VU = DichVuTheoDoi(goi_ui, khi_xong, bao)
    else:
        if goi_ui:
            DICH_VU.goi_ui = goi_ui
        if khi_xong:
            DICH_VU.khi_xong = khi_xong
        if bao:
            DICH_VU.bao = bao
    return DICH_VU


if __name__ == "__main__":
    ch = doc_cau_hinh()
    t = tim_tep_moi(ch)
    print("Tìm thấy %d tệp, chưa nạp %d tệp." % (len(t), len(loc_tep_chua_nap(t))))
