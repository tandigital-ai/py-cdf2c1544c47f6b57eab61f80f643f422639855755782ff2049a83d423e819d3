# -*- coding: utf-8 -*-
"""
TAX INVOICE PRO v1.0.0
Thanh công cụ, bảng kết quả (ttk.Treeview), phân trang và ba thẻ cuối trang.
Tác giả: TDA - Điện thoại: 0986509106
"""

import math
from datetime import datetime
from tkinter import ttk

import customtkinter as ctk

import store

F_SM = ("Segoe UI", 11)
F_MD = ("Segoe UI", 12)
F_MD_B = ("Segoe UI", 12, "bold")
F_LG_B = ("Segoe UI", 15, "bold")

TICK_ON = "☑"
TICK_OFF = "☐"
THAO_TAC = "[XML]  [IN]  [MỞ]"
SO_BAN_GHI = ["10", "20", "50", "100"]


def _cai_dat_style():
    style = ttk.Style()
    try:
        style.theme_use("clam")
    except Exception:
        pass
    style.configure("Invoice.Treeview",
                    background="white", fieldbackground="white",
                    foreground=store.TEXT, rowheight=28,
                    font=("Segoe UI", 11), borderwidth=0)
    style.configure("Invoice.Treeview.Heading",
                    background=store.HEAD_BG, foreground=store.BLUE_SIDE,
                    font=("Segoe UI", 11, "bold"), relief="flat", padding=(4, 7))
    style.map("Invoice.Treeview.Heading", background=[("active", "#D6E7FA")])
    style.map("Invoice.Treeview",
              background=[("selected", "#CFE4FB")],
              foreground=[("selected", store.BLUE_SIDE)])
    style.layout("Invoice.Treeview", [("Invoice.Treeview.treearea", {"sticky": "nswe"})])


class ResultTable(ctk.CTkFrame):
    """Thanh công cụ + bảng + phân trang."""

    def __init__(self, master, actions, page_size=10, on_doi_so_dong=None):
        super().__init__(master, fg_color=store.CARD, corner_radius=10,
                         border_width=1, border_color=store.BORDER)
        _cai_dat_style()
        self.actions = actions or {}
        self.on_doi_so_dong = on_doi_so_dong
        self.data = []
        self.chon = set()
        self.trang = 1
        self.page_size = int(page_size or 10)
        self.sort_key = "ngay_lap"
        self.sort_desc = False
        self._row_map = {}

        # ---- thanh công cụ -------------------------------------------------
        tool = ctk.CTkFrame(self, fg_color="transparent")
        tool.pack(fill="x", padx=14, pady=(12, 6))
        self.lb_title = ctk.CTkLabel(tool, text="KẾT QUẢ TRA CỨU (0 hóa đơn)",
                                     font=F_LG_B, text_color=store.BLUE_SIDE)
        self.lb_title.pack(side="left")

        def nut(text, mau, cmd, w=104):
            return ctk.CTkButton(tool, text=text, width=w, height=28, font=F_SM,
                                 corner_radius=6, fg_color=mau, command=cmd)

        nut("Xuất Excel", "#1E8E3E", lambda: self._goi("excel"), 96).pack(side="right", padx=3)
        nut("Tải XML + PDF", "#8E24AA", lambda: self._goi("xml_pdf"), 112).pack(side="right", padx=3)
        nut("Tải PDF", "#E53935", lambda: self._goi("pdf"), 84).pack(side="right", padx=3)
        nut("Tải XML", "#0288D1", lambda: self._goi("xml"), 84).pack(side="right", padx=3)
        nut("Bỏ chọn", "#90A4AE", self.bo_chon_tat_ca, 84).pack(side="right", padx=3)
        nut("Chọn tất cả", store.BLUE_TOP, self.chon_tat_ca, 104).pack(side="right", padx=3)

        # ---- bảng ----------------------------------------------------------
        khung = ctk.CTkFrame(self, fg_color="transparent")
        khung.pack(fill="both", expand=True, padx=14)
        khung.grid_rowconfigure(0, weight=1)
        khung.grid_columnconfigure(0, weight=1)

        cols = [c[0] for c in store.COT_BANG]
        self.tree = ttk.Treeview(khung, columns=cols, show="headings", height=10,
                                 style="Invoice.Treeview", selectmode="browse")
        for khoa, nhan, w, anchor in store.COT_BANG:
            if khoa in store.COT_SAP_XEP:
                self.tree.heading(khoa, text=nhan, anchor="center",
                                  command=lambda k=khoa: self.doi_sap_xep(k))
            else:
                self.tree.heading(khoa, text=nhan, anchor="center")
            self.tree.column(khoa, width=w, minwidth=w, anchor=anchor, stretch=False)

        vsb = ttk.Scrollbar(khung, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(khung, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")

        self.tree.tag_configure("le", background="white")
        self.tree.tag_configure("chan", background=store.STRIPE)
        for tt, mau in store.MAU_TRANG_THAI.items():
            self.tree.tag_configure("tt_" + tt, foreground=mau)
        self.tree.bind("<Button-1>", self._click)

        # ---- phân trang ----------------------------------------------------
        self.pager = ctk.CTkFrame(self, fg_color="transparent", height=40)
        self.pager.pack(fill="x", padx=14, pady=(6, 12))

        self.refresh()

    # -- dữ liệu -------------------------------------------------------------
    def set_data(self, data, giu_chon=False):
        self.data = list(data or [])
        if not giu_chon:
            self.chon.clear()
        else:
            ids = set(i["id"] for i in self.data)
            self.chon &= ids
        self.trang = 1
        self._sap_xep()
        self.refresh()

    def du_lieu_hien_tai(self):
        return list(self.data)

    def danh_sach_chon(self):
        return [i for i in self.data if i["id"] in self.chon]

    def _sap_xep(self):
        self.data = store.sap_xep(self.data, self.sort_key, self.sort_desc)

    def doi_sap_xep(self, khoa):
        if khoa == self.sort_key:
            self.sort_desc = not self.sort_desc
        else:
            self.sort_key = khoa
            self.sort_desc = False
        self._sap_xep()
        self.refresh()

    def chon_tat_ca(self):
        # chỉ tác động lên các dòng đang hiển thị sau lọc
        self.chon = set(i["id"] for i in self.data)
        self.refresh()

    def bo_chon_tat_ca(self):
        self.chon.clear()
        self.refresh()

    def dat_so_dong(self, n):
        self.page_size = int(n)
        self.trang = 1
        self.refresh()
        if self.on_doi_so_dong:
            self.on_doi_so_dong(self.page_size)

    # -- vẽ ------------------------------------------------------------------
    def so_trang(self):
        return max(1, math.ceil(len(self.data) / self.page_size))

    def refresh(self):
        for khoa, nhan, _w, _a in store.COT_BANG:
            if khoa in store.COT_SAP_XEP:
                mui = ""
                if khoa == self.sort_key:
                    mui = "  ▼" if self.sort_desc else "  ▲"
                self.tree.heading(khoa, text=nhan + mui)

        self.lb_title.configure(text="KẾT QUẢ TRA CỨU (%d hóa đơn)" % len(self.data))
        self.tree.delete(*self.tree.get_children())
        self._row_map.clear()

        if self.trang > self.so_trang():
            self.trang = self.so_trang()
        dau = (self.trang - 1) * self.page_size
        phan = self.data[dau:dau + self.page_size]

        for i, inv in enumerate(phan):
            tt = inv.get("trang_thai", "")
            vals = (
                TICK_ON if inv["id"] in self.chon else TICK_OFF,
                dau + i + 1,
                store.fmt_date(inv.get("ngay_lap")),
                inv.get("so_hoa_don", ""),
                inv.get("ky_hieu_mau_so", ""),
                inv.get("ky_hieu_hoa_don", ""),
                inv.get("mst_nguoi_ban", ""),
                inv.get("ten_nguoi_ban", ""),
                store.fmt_money(inv.get("tien_hang")),
                store.fmt_money(inv.get("thue_gtgt")),
                store.fmt_money(inv.get("tong_tien")),
                "● " + tt,
                THAO_TAC,
            )
            tags = ("chan" if i % 2 else "le", "tt_" + tt if tt in store.MAU_TRANG_THAI else "le")
            self.tree.insert("", "end", iid=inv["id"], values=vals, tags=tags)
            self._row_map[inv["id"]] = inv

        self._ve_phan_trang()

    def _ve_phan_trang(self):
        for w in self.pager.winfo_children():
            w.destroy()
        tong = len(self.data)
        dau = 0 if tong == 0 else (self.trang - 1) * self.page_size + 1
        cuoi = min(self.trang * self.page_size, tong)
        ctk.CTkLabel(self.pager,
                     text="Hiển thị %d - %d của %d bản ghi" % (dau, cuoi, tong),
                     font=F_SM, text_color=store.MUTED).pack(side="left")

        phai = ctk.CTkFrame(self.pager, fg_color="transparent")
        phai.pack(side="right")
        ctk.CTkOptionMenu(phai, values=SO_BAN_GHI, width=70, height=26, font=F_SM,
                          fg_color="white", text_color=store.TEXT,
                          button_color="#DCE9F9", button_hover_color="#C5DAF4",
                          dropdown_font=F_SM,
                          variable=ctk.StringVar(value=str(self.page_size)),
                          command=lambda v: self.dat_so_dong(int(v))).pack(side="right")
        ctk.CTkLabel(phai, text="Số bản ghi/trang:", font=F_SM,
                     text_color=store.MUTED).pack(side="right", padx=(0, 6))

        giua = ctk.CTkFrame(self.pager, fg_color="transparent")
        giua.pack(side="right", padx=18)
        sp = self.so_trang()

        def nut_nho(text, cmd, active=False, enable=True):
            ctk.CTkButton(giua, text=text, width=28, height=26, font=F_SM,
                          corner_radius=5,
                          fg_color=store.BLUE_TOP if active else "white",
                          text_color="white" if active else store.TEXT,
                          hover_color="#DCE9F9" if not active else store.BLUE_SIDE,
                          border_width=1, border_color=store.BORDER,
                          state="normal" if enable else "disabled",
                          command=cmd).pack(side="left", padx=2)

        nut_nho("«", lambda: self._di_trang(1), enable=self.trang > 1)
        nut_nho("‹", lambda: self._di_trang(self.trang - 1), enable=self.trang > 1)
        d = max(1, min(self.trang - 2, sp - 4))
        for p in range(d, min(sp, d + 4) + 1):
            nut_nho(str(p), lambda x=p: self._di_trang(x), active=(p == self.trang))
        nut_nho("›", lambda: self._di_trang(self.trang + 1), enable=self.trang < sp)
        nut_nho("»", lambda: self._di_trang(sp), enable=self.trang < sp)

    def _di_trang(self, p):
        self.trang = max(1, min(int(p), self.so_trang()))
        self.refresh()

    # -- tương tác -----------------------------------------------------------
    def _goi(self, ten):
        fn = self.actions.get(ten)
        if fn:
            fn()

    def _click(self, event):
        if self.tree.identify("region", event.x, event.y) != "cell":
            return
        iid = self.tree.identify_row(event.y)
        if not iid:
            return
        col = self.tree.identify_column(event.x)
        try:
            idx = int(col.replace("#", "")) - 1
        except ValueError:
            return
        if idx < 0 or idx >= len(store.COT_BANG):
            return
        khoa = store.COT_BANG[idx][0]
        inv = self._row_map.get(iid)
        if inv is None:
            return

        if khoa == "sel":
            if iid in self.chon:
                self.chon.discard(iid)
            else:
                self.chon.add(iid)
            self.tree.set(iid, "sel", TICK_ON if iid in self.chon else TICK_OFF)
            return "break"

        if khoa == "thao_tac":
            box = self.tree.bbox(iid, col)
            if not box:
                return
            x, _y, w, _h = box
            vung = int((event.x - x) / max(1, w / 3))
            vung = max(0, min(2, vung))
            fn = self.actions.get("dong_" + ("xml", "pdf", "mo")[vung])
            if fn:
                fn(inv)
            return "break"


# ----------------------------------------------------------------------------
# Ba thẻ cuối trang
# ----------------------------------------------------------------------------
class FooterCards(ctk.CTkFrame):
    def __init__(self, master, thu_muc, on_chon_thu_muc, on_mo_thu_muc):
        super().__init__(master, fg_color="transparent")
        self.grid_columnconfigure(0, weight=5)
        self.grid_columnconfigure(1, weight=3)
        self.grid_columnconfigure(2, weight=3)

        def the(col, tieu_de):
            f = ctk.CTkFrame(self, fg_color=store.CARD, corner_radius=10,
                             border_width=1, border_color=store.BORDER)
            f.grid(row=0, column=col, sticky="nsew", padx=(0 if col == 0 else 10, 0))
            ctk.CTkLabel(f, text=tieu_de, font=F_MD_B, text_color=store.BLUE_SIDE
                         ).pack(anchor="w", padx=14, pady=(10, 4))
            return f

        # Thẻ 1 - thư mục lưu trữ
        f1 = the(0, "THƯ MỤC LƯU TRỮ")
        hang = ctk.CTkFrame(f1, fg_color="transparent")
        hang.pack(fill="x", padx=14, pady=(0, 12))
        hang.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(hang, text="Đường dẫn lưu file:", font=F_SM,
                     text_color=store.LABEL).grid(row=0, column=0, padx=(0, 8))
        self.var_folder = ctk.StringVar(value=thu_muc)
        e = ctk.CTkEntry(hang, textvariable=self.var_folder, height=30, font=F_SM,
                         fg_color="#F7FAFF", text_color=store.TEXT,
                         border_color=store.BORDER)
        e.grid(row=0, column=1, sticky="ew")
        e.configure(state="readonly")
        ctk.CTkButton(hang, text="Chọn thư mục", width=110, height=30, font=F_SM,
                      corner_radius=6, fg_color=store.BLUE_TOP,
                      command=on_chon_thu_muc).grid(row=0, column=2, padx=(8, 0))
        ctk.CTkButton(hang, text="Mở", width=46, height=30, font=F_SM, corner_radius=6,
                      fg_color="#90A4AE", hover_color="#78909C",
                      command=on_mo_thu_muc).grid(row=0, column=3, padx=(6, 0))

        # Thẻ 2 - thông tin hệ thống
        f2 = the(1, "THÔNG TIN HỆ THỐNG")
        self.lb_tt = ctk.CTkLabel(f2, text="Trạng thái:  ● Đã sẵn sàng", font=F_SM,
                                  text_color=store.GREEN, anchor="w")
        self.lb_tt.pack(anchor="w", padx=14)
        self.lb_gio = ctk.CTkLabel(f2, text="Thời gian:", font=F_SM,
                                   text_color=store.MUTED, anchor="w")
        self.lb_gio.pack(anchor="w", padx=14, pady=(2, 12))

        # Thẻ 3 - thống kê
        f3 = the(2, "THỐNG KÊ")
        self.lb_tong = ctk.CTkLabel(f3, text="Tổng số hóa đơn:  0", font=F_SM,
                                    text_color=store.TEXT, anchor="w")
        self.lb_tong.pack(anchor="w", padx=14)
        self.lb_datai = ctk.CTkLabel(f3, text="Đã tải:  0", font=F_SM,
                                     text_color=store.GREEN, anchor="w")
        self.lb_datai.pack(anchor="w", padx=14, pady=2)
        self.lb_chuatai = ctk.CTkLabel(f3, text="Chưa tải:  0", font=F_SM,
                                       text_color=store.ORANGE, anchor="w")
        self.lb_chuatai.pack(anchor="w", padx=14, pady=(0, 12))

        self._tick()

    def _tick(self):
        self.lb_gio.configure(text="Thời gian:  " +
                                   datetime.now().strftime("%d/%m/%Y %H:%M:%S"))
        self.after(1000, self._tick)

    def dat_thu_muc(self, path):
        self.var_folder.set(path)

    def dat_thong_ke(self, tong, da_tai, chua_tai):
        self.lb_tong.configure(text="Tổng số hóa đơn:  %d" % tong)
        self.lb_datai.configure(text="Đã tải:  %d" % da_tai)
        self.lb_chuatai.configure(text="Chưa tải:  %d" % chua_tai)

    def dat_trang_thai(self, text, mau=None):
        self.lb_tt.configure(text="Trạng thái:  ● " + text,
                             text_color=mau or store.GREEN)