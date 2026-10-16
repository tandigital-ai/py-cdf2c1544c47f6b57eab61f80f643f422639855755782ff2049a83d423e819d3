# -*- coding: utf-8 -*-
"""
man_hinh_phu.py - TAX INVOICE PRO v1.2.0
Cac man hinh: Trang chu, Quan ly tep da tai, Lich su tra cuu, Thiet lap,
Huong dan su dung, Lien he ho tro.
Tac gia: TDA - 0986509106
"""

import os
import tkinter as tk
from tkinter import filedialog, ttk

import customtkinter as ctk

import exporter
import kho
import tt91


def _tieu_de(cha, chu, phu=""):
    k = ctk.CTkFrame(cha, fg_color="transparent")
    k.pack(fill="x", padx=18, pady=(14, 6))
    ctk.CTkLabel(k, text=chu, font=ctk.CTkFont(size=19, weight="bold"),
                 text_color=kho.MAU_XANH_DAM).pack(anchor="w")
    if phu:
        ctk.CTkLabel(k, text=phu, font=ctk.CTkFont(size=12),
                     text_color=kho.MAU_XAM).pack(anchor="w", pady=(2, 0))
    return k


def _the(cha, tieu_de):
    k = ctk.CTkFrame(cha, fg_color=kho.MAU_TRANG, corner_radius=10,
                     border_width=1, border_color=kho.MAU_VIEN)
    if tieu_de:
        ctk.CTkLabel(k, text=tieu_de, font=ctk.CTkFont(size=13, weight="bold"),
                     text_color=kho.MAU_XANH_DAM).pack(anchor="w", padx=14,
                                                       pady=(10, 4))
    return k


# ======================================================================
class TrangChu(ctk.CTkFrame):
    def __init__(self, cha, app):
        super().__init__(cha, fg_color=kho.MAU_NEN)
        self.app = app
        _tieu_de(self, "Trang chủ",
                 "Tổng quan kho hóa đơn điện tử đang lưu trên máy này")
        self.vung = ctk.CTkScrollableFrame(self, fg_color=kho.MAU_NEN)
        self.vung.pack(fill="both", expand=True, padx=18, pady=(0, 14))
        self.lam_moi()

    def lam_moi(self):
        for w in self.vung.winfo_children():
            w.destroy()
        tk_ = kho.thong_ke()
        tu, den = kho.khoang_thoi_gian()

        hang = ctk.CTkFrame(self.vung, fg_color="transparent")
        hang.pack(fill="x", pady=(0, 10))
        hang.grid_columnconfigure((0, 1, 2, 3), weight=1, uniform="a")
        the = [("Tổng số hóa đơn", "{:,}".format(tk_["tong"]).replace(",", "."),
                kho.MAU_XANH),
               ("Tổng tiền hàng", kho.fmt_tien(tk_["tien_hang"]), kho.MAU_LUC),
               ("Tổng thuế GTGT", kho.fmt_tien(tk_["thue"]), kho.MAU_CAM),
               ("Tổng thanh toán", kho.fmt_tien(tk_["tong_tien"]),
                kho.MAU_XANH_DAM)]
        for i, (nhan, gt, mau) in enumerate(the):
            k = ctk.CTkFrame(hang, fg_color=kho.MAU_TRANG, corner_radius=10,
                             border_width=1, border_color=kho.MAU_VIEN)
            k.grid(row=0, column=i, sticky="nsew", padx=(0 if i == 0 else 8, 0))
            ctk.CTkLabel(k, text=nhan, font=ctk.CTkFont(size=12),
                         text_color=kho.MAU_XAM).pack(anchor="w", padx=14,
                                                      pady=(12, 0))
            ctk.CTkLabel(k, text=gt, font=ctk.CTkFont(size=20, weight="bold"),
                         text_color=mau).pack(anchor="w", padx=14, pady=(0, 12))

        hang2 = ctk.CTkFrame(self.vung, fg_color="transparent")
        hang2.pack(fill="x", pady=(0, 10))
        hang2.grid_columnconfigure((0, 1), weight=1, uniform="b")

        k1 = _the(hang2, "Theo trạng thái")
        k1.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        self._bieu_do(k1, tk_["theo_trang_thai"],
                      lambda t: kho.MAU_TRANG_THAI.get(t, kho.MAU_XANH))
        k2 = _the(hang2, "Theo loại hóa đơn")
        k2.grid(row=0, column=1, sticky="nsew")
        self._bieu_do(k2, tk_["theo_loai"], lambda t: kho.MAU_XANH)

        k3 = _the(self.vung, "Tình trạng kho dữ liệu")
        k3.pack(fill="x", pady=(0, 10))
        ch = kho.doc_cau_hinh()
        ds = [("Khoảng thời gian dữ liệu",
               ("%s → %s" % (kho.fmt_ngay(tu), kho.fmt_ngay(den)))
               if tu else "(chưa có dữ liệu)"),
              ("Đã tải tệp XML về máy", "%d hóa đơn" % tk_["da_tai"]),
              ("Chưa có tệp XML", "%d hóa đơn" % tk_["chua_tai"]),
              ("Thư mục lưu trữ", ch.get("thu_muc_luu_tru")),
              ("Tệp cơ sở dữ liệu", kho.DUONG_DAN_DB),
              ("Chuẩn dữ liệu áp dụng", tt91.VAN_BAN_AP_DUNG)]
        for nhan, gt in ds:
            d = ctk.CTkFrame(k3, fg_color="transparent")
            d.pack(fill="x", padx=14, pady=2)
            ctk.CTkLabel(d, text=nhan + ":", width=200, anchor="w",
                         font=ctk.CTkFont(size=12),
                         text_color=kho.MAU_XAM).pack(side="left")
            ctk.CTkLabel(d, text=str(gt), anchor="w", wraplength=620,
                         justify="left",
                         font=ctk.CTkFont(size=12, weight="bold"),
                         text_color=kho.MAU_CHU).pack(side="left", fill="x")
        ctk.CTkLabel(k3, text="").pack(pady=2)

        nut = ctk.CTkFrame(self.vung, fg_color="transparent")
        nut.pack(fill="x", pady=(0, 14))
        ctk.CTkButton(nut, text="Tra cứu hóa đơn", width=180, height=38,
                      fg_color=kho.MAU_XANH,
                      command=lambda: self.app.hien_man_hinh("tra_cuu")
                      ).pack(side="left")
        ctk.CTkButton(nut, text="Nạp hóa đơn từ máy", width=180, height=38,
                      fg_color=kho.MAU_LUC,
                      command=self.app.mo_hop_nap).pack(side="left", padx=10)
        ctk.CTkButton(nut, text="Làm mới", width=120, height=38,
                      fg_color="#6B7A8C", command=self.lam_moi).pack(side="left")

    def _bieu_do(self, cha, du_lieu, ham_mau):
        if not du_lieu:
            ctk.CTkLabel(cha, text="Chưa có dữ liệu.", text_color=kho.MAU_XAM,
                         font=ctk.CTkFont(size=12)).pack(anchor="w", padx=14,
                                                         pady=(0, 12))
            return
        lon = max(du_lieu.values()) or 1
        for ten, n in sorted(du_lieu.items(), key=lambda x: -x[1]):
            d = ctk.CTkFrame(cha, fg_color="transparent")
            d.pack(fill="x", padx=14, pady=3)
            ctk.CTkLabel(d, text=ten, width=150, anchor="w",
                         font=ctk.CTkFont(size=12),
                         text_color=kho.MAU_CHU).pack(side="left")
            ctk.CTkLabel(d, text=str(n), width=46, anchor="e",
                         font=ctk.CTkFont(size=12, weight="bold"),
                         text_color=ham_mau(ten)).pack(side="right")
            thanh = ctk.CTkProgressBar(d, height=12, corner_radius=6,
                                       progress_color=ham_mau(ten),
                                       fg_color="#E7EDF5")
            thanh.pack(side="left", fill="x", expand=True, padx=8)
            thanh.set(n / lon)
        ctk.CTkLabel(cha, text="").pack(pady=2)


# ======================================================================
class QuanLyTep(ctk.CTkFrame):
    def __init__(self, cha, app):
        super().__init__(cha, fg_color=kho.MAU_NEN)
        self.app = app
        _tieu_de(self, "Quản lý tệp đã tải",
                 "Nhật ký các lần nạp dữ liệu và tệp XML đang lưu trong kho")
        thanh = ctk.CTkFrame(self, fg_color="transparent")
        thanh.pack(fill="x", padx=18, pady=(0, 6))
        ctk.CTkButton(thanh, text="Mở thư mục lưu trữ", width=170, height=32,
                      fg_color=kho.MAU_XANH, command=self.mo_thu_muc
                      ).pack(side="left")
        ctk.CTkButton(thanh, text="Nạp thêm hóa đơn", width=170, height=32,
                      fg_color=kho.MAU_LUC, command=self.app.mo_hop_nap
                      ).pack(side="left", padx=8)
        ctk.CTkButton(thanh, text="Làm mới", width=110, height=32,
                      fg_color="#6B7A8C", command=self.lam_moi).pack(side="left")
        ctk.CTkButton(thanh, text="Xóa nhật ký", width=130, height=32,
                      fg_color=kho.MAU_DO, command=self.xoa_nhat_ky
                      ).pack(side="right")

        khung = ctk.CTkFrame(self, fg_color=kho.MAU_TRANG, corner_radius=10,
                             border_width=1, border_color=kho.MAU_VIEN)
        khung.pack(fill="both", expand=True, padx=18, pady=(0, 8))
        cot = [("thoi_diem", "Thời điểm", 150), ("nguon", "Nguồn nạp", 210),
               ("duong_dan", "Đường dẫn", 420), ("tong_tep", "Số tệp", 70),
               ("them", "Thêm mới", 80), ("trung", "Trùng", 70),
               ("loi", "Lỗi", 60)]
        self.tv = ttk.Treeview(khung, columns=[c[0] for c in cot],
                               show="headings", style="Invoice.Treeview")
        for ma, nhan, rong in cot:
            self.tv.heading(ma, text=nhan)
            self.tv.column(ma, width=rong,
                           anchor="w" if ma in ("duong_dan", "nguon") else "center",
                           stretch=(ma == "duong_dan"))
        self.tv.pack(side="left", fill="both", expand=True, padx=(8, 0), pady=8)
        sb = ttk.Scrollbar(khung, orient="vertical", command=self.tv.yview)
        self.tv.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y", pady=8, padx=(0, 8))
        self.tv.bind("<Double-1>", self.xem_chi_tiet)

        self.o_log = ctk.CTkTextbox(self, height=150, fg_color=kho.MAU_TRANG,
                                    border_width=1, border_color=kho.MAU_VIEN,
                                    font=ctk.CTkFont(family="Consolas", size=12))
        self.o_log.pack(fill="x", padx=18, pady=(0, 14))
        self.lam_moi()

    def lam_moi(self):
        for i in self.tv.get_children():
            self.tv.delete(i)
        self.ds = kho.lay_nhat_ky_nap()
        for r in self.ds:
            self.tv.insert("", "end", iid=str(r["ma"]), values=(
                r["thoi_diem"], r["nguon"], r["duong_dan"], r["tong_tep"],
                r["them"], r["trung"], r["loi"]))
        self.o_log.configure(state="normal")
        self.o_log.delete("1.0", "end")
        self.o_log.insert("1.0", "Nháy đúp một dòng ở bảng trên để xem chi tiết "
                                 "từng tệp đã nạp.")
        self.o_log.configure(state="disabled")

    def xem_chi_tiet(self, _e=None):
        ch = self.tv.focus()
        if not ch:
            return
        for r in self.ds:
            if str(r["ma"]) == ch:
                self.o_log.configure(state="normal")
                self.o_log.delete("1.0", "end")
                self.o_log.insert("1.0", "\n".join(r["chi_tiet"])
                                  or "(không có chi tiết)")
                self.o_log.configure(state="disabled")
                return

    def mo_thu_muc(self):
        d = kho.doc_cau_hinh().get("thu_muc_luu_tru")
        if d and not os.path.isdir(d):
            try:
                os.makedirs(d, exist_ok=True)
            except OSError:
                pass
        exporter.mo_duong_dan(d)

    def xoa_nhat_ky(self):
        if self.app.hoi("Xóa toàn bộ nhật ký nạp?\n\n"
                        "Chỉ xóa lịch sử ghi chép, không xóa hóa đơn."):
            kho.xoa_nhat_ky_nap()
            self.lam_moi()


# ======================================================================
class LichSu(ctk.CTkFrame):
    def __init__(self, cha, app):
        super().__init__(cha, fg_color=kho.MAU_NEN)
        self.app = app
        _tieu_de(self, "Lịch sử tra cứu",
                 "Các lần tra cứu gần đây — nháy đúp để áp dụng lại bộ lọc")
        thanh = ctk.CTkFrame(self, fg_color="transparent")
        thanh.pack(fill="x", padx=18, pady=(0, 6))
        ctk.CTkButton(thanh, text="Làm mới", width=110, height=32,
                      fg_color="#6B7A8C", command=self.lam_moi).pack(side="left")
        ctk.CTkButton(thanh, text="Áp dụng lại", width=140, height=32,
                      fg_color=kho.MAU_XANH, command=self.ap_dung
                      ).pack(side="left", padx=8)
        ctk.CTkButton(thanh, text="Xóa lịch sử", width=130, height=32,
                      fg_color=kho.MAU_DO, command=self.xoa).pack(side="right")

        khung = ctk.CTkFrame(self, fg_color=kho.MAU_TRANG, corner_radius=10,
                             border_width=1, border_color=kho.MAU_VIEN)
        khung.pack(fill="both", expand=True, padx=18, pady=(0, 14))
        cot = [("thoi_diem", "Thời điểm", 160),
               ("mo_ta", "Điều kiện tra cứu", 700),
               ("so_ket_qua", "Số kết quả", 100)]
        self.tv = ttk.Treeview(khung, columns=[c[0] for c in cot],
                               show="headings", style="Invoice.Treeview")
        for ma, nhan, rong in cot:
            self.tv.heading(ma, text=nhan)
            self.tv.column(ma, width=rong, anchor="w" if ma == "mo_ta" else "center",
                           stretch=(ma == "mo_ta"))
        self.tv.pack(side="left", fill="both", expand=True, padx=(8, 0), pady=8)
        sb = ttk.Scrollbar(khung, orient="vertical", command=self.tv.yview)
        self.tv.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y", pady=8, padx=(0, 8))
        self.tv.bind("<Double-1>", lambda e: self.ap_dung())
        self.lam_moi()

    def lam_moi(self):
        for i in self.tv.get_children():
            self.tv.delete(i)
        self.ds = kho.lay_lich_su()
        for r in self.ds:
            self.tv.insert("", "end", iid=str(r["ma"]),
                           values=(r["thoi_diem"], r["mo_ta"], r["so_ket_qua"]))

    def ap_dung(self):
        ch = self.tv.focus()
        for r in self.ds:
            if str(r["ma"]) == ch:
                self.app.ap_dung_dieu_kien(r["dieu_kien"])
                return

    def xoa(self):
        if self.app.hoi("Xóa toàn bộ lịch sử tra cứu?"):
            kho.xoa_lich_su()
            self.lam_moi()


# ======================================================================
class ThietLap(ctk.CTkFrame):
    def __init__(self, cha, app):
        super().__init__(cha, fg_color=kho.MAU_NEN)
        self.app = app
        _tieu_de(self, "Thiết lập",
                 "Cấu hình thư mục, hiển thị và dữ liệu — lưu trong config.json")
        v = ctk.CTkScrollableFrame(self, fg_color=kho.MAU_NEN)
        v.pack(fill="both", expand=True, padx=18, pady=(0, 14))
        ch = kho.doc_cau_hinh()

        k1 = _the(v, "Thư mục làm việc")
        k1.pack(fill="x", pady=(0, 10))
        self.o_luu = self._dong_thu_muc(k1, "Thư mục lưu trữ XML",
                                        ch.get("thu_muc_luu_tru"))
        self.o_xuat = self._dong_thu_muc(k1, "Thư mục xuất mặc định",
                                         ch.get("thu_muc_xuat"))
        ctk.CTkLabel(k1, text="").pack(pady=2)

        k2 = _the(v, "Hiển thị và tra cứu")
        k2.pack(fill="x", pady=(0, 10))
        self.o_trang = self._dong_nhap(k2, "Số bản ghi mỗi trang",
                                       ch.get("so_ban_ghi_moi_trang"), 120)
        self.o_mst = self._dong_nhap(k2, "MST người mua mặc định (để trống "
                                         "nếu không muốn lọc sẵn)",
                                     ch.get("mst_mac_dinh"), 220)
        self.b_chep = ctk.BooleanVar(value=bool(ch.get("tu_chep_xml", True)))
        self.b_mo = ctk.BooleanVar(value=bool(ch.get("mo_sau_khi_xuat", True)))
        self.b_hoi = ctk.BooleanVar(
            value=bool(ch.get("xac_nhan_truoc_khi_xoa", True)))
        for bien, nhan in ((self.b_chep, "Tự chép tệp XML vào thư mục lưu trữ "
                                         "khi nạp"),
                           (self.b_mo, "Mở tệp ngay sau khi xuất"),
                           (self.b_hoi, "Hỏi xác nhận trước khi xóa hóa đơn")):
            ctk.CTkCheckBox(k2, text=nhan, variable=bien,
                            font=ctk.CTkFont(size=12),
                            text_color=kho.MAU_CHU).pack(anchor="w", padx=14,
                                                         pady=3)
        ctk.CTkLabel(k2, text="").pack(pady=2)

        k3 = _the(v, "Dữ liệu")
        k3.pack(fill="x", pady=(0, 10))
        ctk.CTkLabel(k3, text="Tệp cơ sở dữ liệu: %s" % kho.DUONG_DAN_DB,
                     font=ctk.CTkFont(size=12), text_color=kho.MAU_XAM,
                     anchor="w").pack(fill="x", padx=14)
        hang = ctk.CTkFrame(k3, fg_color="transparent")
        hang.pack(fill="x", padx=14, pady=10)
        ctk.CTkButton(hang, text="Sao lưu ngay", width=150, height=32,
                      fg_color=kho.MAU_XANH, command=self.sao_luu
                      ).pack(side="left")
        ctk.CTkButton(hang, text="Mở thư mục sao lưu", width=170, height=32,
                      fg_color="#6B7A8C",
                      command=lambda: exporter.mo_duong_dan(kho.THU_MUC_BACKUP)
                      ).pack(side="left", padx=8)
        ctk.CTkButton(hang, text="Nạp 12 hóa đơn mẫu", width=180, height=32,
                      fg_color=kho.MAU_CAM, command=self.nap_mau
                      ).pack(side="left")
        ctk.CTkButton(hang, text="Xóa dữ liệu mẫu", width=160, height=32,
                      fg_color=kho.MAU_DO, command=self.xoa_mau
                      ).pack(side="left", padx=8)
        ctk.CTkButton(hang, text="Xem tệp nhật ký", width=150, height=32,
                      fg_color="#6B7A8C",
                      command=lambda: exporter.mo_duong_dan(
                          os.path.join(kho.THU_MUC_LOG, "app.log"))
                      ).pack(side="left")

        ctk.CTkButton(v, text="LƯU THIẾT LẬP", width=200, height=40,
                      fg_color=kho.MAU_LUC,
                      font=ctk.CTkFont(size=13, weight="bold"),
                      command=self.luu).pack(anchor="w", pady=(0, 16))

    def _dong_nhap(self, cha, nhan, gt, rong):
        d = ctk.CTkFrame(cha, fg_color="transparent")
        d.pack(fill="x", padx=14, pady=4)
        ctk.CTkLabel(d, text=nhan, width=330, anchor="w",
                     font=ctk.CTkFont(size=12),
                     text_color=kho.MAU_CHU).pack(side="left")
        o = ctk.CTkEntry(d, width=rong, height=30, fg_color=kho.MAU_TRANG,
                         border_color=kho.MAU_VIEN, text_color=kho.MAU_CHU)
        o.insert(0, str(gt or ""))
        o.pack(side="left")
        return o

    def _dong_thu_muc(self, cha, nhan, gt):
        d = ctk.CTkFrame(cha, fg_color="transparent")
        d.pack(fill="x", padx=14, pady=4)
        ctk.CTkLabel(d, text=nhan, width=200, anchor="w",
                     font=ctk.CTkFont(size=12),
                     text_color=kho.MAU_CHU).pack(side="left")
        o = ctk.CTkEntry(d, height=30, fg_color=kho.MAU_TRANG,
                         border_color=kho.MAU_VIEN, text_color=kho.MAU_CHU)
        o.insert(0, str(gt or ""))
        o.pack(side="left", fill="x", expand=True, padx=8)

        def chon():
            t = filedialog.askdirectory(title=nhan, initialdir=o.get() or "/")
            if t:
                o.delete(0, "end")
                o.insert(0, os.path.normpath(t))

        ctk.CTkButton(d, text="Chọn...", width=90, height=30,
                      fg_color=kho.MAU_XANH, command=chon).pack(side="left")
        return o

    def luu(self):
        ch = kho.doc_cau_hinh()
        ch["thu_muc_luu_tru"] = self.o_luu.get().strip()
        ch["thu_muc_xuat"] = self.o_xuat.get().strip()
        ch["so_ban_ghi_moi_trang"] = self.o_trang.get().strip() or "50"
        ch["mst_mac_dinh"] = self.o_mst.get().strip()
        ch["tu_chep_xml"] = bool(self.b_chep.get())
        ch["mo_sau_khi_xuat"] = bool(self.b_mo.get())
        ch["xac_nhan_truoc_khi_xoa"] = bool(self.b_hoi.get())
        kho.ghi_cau_hinh(ch)
        self.app.cau_hinh = ch
        self.app.bao("Đã lưu thiết lập.")

    def sao_luu(self):
        d = kho.sao_luu("thu_cong")
        self.app.bao("Đã sao lưu:\n%s" % d if d else "Chưa có dữ liệu để sao lưu.")

    def nap_mau(self):
        n = kho.nap_du_lieu_mau()
        self.app.bao("Đã nạp %d hóa đơn mẫu." % n)
        self.app.lam_moi_tat_ca()

    def xoa_mau(self):
        if self.app.hoi("Xóa toàn bộ hóa đơn thuộc nhóm “Dữ liệu mẫu”?\n\n"
                        "Hóa đơn thật nạp từ tệp XML không bị ảnh hưởng."):
            n = kho.xoa_du_lieu_mau()
            self.app.bao("Đã xóa %d hóa đơn mẫu." % n)
            self.app.lam_moi_tat_ca()


# ======================================================================
_HUONG_DAN = """1. NẠP HÓA ĐƠN VÀO PHẦN MỀM

Phần mềm chạy hoàn toàn ngoại tuyến, chỉ đọc tệp đã có trên máy. Trình tự
đúng quy định:

  Bước 1. Đăng nhập hoadondientu.gdt.gov.vn bằng trình duyệt, vào mục
          Tra cứu → Tra cứu hóa đơn, chọn khoảng thời gian cần lấy.
  Bước 2. Bấm Xuất XML (hoặc Xuất Excel) — Cổng Thuế sẽ tải về một gói ZIP
          hoặc nhiều tệp XML trong thư mục Downloads.
  Bước 3. Quay lại phần mềm, bấm TẢI HÓA ĐƠN và chọn một trong ba nguồn:
            • Gói ZIP tải từ Cổng Thuế
            • Thư mục chứa tệp XML
            • Thư mục và tất cả thư mục con
  Bước 4. Phần mềm đọc từng tệp, kiểm tra số liệu, chép bản sao XML vào
          thư mục lưu trữ và hiển thị báo cáo số hóa đơn thêm mới / trùng / lỗi.

Phần mềm KHÔNG tự đăng nhập, KHÔNG vượt mã xác nhận và KHÔNG gửi dữ liệu
ra ngoài máy tính.

2. TRA CỨU

Điền vào ô nào thì lọc theo ô đó, ô để trống được bỏ qua. Khoảng ngày lấy
cả hai đầu. Tên người bán không phân biệt chữ hoa chữ thường. Bấm vào tiêu
đề cột Ngày lập, Số hóa đơn, Tổng tiền… để sắp xếp.

3. THAO TÁC TRÊN TỪNG DÒNG

  [XEM]  mở cửa sổ chi tiết hóa đơn, có đầy đủ dòng hàng và chữ ký số.
  [XML]  mở tệp XML gốc của hóa đơn đó.
  [IN]   tạo bản thể hiện HTML và mở trình duyệt; nhấn Ctrl+P rồi chọn
         “Microsoft Print to PDF” để lưu thành PDF.
  [XÓA]  xóa hóa đơn khỏi kho dữ liệu.

Nháy đúp vào một dòng cũng mở cửa sổ xem hóa đơn. Bấm chuột phải để hiện
thực đơn thao tác nhanh.

4. CHỌN NHIỀU DÒNG VÀ XÓA

Nhấp vào ô vuông ở cột đầu tiên để chọn từng dòng, hoặc dùng nút Chọn tất cả
/ Bỏ chọn. Sau đó bấm Xóa đã chọn, hoặc nhấn phím Delete. Muốn xóa mọi hóa
đơn đang thỏa bộ lọc hiện tại, dùng nút Xóa kết quả lọc.

Trước mỗi lần xóa, phần mềm tự sao lưu cơ sở dữ liệu vào thư mục
data\\backup và giữ lại 10 bản gần nhất, nên dữ liệu vẫn khôi phục được.

5. XUẤT DỮ LIỆU

  Tải XML    chép tệp XML gốc của các dòng đang chọn sang thư mục tùy ý.
  Tải PDF    xuất bản thể hiện HTML của các dòng đang chọn.
  Xuất Excel xuất toàn bộ kết quả đang lọc, cột tiền là số để cộng được.

6. CHUẨN DỮ LIỆU

Phần mềm đọc hóa đơn theo Nghị định 254/2026/NĐ-CP và Thông tư 91/2026/TT-BTC
(hiệu lực 01/07/2026), hỗ trợ cả 9 loại mẫu số, hóa đơn khởi tạo từ máy tính
tiền, hóa đơn ngoại tệ, nhiều mức thuế suất, hóa đơn điều chỉnh và thay thế.
Khi số liệu trên hóa đơn không khớp, phần mềm chỉ cảnh báo chứ không bao giờ
tự sửa số của hóa đơn.
"""


class HuongDan(ctk.CTkFrame):
    def __init__(self, cha, app):
        super().__init__(cha, fg_color=kho.MAU_NEN)
        _tieu_de(self, "Hướng dẫn sử dụng",
                 "Quy trình nạp và khai thác hóa đơn điện tử trên máy")
        o = ctk.CTkTextbox(self, fg_color=kho.MAU_TRANG, border_width=1,
                           border_color=kho.MAU_VIEN, wrap="word",
                           text_color=kho.MAU_CHU,
                           font=ctk.CTkFont(size=13))
        o.pack(fill="both", expand=True, padx=18, pady=(0, 14))
        o.insert("1.0", _HUONG_DAN)
        o.configure(state="disabled")

    def lam_moi(self):
        pass


# ======================================================================
class LienHe(ctk.CTkFrame):
    def __init__(self, cha, app):
        super().__init__(cha, fg_color=kho.MAU_NEN)
        _tieu_de(self, "Liên hệ hỗ trợ", "Thông tin tác giả và hỗ trợ kỹ thuật")
        k = _the(self, "")
        k.pack(fill="x", padx=18, pady=(0, 12))
        ctk.CTkLabel(k, text=kho.APP_NAME,
                     font=ctk.CTkFont(size=24, weight="bold"),
                     text_color=kho.MAU_XANH_DAM).pack(anchor="w", padx=20,
                                                       pady=(18, 0))
        ctk.CTkLabel(k, text="Phần mềm tra cứu và lưu trữ hóa đơn điện tử "
                             "trên máy tính — phiên bản %s" % kho.APP_VERSION,
                     font=ctk.CTkFont(size=13),
                     text_color=kho.MAU_XAM).pack(anchor="w", padx=20,
                                                  pady=(2, 16))
        for nhan, gt in (("Tác giả", kho.TAC_GIA),
                         ("Điện thoại", kho.DIEN_THOAI),
                         ("Cập nhật", kho.NGAY_CAP_NHAT),
                         ("Chuẩn dữ liệu", tt91.VAN_BAN_AP_DUNG),
                         ("Thư mục cài đặt", kho.THU_MUC_GOC),
                         ("Tệp nhật ký", os.path.join(kho.THU_MUC_LOG,
                                                      "app.log"))):
            d = ctk.CTkFrame(k, fg_color="transparent")
            d.pack(fill="x", padx=20, pady=3)
            ctk.CTkLabel(d, text=nhan + ":", width=150, anchor="w",
                         font=ctk.CTkFont(size=13),
                         text_color=kho.MAU_XAM).pack(side="left")
            ctk.CTkLabel(d, text=str(gt), anchor="w", wraplength=620,
                         justify="left",
                         font=ctk.CTkFont(size=13, weight="bold"),
                         text_color=kho.MAU_CHU).pack(side="left", fill="x")
        ctk.CTkLabel(k, text="").pack(pady=8)

        k2 = _the(self, "Lưu ý pháp lý")
        k2.pack(fill="x", padx=18, pady=(0, 14))
        ctk.CTkLabel(
            k2, anchor="w", justify="left", wraplength=900,
            font=ctk.CTkFont(size=12), text_color=kho.MAU_CHU,
            text="Phần mềm chỉ đọc dữ liệu hóa đơn đã được người dùng tải hợp "
                 "pháp về máy từ Cổng Hóa đơn điện tử hoặc nhận từ người bán. "
                 "Phần mềm không kết nối, không đăng nhập và không truy vấn tự "
                 "động tới bất kỳ máy chủ nào của cơ quan thuế. Tệp XML là bản "
                 "gốc có giá trị pháp lý; bản thể hiện HTML/PDF chỉ dùng để "
                 "xem và lưu nội bộ."
        ).pack(fill="x", padx=20, pady=(0, 16))

    def lam_moi(self):
        pass
