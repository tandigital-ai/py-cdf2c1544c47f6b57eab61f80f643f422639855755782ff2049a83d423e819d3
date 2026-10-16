# -*- coding: utf-8 -*-
"""
khoi_dong.py - TAX INVOICE PRO v1.7.2
Tep khoi dong chinh. Khong sua app.py. Them man hinh moi, chuan hoa hien thi,
bat bo giam sat va dong ung dung sach se.
Tham so dong lenh:
    --an-toan        chay che do an toan (bo bo cuc va man hinh moi)
    --khong-giam-sat tat bo giam sat
Tac gia: TDA - 0986509106
"""

import os
import sys
import traceback
import datetime as dt
import tkinter as tk

THU_MUC = os.path.dirname(os.path.abspath(__file__))
if THU_MUC not in sys.path:
    sys.path.insert(0, THU_MUC)
os.chdir(THU_MUC)

THU_MUC_LOG = os.path.join(THU_MUC, "logs")
os.makedirs(THU_MUC_LOG, exist_ok=True)
TEP_LOG = os.path.join(THU_MUC_LOG, "app.log")

PHIEN_BAN = "v1.7.2"
TAC_GIA = "TDA - 0986509106"

AN_TOAN = "--an-toan" in sys.argv
KHONG_GIAM_SAT = "--khong-giam-sat" in sys.argv


def ghi_log(muc, noi_dung):
    dong = "%s [%s] %s" % (dt.datetime.now().strftime("%d/%m/%Y %H:%M:%S"), muc, noi_dung)
    try:
        with open(TEP_LOG, "a", encoding="utf-8") as f:
            f.write(dong + "\n")
    except Exception:
        pass
    try:
        print(dong)
    except Exception:
        pass


# -- cung hoa CSDL truoc khi bat ky module nao mo ket noi ---------------------
try:
    import giam_sat
    giam_sat.cung_hoa_sqlite()
except Exception:
    giam_sat = None
    ghi_log("WARN", "Khong nap duoc giam_sat:\n%s" % traceback.format_exc())

try:
    import va_ttk  # va loi command=None cua ttk tren Python 3.12+
except Exception:
    pass

import giao_dien as gd
gd.bat_dpi()

if not AN_TOAN:
    try:
        import bo_cuc
    except Exception:
        bo_cuc = None
        ghi_log("ERROR", "Khong nap duoc bo_cuc:\n%s" % traceback.format_exc())
else:
    bo_cuc = None

import customtkinter as ctk
import kho
import app as app_goc


# ---------------------------------------------------------------- menu trai
MUC_MOI = [("doi_chieu", "Đối chiếu & Kiểm tra"),
           ("bao_cao", "Báo cáo & Kê khai"),
           ("ncc", "Nhà cung cấp & Rủi ro")]


def _ma_muc(m):
    if isinstance(m, dict):
        for k in ("ma", "id", "key", "code"):
            if m.get(k):
                return str(m[k])
        return ""
    if isinstance(m, (list, tuple)) and m:
        return str(m[0])
    return str(m)


def chen_menu():
    ds = list(getattr(kho, "MENU_TRAI", []) or [])
    if not ds:
        return ds
    co = {_ma_muc(m) for m in ds}
    vt = len(ds)
    for i, m in enumerate(ds):
        if _ma_muc(m) in ("lich_su", "lich_su_tra_cuu"):
            vt = i + 1
            break
    them = []
    mau = ds[0]
    for ma, nhan in MUC_MOI:
        if ma in co:
            continue
        if isinstance(mau, dict):
            d = {k: "" for k in mau.keys()}
            for k in ("ma", "id", "key", "code"):
                if k in d:
                    d[k] = ma
            for k in ("ten", "nhan", "label", "title", "text"):
                if k in d:
                    d[k] = nhan
            d.setdefault("ma", ma)
            d.setdefault("ten", nhan)
            them.append(d)
        else:
            them.append((ma, nhan))
    if them:
        ds[vt:vt] = them
        kho.MENU_TRAI = ds
        for doi_tuong in (app_goc, getattr(app_goc, "kho", None)):
            try:
                if doi_tuong is not None:
                    doi_tuong.MENU_TRAI = ds
            except Exception:
                pass
    return ds


# ---------------------------------------------------------------- man hinh moi
LOI_NAP = {}


def nap_lop():
    lop = {}
    if AN_TOAN:
        return lop
    try:
        import man_hinh_moi
        lop.update(getattr(man_hinh_moi, "LOP_MAN_HINH", {}) or {})
    except Exception:
        LOI_NAP["man_hinh_moi"] = traceback.format_exc()
    try:
        import trang_chu_pro
        l = getattr(trang_chu_pro, "TrangChuPro", None) or getattr(trang_chu_pro, "ManHinh", None)
        if l is not None:
            lop["trang_chu"] = l
    except Exception:
        LOI_NAP["trang_chu_pro"] = traceback.format_exc()
    try:
        import man_hinh_ncc
        l = getattr(man_hinh_ncc, "ManHinhNCC", None) or getattr(man_hinh_ncc, "ManHinh", None)
        if l is not None:
            lop["ncc"] = l
    except Exception:
        LOI_NAP["man_hinh_ncc"] = traceback.format_exc()
    try:
        import huong_dan
        l = getattr(huong_dan, "ManHinhHuongDan", None)
        if l is not None:
            lop["huong_dan"] = l
            lop["huong_dan_su_dung"] = l
    except Exception:
        LOI_NAP["huong_dan"] = traceback.format_exc()
    return lop


class ManHinhLoi(ctk.CTkFrame):
    def __init__(self, master, ma, noi_dung, **kw):
        super().__init__(master, fg_color="#F4F7FB", **kw)
        ctk.CTkLabel(self, text="Màn hình \"%s\" không dựng được" % ma,
                     font=("Segoe UI", 16, "bold"), text_color="#C62828"
                     ).pack(anchor="w", padx=16, pady=(16, 4))
        ctk.CTkLabel(self, text="Các màn hình khác vẫn dùng bình thường. "
                                "Chép nguyên văn phần bên dưới để sửa lỗi:",
                     font=("Segoe UI", 12), text_color="#64748B"
                     ).pack(anchor="w", padx=16, pady=(0, 8))
        tb = ctk.CTkTextbox(self, font=("Consolas", 11), wrap="none")
        tb.pack(fill="both", expand=True, padx=16, pady=(0, 16))
        tb.insert("1.0", noi_dung)


# ---------------------------------------------------------------- ung dung
class UngDungMoi(app_goc.UngDung):

    def __init__(self, *a, **kw):
        self._lop_moi = nap_lop()
        self._mh_moi = {}
        self._hong = set()
        self._hen_tuoi = None
        self.k_gd = 1.0
        super().__init__(*a, **kw)

        self.k_gd = gd.ap_dung(self)
        gd.co_cua_so(self)
        gd.gan_phim_tat(self, self._sau_doi_ty_le)
        try:
            self.title("TAX INVOICE PRO %s — Chế độ ngoại tuyến — đọc dữ liệu đã lưu trên máy"
                       % PHIEN_BAN)
        except Exception:
            pass

        if giam_sat is not None and not KHONG_GIAM_SAT:
            giam_sat.bat_dau(self, nguong=8.0)
            giam_sat.bao_ve_luong(self)
        if bo_cuc is not None:
            bo_cuc.bat_dau_quet(self)

        self._lam_tuoi(250)
        self.protocol("WM_DELETE_WINDOW", self._dong)

    # -- tien ich -----------------------------------------------------------
    def _vung_noi_dung(self):
        for ten in ("vung", "vung_noi_dung", "khung_noi_dung", "noi_dung",
                    "khung_chinh", "content", "main", "body"):
            w = getattr(self, ten, None)
            if isinstance(w, tk.Misc):
                try:
                    if w.winfo_exists():
                        return w
                except Exception:
                    pass
        return None

    def _lam_tuoi(self, tre=60):
        try:
            if self._hen_tuoi:
                self.after_cancel(self._hen_tuoi)
        except Exception:
            pass
        try:
            self._hen_tuoi = self.after(tre, self._chay_lam_tuoi)
        except Exception:
            self._hen_tuoi = None

    def _chay_lam_tuoi(self):
        self._hen_tuoi = None
        try:
            gd.dong_bo_bang(self, self.k_gd)
        except Exception:
            ghi_log("WARN", "Làm tươi hiển thị lỗi:\n%s" % traceback.format_exc())

    def _sau_doi_ty_le(self, k, hs):
        self.k_gd = k
        gd.co_cua_so(self)
        self._lam_tuoi(80)
        ghi_log("INFO", "Đổi tỷ lệ hiển thị: %.2f (hệ số người dùng %.2f)" % (k, hs))

    def _danh_dau_menu(self, ma):
        for ten in ("to_nut_menu", "danh_dau_menu", "chon_menu", "_to_menu", "cap_nhat_menu"):
            ham = getattr(self, ten, None)
            if callable(ham):
                try:
                    ham(ma)
                    return
                except Exception:
                    pass
        for ten in ("nut_menu", "nut", "nut_trai", "cac_nut", "menu_nut", "nut_mh"):
            d = getattr(self, ten, None)
            if isinstance(d, dict) and ma in d:
                for k, b in d.items():
                    try:
                        b.configure(fg_color=("#1565C0" if k == ma else "transparent"))
                    except Exception:
                        pass
                return

    # -- chuyen man hinh ----------------------------------------------------
    def hien_man_hinh(self, ma, *a, **kw):
        vung = self._vung_noi_dung()
        gd.don_vung(vung)

        lop = self._lop_moi.get(ma)
        if lop is None or ma in self._hong:
            try:
                super().hien_man_hinh(ma, *a, **kw)
            except Exception:
                loi = traceback.format_exc()
                ghi_log("ERROR", "Màn hình %s lỗi:\n%s" % (ma, loi))
                if vung is not None:
                    gd.hien(ManHinhLoi(vung, ma, loi))
            self._ket_thuc(ma)
            return

        if vung is None:
            ghi_log("ERROR", "Không tìm thấy vùng nội dung trong app.py")
            return

        mh = self._mh_moi.get(ma)
        try:
            if mh is not None and not mh.winfo_exists():
                mh = None
        except Exception:
            mh = None

        if mh is None:
            loi = ""
            for doi_so in ((vung, self), (vung,)):
                try:
                    mh = lop(*doi_so)
                    break
                except TypeError:
                    loi = traceback.format_exc()
                    mh = None
                    continue
                except Exception:
                    loi = traceback.format_exc()
                    mh = None
                    break
            if mh is None:
                self._hong.add(ma)
                ghi_log("ERROR", "Không dựng được màn hình %s:\n%s" % (ma, loi))
                mh = ManHinhLoi(vung, ma, loi)
            self._mh_moi[ma] = mh

        gd.hien(mh)
        self._ket_thuc(ma)

    def _ket_thuc(self, ma):
        try:
            self.man_hinh_hien_tai = ma
        except Exception:
            pass
        self._danh_dau_menu(ma)
        self._lam_tuoi(60)
        ghi_log("INFO", "Mở màn hình: %s" % ma)

    # -- dong ung dung ------------------------------------------------------
    def _dong(self):
        try:
            ch = gd.doc_ch()
            ch["rong"] = int(self.winfo_width() / max(0.7, self.k_gd))
            ch["cao"] = int(self.winfo_height() / max(0.7, self.k_gd))
            gd.ghi_ch(ch)
        except Exception:
            pass
        if bo_cuc is not None:
            try:
                bo_cuc.dung_quet()
            except Exception:
                pass
        if giam_sat is not None:
            try:
                giam_sat.dung_dich_vu()
                if giam_sat.so_lan_treo():
                    ghi_log("WARN", "Phiên này ghi nhận %d lần giao diện không phản hồi "
                                    "(xem logs\\treo.txt)." % giam_sat.so_lan_treo())
                giam_sat.dung()
            except Exception:
                pass
        try:
            self.destroy()
        except Exception:
            pass


# ---------------------------------------------------------------- chay
def main():
    ghi_log("INFO", "Khởi động TAX INVOICE PRO %s%s" %
            (PHIEN_BAN, " (chế độ an toàn)" if AN_TOAN else ""))
    ds = chen_menu()
    ghi_log("INFO", "Menu trái: %d mục — %s" % (len(ds), ", ".join(_ma_muc(m) for m in ds)))
    for ten, loi in LOI_NAP.items():
        ghi_log("ERROR", "Không nạp được %s:\n%s" % (ten, loi))
    try:
        ctk.set_appearance_mode("light")
    except Exception:
        pass
    try:
        ung_dung = UngDungMoi()
    except Exception:
        loi = traceback.format_exc()
        ghi_log("ERROR", "Không khởi tạo được cửa sổ chính:\n%s" % loi)
        print(loi)
        try:
            from tkinter import messagebox
            messagebox.showerror("TAX INVOICE PRO", loi[-1500:])
        except Exception:
            pass
        return 1
    ung_dung.mainloop()
    if giam_sat is not None:
        con = giam_sat.luong_con_song()
        if con:
            ghi_log("WARN", "Còn luồng chưa dừng: %s" % ", ".join(con))
    ghi_log("INFO", "Đã đóng ứng dụng.")
    return 0


if __name__ == "__main__":
    sys.exit(main())


TEP_DAY_DU = True  # dau hieu tep da duoc dan day du - dung xoa dong nay
