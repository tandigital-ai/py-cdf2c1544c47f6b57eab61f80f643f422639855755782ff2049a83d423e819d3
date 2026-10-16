# -*- coding: utf-8 -*-
"""
giao_dien.py - TAX INVOICE PRO v1.7.0
Chuan hoa ty le hien thi (man hinh 4K, Windows 11) va don vung noi dung.
Tac gia: TDA - 0986509106
"""

import os
import json
import ctypes
import tkinter as tk
from tkinter import ttk, font as tkfont

try:
    import customtkinter as ctk
except Exception:
    ctk = None

THU_MUC = os.path.dirname(os.path.abspath(__file__))
THU_MUC_DL = os.path.join(THU_MUC, "data")
os.makedirs(THU_MUC_DL, exist_ok=True)
TEP_CH = os.path.join(THU_MUC_DL, "giao_dien.json")

MAC_DINH = {"he_so": 0.0, "rong": 1480, "cao": 920}
CO_CHU = 10          # diem, co chu co ban
CAO_DONG = 28        # pixel, chieu cao mot dong bang o ty le 1.0


# ---------------------------------------------------------------- cau hinh
def doc_ch():
    ch = dict(MAC_DINH)
    try:
        if os.path.exists(TEP_CH):
            with open(TEP_CH, "r", encoding="utf-8") as f:
                d = json.load(f)
            if isinstance(d, dict):
                ch.update(d)
    except Exception:
        pass
    return ch


def ghi_ch(ch):
    try:
        with open(TEP_CH, "w", encoding="utf-8") as f:
            json.dump(ch, f, ensure_ascii=False, indent=2)
        return True
    except Exception:
        return False


# ---------------------------------------------------------------- DPI
def bat_dpi():
    """Goi cang som cang tot, truoc khi tao cua so."""
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(2)
        return True
    except Exception:
        pass
    try:
        ctypes.windll.user32.SetProcessDPIAware()
        return True
    except Exception:
        return False


def ty_le_dpi():
    for ham in ("GetDpiForSystem",):
        try:
            dpi = getattr(ctypes.windll.user32, ham)()
            if dpi:
                return max(1.0, float(dpi) / 96.0)
        except Exception:
            pass
    try:
        hdc = ctypes.windll.user32.GetDC(0)
        dpi = ctypes.windll.gdi32.GetDeviceCaps(hdc, 88)  # LOGPIXELSX
        ctypes.windll.user32.ReleaseDC(0, hdc)
        if dpi:
            return max(1.0, float(dpi) / 96.0)
    except Exception:
        pass
    return 1.0


def ty_le_ctk(root):
    """Ty le customtkinter dang thuc su dung (da gom DPI)."""
    try:
        from customtkinter.windows.widgets.scaling.scaling_tracker import ScalingTracker
        return float(ScalingTracker.get_widget_scaling(root))
    except Exception:
        pass
    try:
        return float(ctk.ScalingTracker.get_widget_scaling(root))
    except Exception:
        return ty_le_dpi()


def px(diem, k):
    """Doi co chu tu diem sang pixel am (khong bi Tk nhan them lan nua)."""
    return -max(9, int(round(float(diem) * 1.333 * float(k))))


# ---------------------------------------------------------------- ap dung
def _font_mac_dinh(root, k):
    bang = (("TkDefaultFont", "Segoe UI", CO_CHU, "normal"),
            ("TkTextFont", "Segoe UI", CO_CHU, "normal"),
            ("TkMenuFont", "Segoe UI", CO_CHU, "normal"),
            ("TkHeadingFont", "Segoe UI", CO_CHU, "bold"),
            ("TkCaptionFont", "Segoe UI", CO_CHU, "bold"),
            ("TkSmallCaptionFont", "Segoe UI", CO_CHU - 1, "normal"),
            ("TkTooltipFont", "Segoe UI", CO_CHU - 1, "normal"),
            ("TkIconFont", "Segoe UI", CO_CHU, "normal"),
            ("TkFixedFont", "Consolas", CO_CHU, "normal"))
    for ten, ho, diem, nang in bang:
        try:
            f = tkfont.nametofont(ten, root=root)
            f.configure(family=ho, size=px(diem, k), weight=nang)
        except Exception:
            pass


def ap_dung_ttk(k):
    st = ttk.Style()
    try:
        st.theme_use("clam")
    except Exception:
        pass
    f = ("Segoe UI", px(CO_CHU, k))
    fh = ("Segoe UI", px(CO_CHU, k), "bold")
    cao = int(round(CAO_DONG * k))
    rong_cuon = max(14, int(round(16 * k)))
    ten_style = ("Treeview", "NCC.Treeview", "Kho.Treeview", "Bang.Treeview",
                 "App.Treeview", "TDA.Treeview", "Pro.Treeview", "DC.Treeview",
                 "BC.Treeview", "Mau.Treeview")
    for ten in ten_style:
        try:
            st.configure(ten, font=f, rowheight=cao)
            st.configure(ten + ".Heading", font=fh)
        except Exception:
            pass
    for ten in ("TCombobox", "TEntry", "TButton", "TLabel", "TCheckbutton",
                "TRadiobutton", "TNotebook.Tab"):
        try:
            st.configure(ten, font=f)
        except Exception:
            pass
    try:
        st.configure("TNotebook.Tab", padding=(int(14 * k), int(7 * k)))
        st.configure("Vertical.TScrollbar", width=rong_cuon, arrowsize=rong_cuon)
        st.configure("Horizontal.TScrollbar", width=rong_cuon, arrowsize=rong_cuon)
    except Exception:
        pass
    return k


def _duyet(w):
    yield w
    try:
        con = w.winfo_children()
    except Exception:
        con = []
    for c in con:
        for x in _duyet(c):
            yield x


def dong_bo_bang(goc, k):
    """Phong to moi ttk.Treeview dang hien (chu, chieu cao dong, be rong cot)."""
    st = ttk.Style()
    f = ("Segoe UI", px(CO_CHU, k))
    fh = ("Segoe UI", px(CO_CHU, k), "bold")
    cao = int(round(CAO_DONG * k))
    for w in _duyet(goc):
        if not isinstance(w, ttk.Treeview):
            continue
        try:
            ten = str(w.cget("style") or "") or "Treeview"
            st.configure(ten, font=f, rowheight=cao)
            st.configure(ten + ".Heading", font=fh)
        except Exception:
            pass
        try:
            cot = list(w["columns"]) or []
        except Exception:
            cot = []
        goc_rong = getattr(w, "_tda_w0", None)
        if goc_rong is None:
            goc_rong = {}
            for c in cot:
                try:
                    goc_rong[str(c)] = int(w.column(c, "width"))
                except Exception:
                    pass
            try:
                w._tda_w0 = goc_rong
            except Exception:
                pass
        for c in cot:
            w0 = goc_rong.get(str(c))
            if not w0:
                continue
            try:
                w.column(c, width=max(34, int(round(w0 * k))))
            except Exception:
                pass


def ap_dung(root, he_so=None, dong_bo=True):
    """Dat ty le cho toan bo ung dung. Tra ve he so k dang dung."""
    ch = doc_ch()
    if he_so is not None:
        ch["he_so"] = max(0.6, min(3.0, float(he_so)))
        ghi_ch(ch)

    hs = float(ch.get("he_so") or 0)
    if hs <= 0:
        # lan dau: neu customtkinter chua tu nhan DPI thi tu bu vao
        hien_tai = ty_le_ctk(root)
        hs = 1.0 if hien_tai > 1.2 else round(ty_le_dpi(), 2)
        hs = max(1.0, min(2.5, hs))
        ch["he_so"] = hs
        ghi_ch(ch)

    if ctk is not None:
        try:
            ctk.set_widget_scaling(hs)
            ctk.set_window_scaling(hs)
        except Exception:
            pass
    try:
        root.update_idletasks()
    except Exception:
        pass

    k = max(0.7, min(3.5, ty_le_ctk(root)))
    try:
        root.tk.call("tk", "scaling", k * 96.0 / 72.0)
    except Exception:
        pass
    _font_mac_dinh(root, k)
    ap_dung_ttk(k)
    if dong_bo:
        dong_bo_bang(root, k)
    try:
        root._tda_k = k
        root._tda_hs = hs
    except Exception:
        pass
    return k


def co_cua_so(root, rong=None, cao=None):
    """Dat kich thuoc hop ly va canh giua man hinh."""
    ch = doc_ch()
    rl = int(rong or ch.get("rong") or 1480)
    cl = int(cao or ch.get("cao") or 920)
    k = float(getattr(root, "_tda_k", 1.0)) or 1.0
    try:
        sw, sh = root.winfo_screenwidth(), root.winfo_screenheight()
    except Exception:
        return
    rl = max(1000, min(rl, int(sw / k * 0.96)))
    cl = max(640, min(cl, int(sh / k * 0.90)))
    try:
        root.geometry("%dx%d" % (rl, cl))      # CTk tu nhan ty le
        root.minsize(1000, 640)
    except Exception:
        pass
    try:
        root.update_idletasks()
        w, h = root.winfo_width(), root.winfo_height()
        x = max(0, (sw - w) // 2)
        y = max(0, (sh - h) // 2 - int(24 * k))
        tk.Wm.wm_geometry(root, "+%d+%d" % (x, y))
    except Exception:
        pass


# ---------------------------------------------------------------- phim tat
def doi_ty_le(root, buoc, khi_doi=None):
    ch = doc_ch()
    hs = float(ch.get("he_so") or 1.0)
    hs = max(0.7, min(2.6, round(hs + buoc, 2)))
    k = ap_dung(root, he_so=hs)
    if callable(khi_doi):
        try:
            khi_doi(k, hs)
        except Exception:
            pass
    return k


def gan_phim_tat(root, khi_doi=None):
    """Ctrl + =  phong to, Ctrl + -  thu nho, Ctrl + 0  dat lai."""
    def to(_e=None):
        doi_ty_le(root, 0.10, khi_doi)
        return "break"

    def nho(_e=None):
        doi_ty_le(root, -0.10, khi_doi)
        return "break"

    def lai(_e=None):
        ch = doc_ch()
        ch["he_so"] = 0.0
        ghi_ch(ch)
        k = ap_dung(root)
        if callable(khi_doi):
            try:
                khi_doi(k, float(doc_ch().get("he_so") or 1.0))
            except Exception:
                pass
        return "break"

    for phim in ("<Control-plus>", "<Control-equal>", "<Control-KP_Add>"):
        try:
            root.bind(phim, to)
        except Exception:
            pass
    for phim in ("<Control-minus>", "<Control-KP_Subtract>"):
        try:
            root.bind(phim, nho)
        except Exception:
            pass
    for phim in ("<Control-0>", "<Control-KP_0>"):
        try:
            root.bind(phim, lai)
        except Exception:
            pass


# ---------------------------------------------------------------- vung noi dung
def don_vung(vung, giu=None):
    """Go moi man hinh dang nam trong vung noi dung (chong chong lap)."""
    if vung is None:
        return 0
    n = 0
    try:
        con = list(vung.winfo_children())
    except Exception:
        return 0
    for w in con:
        if giu is not None and w is giu:
            continue
        try:
            cach = w.winfo_manager()
        except Exception:
            cach = ""
        try:
            if cach == "pack":
                w.pack_forget()
            elif cach == "grid":
                w.grid_forget()
            elif cach == "place":
                w.place_forget()
            else:
                continue
            n += 1
        except Exception:
            pass
    return n


def hien(w):
    try:
        w.pack(fill="both", expand=True)
    except Exception:
        pass
    return w


TEP_DAY_DU = True  # dau hieu tep da duoc dan day du - dung xoa dong nay
