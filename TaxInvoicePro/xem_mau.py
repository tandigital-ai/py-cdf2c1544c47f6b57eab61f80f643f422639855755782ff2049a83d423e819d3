# -*- coding: utf-8 -*-
"""
TAX INVOICE PRO - xem_mau.py (v1.6.1)
Cua so "Xem ban the hien": theo mau nha cung cap (XSLT nhung) hoac mau chuan
cua phan mem, va so sanh hai hoa don canh nhau.
Chay doc lap, khong sua tep nao dang chay.
Tac gia: TDA - 0986509106
"""
import os
import sys
import traceback
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

THU_MUC = os.path.dirname(os.path.abspath(__file__))
os.chdir(THU_MUC)
sys.path.insert(0, THU_MUC)

try:
    import va_ttk
except Exception:
    pass

import customtkinter as ctk

import xslt_nhung as xn
import mst_tra_cuu as mst

XANH = "#1565C0"
XANH_DAM = "#0D47A1"
NEN = "#F4F7FB"
TRANG = "#FFFFFF"
DO = "#C62828"
LUC = "#2E7D32"
TIM = "#6A1B9A"
CAM = "#EF6C00"
XAM = "#546E7A"


class CuaSoXemMau(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Xem bản thể hiện hóa đơn — TAX INVOICE PRO v%s" % xn.PHIEN_BAN)
        self.geometry("1240x760")
        self.configure(fg_color=NEN)
        self.ds = []
        self._dung_giao_dien()
        self.after(150, self.nap_kho)

    # ------------------------------------------------------------------
    def _dung_giao_dien(self):
        d = ctk.CTkFrame(self, fg_color=XANH, corner_radius=0)
        d.pack(fill="x")
        ctk.CTkLabel(d, text="  Xem bản thể hiện hóa đơn",
                     font=ctk.CTkFont(size=18, weight="bold"),
                     text_color="#FFFFFF").pack(side="left", pady=10, padx=8)
        self.lb_lxml = ctk.CTkLabel(d, text="", text_color="#FFFFFF",
                                    font=ctk.CTkFont(size=12))
        self.lb_lxml.pack(side="right", padx=14)

        tc = ctk.CTkFrame(self, fg_color="transparent")
        tc.pack(fill="x", padx=14, pady=10)
        ctk.CTkButton(tc, text="Nạp lại từ kho", width=130, fg_color=XAM,
                      command=self.nap_kho).pack(side="left", padx=3)
        ctk.CTkButton(tc, text="Mở tệp XML từ máy", width=160, fg_color=XAM,
                      command=self.mo_tep).pack(side="left", padx=3)
        ctk.CTkButton(tc, text="XEM THEO MẪU NHÀ CUNG CẤP", width=250,
                      fg_color=XANH, command=self.xem_ncc).pack(side="left", padx=3)
        ctk.CTkButton(tc, text="Xem mẫu chuẩn phần mềm", width=200, fg_color=TIM,
                      command=self.xem_chuan).pack(side="left", padx=3)
        ctk.CTkButton(tc, text="So sánh hai hóa đơn", width=170, fg_color=LUC,
                      command=self.so_sanh).pack(side="left", padx=3)
        self.nut_lxml = ctk.CTkButton(tc, text="Cài thư viện lxml", width=150,
                                      fg_color=CAM, command=self.cai_lxml)
        self.nut_lxml.pack(side="right", padx=3)
        ctk.CTkButton(tc, text="Xuất cặp XML + XSL", width=170, fg_color="#00897B",
                      command=self.xuat_cap).pack(side="right", padx=3)

        cot = ("ngay", "so", "ky_hieu", "ban", "tong", "mau", "tep")
        nhan = ("Ngày lập", "Số HĐ", "Ký hiệu", "Người bán", "Tổng tiền",
                "Mẫu nhà cung cấp", "Tệp XML")
        rong = (90, 90, 110, 330, 130, 190, 420)
        try:
            st = ttk.Style()
            st.configure("XM.Treeview", rowheight=26, font=("Segoe UI", 10))
            st.configure("XM.Treeview.Heading", font=("Segoe UI", 10, "bold"))
        except Exception:
            pass
        kb = tk.Frame(self, bg=TRANG)
        kb.pack(fill="both", expand=True, padx=14, pady=(0, 6))
        self.tv = ttk.Treeview(kb, columns=cot, show="headings", style="XM.Treeview",
                               selectmode="extended")
        for i, c in enumerate(cot):
            self.tv.heading(c, text=nhan[i])
            self.tv.column(c, width=rong[i], anchor="e" if c == "tong" else "w")
        sb = ttk.Scrollbar(kb, orient="vertical", command=self.tv.yview)
        self.tv.configure(yscrollcommand=sb.set)
        self.tv.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")
        self.tv.tag_configure("co", foreground="#1B5E20")
        self.tv.tag_configure("khong", foreground="#78909C")
        self.tv.tag_configure("mat", foreground="#B71C1C")
        self.tv.bind("<Double-1>", lambda e: self.xem_ncc())

        self.lb = ctk.CTkLabel(self, text="", anchor="w", text_color=XAM,
                               font=ctk.CTkFont(size=12), justify="left",
                               wraplength=1180)
        self.lb.pack(fill="x", padx=16, pady=(0, 4))
        ctk.CTkLabel(self, anchor="w", text_color=XAM,
                     font=ctk.CTkFont(size=11), justify="left", wraplength=1180,
                     text="Chọn một dòng rồi bấm XEM THEO MẪU NHÀ CUNG CẤP để mở "
                          "bản thể hiện giống hệt bản của bên bán. Chọn đúng hai "
                          "dòng rồi bấm So sánh hai hóa đơn để đối chiếu hóa đơn "
                          "gốc với hóa đơn điều chỉnh hoặc thay thế. In ra PDF "
                          "bằng Ctrl+P → Microsoft Print to PDF.   |   "
                          "Tác giả: TDA - 0986509106").pack(fill="x", padx=16,
                                                            pady=(0, 10))
        self._cap_nhat_lxml()

    def _cap_nhat_lxml(self):
        if xn.co_lxml():
            self.lb_lxml.configure(text="lxml: đã cài — dựng được mẫu nhà cung cấp")
            try:
                self.nut_lxml.configure(state="disabled", text="lxml đã cài")
            except Exception:
                pass
        else:
            self.lb_lxml.configure(text="lxml: chưa cài — bấm nút màu cam một lần")

    # ------------------------------------------------------------------
    def nap_kho(self):
        try:
            mst.khoi_tao_bang()
            hd = mst.doc_hoa_don()
        except Exception as e:
            messagebox.showerror("Lỗi", str(e), parent=self)
            return
        self.ds = [h for h in hd if h.get("xml")]
        self._ve()

    def mo_tep(self):
        ps = filedialog.askopenfilenames(
            parent=self, title="Chọn tệp XML hóa đơn",
            filetypes=[("Tệp XML", "*.xml"), ("Tất cả", "*.*")])
        if not ps:
            return
        for p in ps:
            self.ds.append({"ngay_lap": "", "so_hd": "", "ky_hieu": "",
                            "ten_ban": os.path.basename(p), "tong": 0, "xml": p})
        self._ve()

    def _ve(self):
        for i in self.tv.get_children():
            self.tv.delete(i)
        n_co = 0
        for idx, h in enumerate(self.ds):
            p = h.get("xml", "")
            if not os.path.exists(p):
                nhan, tag = "Thiếu tệp XML", "mat"
            else:
                try:
                    mau = xn.tim_xslt(p)
                except Exception:
                    mau = []
                if mau:
                    nhan, tag = "Có (%d mẫu)" % len(mau), "co"
                    n_co += 1
                else:
                    nhan, tag = "Không nhúng", "khong"
            self.tv.insert("", "end", iid=str(idx), tags=(tag,), values=(
                mst.ngay_vn(h.get("ngay_lap", "")), h.get("so_hd", ""),
                h.get("ky_hieu", ""), (h.get("ten_ban") or "")[:60],
                mst.tien(h.get("tong", 0)), nhan, p))
        self.lb.configure(
            text="Tổng %d hóa đơn có tệp XML — %d tệp nhúng sẵn mẫu trình bày của "
                 "nhà cung cấp, %d tệp còn lại sẽ dùng mẫu chuẩn của phần mềm."
                 % (len(self.ds), n_co, len(self.ds) - n_co))

    def _chon(self, so_luong=1):
        c = self.tv.selection()
        if len(c) < so_luong:
            messagebox.showinfo("Chưa chọn",
                                "Hãy chọn %d dòng trong bảng." % so_luong,
                                parent=self)
            return None
        kq = []
        for iid in c[:max(so_luong, len(c))]:
            h = self.ds[int(iid)]
            if not os.path.exists(h.get("xml", "")):
                messagebox.showwarning("Thiếu tệp",
                                       "Không tìm thấy tệp:\n%s" % h.get("xml"),
                                       parent=self)
                return None
            kq.append(h)
        return kq

    # ------------------------------------------------------------------
    def xem_ncc(self):
        c = self._chon(1)
        if not c:
            return
        h = c[0]
        try:
            p, mo_ta = xn.ban_the_hien_ncc(h["xml"])
            xn.mo(p)
            self.lb.configure(text="Đã mở bản thể hiện theo %s — %s" % (mo_ta, p))
        except Exception as e:
            if messagebox.askyesno(
                    "Chưa dùng được mẫu nhà cung cấp",
                    "%s\n\nMở bản thể hiện chuẩn của phần mềm thay thế?" % e,
                    parent=self):
                self.xem_chuan()

    def xem_chuan(self):
        c = self._chon(1)
        if not c:
            return
        try:
            p = xn.ban_the_hien_chuan(c[0]["xml"])
            xn.mo(p)
            self.lb.configure(text="Đã mở bản thể hiện chuẩn: %s" % p)
        except Exception:
            messagebox.showerror("Lỗi", traceback.format_exc()[-1500:], parent=self)

    def _mot_ban(self, h):
        try:
            return xn.ban_the_hien_ncc(h["xml"])[0]
        except Exception:
            return xn.ban_the_hien_chuan(h["xml"])

    def so_sanh(self):
        c = self.tv.selection()
        if len(c) != 2:
            messagebox.showinfo("Chọn hai dòng",
                                "Hãy chọn đúng hai hóa đơn (giữ Ctrl rồi nháy "
                                "chuột) để so sánh cạnh nhau.", parent=self)
            return
        try:
            a, b = self.ds[int(c[0])], self.ds[int(c[1])]
            pa, pb = self._mot_ban(a), self._mot_ban(b)
            na = "Số %s — ký hiệu %s — %s" % (a.get("so_hd", ""),
                                              a.get("ky_hieu", ""),
                                              mst.ngay_vn(a.get("ngay_lap", "")))
            nb = "Số %s — ký hiệu %s — %s" % (b.get("so_hd", ""),
                                              b.get("ky_hieu", ""),
                                              mst.ngay_vn(b.get("ngay_lap", "")))
            p = xn.so_sanh_canh_nhau(pa, pb, na, nb)
            xn.mo(p)
            self.lb.configure(text="Đã mở trang so sánh: %s" % p)
        except Exception:
            messagebox.showerror("Lỗi", traceback.format_exc()[-1500:], parent=self)

    def xuat_cap(self):
        c = self._chon(1)
        if not c:
            return
        try:
            mau = xn.tim_xslt(c[0]["xml"])
            if not mau:
                messagebox.showinfo("Không có mẫu",
                                    "Tệp này không nhúng mẫu của nhà cung cấp.",
                                    parent=self)
                return
            p_xml, p_xsl = xn.xuat_cap_tep(c[0]["xml"], mau[0][1])
            messagebox.showinfo(
                "Đã xuất",
                "Đã tạo hai tệp:\n%s\n%s\n\nMở tệp .xml vừa tạo bằng trình duyệt "
                "Firefox sẽ thấy đúng mẫu của nhà cung cấp." % (p_xml, p_xsl),
                parent=self)
            try:
                os.startfile(os.path.dirname(p_xml))
            except Exception:
                pass
        except Exception:
            messagebox.showerror("Lỗi", traceback.format_exc()[-1500:], parent=self)

    def cai_lxml(self):
        self.nut_lxml.configure(state="disabled", text="Đang cài...")
        self.update_idletasks()
        ok, ra = xn.cai_lxml()
        self._cap_nhat_lxml()
        if ok:
            messagebox.showinfo("Xong", "Đã cài xong lxml. Bấm lại nút XEM THEO "
                                        "MẪU NHÀ CUNG CẤP.", parent=self)
        else:
            self.nut_lxml.configure(state="normal", text="Cài thư viện lxml")
            messagebox.showerror("Không cài được", ra[-1500:], parent=self)


def main():
    try:
        CuaSoXemMau().mainloop()
    except Exception:
        print(traceback.format_exc())
        input("Nhan Enter de dong...")


if __name__ == "__main__":
    main()

TEP_DAY_DU = True  # dau hieu tep da duoc dan day du - dung xoa dong nay
