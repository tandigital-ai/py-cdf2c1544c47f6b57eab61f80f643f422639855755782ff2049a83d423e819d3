# -*- coding: utf-8 -*-
"""
giam_sat.py - TAX INVOICE PRO v1.7.2
Giam sat suc khoe ung dung: phat hien treo giao dien va ghi lai ngan xep
cua moi luong; bat loi trong callback Tk; cung hoa SQLite de khong ket khoa;
dua moi loi goi tu luong nen ve dung luong giao dien.
Tac gia: TDA - 0986509106
"""

import os
import sys
import time
import sqlite3
import threading
import traceback
import datetime as dt

try:
    import faulthandler
except Exception:
    faulthandler = None

PHIEN_BAN = "v1.7.2"
THU_MUC = os.path.dirname(os.path.abspath(__file__))
THU_MUC_LOG = os.path.join(THU_MUC, "logs")
os.makedirs(THU_MUC_LOG, exist_ok=True)

TEP_APP = os.path.join(THU_MUC_LOG, "app.log")
TEP_TREO = os.path.join(THU_MUC_LOG, "treo.txt")
TEP_LOI_UI = os.path.join(THU_MUC_LOG, "loi_ui.txt")
TEP_SUP = os.path.join(THU_MUC_LOG, "sup_do.txt")

_tt = {"nhip": 0.0, "chay": False, "nguong": 8.0,
       "lan_treo": 0, "bao_gan_nhat": 0.0, "tep_sup": None}


# ------------------------------------------------------------------ ghi log
def _gio():
    return dt.datetime.now().strftime("%d/%m/%Y %H:%M:%S")


def _ghi(tep, noi_dung):
    try:
        with open(tep, "a", encoding="utf-8") as f:
            f.write(noi_dung + "\n")
    except Exception:
        pass


def nhat_ky(muc, s):
    dong = "%s [%s] %s" % (_gio(), muc, s)
    _ghi(TEP_APP, dong)
    try:
        print(dong)
    except Exception:
        pass


# ------------------------------------------------------------------ SQLite
def cung_hoa_sqlite():
    """Cho phep nhieu luong dung chung CSDL, cho khoa thay vi dung hinh."""
    if getattr(sqlite3, "_tda_cung", False):
        return False
    goc = sqlite3.connect

    def moi(*a, **kw):
        kw.setdefault("timeout", 20.0)
        kw["check_same_thread"] = False
        cn = goc(*a, **kw)
        for lenh in ("PRAGMA busy_timeout=20000",
                     "PRAGMA journal_mode=WAL",
                     "PRAGMA synchronous=NORMAL"):
            try:
                cn.execute(lenh)
            except Exception:
                pass
        return cn

    moi._tda_goc = goc
    sqlite3.connect = moi
    sqlite3._tda_cung = True
    return True


# ------------------------------------------------------------------ ngan xep
def do_ngan_xep(ly_do):
    """Ghi ngan xep cua tat ca cac luong - goi duoc tu bat ky luong nao."""
    p = ["", "=" * 78,
         "%s  %s" % (_gio(), ly_do),
         "=" * 78]
    try:
        ten_luong = {t.ident: t.name for t in threading.enumerate()}
    except Exception:
        ten_luong = {}
    try:
        khung = sys._current_frames()
    except Exception:
        khung = {}
    for ma, f in khung.items():
        p.append("")
        p.append("--- Luong %s (id %s) ---" % (ten_luong.get(ma, "?"), ma))
        try:
            p.append("".join(traceback.format_stack(f)).rstrip())
        except Exception:
            p.append("(khong doc duoc ngan xep)")
    _ghi(TEP_TREO, "\n".join(p))
    nhat_ky("ERROR", "%s — da ghi ngan xep vao logs\\treo.txt" % ly_do)


# ------------------------------------------------------------------ canh gac
def _canh_gac():
    while _tt["chay"]:
        time.sleep(2.0)
        moc = _tt["nhip"] or time.time()
        tre = time.time() - moc
        if tre > _tt["nguong"] and (time.time() - _tt["bao_gan_nhat"]) > 30:
            _tt["bao_gan_nhat"] = time.time()
            _tt["lan_treo"] += 1
            do_ngan_xep("Giao dien khong phan hoi %.1f giay (lan thu %d)"
                        % (tre, _tt["lan_treo"]))


def dem_hen_gio(root):
    """So viec hen gio dang cho - chi goi tu luong giao dien."""
    try:
        return len(root.tk.splitlist(root.tk.call("after", "info")))
    except Exception:
        return -1


def _bat_loi_ui(root):
    def bao(loai, gia_tri, vet):
        s = "".join(traceback.format_exception(loai, gia_tri, vet))
        _ghi(TEP_LOI_UI, "%s\n%s" % ("-" * 70 + "\n" + _gio(), s))
        nhat_ky("ERROR", "Loi trong giao dien: %s: %s (xem logs\\loi_ui.txt)"
                % (getattr(loai, "__name__", loai), gia_tri))
    try:
        root.report_callback_exception = bao
        return True
    except Exception:
        return False


def bat_dau(root, nguong=8.0):
    """Khoi dong bo giam sat. Goi mot lan sau khi tao cua so chinh."""
    if _tt["chay"]:
        return False
    _tt["chay"] = True
    _tt["nguong"] = float(nguong)
    _tt["nhip"] = time.time()

    if faulthandler is not None:
        try:
            _tt["tep_sup"] = open(TEP_SUP, "a", encoding="utf-8")
            faulthandler.enable(_tt["tep_sup"])
        except Exception:
            pass

    _bat_loi_ui(root)

    dem = [0]

    def nhip():
        _tt["nhip"] = time.time()
        dem[0] += 1
        if dem[0] % 30 == 0:
            n = dem_hen_gio(root)
            if n > 300:
                nhat_ky("WARN", "Co %d viec hen gio dang cho - co the co vong lap." % n)
        try:
            root.after(1000, nhip)
        except Exception:
            _tt["chay"] = False

    try:
        root.after(1000, nhip)
    except Exception:
        _tt["chay"] = False
        return False

    threading.Thread(target=_canh_gac, daemon=True, name="TDA-CanhGac").start()
    nhat_ky("INFO", "Bo giam sat da bat (nguong treo %.0f giay)." % _tt["nguong"])
    return True


def dung():
    _tt["chay"] = False
    if faulthandler is not None:
        try:
            faulthandler.disable()
        except Exception:
            pass
    try:
        if _tt["tep_sup"]:
            _tt["tep_sup"].close()
    except Exception:
        pass


def so_lan_treo():
    return _tt["lan_treo"]


# ------------------------------------------------------------------ luong nen
def boc_ui(root, ham):
    """Bao mot ham lai de no luon chay tren luong giao dien."""
    def moi(*a, **kw):
        try:
            root.after(0, lambda: ham(*a, **kw))
        except Exception:
            try:
                ham(*a, **kw)
            except Exception:
                pass
    moi._tda_boc = True
    return moi


def bao_ve_luong(root):
    """Dua callback cua dich vu nen ve luong giao dien, gian chu ky quet."""
    n = 0
    try:
        import theo_doi
    except Exception:
        return 0

    for ten in ("goi_ui", "bao_ui", "day_ui", "gui_ui"):
        h = getattr(theo_doi, ten, None)
        if callable(h) and not getattr(h, "_tda_boc", False):
            setattr(theo_doi, ten, boc_ui(root, h))
            n += 1

    lop = getattr(theo_doi, "DichVuTheoDoi", None)
    if lop is not None:
        for ten in ("goi_ui", "bao_ui", "day_ui"):
            h = getattr(lop, ten, None)
            if callable(h) and not getattr(h, "_tda_boc", False):
                def tao(h0):
                    def moi(self, *a, **kw):
                        try:
                            root.after(0, lambda: h0(self, *a, **kw))
                        except Exception:
                            pass
                    moi._tda_boc = True
                    return moi
                try:
                    setattr(lop, ten, tao(h))
                    n += 1
                except Exception:
                    pass
    try:
        if getattr(theo_doi, "CHU_KY_TOI_THIEU", 0) < 60:
            theo_doi.CHU_KY_TOI_THIEU = 60
    except Exception:
        pass
    if n:
        nhat_ky("INFO", "Da bao ve %d loi goi tu luong nen." % n)
    return n


def dung_dich_vu():
    """Dung moi dich vu nen truoc khi thoat de ung dung khong treo luc dong."""
    try:
        import theo_doi
    except Exception:
        return 0
    n = 0
    for ten in ("dung_tat_ca", "dung", "tat"):
        h = getattr(theo_doi, ten, None)
        if callable(h):
            try:
                h()
                n += 1
                break
            except Exception:
                pass
    dv = getattr(theo_doi, "DICH_VU", None)
    if dv is not None:
        for ten in ("dung", "tat", "stop"):
            h = getattr(dv, ten, None)
            if callable(h):
                try:
                    h()
                    n += 1
                    break
                except Exception:
                    pass
    return n


def luong_con_song():
    return [t.name for t in threading.enumerate()
            if t is not threading.main_thread() and not t.daemon and t.is_alive()]


TEP_DAY_DU = True  # dau hieu tep da duoc dan day du - dung xoa dong nay
