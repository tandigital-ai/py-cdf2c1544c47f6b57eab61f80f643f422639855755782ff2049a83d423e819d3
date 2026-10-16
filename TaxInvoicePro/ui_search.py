# -*- coding: utf-8 -*-
"""
TAX INVOICE PRO v1.0.0
Thanh trên cùng, cột trái, banner, khối THÔNG TIN TRA CỨU và bộ chọn ngày.
Tác giả: TDA - Điện thoại: 0986509106
"""

import calendar
from datetime import date

import customtkinter as ctk

import store

F_SM = ("Segoe UI", 11)
F_MD = ("Segoe UI", 12)
F_MD_B = ("Segoe UI", 12, "bold")
F_LG_B = ("Segoe UI", 15, "bold")
F_XL_B = ("Segoe UI", 19, "bold")


# ----------------------------------------------------------------------------
# Bộ chọn ngày (chỉ dùng thư viện chuẩn + customtkinter)
# ----------------------------------------------------------------------------
class ChonNgay(ctk.CTkToplevel):
    THU = ["T2", "T3", "T4", "T5", "T6", "T7", "CN"]

    def __init__(self, master, entry):
        super().__init__(master)
        self.entry = entry
        self.title("Chọn ngày")
        self.resizable(False, False)
        self.configure(fg_color=store.CARD)
        self.transient(master)

        iso = store.parse_date(entry.get())
        d = date.fromisoformat(iso) if iso else date.today()
        self.nam, self.thang = d.year, d.month

        head = ctk.CTkFrame(self, fg_color=store.BLUE_TOP, corner_radius=0, height=38)
        head.pack(fill="x")
        ctk.CTkButton(head, text="‹", width=30, height=26, font=F_MD_B,
                      fg_color=store.BLUE_DARK, hover_color=store.BLUE_SIDE,
                      command=lambda: self._doi_thang(-1)).pack(side="left", padx=6, pady=6)
        self.lb = ctk.CTkLabel(head, text="", font=F_MD_B, text_color="white")
        self.lb.pack(side="left", expand=True)
        ctk.CTkButton(head, text="›", width=30, height=26, font=F_MD_B,
                      fg_color=store.BLUE_DARK, hover_color=store.BLUE_SIDE,
                      command=lambda: self._doi_thang(1)).pack(side="right", padx=6, pady=6)

        self.grid_frame = ctk.CTkFrame(self, fg_color=store.CARD)
        self.grid_frame.pack(padx=8, pady=8)

        bot = ctk.CTkFrame(self, fg_color=store.CARD)
        bot.pack(fill="x", padx=8, pady=(0, 8))
        ctk.CTkButton(bot, text="Hôm nay", width=86, height=26, font=F_SM,
                      fg_color=store.BLUE_TOP, command=self._hom_nay).pack(side="left")
        ctk.CTkButton(bot, text="Xóa ngày", width=86, height=26, font=F_SM,
                      fg_color="#90A4AE", hover_color="#78909C",
                      command=self._xoa).pack(side="right")

        self._ve()
        self.update_idletasks()
        try:
            x = entry.winfo_rootx()
            y = entry.winfo_rooty() + entry.winfo_height() + 4
            self.geometry("+%d+%d" % (x, y))
        except Exception:
            pass
        self.grab_set()
        self.focus()

    def _doi_thang(self, delta):
        m = self.thang + delta
        y = self.nam
        if m < 1:
            m, y = 12, y - 1
        elif m > 12:
            m, y = 1, y + 1
        self.thang, self.nam = m, y
        self._ve()

    def _ve(self):
        for w in self.grid_frame.winfo_children():
            w.destroy()
        self.lb.configure(text="Tháng %02d / %d" % (self.thang, self.nam))
        for j, t in enumerate(self.THU):
            ctk.CTkLabel(self.grid_frame, text=t, width=34, font=F_SM,
                         text_color=store.MUTED).grid(row=0, column=j, padx=1, pady=2)
        cal = calendar.Calendar(firstweekday=0)
        for i, tuan in enumerate(cal.monthdayscalendar(self.nam, self.thang), start=1):
            for j, ngay in enumerate(tuan):
                if ngay == 0:
                    ctk.CTkLabel(self.grid_frame, text="", width=34).grid(row=i, column=j)
                    continue
                hom_nay = (date.today() == date(self.nam, self.thang, ngay))
                ctk.CTkButton(
                    self.grid_frame, text=str(ngay), width=34, height=26, font=F_SM,
                    corner_radius=4,
                    fg_color=store.BLUE_TOP if hom_nay else store.CARD,
                    text_color="white" if hom_nay else store.TEXT,
                    hover_color="#BBDEFB",
                    command=lambda d=ngay: self._chon(d)
                ).grid(row=i, column=j, padx=1, pady=1)

    def _chon(self, ngay):
        self.entry.delete(0, "end")
        self.entry.insert(0, "%02d/%02d/%d" % (ngay, self.thang, self.nam))
        self.destroy()

    def _hom_nay(self):
        d = date.today()
        self.nam, self.thang = d.year, d.month
        self._chon(d.day)

    def _xoa(self):
        self.entry.delete(0, "end")
        self.destroy()


# ----------------------------------------------------------------------------
# Thanh trên cùng
# ----------------------------------------------------------------------------
class TopBar(ctk.CTkFrame):
    def __init__(self, master, nguoi_dung, on_cai_dat, on_tai_khoan):
        super().__init__(master, fg_color=store.BLUE_TOP, corner_radius=0, height=56)
        self.pack_propagate(False)

        trai = ctk.CTkFrame(self, fg_color="transparent")
        trai.pack(side="left", padx=16)
        ctk.CTkLabel(trai, text="◆", font=("Segoe UI", 20, "bold"),
                     text_color="#90CAF9").pack(side="left", padx=(0, 8))
        ctk.CTkLabel(trai, text=store.APP_NAME, font=("Segoe UI", 17, "bold"),
                     text_color="white").pack(side="left")
        ctk.CTkLabel(trai, text=store.APP_VERSION, font=F_SM, text_color="white",
                     fg_color=store.BLUE_DARK, corner_radius=8,
                     width=48, height=20).pack(side="left", padx=8)
        ctk.CTkLabel(trai, text=store.APP_SLOGAN, font=F_MD,
                     text_color="#D6E8FB").pack(side="left", padx=10)

        phai = ctk.CTkFrame(self, fg_color="transparent")
        phai.pack(side="right", padx=16)
        ctk.CTkButton(phai, text="Kế toán Info  ▾", width=130, height=30, font=F_MD,
                      corner_radius=6, fg_color=store.BLUE_DARK,
                      hover_color="#08306B", command=on_tai_khoan).pack(side="right", padx=(8, 0))
        ctk.CTkButton(phai, text="Cài đặt", width=86, height=30, font=F_MD,
                      corner_radius=6, fg_color=store.BLUE_DARK,
                      hover_color="#08306B", command=on_cai_dat).pack(side="right")
        ctk.CTkLabel(phai, text="●  " + store.OFFLINE_TEXT, font=F_MD,
                     text_color="#0D47A1", fg_color="#E3F2FD", corner_radius=14,
                     height=28, padx=0).pack(side="right", padx=10, ipadx=12)


# ----------------------------------------------------------------------------
# Cột trái
# ----------------------------------------------------------------------------
class Sidebar(ctk.CTkFrame):
    def __init__(self, master, on_menu):
        super().__init__(master, fg_color=store.BLUE_SIDE, corner_radius=0, width=200)
        self.pack_propagate(False)
        self.grid_propagate(False)

        top = ctk.CTkFrame(self, fg_color="transparent")
        top.pack(fill="x", pady=(10, 0))
        for ten in store.MENU_TRAI:
            active = (ten == store.MENU_ACTIVE)
            btn = ctk.CTkButton(
                top, text="   " + ten, anchor="w", height=40, corner_radius=0,
                font=("Segoe UI", 12, "bold") if active else F_MD,
                fg_color=store.BLUE_SIDE_ACTIVE if active else "transparent",
                hover_color="#1565C0", text_color="white",
                command=(lambda t=ten: on_menu(t)))
            btn.pack(fill="x", padx=0, pady=1)

        duoi = ctk.CTkFrame(self, fg_color="#0A3C87", corner_radius=10)
        duoi.pack(side="bottom", fill="x", padx=12, pady=16)
        ctk.CTkLabel(duoi, text="HÓA ĐƠN\nĐIỆN TỬ", font=("Segoe UI", 13, "bold"),
                     text_color="#90CAF9", justify="center").pack(pady=(12, 6))
        ctk.CTkLabel(duoi, text="Đồng hành\ncùng kế toán Việt", font=F_SM,
                     text_color="#BBDEFB", justify="center").pack(pady=(0, 12))


# ----------------------------------------------------------------------------
# Banner
# ----------------------------------------------------------------------------
class Banner(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, fg_color="#E8F1FC", corner_radius=10,
                         border_width=1, border_color=store.BORDER, height=86)
        self.pack_propagate(False)

        trai = ctk.CTkFrame(self, fg_color="transparent")
        trai.pack(side="left", padx=18, pady=10)
        ctk.CTkLabel(trai, text=store.BANNER_TITLE, font=F_XL_B,
                     text_color=store.BLUE_SIDE).pack(anchor="w")
        ctk.CTkLabel(trai, text=store.BANNER_SUB, font=F_MD,
                     text_color=store.MUTED).pack(anchor="w", pady=(2, 0))

        phai = ctk.CTkFrame(self, fg_color="transparent")
        phai.pack(side="right", padx=20)
        ctk.CTkLabel(phai, text=store.BANNER_QUOTE_1, font=("Segoe UI", 12, "italic"),
                     text_color=store.BLUE_TOP).pack(anchor="e")
        ctk.CTkLabel(phai, text=store.BANNER_QUOTE_2, font=("Segoe UI", 12, "italic"),
                     text_color=store.BLUE_TOP).pack(anchor="e")


# ----------------------------------------------------------------------------
# Khối THÔNG TIN TRA CỨU
# ----------------------------------------------------------------------------
class SearchPanel(ctk.CTkFrame):
    def __init__(self, master, cfg, on_tra_cuu, on_tai_hoa_don, on_lam_moi):
        super().__init__(master, fg_color=store.CARD, corner_radius=10,
                         border_width=1, border_color=store.BORDER)
        self.cfg = cfg
        self.on_tra_cuu = on_tra_cuu
        self.on_tai_hoa_don = on_tai_hoa_don
        self.on_lam_moi = on_lam_moi
        self.entries = {}
        self.nang_cao_mo = False

        head = ctk.CTkFrame(self, fg_color="transparent")
        head.pack(fill="x", padx=16, pady=(12, 4))
        ctk.CTkLabel(head, text="THÔNG TIN TRA CỨU", font=F_LG_B,
                     text_color=store.BLUE_SIDE).pack(side="left")
        ctk.CTkButton(head, text="⟳  Làm mới", width=96, height=26, font=F_SM,
                      corner_radius=6, fg_color="#ECF3FC", text_color=store.BLUE_TOP,
                      hover_color="#DCE9F9", border_width=1, border_color=store.BORDER,
                      command=self._lam_moi).pack(side="right")

        luoi = ctk.CTkFrame(self, fg_color="transparent")
        luoi.pack(fill="x", padx=16, pady=(4, 2))
        for c in (1, 3, 5):
            luoi.grid_columnconfigure(c, weight=1, minsize=180)
        for c in (0, 2, 4):
            luoi.grid_columnconfigure(c, minsize=116)

        self._o_nhap(luoi, 0, 0, "MST người mua", "mst_nguoi_mua", "Nhập MST người mua")
        self._o_nhap(luoi, 0, 2, "CCCD người mua", "cccd_nguoi_mua", "Nhập CCCD (nếu có)")
        self._o_nhap(luoi, 0, 4, "Ký hiệu hóa đơn", "ky_hieu_hoa_don", "Nhập ký hiệu hóa đơn")

        self._o_chon(luoi, 1, 0, "Trạng thái", "trang_thai",
                     [store.TAT_CA] + store.TRANG_THAI_LIST)
        self._o_ngay(luoi, 1, 2, "Từ ngày", "tu_ngay")
        self._o_ngay(luoi, 1, 4, "Đến ngày", "den_ngay")

        self._o_nhap(luoi, 2, 0, "Số hóa đơn", "so_hoa_don", "Nhập số hóa đơn (nếu có)")
        self._o_nhap(luoi, 2, 2, "Ký hiệu mẫu số", "ky_hieu_mau_so", "Nhập ký hiệu mẫu số")
        self._o_chon(luoi, 2, 4, "Loại hóa đơn", "loai_hoa_don",
                     [store.TAT_CA] + store.LOAI_HD_LIST)

        # Nâng cao (mặc định thu gọn)
        self.btn_nc = ctk.CTkButton(
            self, text="▼  Nâng cao", width=120, height=26, font=F_MD,
            fg_color="transparent", text_color=store.BLUE_TOP, hover_color="#ECF3FC",
            anchor="w", command=self._toggle_nang_cao)
        self.btn_nc.pack(anchor="w", padx=12, pady=(4, 0))

        self.khung_nc = ctk.CTkFrame(self, fg_color="#F7FAFF", corner_radius=8,
                                     border_width=1, border_color=store.BORDER)
        for c in (1, 3, 5):
            self.khung_nc.grid_columnconfigure(c, weight=1, minsize=170)
        for c in (0, 2, 4):
            self.khung_nc.grid_columnconfigure(c, minsize=116)
        self._o_nhap(self.khung_nc, 0, 0, "Tên người bán", "ten_nguoi_ban",
                     "Nhập tên người bán")
        self._o_nhap(self.khung_nc, 0, 2, "MST người bán", "mst_nguoi_ban",
                     "Nhập MST người bán")
        self._o_nhap(self.khung_nc, 0, 4, "Tổng tiền từ", "tong_tien_tu", "0")
        self._o_nhap(self.khung_nc, 1, 4, "Tổng tiền đến", "tong_tien_den", "Không giới hạn")

        hang_nut = ctk.CTkFrame(self, fg_color="transparent")
        hang_nut.pack(fill="x", padx=16, pady=(10, 14))
        ctk.CTkButton(hang_nut, text="⬇   TẢI HÓA ĐƠN", width=186, height=40,
                      font=("Segoe UI", 13, "bold"), corner_radius=8,
                      fg_color=store.GREEN_BTN, hover_color=store.GREEN_BTN_HOVER,
                      command=self.on_tai_hoa_don).pack(side="right")
        ctk.CTkButton(hang_nut, text="🔍   TRA CỨU", width=186, height=40,
                      font=("Segoe UI", 13, "bold"), corner_radius=8,
                      fg_color=store.BLUE_TOP, hover_color=store.BLUE_SIDE,
                      command=self.on_tra_cuu).pack(side="right", padx=(0, 12))

        self.dat_mac_dinh()

    # -- widget con ----------------------------------------------------------
    def _nhan(self, parent, r, c, text):
        ctk.CTkLabel(parent, text=text, font=F_MD, text_color=store.LABEL,
                     anchor="w").grid(row=r, column=c, sticky="w", padx=(6, 8), pady=7)

    def _o_nhap(self, parent, r, c, nhan, khoa, placeholder):
        self._nhan(parent, r, c, nhan)
        e = ctk.CTkEntry(parent, height=32, font=F_MD, corner_radius=6,
                         fg_color="white", text_color=store.TEXT,
                         border_color=store.BORDER, placeholder_text=placeholder)
        e.grid(row=r, column=c + 1, sticky="ew", padx=(0, 18), pady=7)
        self.entries[khoa] = e
        e.bind("<Return>", lambda _e: self.on_tra_cuu())

    def _o_chon(self, parent, r, c, nhan, khoa, values):
        self._nhan(parent, r, c, nhan)
        var = ctk.StringVar(value=values[0])
        om = ctk.CTkOptionMenu(parent, values=values, variable=var, height=32,
                               font=F_MD, corner_radius=6, fg_color="white",
                               text_color=store.TEXT, button_color="#DCE9F9",
                               button_hover_color="#C5DAF4",
                               dropdown_font=F_MD, dropdown_fg_color="white",
                               dropdown_text_color=store.TEXT)
        om.grid(row=r, column=c + 1, sticky="ew", padx=(0, 18), pady=7)
        self.entries[khoa] = var

    def _o_ngay(self, parent, r, c, nhan, khoa):
        self._nhan(parent, r, c, nhan)
        box = ctk.CTkFrame(parent, fg_color="transparent")
        box.grid(row=r, column=c + 1, sticky="ew", padx=(0, 18), pady=7)
        box.grid_columnconfigure(0, weight=1)
        e = ctk.CTkEntry(box, height=32, font=F_MD, corner_radius=6, fg_color="white",
                         text_color=store.TEXT, border_color=store.BORDER,
                         placeholder_text="dd/mm/yyyy")
        e.grid(row=0, column=0, sticky="ew")
        ctk.CTkButton(box, text="📅", width=34, height=32, font=F_MD, corner_radius=6,
                      fg_color="#ECF3FC", text_color=store.BLUE_TOP,
                      hover_color="#DCE9F9",
                      command=lambda en=e: ChonNgay(self.winfo_toplevel(), en)
                      ).grid(row=0, column=1, padx=(4, 0))
        self.entries[khoa] = e
        e.bind("<Return>", lambda _e: self.on_tra_cuu())

    # -- hành vi -------------------------------------------------------------
    def _toggle_nang_cao(self):
        self.nang_cao_mo = not self.nang_cao_mo
        if self.nang_cao_mo:
            self.khung_nc.pack(fill="x", padx=16, pady=(6, 0), before=None)
            self.khung_nc.pack_configure(after=self.btn_nc)
            self.btn_nc.configure(text="▲  Nâng cao")
        else:
            self.khung_nc.pack_forget()
            self.btn_nc.configure(text="▼  Nâng cao")

    def _dat(self, khoa, gia_tri):
        w = self.entries[khoa]
        if isinstance(w, ctk.StringVar):
            w.set(gia_tri)
        else:
            w.delete(0, "end")
            if gia_tri:
                w.insert(0, gia_tri)

    def dat_mac_dinh(self):
        for khoa, w in self.entries.items():
            if isinstance(w, ctk.StringVar):
                w.set(store.TAT_CA)
            else:
                w.delete(0, "end")
        self._dat("mst_nguoi_mua", self.cfg.get("mst_mac_dinh", ""))
        self._dat("tu_ngay", self.cfg.get("tu_ngay_mac_dinh", ""))
        self._dat("den_ngay", self.cfg.get("den_ngay_mac_dinh", ""))

    def xoa_het(self):
        for khoa, w in self.entries.items():
            if isinstance(w, ctk.StringVar):
                w.set(store.TAT_CA)
            else:
                w.delete(0, "end")

    def _lam_moi(self):
        self.xoa_het()
        self.on_lam_moi()

    def lay_dieu_kien(self):
        dk = {}
        for khoa, w in self.entries.items():
            dk[khoa] = w.get().strip() if not isinstance(w, ctk.StringVar) else w.get()
        return dk