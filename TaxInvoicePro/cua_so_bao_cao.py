# -*- coding: utf-8 -*-
"""
cua_so_bao_cao.py - TAX INVOICE PRO v1.4.0
Cua so "Bao cao chi tiet & Ke khai thue GTGT".
Chay doc lap: python cua_so_bao_cao.py  (hoac ChayBaoCao.bat)
Tac gia: TDA - 0986509106
"""
import os
import json
import datetime
import threading
import traceback
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

try:
    import va_ttk
except Exception:
    pass

import customtkinter as ctk

import doi_chieu as dc
import bao_cao_chi_tiet as bct

XANH, XANH_DAM, NEN = "#1565C0", "#0D47A1", "#F4F7FB"
LUC, CAM, TIM, XAM = "#2E7D32", "#EF6C00", "#6A1B9A", "#607D8B"
THU_MUC = os.path.dirname(os.path.abspath(__file__))


def mst_tu_config():
    try:
        with open(os.path.join(THU_MUC, "config.json"), "r",
                  encoding="utf-8") as f:
            c = json.load(f)
        for k, v in c.items():
            if "mst" in k.lower() and str(v).strip():
                return str(v).strip()
    except Exception:
        pass
    return ""


class CuaSoBaoCao(ctk.CTk):
    def __init__(self):
        super().__init__()
        ctk.set_appearance_mode("light")
        self.title("TAX INVOICE PRO v1.4.0 — Báo cáo chi tiết & Kê khai GTGT")
        self.geometry("1200x800")
        self.minsize(1020, 660)
        self.configure(fg_color=NEN)
        self.ds, self.dong = [], []
        self._style()
        self._dau()
        self._dieu_khien()
        self._bang()
        self._chan()
        self.nap_kho()

    def _style(self):
        s = ttk.Style()
        try:
            s.theme_use("clam")
        except Exception:
            pass
        s.configure("BC.Treeview", rowheight=24, font=("Segoe UI", 9),
                    background="white", fieldbackground="white")
        s.configure("BC.Treeview.Heading", font=("Segoe UI", 9, "bold"),
                    background=XANH, foreground="white", relief="flat")

    def _dau(self):
        h = ctk.CTkFrame(self, height=52, corner_radius=0, fg_color=XANH)
        h.pack(fill="x")
        h.pack_propagate(False)
        ctk.CTkLabel(h, text="◆  BÁO CÁO CHI TIẾT & KÊ KHAI THUẾ GTGT",
                     font=ctk.CTkFont("Segoe UI", 17, "bold"),
                     text_color="white").pack(side="left", padx=18)
        self.lb_kho = ctk.CTkLabel(h, text="", text_color="white",
                                   font=ctk.CTkFont("Segoe UI", 11))
        self.lb_kho.pack(side="right", padx=18)

    def _chan(self):
        f = ctk.CTkFrame(self, height=30, corner_radius=0, fg_color="#E8EEF6")
        f.pack(fill="x", side="bottom")
        f.pack_propagate(False)
        self.lb_tt = ctk.CTkLabel(f, text="Sẵn sàng.", text_color="#44546A",
                                  font=ctk.CTkFont("Segoe UI", 10))
        self.lb_tt.pack(side="left", padx=14)
        ctk.CTkLabel(f, text="Tác giả: TDA   •   0986509106   •   Phiên bản 1.4.0",
                     font=ctk.CTkFont("Segoe UI", 10, "bold"),
                     text_color=XANH_DAM).pack(side="right", padx=14)

    def _dieu_khien(self):
        k = ctk.CTkFrame(self, fg_color="white")
        k.pack(fill="x", padx=12, pady=(10, 6))
        ctk.CTkLabel(k, text="Tham số báo cáo",
                     font=ctk.CTkFont("Segoe UI", 13, "bold"),
                     text_color=XANH_DAM).grid(row=0, column=0, columnspan=6,
                                               sticky="w", padx=12, pady=(10, 2))
        ctk.CTkLabel(k, text="MST đơn vị kê khai").grid(row=1, column=0, padx=12,
                                                        pady=8, sticky="w")
        self.o_mst = ctk.CTkEntry(k, width=180, height=32,
                                  placeholder_text="VD: 0101234567")
        self.o_mst.grid(row=1, column=1, sticky="w")
        self.o_mst.insert(0, mst_tu_config())
        ctk.CTkLabel(k, text="Từ ngày").grid(row=1, column=2, padx=(24, 6),
                                             sticky="w")
        self.o_tu = ctk.CTkEntry(k, width=130, height=32,
                                 placeholder_text="dd/mm/yyyy")
        self.o_tu.grid(row=1, column=3, sticky="w")
        ctk.CTkLabel(k, text="Đến ngày").grid(row=1, column=4, padx=(24, 6),
                                              sticky="w")
        self.o_den = ctk.CTkEntry(k, width=130, height=32,
                                  placeholder_text="dd/mm/yyyy")
        self.o_den.grid(row=1, column=5, sticky="w")
        ctk.CTkLabel(k, text="MST đơn vị dùng để tách Mua vào / Bán ra. "
                             "Để trống hai ô ngày nếu lấy toàn bộ kho.",
                     text_color="#667",
                     font=ctk.CTkFont("Segoe UI", 11)).grid(
            row=2, column=0, columnspan=6, sticky="w", padx=12, pady=(2, 10))

        t = ctk.CTkFrame(self, fg_color="transparent")
        t.pack(fill="x", padx=12)
        def nut(text, lenh, mau, w):
            ctk.CTkButton(t, text=text, command=lenh, width=w, height=34,
                          fg_color=mau, hover_color=XANH_DAM,
                          font=ctk.CTkFont("Segoe UI", 12, "bold")
                          ).pack(side="left", padx=(0, 8))
        nut("Xem trước chi tiết", self.xem_truoc, XAM, 165)
        nut("XUẤT EXCEL ĐẦY ĐỦ (9 sheet)", self.xuat_excel, LUC, 255)
        nut("Xuất CSV bảng phẳng", self.xuat_csv, CAM, 180)
        nut("Mở thư mục xuất", self.mo_thu_muc, XANH, 150)

    def _bang(self):
        cot = [("ngay", "Ngày", 85), ("loai", "Loại GD", 80),
               ("so", "Số HĐ", 80), ("doi_tac", "Đối tác", 240),
               ("hang", "Tên hàng hóa, dịch vụ", 320), ("dvt", "ĐVT", 60),
               ("sl", "Số lượng", 80), ("dg", "Đơn giá", 100),
               ("tt", "Thành tiền", 110), ("ts", "Thuế suất", 150),
               ("thue", "Tiền thuế", 100), ("nguon", "Nguồn dòng", 130)]
        kh = ctk.CTkFrame(self, fg_color="white")
        kh.pack(fill="both", expand=True, padx=12, pady=10)
        self.tv = ttk.Treeview(kh, columns=[c[0] for c in cot],
                               show="headings", style="BC.Treeview")
        for ma, nhan, w in cot:
            self.tv.heading(ma, text=nhan)
            self.tv.column(ma, width=w, anchor="w", stretch=(w >= 240))
        d = ttk.Scrollbar(kh, orient="vertical", command=self.tv.yview)
        n = ttk.Scrollbar(kh, orient="horizontal", command=self.tv.xview)
        self.tv.configure(yscrollcommand=d.set, xscrollcommand=n.set)
        self.tv.grid(row=0, column=0, sticky="nsew")
        d.grid(row=0, column=1, sticky="ns")
        n.grid(row=1, column=0, sticky="ew")
        kh.grid_rowconfigure(0, weight=1)
        kh.grid_columnconfigure(0, weight=1)
        self.tv.tag_configure("suy", background="#FFF8E1")
        self.tv.tag_configure("ban", background="#E8F5E9")

    # --------------------------------------------------------- xu ly
    def bao(self, t):
        self.lb_tt.configure(text=t)
        self.update_idletasks()

    def nap_kho(self):
        try:
            self.ds = dc.doc_hoa_don()
        except Exception as e:
            messagebox.showerror("Không mở được kho",
                                 "%s\n\nHãy chạy ChayApp.bat ít nhất một lần."
                                 % e)
            self.ds = []
        self.lb_kho.configure(text="Kho: %d hóa đơn" % len(self.ds))
        self.bao("Đã nạp %d hóa đơn." % len(self.ds))

    def _ds_ky(self):
        tu = dc.ngay_chuan(self.o_tu.get().strip())
        den = dc.ngay_chuan(self.o_den.get().strip())
        ds = [h for h in self.ds
              if (not tu or (h["ngay_lap"] and h["ngay_lap"] >= tu))
              and (not den or (h["ngay_lap"] and h["ngay_lap"] <= den))]
        return ds, tu, den, self.o_mst.get().strip()

    def xem_truoc(self):
        ds, tu, den, mst = self._ds_ky()
        if not ds:
            messagebox.showinfo("Không có dữ liệu", "Kỳ đã chọn không có hóa đơn.")
            return
        self.bao("Đang dựng bảng chi tiết…")
        self.dong = bct.bang_phang(ds, mst)
        self.tv.delete(*self.tv.get_children())
        for r in self.dong[:1500]:
            tag = ("suy",) if r["nguon_dong"].startswith("Suy") else (
                ("ban",) if r["loai_gd"] == "Bán ra" else ())
            doi_tac = (r["ten_ban"] if r["loai_gd"] != "Bán ra"
                       else r["ten_mua"])
            self.tv.insert("", "end", tags=tag, values=(
                r["ngay_lap"], r["loai_gd"], r["so_hd"], doi_tac,
                r["ten_hang"], r["dvt"], "%g" % r["so_luong"],
                dc.fmt_tien(r["don_gia"]), dc.fmt_tien(r["thanh_tien"]),
                r["ts_nhan"], dc.fmt_tien(r["tien_thue_dong"]),
                r["nguon_dong"]))
        mua = len([r for r in self.dong if r["loai_gd"] == "Mua vào"])
        ban = len([r for r in self.dong if r["loai_gd"] == "Bán ra"])
        suy = len([r for r in self.dong if r["nguon_dong"].startswith("Suy")])
        self.bao("%d hóa đơn → %d dòng mặt hàng (mua vào %d, bán ra %d, "
                 "suy từ tổng hóa đơn %d). Hiển thị tối đa 1500 dòng."
                 % (len(ds), len(self.dong), mua, ban, suy))

    def xuat_excel(self):
        ds, tu, den, mst = self._ds_ky()
        if not ds:
            messagebox.showinfo("Không có dữ liệu", "Kỳ đã chọn không có hóa đơn.")
            return
        d = filedialog.asksaveasfilename(
            title="Lưu báo cáo chi tiết", defaultextension=".xlsx",
            initialfile="BaoCaoChiTiet_%s.xlsx"
                        % datetime.datetime.now().strftime("%Y%m%d_%H%M"),
            filetypes=[("Excel", "*.xlsx")])
        if not d:
            return
        self.bao("Đang lập báo cáo…")

        def chay():
            try:
                kq = bct.xuat_chi_tiet_day_du(ds, d, mst, tu, den)
            except Exception as e:
                loi = traceback.format_exc()
                self.after(0, lambda: messagebox.showerror(
                    "Lỗi", "%s\n\n%s" % (e, loi[-900:])))
                return

            def xong():
                self.bao("Đã lưu: %s" % kq["tep"])
                if messagebox.askyesno(
                        "Hoàn tất",
                        "Đã lập báo cáo:\n%s\n\nHóa đơn: %d\nDòng mặt hàng: %d\n"
                        "Dòng mua vào: %d\nDòng bán ra: %d\n\n"
                        "Các sheet: Thông tin, Chi tiết mặt hàng, Bảng kê mua "
                        "vào, Bảng kê bán ra, Thống kê theo tháng, theo đối "
                        "tác, mặt hàng, thuế suất, Tổng hợp kê khai.\n\nMở ngay?"
                        % (kq["tep"], kq["so_hoa_don"], kq["so_dong"],
                           kq["mua"], kq["ban"])):
                    os.startfile(kq["tep"])
            self.after(0, xong)

        threading.Thread(target=chay, daemon=True).start()

    def xuat_csv(self):
        ds, tu, den, mst = self._ds_ky()
        if not ds:
            messagebox.showinfo("Không có dữ liệu", "Kỳ đã chọn không có hóa đơn.")
            return
        d = filedialog.asksaveasfilename(
            title="Lưu bảng phẳng CSV", defaultextension=".csv",
            initialfile="ChiTietMatHang_%s.csv"
                        % datetime.datetime.now().strftime("%Y%m%d_%H%M"),
            filetypes=[("CSV (dấu chấm phẩy)", "*.csv")])
        if not d:
            return
        try:
            bct.xuat_csv(bct.bang_phang(ds, mst), d)
            self.bao("Đã lưu: %s" % d)
            if messagebox.askyesno("Xong", "Đã lưu CSV:\n%s\n\nMở ngay?" % d):
                os.startfile(d)
        except Exception as e:
            messagebox.showerror("Lỗi", str(e))

    def mo_thu_muc(self):
        try:
            os.startfile(THU_MUC)
        except Exception as e:
            messagebox.showerror("Lỗi", str(e))


def main():
    try:
        CuaSoBaoCao().mainloop()
    except Exception:
        t = os.path.join(THU_MUC, "logs")
        os.makedirs(t, exist_ok=True)
        with open(os.path.join(t, "app.log"), "a", encoding="utf-8") as f:
            f.write("\n%s [ERROR] cua_so_bao_cao.py\n%s\n"
                    % (datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
                       traceback.format_exc()))
        raise


if __name__ == "__main__":
    main()
