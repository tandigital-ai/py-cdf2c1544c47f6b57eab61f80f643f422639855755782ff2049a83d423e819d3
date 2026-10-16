# -*- coding: utf-8 -*-
"""
TAX INVOICE PRO - trang_chu_pro.py (v1.6.0)
Bang dieu khien (Trang chu) chuyen sau cho ke toan hoa don dau vao / dau ra.
Tac gia: TDA - 0986509106
"""
import os
import csv
import datetime
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

try:
    import va_ttk  # va loi command=None cua ttk tren Python 3.12+
except Exception:
    pass

import customtkinter as ctk

import mst_tra_cuu as mst
import canh_bao as cb

XANH = "#1565C0"
XANH_DAM = "#0D47A1"
NEN = "#F4F7FB"
TRANG = "#FFFFFF"
DO = "#C62828"
CAM = "#EF6C00"
LUC = "#2E7D32"
TIM = "#6A1B9A"
XAM = "#546E7A"
VIEN = "#D6E2F0"

MAU_MUC = {cb.CAO: DO, cb.TB: CAM, cb.THAP: XAM}


def _tien(v):
    return mst.tien(v)


def _rut(v):
    v = float(v or 0)
    for n, d in ((1e9, " tỷ"), (1e6, " tr"), (1e3, " ng")):
        if abs(v) >= n:
            return ("%.1f" % (v / n)).rstrip("0").rstrip(".") + d
    return "%.0f" % v


class TheSo(ctk.CTkFrame):
    def __init__(self, master, tieu_de, mau=XANH):
        super().__init__(master, fg_color=TRANG, corner_radius=10,
                         border_width=1, border_color=VIEN)
        self.mau = mau
        ctk.CTkFrame(self, fg_color=mau, height=4, corner_radius=2).pack(
            fill="x", padx=10, pady=(8, 0))
        self.lb_td = ctk.CTkLabel(self, text=tieu_de, font=ctk.CTkFont(size=11),
                                  text_color=XAM, anchor="w", justify="left",
                                  wraplength=220)
        self.lb_td.pack(fill="x", padx=12, pady=(6, 0))
        self.lb_gt = ctk.CTkLabel(self, text="-", anchor="w",
                                  font=ctk.CTkFont(size=22, weight="bold"),
                                  text_color=mau)
        self.lb_gt.pack(fill="x", padx=12)
        self.lb_phu = ctk.CTkLabel(self, text="", anchor="w",
                                   font=ctk.CTkFont(size=11), text_color=XAM,
                                   wraplength=220, justify="left")
        self.lb_phu.pack(fill="x", padx=12, pady=(0, 10))

    def dat(self, gia_tri, phu="", mau=None):
        self.lb_gt.configure(text=str(gia_tri), text_color=mau or self.mau)
        self.lb_phu.configure(text=phu)


class TrangChuPro(ctk.CTkFrame):
    """Man hinh Trang chu. Duoc khoi_dong.py nap thay cho ban cu."""

    def __init__(self, master, app=None, **kw):
        super().__init__(master, fg_color=NEN)
        self.app = app
        self.ds_tat_ca = []
        self.ds_ky = []
        self.kq = None
        self.cache_ncc = {}
        self.ds_rr = {}
        self.ch = mst.doc_cau_hinh()
        self._dung_giao_dien()
        self.after(120, self.lam_moi)

    # ------------------------------------------------------------------
    def _dung_giao_dien(self):
        self.cuon = ctk.CTkScrollableFrame(self, fg_color=NEN)
        self.cuon.pack(fill="both", expand=True, padx=16, pady=12)

        dau = ctk.CTkFrame(self.cuon, fg_color="transparent")
        dau.pack(fill="x")
        ctk.CTkLabel(dau, text="Bảng điều khiển",
                     font=ctk.CTkFont(size=22, weight="bold"),
                     text_color=XANH_DAM).pack(side="left")
        ctk.CTkLabel(dau, text="   Toàn cảnh hóa đơn, nghĩa vụ thuế và rủi ro cần xử lý",
                     font=ctk.CTkFont(size=12), text_color=XAM).pack(
            side="left", pady=(8, 0))

        thanh = ctk.CTkFrame(self.cuon, fg_color=TRANG, corner_radius=10,
                             border_width=1, border_color=VIEN)
        thanh.pack(fill="x", pady=(10, 12))
        ctk.CTkLabel(thanh, text="Kỳ kê khai:", font=ctk.CTkFont(size=12)).pack(
            side="left", padx=(12, 6), pady=10)
        self.cb_ky = ctk.CTkComboBox(thanh, values=["Tất cả"], width=190,
                                     command=lambda v: self.ve_lai())
        self.cb_ky.pack(side="left", pady=10)
        ctk.CTkLabel(thanh, text="   MST đơn vị:", font=ctk.CTkFont(size=12)).pack(
            side="left", padx=(10, 6))
        self.o_mst = ctk.CTkEntry(thanh, width=150,
                                  placeholder_text="VD: 0101234567")
        self.o_mst.pack(side="left")
        self.o_mst.insert(0, self.ch.get("mst_don_vi", ""))
        ctk.CTkButton(thanh, text="Lưu MST", width=80, command=self.luu_mst).pack(
            side="left", padx=6)
        ctk.CTkButton(thanh, text="Làm mới dữ liệu", width=130, fg_color=XANH,
                      command=self.lam_moi).pack(side="right", padx=12)
        ctk.CTkButton(thanh, text="Tra cứu NCC", width=110, fg_color=TIM,
                      command=lambda: self._mo("ncc")).pack(side="right")

        self.khung_kpi = ctk.CTkFrame(self.cuon, fg_color="transparent")
        self.khung_kpi.pack(fill="x")
        for i in range(4):
            self.khung_kpi.grid_columnconfigure(i, weight=1, uniform="k")
        dsthe = [
            ("Hóa đơn MUA VÀO trong kỳ", XANH),
            ("Thuế GTGT đầu vào (chỉ tiêu [23],[24])", LUC),
            ("Hóa đơn BÁN RA trong kỳ", TIM),
            ("Thuế GTGT đầu ra (chỉ tiêu [32],[33])", CAM),
            ("Chênh lệch thuế phải nộp trong kỳ", XANH_DAM),
            ("Cảnh báo mức CAO cần xử lý", DO),
            ("Nhà cung cấp đang giao dịch", XAM),
            ("Hạn nộp hồ sơ khai thuế", CAM),
        ]
        self.the = []
        for i, (t, m) in enumerate(dsthe):
            w = TheSo(self.khung_kpi, t, m)
            w.grid(row=i // 4, column=i % 4, sticky="nsew", padx=5, pady=5)
            self.the.append(w)

        bd = ctk.CTkFrame(self.cuon, fg_color="transparent")
        bd.pack(fill="x", pady=(8, 0))
        bd.grid_columnconfigure(0, weight=3, uniform="b")
        bd.grid_columnconfigure(1, weight=2, uniform="b")

        k1 = self._khung("Mua vào và bán ra 12 tháng gần nhất (tổng thanh toán)", bd)
        k1.grid(row=0, column=0, sticky="nsew", padx=(0, 6), pady=5)
        self.cv_thang = tk.Canvas(k1, height=240, bg=TRANG, highlightthickness=0)
        self.cv_thang.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        self.cv_thang.bind("<Configure>", lambda e: self._ve_thang())

        k2 = self._khung("Top nhà cung cấp theo giá trị mua vào", bd)
        k2.grid(row=0, column=1, sticky="nsew", padx=(6, 0), pady=5)
        self.cv_ncc = tk.Canvas(k2, height=240, bg=TRANG, highlightthickness=0)
        self.cv_ncc.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        self.cv_ncc.bind("<Configure>", lambda e: self._ve_ncc())

        k3 = self._khung("Cơ cấu theo thuế suất (tiền hàng)", self.cuon)
        k3.pack(fill="x", pady=5)
        self.cv_ts = tk.Canvas(k3, height=150, bg=TRANG, highlightthickness=0)
        self.cv_ts.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        self.cv_ts.bind("<Configure>", lambda e: self._ve_ts())

        k4 = self._khung("Cảnh báo cần xử lý (bấm đúp để xem danh sách hóa đơn)",
                         self.cuon)
        k4.pack(fill="both", expand=True, pady=5)
        cot = ("muc", "nhom", "tieu_de", "sl", "tien", "can_cu")
        nhan = {"muc": "Mức", "nhom": "Nhóm", "tieu_de": "Nội dung cảnh báo",
                "sl": "Số HĐ", "tien": "Giá trị", "can_cu": "Căn cứ"}
        rong = {"muc": 90, "nhom": 130, "tieu_de": 520, "sl": 70, "tien": 130,
                "can_cu": 420}
        st = ttk.Style()
        try:
            st.configure("TCP.Treeview", rowheight=26, font=("Segoe UI", 10))
            st.configure("TCP.Treeview.Heading", font=("Segoe UI", 10, "bold"))
        except Exception:
            pass
        kbang = tk.Frame(k4, bg=TRANG)
        kbang.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        self.tv = ttk.Treeview(kbang, columns=cot, show="headings", height=9,
                               style="TCP.Treeview")
        for c in cot:
            self.tv.heading(c, text=nhan[c])
            self.tv.column(c, width=rong[c],
                           anchor="e" if c in ("sl", "tien") else "w")
        sb = ttk.Scrollbar(kbang, orient="vertical", command=self.tv.yview)
        self.tv.configure(yscrollcommand=sb.set)
        self.tv.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")
        self.tv.tag_configure("Cao", background="#FFEBEE", foreground="#B71C1C")
        self.tv.tag_configure("Trung bình", background="#FFF8E1",
                              foreground="#8D4E00")
        self.tv.tag_configure("Thấp", background="#F5F7FA", foreground="#37474F")
        self.tv.bind("<Double-1>", self._mo_chi_tiet)
        self.lb_ghi = ctk.CTkLabel(k4, text=cb.LY_DO_BO_QUY_TAC,
                                   font=ctk.CTkFont(size=11), text_color=XAM,
                                   wraplength=1100, justify="left", anchor="w")
        self.lb_ghi.pack(fill="x", padx=12, pady=(0, 10))

        k5 = self._khung("Chất lượng dữ liệu và mức độ sẵn sàng giải trình",
                         self.cuon)
        k5.pack(fill="x", pady=5)
        self.thanh_cl = {}
        for ma, ten in (("xml", "Hóa đơn có tệp XML gốc (bản có giá trị pháp lý)"),
                        ("chung_tu", "Hóa đơn ≥ 5 triệu đã có chứng từ thanh toán "
                                     "không dùng tiền mặt"),
                        ("tra_ncc", "Nhà cung cấp đã tra cứu tình trạng hoạt động")):
            h = ctk.CTkFrame(k5, fg_color="transparent")
            h.pack(fill="x", padx=12, pady=4)
            ctk.CTkLabel(h, text=ten, font=ctk.CTkFont(size=12), anchor="w",
                         width=560).pack(side="left")
            p = ctk.CTkProgressBar(h, width=380, progress_color=LUC)
            p.set(0)
            p.pack(side="left", padx=10)
            l = ctk.CTkLabel(h, text="0%", font=ctk.CTkFont(size=12, weight="bold"),
                             width=60)
            l.pack(side="left")
            self.thanh_cl[ma] = (p, l)
        ctk.CTkLabel(k5, text="", height=4).pack()

        nut = ctk.CTkFrame(self.cuon, fg_color="transparent")
        nut.pack(fill="x", pady=(6, 2))
        for t, m, ma in (("Tra cứu hóa đơn", XANH, "tra_cuu"),
                         ("Đối chiếu & Kiểm tra", "#00897B", "doi_chieu"),
                         ("Báo cáo & Kê khai", TIM, "bao_cao"),
                         ("Nhà cung cấp & Rủi ro", CAM, "ncc")):
            ctk.CTkButton(nut, text=t, fg_color=m, width=180,
                          command=lambda x=ma: self._mo(x)).pack(side="left", padx=5)

        ctk.CTkLabel(self.cuon,
                     text="Số liệu tổng hợp từ dữ liệu đã lưu trên máy, dùng để kiểm "
                          "soát nội bộ. Bản gốc có giá trị pháp lý là tệp XML và dữ "
                          "liệu trên Cổng Thuế.   |   Tác giả: TDA - 0986509106",
                     font=ctk.CTkFont(size=11), text_color=XAM,
                     wraplength=1200, justify="left").pack(fill="x", pady=(8, 4))

    def _khung(self, tieu_de, cha):
        f = ctk.CTkFrame(cha, fg_color=TRANG, corner_radius=10, border_width=1,
                         border_color=VIEN)
        ctk.CTkLabel(f, text=tieu_de, font=ctk.CTkFont(size=13, weight="bold"),
                     text_color=XANH_DAM, anchor="w").pack(fill="x", padx=12,
                                                           pady=(10, 6))
        return f

    # ------------------------------------------------------------------
    def _mo(self, ma):
        try:
            if self.app and hasattr(self.app, "hien_man_hinh"):
                self.app.hien_man_hinh(ma)
        except Exception as e:
            messagebox.showerror("Lỗi", str(e), parent=self)

    def luu_mst(self):
        self.ch["mst_don_vi"] = mst.chuan_mst(self.o_mst.get())
        mst.ghi_cau_hinh(self.ch)
        self.ve_lai()
        messagebox.showinfo("Đã lưu",
                            "Đã lưu MST đơn vị: %s" % (self.ch["mst_don_vi"] or "(trống)"),
                            parent=self)

    # ------------------------------------------------------------------
    def lam_moi(self):
        try:
            mst.khoi_tao_bang()
            self.ch = mst.doc_cau_hinh()
            self.ds_tat_ca = mst.doc_hoa_don()
            self.cache_ncc = mst.doc_cache_tat_ca()
            self.ds_rr = mst.doc_ds_rui_ro()
        except Exception as e:
            messagebox.showerror("Lỗi đọc dữ liệu", str(e), parent=self)
            return
        kys = sorted({h["ngay_lap"][:7] for h in self.ds_tat_ca if h["ngay_lap"]},
                     reverse=True)
        gt = ["Tất cả"]
        nam = sorted({k[:4] for k in kys}, reverse=True)
        gt += ["Năm %s" % n for n in nam]
        quy = sorted({cb.ky_quy(k + "-01") for k in kys}, reverse=True)
        gt += ["Quý %s/%s" % (q[-1], q[:4]) for q in quy if q]
        gt += ["Tháng %s/%s" % (k[5:7], k[:4]) for k in kys]
        hien = self.cb_ky.get()
        self.cb_ky.configure(values=gt)
        if hien not in gt:
            self.cb_ky.set(gt[-1] if len(gt) > 1 and kys else "Tất cả")
        self.ve_lai()

    def _loc_ky(self):
        v = (self.cb_ky.get() or "Tất cả").strip()
        ds = self.ds_tat_ca
        if v == "Tất cả":
            return ds, None, ""
        if v.startswith("Năm "):
            n = v[4:]
            return [h for h in ds if h["ngay_lap"][:4] == n], None, v
        if v.startswith("Quý "):
            q, n = v[4:].split("/")
            ky = "%s-Q%s" % (n, q)
            return [h for h in ds if cb.ky_quy(h["ngay_lap"]) == ky], \
                cb.han_nop_quy(ky), v
        if v.startswith("Tháng "):
            t, n = v[6:].split("/")
            ky = "%s-%s" % (n, t)
            return [h for h in ds if h["ngay_lap"][:7] == ky], \
                cb.han_nop_thang(ky), v
        return ds, None, v

    def ve_lai(self):
        ds, han, ten_ky = self._loc_ky()
        self.ds_ky = ds
        mst_dv = self.ch.get("mst_don_vi", "")
        self.kq = cb.phan_tich(ds, mst_dv, self.cache_ncc, self.ds_rr)
        k = self.kq["kpi"]
        self.the[0].dat("%d HĐ" % k["mua_sl"],
                        "Tiền hàng %s đ\nTổng thanh toán %s đ"
                        % (_tien(k["mua_hang"]), _tien(k["mua_tong"])))
        self.the[1].dat("%s đ" % _tien(k["mua_thue"]),
                        "Thuế đầu vào được khấu trừ (sau khi loại các cảnh báo)")
        self.the[2].dat("%d HĐ" % k["ban_sl"],
                        "Doanh thu %s đ\nTổng thanh toán %s đ"
                        % (_tien(k["ban_hang"]), _tien(k["ban_tong"])))
        self.the[3].dat("%s đ" % _tien(k["ban_thue"]), "Thuế GTGT đầu ra trong kỳ")
        ch = k["chenh_thue"]
        self.the[4].dat("%s đ" % _tien(abs(ch)),
                        "Phải nộp trong kỳ" if ch > 0 else
                        ("Còn được khấu trừ chuyển kỳ sau" if ch < 0 else "Cân bằng"),
                        DO if ch > 0 else LUC)
        self.the[5].dat("%d HĐ" % k["cao"],
                        "Tổng %d nhóm cảnh báo" % k["so_canh_bao"],
                        DO if k["cao"] else LUC)
        srr = self.kq["chat_luong"]["so_ncc_rui_ro"]
        self.the[6].dat("%d NCC" % k["so_ncc"],
                        "Trong đó %d nhà cung cấp có dấu hiệu rủi ro" % srr,
                        DO if srr else XAM)
        if han:
            con = (han - datetime.date.today()).days
            self.the[7].dat(han.strftime("%d/%m/%Y"),
                            ("Còn %d ngày" % con) if con >= 0
                            else ("Đã quá hạn %d ngày" % -con),
                            LUC if con > 5 else (CAM if con >= 0 else DO))
        else:
            self.the[7].dat("—", "Chọn kỳ theo tháng hoặc quý để xem hạn nộp")

        for ma, (p, l) in self.thanh_cl.items():
            v = float(self.kq["chat_luong"].get(ma, 0))
            p.set(v)
            p.configure(progress_color=LUC if v >= 0.9 else (CAM if v >= 0.5 else DO))
            l.configure(text="%d%%" % round(v * 100))

        for i in self.tv.get_children():
            self.tv.delete(i)
        self._ban_do_cb = {}
        for c in self.kq["canh_bao"]:
            iid = self.tv.insert("", "end", values=(
                c["muc"], c["nhom"], c["tieu_de"], c["so_luong"],
                _tien(c["tien"]) + " đ" if c["tien"] else "", c["can_cu"]),
                tags=(c["muc"],))
            self._ban_do_cb[iid] = c
        if not self.kq["canh_bao"]:
            self.tv.insert("", "end", values=(
                "", "", "Không có cảnh báo nào trong kỳ đã chọn.", "", "", ""))
        self._ve_thang()
        self._ve_ncc()
        self._ve_ts()

    # ------------------------------------------------------------------
    def _ve_thang(self):
        c = self.cv_thang
        c.delete("all")
        W = c.winfo_width() or 700
        H = c.winfo_height() or 240
        if W < 60:
            return
        thang = sorted({h["ngay_lap"][:7] for h in self.ds_tat_ca if h["ngay_lap"]})[-12:]
        if not thang:
            c.create_text(W / 2, H / 2, text="Chưa có dữ liệu", fill=XAM)
            return
        dv = self.ch.get("mst_don_vi", "")
        mua = {t: 0.0 for t in thang}
        ban = {t: 0.0 for t in thang}
        for h in self.ds_tat_ca:
            t = h["ngay_lap"][:7]
            if t not in mua:
                continue
            if cb.phan_loai_gd(h, dv) == "Bán ra":
                ban[t] += h["tong"]
            else:
                mua[t] += h["tong"]
        cao = max(list(mua.values()) + list(ban.values()) + [1])
        T, D, L, R = 18, 34, 58, 14
        vh = H - T - D
        vw = W - L - R
        for i in range(5):
            y = T + vh * i / 4
            c.create_line(L, y, W - R, y, fill="#ECF1F7")
            c.create_text(L - 6, y, text=_rut(cao * (4 - i) / 4), anchor="e",
                          fill=XAM, font=("Segoe UI", 8))
        c.create_line(L, T + vh, W - R, T + vh, fill="#B0BEC5")
        n = len(thang)
        bw = vw / n
        for i, t in enumerate(thang):
            x = L + i * bw
            for j, (gt, mau) in enumerate(((mua[t], XANH), (ban[t], TIM))):
                h0 = vh * (gt / cao) if cao else 0
                x1 = x + bw * (0.16 + j * 0.34)
                x2 = x1 + bw * 0.3
                c.create_rectangle(x1, T + vh - h0, x2, T + vh, fill=mau, outline="")
                if gt > 0 and bw > 42:
                    c.create_text((x1 + x2) / 2, T + vh - h0 - 7, text=_rut(gt),
                                  fill=mau, font=("Segoe UI", 7))
            c.create_text(x + bw / 2, T + vh + 12, text="%s/%s" % (t[5:7], t[2:4]),
                          fill=XAM, font=("Segoe UI", 8))
        c.create_rectangle(L, H - 14, L + 11, H - 4, fill=XANH, outline="")
        c.create_text(L + 16, H - 9, text="Mua vào", anchor="w", fill=XAM,
                      font=("Segoe UI", 8))
        c.create_rectangle(L + 80, H - 14, L + 91, H - 4, fill=TIM, outline="")
        c.create_text(L + 96, H - 9, text="Bán ra", anchor="w", fill=XAM,
                      font=("Segoe UI", 8))

    def _ve_ncc(self):
        c = self.cv_ncc
        c.delete("all")
        W = c.winfo_width() or 400
        H = c.winfo_height() or 240
        if W < 60:
            return
        ds = mst.tong_hop_ncc(self.ds_ky, self.ch.get("mst_don_vi", ""))[:7]
        if not ds:
            c.create_text(W / 2, H / 2, text="Chưa có dữ liệu mua vào", fill=XAM)
            return
        cao = max([d["tong"] for d in ds] + [1])
        bh = min(26, (H - 20) / len(ds))
        for i, d in enumerate(ds):
            y = 10 + i * bh
            r = self.cache_ncc.get(d["mst"], {})
            muc = r.get("muc_rui_ro")
            if d["mst"] in self.ds_rr or muc == mst.RUI_RO:
                mau = DO
            elif muc == mst.THEO_DOI:
                mau = CAM
            elif muc == mst.AN_TOAN:
                mau = LUC
            else:
                mau = XAM
            w = (W - 150) * (d["tong"] / cao)
            c.create_rectangle(8, y + 4, 8 + max(2, w), y + bh - 6, fill=mau,
                               outline="")
            ten = (d.get("ten_hd") or d["mst"])[:34]
            c.create_text(12, y + bh / 2 - 1, text=ten, anchor="w", fill="#FFFFFF"
                          if w > 160 else "#263238", font=("Segoe UI", 8))
            c.create_text(W - 8, y + bh / 2 - 1, text=_tien(d["tong"]) + " đ",
                          anchor="e", fill="#263238", font=("Segoe UI", 8, "bold"))
        c.create_text(8, H - 8, anchor="w", fill=XAM, font=("Segoe UI", 8),
                      text="Màu: xanh = đang hoạt động, cam = cần theo dõi, "
                           "đỏ = rủi ro, xám = chưa tra cứu")

    def _ve_ts(self):
        c = self.cv_ts
        c.delete("all")
        W = c.winfo_width() or 700
        H = c.winfo_height() or 150
        if W < 60:
            return
        gom = {}
        for h in self.ds_ky:
            tl = cb.ty_le_thue(h)
            if tl is None:
                nhan = "Không xác định"
            elif h["thue"] == 0:
                nhan = "Không chịu thuế / 0%"
            else:
                g = min(cb.TS_CHUAN, key=lambda x: abs(x - tl))
                nhan = "%d%%" % round(g * 100) if abs(g - tl) <= 0.005 \
                    else "Khác (%.1f%%)" % (tl * 100)
            gom[nhan] = gom.get(nhan, 0) + h["tien_hang"]
        if not gom:
            c.create_text(W / 2, H / 2, text="Chưa có dữ liệu", fill=XAM)
            return
        tong = sum(gom.values()) or 1
        mau_ds = [XANH, LUC, CAM, TIM, XAM, DO]
        x = 10
        bw = W - 20
        y = 24
        for i, (k, v) in enumerate(sorted(gom.items(), key=lambda a: -a[1])):
            w = bw * (v / tong)
            m = mau_ds[i % len(mau_ds)]
            c.create_rectangle(x, y, x + max(2, w), y + 26, fill=m, outline="")
            if w > 70:
                c.create_text(x + w / 2, y + 13,
                              text="%s  %.1f%%" % (k, v / tong * 100),
                              fill="#FFFFFF", font=("Segoe UI", 8, "bold"))
            x += w
        yy = y + 42
        for i, (k, v) in enumerate(sorted(gom.items(), key=lambda a: -a[1])):
            cx = 12 + (i % 3) * (W / 3)
            cy = yy + (i // 3) * 20
            c.create_rectangle(cx, cy, cx + 11, cy + 11,
                               fill=mau_ds[i % len(mau_ds)], outline="")
            c.create_text(cx + 16, cy + 5,
                          text="%s: %s đ" % (k, _tien(v)), anchor="w",
                          fill="#263238", font=("Segoe UI", 9))

    # ------------------------------------------------------------------
    def _mo_chi_tiet(self, _e=None):
        iid = self.tv.focus()
        c = getattr(self, "_ban_do_cb", {}).get(iid)
        if not c:
            return
        CuaSoDanhSach(self, c)


class CuaSoDanhSach(ctk.CTkToplevel):
    def __init__(self, master, c):
        super().__init__(master)
        self.c = c
        self.title("Chi tiết cảnh báo - TAX INVOICE PRO")
        self.geometry("1150x620")
        self.configure(fg_color=NEN)
        self.after(200, self.lift)
        d = ctk.CTkFrame(self, fg_color=MAU_MUC.get(c["muc"], XANH), corner_radius=0)
        d.pack(fill="x")
        ctk.CTkLabel(d, text="  [%s] %s" % (c["muc"], c["tieu_de"]),
                     font=ctk.CTkFont(size=15, weight="bold"),
                     text_color="#FFFFFF", anchor="w").pack(fill="x", pady=8, padx=8)
        ctk.CTkLabel(self, text="Căn cứ: %s" % c["can_cu"], anchor="w",
                     font=ctk.CTkFont(size=12), wraplength=1100,
                     justify="left").pack(fill="x", padx=14, pady=(10, 0))
        ctk.CTkLabel(self, text="Hướng xử lý: %s" % c["xu_ly"], anchor="w",
                     font=ctk.CTkFont(size=12), text_color=XANH_DAM,
                     wraplength=1100, justify="left").pack(fill="x", padx=14,
                                                           pady=(4, 8))
        cot = ("ngay", "so", "ky_hieu", "mst", "ten", "hang", "thue", "tong",
               "tt", "ghi")
        nhan = ("Ngày lập", "Số HĐ", "Ký hiệu", "MST người bán", "Tên người bán",
                "Tiền hàng", "Thuế GTGT", "Tổng tiền", "Trạng thái", "Ghi chú")
        rong = (90, 90, 110, 120, 330, 110, 100, 120, 100, 220)
        kb = tk.Frame(self, bg=TRANG)
        kb.pack(fill="both", expand=True, padx=14, pady=6)
        self.tv = ttk.Treeview(kb, columns=cot, show="headings")
        for i, c2 in enumerate(cot):
            self.tv.heading(c2, text=nhan[i])
            self.tv.column(c2, width=rong[i],
                           anchor="e" if c2 in ("hang", "thue", "tong") else "w")
        sb = ttk.Scrollbar(kb, orient="vertical", command=self.tv.yview)
        self.tv.configure(yscrollcommand=sb.set)
        self.tv.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")
        for h in c["danh_sach"]:
            self.tv.insert("", "end", values=(
                mst.ngay_vn(h.get("ngay_lap")), h.get("so_hd"), h.get("ky_hieu"),
                h.get("mst_ban"), h.get("ten_ban"), _tien(h.get("tien_hang")),
                _tien(h.get("thue")), _tien(h.get("tong")), h.get("trang_thai"),
                h.get("_ghi", "")))
        n = ctk.CTkFrame(self, fg_color="transparent")
        n.pack(fill="x", padx=14, pady=(0, 12))
        ctk.CTkButton(n, text="Xuất danh sách ra CSV", command=self.xuat,
                      fg_color=LUC, width=190).pack(side="left")
        if c["ma"] == "kdtm":
            ctk.CTkButton(n, text="Đánh dấu đã có chứng từ thanh toán",
                          command=self.danh_dau, fg_color=XANH,
                          width=280).pack(side="left", padx=8)
        ctk.CTkButton(n, text="Đóng", command=self.destroy, fg_color=XAM,
                      width=110).pack(side="right")

    def xuat(self):
        p = filedialog.asksaveasfilename(
            parent=self, defaultextension=".csv",
            initialfile="CanhBao_%s_%s.csv" % (
                self.c["ma"], datetime.datetime.now().strftime("%Y%m%d_%H%M")),
            filetypes=[("CSV", "*.csv")])
        if not p:
            return
        try:
            with open(p, "w", encoding="utf-8-sig", newline="") as f:
                w = csv.writer(f, delimiter=";")
                w.writerow(["Ngày lập", "Số HĐ", "Ký hiệu", "MST người bán",
                            "Tên người bán", "Tiền hàng", "Thuế GTGT", "Tổng tiền",
                            "Trạng thái", "Ghi chú"])
                for h in self.c["danh_sach"]:
                    w.writerow([mst.ngay_vn(h.get("ngay_lap")), h.get("so_hd"),
                                h.get("ky_hieu"), h.get("mst_ban"),
                                h.get("ten_ban"), int(h.get("tien_hang", 0)),
                                int(h.get("thue", 0)), int(h.get("tong", 0)),
                                h.get("trang_thai"), h.get("_ghi", "")])
            messagebox.showinfo("Xong", "Đã lưu: %s" % p, parent=self)
        except Exception as e:
            messagebox.showerror("Lỗi", str(e), parent=self)

    def danh_dau(self):
        chon = self.tv.selection()
        if not chon:
            messagebox.showinfo("Chưa chọn",
                                "Hãy chọn một hoặc nhiều dòng trong bảng.", parent=self)
            return
        n = 0
        ds = self.c["danh_sach"]
        for iid in chon:
            i = self.tv.index(iid)
            if 0 <= i < len(ds) and mst.dat_chung_tu_thanh_toan(ds[i].get("khoa"), True):
                n += 1
        messagebox.showinfo("Xong", "Đã đánh dấu %d hóa đơn có chứng từ thanh toán "
                                    "không dùng tiền mặt." % n, parent=self)
        try:
            self.master.lam_moi()
        except Exception:
            pass
