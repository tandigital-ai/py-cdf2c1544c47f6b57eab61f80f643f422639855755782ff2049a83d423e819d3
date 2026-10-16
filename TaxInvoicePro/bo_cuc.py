# -*- coding: utf-8 -*-
"""
bo_cuc.py - TAX INVOICE PRO v1.7.2
Chuan hoa bo cuc: bang gian het be ngang, cao hop ly, co thanh keo chinh
chieu cao. Ban nay SUA LOI TREO cua v1.7.1: moi lan chinh cot deu co do tre,
co chot chong de quy va co van an toan tu tat khi phat hien co giat lien hoi.
Tac gia: TDA - 0986509106
"""

import os
import sys
import time
import tkinter as tk
from tkinter import ttk

THU_MUC = os.path.dirname(os.path.abspath(__file__))
if THU_MUC not in sys.path:
    sys.path.insert(0, THU_MUC)

try:
    import customtkinter as ctk
except Exception:
    ctk = None

import giao_dien as gd

try:
    import giam_sat
except Exception:
    giam_sat = None

VIEN = "#CBD5E1"
VIEN_DAM = "#90A4AE"
CAO_MIN_DONG = 6
CAO_MAX_DONG = 26

TRE_MS = 160           # do tre truoc khi tinh lai cot
NGUONG_LAN = 25        # so lan chinh trong mot cua so thoi gian
CUA_SO_TG = 6.0        # giay
LECH_TOI_THIEU = 8     # pixel, nho hon thi coi nhu khong doi
TOI_DA_WIDGET = 3000   # chan duyet cay qua lon

_quet = {"id": None, "root": None, "chay": False}


def _log(muc, s):
    if giam_sat is not None:
        giam_sat.nhat_ky(muc, s)


# ------------------------------------------------------------------ duyet cay
def _duyet(w, con_lai=None):
    if con_lai is None:
        con_lai = [TOI_DA_WIDGET]
    if con_lai[0] <= 0:
        return
    con_lai[0] -= 1
    yield w
    try:
        ds = w.winfo_children()
    except Exception:
        ds = []
    for c in ds:
        for x in _duyet(c, con_lai):
            yield x


def _k(w):
    try:
        return float(getattr(w.winfo_toplevel(), "_tda_k", 1.0)) or 1.0
    except Exception:
        return 1.0


def _rong_goc(tv):
    goc = getattr(tv, "_tda_w0", None)
    if goc:
        return goc
    goc = {}
    try:
        for c in list(tv["columns"]) or []:
            goc[str(c)] = int(tv.column(c, "width"))
    except Exception:
        pass
    try:
        tv._tda_w0 = goc
    except Exception:
        pass
    return goc


def _no_rong(w):
    """Widget hoac khung cha cua no co tu gian theo cua so hay khong."""
    for x in (w, getattr(w, "master", None)):
        if x is None:
            continue
        try:
            if x.winfo_manager() == "pack":
                if str(x.pack_info().get("expand", 0)) in ("1", "True", "true"):
                    return True
            elif x.winfo_manager() == "grid":
                return True
        except Exception:
            pass
    return False


# ------------------------------------------------------------------ gian cot
def tu_gian_cot(tv):
    """Chia phan be ngang con thua cho cac cot - co chong vong lap."""
    if getattr(tv, "_tda_gian", False):
        return
    try:
        tv._tda_gian = True
        tv._tda_w_cu = -1
        tv._tda_dang = False
        tv._tda_dem = 0
        tv._tda_moc = time.time()
        tv._tda_hen = None
        tv._tda_tat = False
    except Exception:
        return

    def ap_dung():
        tv._tda_hen = None
        if getattr(tv, "_tda_tat", False):
            return
        try:
            if not tv.winfo_exists():
                return
            co = int(tv.winfo_width())
        except Exception:
            return
        if co <= 1:
            return
        if abs(co - int(getattr(tv, "_tda_w_cu", -1))) < LECH_TOI_THIEU:
            return                      # khong doi gi -> dung lai, het vong lap

        gio = time.time()
        if gio - tv._tda_moc > CUA_SO_TG:
            tv._tda_moc = gio
            tv._tda_dem = 0
        tv._tda_dem += 1
        if tv._tda_dem > NGUONG_LAN:
            tv._tda_tat = True
            _log("WARN", "Da tat tu gian cot cho mot bang vi phat hien co giat lien hoi.")
            return

        tv._tda_w_cu = co
        tv._tda_dang = True
        try:
            cot = list(tv["columns"]) or []
            if cot:
                k = _k(tv)
                goc = _rong_goc(tv)
                rong = [max(38, int(round((goc.get(str(c)) or 80) * k))) for c in cot]
                tong = sum(rong)
                thua = co - int(6 * k) - tong
                if tong > 0 and thua > int(10 * k):
                    for i, c in enumerate(cot):
                        tv.column(c, width=rong[i] + int(thua * rong[i] / float(tong)))
                else:
                    for i, c in enumerate(cot):
                        tv.column(c, width=rong[i])
        except Exception:
            pass
        try:
            tv.after(80, lambda: setattr(tv, "_tda_dang", False))
        except Exception:
            tv._tda_dang = False

    def khi_doi(_e=None):
        if getattr(tv, "_tda_tat", False) or getattr(tv, "_tda_dang", False):
            return
        try:
            if tv._tda_hen:
                tv.after_cancel(tv._tda_hen)
        except Exception:
            pass
        try:
            tv._tda_hen = tv.after(TRE_MS, ap_dung)
        except Exception:
            tv._tda_hen = None

    try:
        tv.bind("<Configure>", khi_doi, add="+")
        tv.after(300, ap_dung)
    except Exception:
        pass


# ------------------------------------------------------------------ chieu cao
def _cao_dong(tv):
    try:
        st = ttk.Style()
        ten = str(tv.cget("style") or "") or "Treeview"
        h = int(st.lookup(ten, "rowheight") or 0)
        return h if h > 6 else int(round(gd.CAO_DONG * _k(tv)))
    except Exception:
        return 28


def cao_hop_ly(tv):
    """Bang qua thap thi nang len cho de doc - chi lam mot lan."""
    if getattr(tv, "_tda_cao", False):
        return
    try:
        tv._tda_cao = True
        if _no_rong(tv):
            return
        so = len(tv.get_children("")) or 0
        cao = max(CAO_MIN_DONG, min(CAO_MAX_DONG, so + 1))
        if int(tv.cget("height") or 0) < cao:
            tv.configure(height=cao)
    except Exception:
        pass


# ------------------------------------------------------------------ thanh keo
def them_thanh_keo(tv):
    """Chen thanh mong duoi bang de nguoi dung keo chinh chieu cao."""
    if getattr(tv, "_tda_keo", False):
        return
    try:
        tv._tda_keo = True
        khung = tv.master
        if khung is None or khung.winfo_manager() != "pack":
            return
        if str(khung.pack_info().get("expand", 0)) in ("1", "True", "true"):
            return                       # khung tu gian roi, khong can thanh keo
        cha = khung.master
        if cha is None:
            return
    except Exception:
        return

    try:
        thanh = tk.Frame(cha, height=8, bg=VIEN, cursor="sb_v_double_arrow",
                         highlightthickness=0)
        tk.Frame(thanh, width=46, height=3, bg=VIEN_DAM).place(
            relx=0.5, rely=0.5, anchor="center")
        thanh.pack(fill="x", padx=10, pady=(0, 6), after=khung)
        thanh.pack_propagate(False)
        thanh._tda_thanh_keo = True
    except Exception:
        return

    tt = {"y": 0, "h": 0}

    def bat_dau(e):
        tt["y"] = e.y_root
        try:
            tt["h"] = int(tv.cget("height") or 10)
        except Exception:
            tt["h"] = 10

    def keo(e):
        try:
            d = (e.y_root - tt["y"]) // max(10, _cao_dong(tv))
            tv.configure(height=max(3, min(60, tt["h"] + int(d))))
        except Exception:
            pass

    def vua_du(_e=None):
        try:
            so = len(tv.get_children("")) or 6
            tv.configure(height=max(4, min(40, so + 1)))
        except Exception:
            pass

    for w in (thanh,) + tuple(thanh.winfo_children()):
        w.bind("<Button-1>", bat_dau)
        w.bind("<B1-Motion>", keo)
        w.bind("<Double-1>", vua_du)
        w.bind("<Enter>", lambda e, x=thanh: x.configure(bg=VIEN_DAM))
        w.bind("<Leave>", lambda e, x=thanh: x.configure(bg=VIEN))


# ------------------------------------------------------------------ cua so phu
def chinh_cua_so(cs):
    """Cho phep keo gian cua so phu - khong goi update_idletasks o day."""
    if getattr(cs, "_tda_cs", False):
        return
    try:
        cs._tda_cs = True
        cs.resizable(True, True)
        cs.minsize(720, 480)
    except Exception:
        pass


# ------------------------------------------------------------------ ap dung
def chinh_cay(goc, k=None):
    """Xu ly moi bang va cua so con chua danh dau trong cay widget."""
    n = 0
    for w in _duyet(goc):
        try:
            if isinstance(w, ttk.Treeview):
                if getattr(w, "_tda_gian", False):
                    continue
                tu_gian_cot(w)
                cao_hop_ly(w)
                them_thanh_keo(w)
                n += 1
            elif isinstance(w, tk.Toplevel):
                chinh_cua_so(w)
        except Exception:
            pass
    return n


def _quet_mot_vong():
    if not _quet["chay"]:
        return
    root = _quet["root"]
    try:
        if root is None or not root.winfo_exists():
            _quet["chay"] = False
            return
    except Exception:
        _quet["chay"] = False
        return
    try:
        chinh_cay(root)
        for cs in root.winfo_children():
            if isinstance(cs, tk.Toplevel):
                chinh_cua_so(cs)
                chinh_cay(cs)
    except Exception:
        pass
    try:
        _quet["id"] = root.after(2500, _quet_mot_vong)
    except Exception:
        _quet["chay"] = False


def bat_dau_quet(root, ms=2500):
    """Quet dinh ky de bat cac bang / cua so moi sinh ra sau nay."""
    if _quet["chay"]:
        return False
    _quet["root"] = root
    _quet["chay"] = True
    try:
        _quet["id"] = root.after(ms, _quet_mot_vong)
    except Exception:
        _quet["chay"] = False
        return False
    return True


def dung_quet():
    _quet["chay"] = False
    try:
        if _quet["id"] and _quet["root"] is not None:
            _quet["root"].after_cancel(_quet["id"])
    except Exception:
        pass
    _quet["id"] = None


# ------------------------------------------------------------------ va he thong
_trang = {"k": None}


def _va_giao_dien():
    """Chi chay lai phan nang khi ty le thay doi, tranh ve lai lien tuc."""
    if getattr(gd, "_tda_bo_cuc", False):
        return
    goc = gd.dong_bo_bang

    def moi(root, k):
        try:
            doi = (_trang["k"] is None) or abs(float(k) - float(_trang["k"])) > 0.01
        except Exception:
            doi = True
        if doi:
            _trang["k"] = float(k)
            for w in _duyet(root):
                if isinstance(w, ttk.Treeview):
                    try:
                        w._tda_w_cu = -1
                        w._tda_tat = False
                        w._tda_dem = 0
                    except Exception:
                        pass
            try:
                goc(root, k)
            except Exception:
                pass
        try:
            chinh_cay(root)
        except Exception:
            pass

    gd.dong_bo_bang = moi
    gd._tda_bo_cuc = True


def _va_huong_dan():
    try:
        import huong_dan
    except Exception:
        return
    lop = getattr(huong_dan, "ManHinhHuongDan", None)
    if lop is None:
        return
    try:
        import man_hinh_moi
        bang = getattr(man_hinh_moi, "LOP_MAN_HINH", None)
        if not isinstance(bang, dict):
            bang = {}
            man_hinh_moi.LOP_MAN_HINH = bang
        for ma in ("huong_dan", "huong_dan_su_dung", "hd"):
            bang[ma] = lop
    except Exception:
        pass


def ap_dung():
    _va_giao_dien()
    _va_huong_dan()
    try:
        import va_excel
        va_excel.va_tat_ca()
    except Exception:
        pass


ap_dung()


TEP_DAY_DU = True  # dau hieu tep da duoc dan day du - dung xoa dong nay
