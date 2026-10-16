# -*- coding: utf-8 -*-
"""
invoice_view.py - TAX INVOICE PRO v1.2.0
Cua so xem chi tiet mot hoa don dien tu doc tu tep XML.
Tac gia: TDA - 0986509106
"""

import os
import tempfile
import tkinter as tk
from tkinter import ttk

import customtkinter as ctk

import exporter
import invoice_render
import kho
import tt91


class CuaSoHoaDon(ctk.CTkToplevel):
    def __init__(self, cha, inv):
        super().__init__(cha)
        self.inv = inv
        self.title("Hóa đơn %s — số %s"
                   % (inv.get("ky_hieu_day_du"), inv.get("so_hoa_don")))
        self.geometry("1000x700")
        self.minsize(840, 560)
        self.configure(fg_color=kho.MAU_NEN)
        self._dung()
        self.after(120, self.lift)
        self.after(160, self.focus_force)

    # ------------------------------------------------------------------
    def _dung(self):
        inv = self.inv
        gm = inv.get("giai_ma_ky_hieu") or tt91.giai_ma_ky_hieu(
            inv.get("ky_hieu_mau_so"), inv.get("ky_hieu_hoa_don"),
            (inv.get("ngay_lap") or "")[:4])

        dau = ctk.CTkFrame(self, fg_color=kho.MAU_XANH, corner_radius=0)
        dau.pack(fill="x")
        ctk.CTkLabel(dau, text=(inv.get("ten_loai_day_du")
                                or inv.get("ten_hoa_don") or "HÓA ĐƠN ĐIỆN TỬ"),
                     font=ctk.CTkFont(size=16, weight="bold"),
                     text_color="#FFFFFF").pack(side="left", padx=16, pady=10)
        ctk.CTkLabel(dau, text="%s   •   Số %s   •   Ngày %s"
                     % (inv.get("ky_hieu_day_du"), inv.get("so_hoa_don"),
                        kho.fmt_ngay(inv.get("ngay_lap"))),
                     font=ctk.CTkFont(size=13), text_color="#D6E6FA"
                     ).pack(side="right", padx=16)

        than = ctk.CTkScrollableFrame(self, fg_color=kho.MAU_NEN)
        than.pack(fill="both", expand=True, padx=12, pady=10)

        self._khoi_doi(than, "NGƯỜI BÁN", [
            ("Tên đơn vị", inv.get("ten_nguoi_ban")),
            ("Mã số thuế", inv.get("mst_nguoi_ban")),
            ("Địa chỉ", inv.get("dia_chi_nguoi_ban")),
            ("Điện thoại", inv.get("sdt_nguoi_ban")),
            ("Số tài khoản", inv.get("stk_nguoi_ban")),
        ], "NGƯỜI MUA", [
            ("Tên đơn vị", inv.get("ten_nguoi_mua")),
            ("Mã số thuế", inv.get("mst_nguoi_mua")),
            ("Số CCCD", inv.get("cccd_nguoi_mua")),
            ("Địa chỉ", inv.get("dia_chi_nguoi_mua")),
            ("Người mua hàng", inv.get("nguoi_mua_hang")),
            ("Hình thức thanh toán", inv.get("hinh_thuc_tt")),
        ])

        self._bang_hang(than)
        self._khoi_tong(than)

        lq = inv.get("hoa_don_lien_quan") or {}
        if lq.get("so_hoa_don") or lq.get("ly_do"):
            self._hop(than, "HÓA ĐƠN LIÊN QUAN", kho.MAU_TIM,
                      "%s cho hóa đơn số %s, ký hiệu %s%s, ngày %s\nLý do: %s"
                      % (lq.get("tinh_chat") or "Liên quan",
                         lq.get("so_hoa_don") or "", lq.get("ma_mau_so") or "",
                         lq.get("ky_hieu") or "",
                         kho.fmt_ngay(lq.get("ngay_lap")),
                         lq.get("ly_do") or "(không ghi)"))

        ky = inv.get("chu_ky") or []
        self._hop(than, "CHỮ KÝ SỐ", kho.MAU_LUC,
                  "\n".join("• %s: %s%s" % (
                      k.get("vai_tro"), k.get("ten"),
                      ("  — ký lúc " + k.get("thoi_diem"))
                      if k.get("thoi_diem") else "") for k in ky)
                  if ky else
                  "Tệp XML không chứa chữ ký số, hoặc chữ ký nằm ngoài tệp. "
                  "Phần mềm chỉ kiểm tra sự hiện diện, không xác thực giá trị "
                  "chữ ký.")

        self._hop(than, "THÔNG TIN KỸ THUẬT", kho.MAU_XANH_DAM,
                  "Giải mã ký hiệu: %s\nMã cơ quan thuế: %s\n"
                  "Phiên bản dữ liệu: %s   •   Đơn vị tiền: %s\n"
                  "Nguồn nạp: %s   •   Nạp lúc: %s\nTệp XML: %s"
                  % (gm.get("mo_ta") or "", inv.get("ma_cqt") or "(không có)",
                     inv.get("phien_ban_xml") or "", inv.get("don_vi_tien_te"),
                     inv.get("nguon") or "", inv.get("ngay_nap") or "",
                     inv.get("duong_dan_xml") or "(không rõ)"))

        cb = inv.get("canh_bao") or []
        if cb:
            self._hop(than, "CẢNH BÁO KIỂM TRA SỐ LIỆU", kho.MAU_CAM,
                      "\n".join("• " + c for c in cb))

        self._thanh_nut()

    # ------------------------------------------------------------------
    def _the(self, cha, tieu_de, mau=None):
        k = ctk.CTkFrame(cha, fg_color=kho.MAU_TRANG, corner_radius=8,
                         border_width=1, border_color=kho.MAU_VIEN)
        ctk.CTkLabel(k, text=tieu_de, font=ctk.CTkFont(size=12, weight="bold"),
                     text_color=mau or kho.MAU_XANH_DAM).pack(
                         anchor="w", padx=12, pady=(8, 2))
        return k

    def _khoi_doi(self, cha, t1, ds1, t2, ds2):
        hang = ctk.CTkFrame(cha, fg_color="transparent")
        hang.pack(fill="x", pady=(0, 8))
        hang.grid_columnconfigure((0, 1), weight=1, uniform="a")
        for i, (tieu_de, ds) in enumerate(((t1, ds1), (t2, ds2))):
            k = self._the(hang, tieu_de)
            k.grid(row=0, column=i, sticky="nsew", padx=(0 if i == 0 else 6,
                                                         6 if i == 0 else 0))
            for nhan, gt in ds:
                if not gt:
                    continue
                d = ctk.CTkFrame(k, fg_color="transparent")
                d.pack(fill="x", padx=12, pady=1)
                ctk.CTkLabel(d, text=nhan + ":", width=130, anchor="w",
                             font=ctk.CTkFont(size=12),
                             text_color=kho.MAU_XAM).pack(side="left")
                ctk.CTkLabel(d, text=str(gt), anchor="w", justify="left",
                             wraplength=330,
                             font=ctk.CTkFont(size=12, weight="bold"),
                             text_color=kho.MAU_CHU).pack(side="left", fill="x")
            ctk.CTkLabel(k, text="").pack(pady=2)

    def _bang_hang(self, cha):
        dong = self.inv.get("dong_hang") or []
        k = self._the(cha, "CHI TIẾT HÀNG HÓA, DỊCH VỤ  (%d dòng)" % len(dong))
        k.pack(fill="x", pady=(0, 8))
        cot = [("stt", "STT", 46, "center"), ("ten_hang", "Tên hàng hóa, dịch vụ",
                                              300, "w"),
               ("dvt", "ĐVT", 70, "center"), ("so_luong", "Số lượng", 85, "e"),
               ("don_gia", "Đơn giá", 110, "e"),
               ("tien_ck", "Chiết khấu", 95, "e"),
               ("thanh_tien", "Thành tiền", 115, "e"),
               ("thue_suat", "Thuế suất", 80, "center")]
        khung = ctk.CTkFrame(k, fg_color=kho.MAU_TRANG)
        khung.pack(fill="x", padx=10, pady=(0, 10))
        cao = max(3, min(len(dong), 12))
        tv = ttk.Treeview(khung, columns=[c[0] for c in cot], show="headings",
                          height=cao, style="Xem.Treeview")
        for ma, nhan, rong, neo in cot:
            tv.heading(ma, text=nhan)
            tv.column(ma, width=rong, anchor=neo, stretch=(ma == "ten_hang"))
        for d in dong:
            tc = str(d.get("tinh_chat") or "1")
            ten = d.get("ten_hang") or ""
            if tc == "2":
                ten += "  (khuyến mại)"
            elif tc == "3":
                ten += "  (chiết khấu thương mại)"
            tv.insert("", "end", values=(
                d.get("stt"), ten, d.get("dvt") or "",
                invoice_render.fmt_sl(d.get("so_luong")),
                invoice_render.fmt_tien(d.get("don_gia"), 2),
                kho.fmt_tien(d.get("tien_ck")) if d.get("tien_ck") else "",
                kho.fmt_tien(d.get("thanh_tien")),
                d.get("thue_suat") or "\\"),
                tags=("km" if tc == "2" else "ck" if tc == "3" else ""))
        tv.tag_configure("km", foreground="#8A6D00")
        tv.tag_configure("ck", foreground="#A33")
        tv.pack(side="left", fill="x", expand=True)
        sb = ttk.Scrollbar(khung, orient="vertical", command=tv.yview)
        tv.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        if not dong:
            ctk.CTkLabel(k, text="Hóa đơn này không có chi tiết dòng hàng "
                                 "trong tệp XML.", text_color=kho.MAU_XAM,
                         font=ctk.CTkFont(size=12)).pack(padx=12, pady=(0, 8))

    def _khoi_tong(self, cha):
        inv = self.inv
        k = ctk.CTkFrame(cha, fg_color=kho.MAU_XANH_NHAT, corner_radius=8,
                         border_width=1, border_color="#B9D3F0")
        k.pack(fill="x", pady=(0, 8))
        ds = [("Cộng tiền hàng chưa thuế", inv.get("tien_hang")),
              ("Tiền thuế giá trị gia tăng", inv.get("thue_gtgt"))]
        if kho.to_int(inv.get("chiet_khau")):
            ds.append(("Chiết khấu thương mại", inv.get("chiet_khau")))
        if kho.to_int(inv.get("phi_khac")):
            ds.append(("Phí khác", inv.get("phi_khac")))
        for nhan, gt in ds:
            d = ctk.CTkFrame(k, fg_color="transparent")
            d.pack(fill="x", padx=14, pady=1)
            ctk.CTkLabel(d, text=nhan, font=ctk.CTkFont(size=12),
                         text_color=kho.MAU_XAM).pack(side="left")
            ctk.CTkLabel(d, text=kho.fmt_tien(gt),
                         font=ctk.CTkFont(size=13, weight="bold"),
                         text_color=kho.MAU_CHU).pack(side="right")
        d = ctk.CTkFrame(k, fg_color="transparent")
        d.pack(fill="x", padx=14, pady=(4, 2))
        ctk.CTkLabel(d, text="TỔNG TIỀN THANH TOÁN",
                     font=ctk.CTkFont(size=14, weight="bold"),
                     text_color=kho.MAU_XANH_DAM).pack(side="left")
        ctk.CTkLabel(d, text="%s %s" % (kho.fmt_tien(inv.get("tong_tien")),
                                        inv.get("don_vi_tien_te") or "VND"),
                     font=ctk.CTkFont(size=16, weight="bold"),
                     text_color=kho.MAU_XANH_DAM).pack(side="right")
        chu = inv.get("tong_tien_chu") or invoice_render.so_tien_bang_chu(
            inv.get("tong_tien"))
        ctk.CTkLabel(k, text="Bằng chữ: " + chu, anchor="w", wraplength=900,
                     font=ctk.CTkFont(size=12, slant="italic"),
                     text_color=kho.MAU_CHU).pack(fill="x", padx=14, pady=(0, 8))

    def _hop(self, cha, tieu_de, mau, noi_dung):
        k = self._the(cha, tieu_de, mau)
        k.pack(fill="x", pady=(0, 8))
        ctk.CTkLabel(k, text=noi_dung, anchor="w", justify="left",
                     wraplength=900, font=ctk.CTkFont(size=12),
                     text_color=kho.MAU_CHU).pack(fill="x", padx=12, pady=(0, 10))

    # ------------------------------------------------------------------
    def _thanh_nut(self):
        t = ctk.CTkFrame(self, fg_color=kho.MAU_TRANG, corner_radius=0,
                         height=54)
        t.pack(fill="x", side="bottom")
        ctk.CTkLabel(t, text="Tác giả: %s — Điện thoại: %s"
                     % (kho.TAC_GIA, kho.DIEN_THOAI),
                     font=ctk.CTkFont(size=11), text_color=kho.MAU_XAM
                     ).pack(side="left", padx=14)
        for nhan, mau, ham in (
                ("Đóng", "#6B7A8C", self.destroy),
                ("Mở tệp XML gốc", kho.MAU_XANH_DAM, self.mo_xml),
                ("Lưu bản thể hiện HTML", kho.MAU_LUC, self.luu_html),
                ("In / Lưu PDF", kho.MAU_XANH, self.in_pdf)):
            ctk.CTkButton(t, text=nhan, width=150, height=32, fg_color=mau,
                          hover=True, corner_radius=6, command=ham,
                          font=ctk.CTkFont(size=12, weight="bold")
                          ).pack(side="right", padx=6, pady=10)

    def mo_xml(self):
        d = self.inv.get("duong_dan_xml") or ""
        if not exporter.mo_duong_dan(d):
            self._bao("Không tìm thấy tệp XML gốc:\n%s" % (d or "(trống)"))

    def luu_html(self):
        thu_muc = kho.doc_cau_hinh().get("thu_muc_xuat") or os.getcwd()
        try:
            d = invoice_render.luu_html(self.inv, thu_muc)
        except OSError as e:
            self._bao("Không ghi được tệp: %s" % e)
            return
        exporter.mo_duong_dan(d)

    def in_pdf(self):
        try:
            d = os.path.join(tempfile.gettempdir(),
                             invoice_render.ten_tep_html(self.inv))
            invoice_render.luu_html(self.inv, duong_dan=d)
        except OSError as e:
            self._bao("Không tạo được bản thể hiện: %s" % e)
            return
        exporter.mo_duong_dan(d)
        kho.cap_nhat_truong(self.inv.get("khoa"), da_tai=1)
        self._bao("Bản thể hiện đã mở trong trình duyệt.\n\n"
                  "Nhấn Ctrl + P → chọn máy in “Microsoft Print to PDF” "
                  "hoặc “Save as PDF” → Lưu.")

    def _bao(self, noi_dung):
        h = ctk.CTkToplevel(self)
        h.title(kho.APP_NAME)
        h.geometry("460x200")
        h.configure(fg_color=kho.MAU_TRANG)
        ctk.CTkLabel(h, text=noi_dung, wraplength=420, justify="left",
                     font=ctk.CTkFont(size=12)).pack(padx=20, pady=20,
                                                     fill="both", expand=True)
        ctk.CTkButton(h, text="Đóng", width=100, command=h.destroy,
                      fg_color=kho.MAU_XANH).pack(pady=10)
        h.after(120, h.lift)
        h.grab_set()


def mo_cua_so(cha, inv):
    """Mo cua so xem hoa don. inv co the la dict rut gon (co 'khoa')."""
    if inv and inv.get("khoa") and not inv.get("dong_hang"):
        day_du = kho.lay_chi_tiet(inv["khoa"])
        if day_du:
            inv = day_du
    return CuaSoHoaDon(cha, inv)
