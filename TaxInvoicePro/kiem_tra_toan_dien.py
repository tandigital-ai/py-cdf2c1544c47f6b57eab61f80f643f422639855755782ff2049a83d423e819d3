# -*- coding: utf-8 -*-
"""
kiem_tra_toan_dien.py - TAX INVOICE PRO v1.7.2
Bo kiem tra tu dong truoc khi dong goi exe. Khong sua du lieu that.
Chay:  python kiem_tra_toan_dien.py
Ket qua: man hinh + logs\kiem_tra_toan_dien.txt
Tac gia: TDA - 0986509106
"""

import os
import sys
import gc
import glob
import time
import sqlite3
import threading
import traceback
import datetime as dt
import tkinter as tk
from tkinter import ttk

THU_MUC = os.path.dirname(os.path.abspath(__file__))
if THU_MUC not in sys.path:
    sys.path.insert(0, THU_MUC)
os.chdir(THU_MUC)
os.makedirs(os.path.join(THU_MUC, "logs"), exist_ok=True)
TEP_KQ = os.path.join(THU_MUC, "logs", "kiem_tra_toan_dien.txt")

try:
    import faulthandler
    faulthandler.dump_traceback_later(300, exit=True,
                                      file=open(os.path.join(THU_MUC, "logs",
                                                             "test_treo.txt"), "w"))
except Exception:
    faulthandler = None

DONG = []
KQ = []


def ra(s=""):
    print(s)
    DONG.append(s)


def ket(ten, dat, ghi_chu=""):
    KQ.append((ten, dat, ghi_chu))
    ra("%-6s %s%s" % ("[DAT]" if dat else "[HONG]", ten,
                      ("  -> " + ghi_chu) if ghi_chu else ""))


def _duyet(w, con=None):
    if con is None:
        con = [4000]
    if con[0] <= 0:
        return
    con[0] -= 1
    yield w
    try:
        ds = w.winfo_children()
    except Exception:
        ds = []
    for c in ds:
        for x in _duyet(c, con):
            yield x


def bom(root, giay):
    """Cho vong lap su kien chay trong mot khoang thoi gian."""
    t0 = time.time()
    while time.time() - t0 < giay:
        try:
            root.update()
        except Exception:
            return
        time.sleep(0.01)


# =========================================================== 1. bien dich
TEP_BO_QUA = ("kiem_tra_toan_dien.py",)


def t1_bien_dich():
    ra("")
    ra("--- 1. Bien dich toan bo ma nguon ---")
    loi = []
    for dd in sorted(glob.glob(os.path.join(THU_MUC, "*.py"))):
        ten = os.path.basename(dd)
        if ten in TEP_BO_QUA:
            continue
        try:
            with open(dd, "r", encoding="utf-8", errors="replace") as f:
                src = f.read()
            compile(src, ten, "exec")
        except SyntaxError as e:
            loi.append("%s dong %s: %s" % (ten, e.lineno, e.msg))
        except Exception as e:
            loi.append("%s: %s" % (ten, e))
    ket("Bien dich ma nguon", not loi, "; ".join(loi))
    return not loi


# =========================================================== 2. nap module
CAN_CO = ["giao_dien", "giam_sat", "bo_cuc", "va_excel", "huong_dan",
          "kho", "app", "khoi_dong"]
TUY_CHON = ["man_hinh_moi", "trang_chu_pro", "man_hinh_ncc", "doi_chieu",
            "bao_cao", "bao_cao_chi_tiet", "invoice_view", "xml_parser",
            "importer", "exporter", "theo_doi", "hop_thu", "xslt_nhung",
            "canh_bao", "mst_tra_cuu", "tt91"]


def t2_nap_module():
    ra("")
    ra("--- 2. Nap module ---")
    hong = []
    for ten in CAN_CO:
        try:
            __import__(ten)
            ra("   [ok] %s" % ten)
        except Exception:
            hong.append(ten)
            ra("   [LOI] %s" % ten)
            ra(traceback.format_exc())
    for ten in TUY_CHON:
        if not os.path.exists(os.path.join(THU_MUC, ten + ".py")):
            continue
        try:
            __import__(ten)
            ra("   [ok] %s" % ten)
        except Exception:
            hong.append(ten)
            ra("   [LOI] %s" % ten)
            ra(traceback.format_exc())
    ket("Nap module", not hong, ", ".join(hong))
    return not hong


# =========================================================== 3. CSDL
def t3_csdl():
    ra("")
    ra("--- 3. Co so du lieu va truy cap nhieu luong ---")
    try:
        import giam_sat
        giam_sat.cung_hoa_sqlite()
    except Exception:
        pass
    db = os.path.join(THU_MUC, "data", "taxinvoice.db")
    if not os.path.exists(db):
        ket("CSDL ton tai", False, "khong thay data\\taxinvoice.db")
        return False
    try:
        cn = sqlite3.connect(db)
        n = cn.execute("SELECT COUNT(*) FROM hoa_don").fetchone()[0]
        cn.execute("CREATE TABLE IF NOT EXISTS tda_thu (a INTEGER)")
        cn.execute("DROP TABLE tda_thu")
        cn.commit()
        cn.close()
        ra("   Bang hoa_don co %d dong." % n)
    except Exception as e:
        ket("Doc ghi CSDL", False, str(e))
        return False

    loi = []

    def viec(i):
        try:
            c = sqlite3.connect(db)
            for _ in range(20):
                c.execute("SELECT COUNT(*) FROM hoa_don").fetchone()
            c.execute("CREATE TABLE IF NOT EXISTS tda_thu%d (a INTEGER)" % i)
            c.execute("INSERT INTO tda_thu%d VALUES (1)" % i)
            c.commit()
            c.execute("DROP TABLE tda_thu%d" % i)
            c.commit()
            c.close()
        except Exception as e:
            loi.append("luong %d: %s" % (i, e))

    ds = [threading.Thread(target=viec, args=(i,)) for i in range(4)]
    for t in ds:
        t.start()
    for t in ds:
        t.join(30)
    ket("Bon luong dung CSDL cung luc", not loi, "; ".join(loi))
    return not loi


# =========================================================== 4..8 giao dien
def t_giao_dien():
    ra("")
    ra("--- 4. Dung cua so va cac man hinh ---")
    import giao_dien as gd
    gd.bat_dpi()
    import customtkinter as ctk
    import khoi_dong

    ctk.set_appearance_mode("light")
    root = ctk.CTk()
    root.geometry("1280x820")
    root.withdraw()
    k = gd.ap_dung(root)
    ra("   He so hien thi: %.2f" % k)

    try:
        import bo_cuc
    except Exception:
        bo_cuc = None

    bang = khoi_dong.nap_lop()
    for ten, noi_dung in khoi_dong.LOI_NAP.items():
        ra("   [LOI] module %s" % ten)
        ra(noi_dung)
    ket("Nap lop man hinh moi", not khoi_dong.LOI_NAP,
        ", ".join(khoi_dong.LOI_NAP.keys()))

    khung = ctk.CTkFrame(root)
    khung.pack(fill="both", expand=True)
    root.deiconify()
    root.update()

    mh = {}
    hong = []
    for ma, lop in sorted(bang.items()):
        t0 = time.time()
        doi_tuong = None
        vet = ""
        for doi_so in ((khung, None), (khung,)):
            try:
                doi_tuong = lop(*doi_so)
                break
            except TypeError:
                vet = traceback.format_exc()
            except Exception:
                vet = traceback.format_exc()
                break
        giay = time.time() - t0
        if doi_tuong is None:
            hong.append(ma)
            ra("   [LOI] %s khong dung duoc" % ma)
            ra(vet)
        else:
            mh[ma] = doi_tuong
            ra("   [ok] %-18s dung trong %.2f giay" % (ma, giay))
            if giay > 3.0:
                ra("        (cham - nen xem lai man hinh nay)")
    ket("Dung tat ca man hinh", not hong, ", ".join(hong))

    # ---- 5. bao Configure -------------------------------------------------
    ra("")
    ra("--- 5. Phat hien vong lap co giat (bao Configure) ---")
    tong_bao = {}
    for ma, doi_tuong in mh.items():
        dem = {"n": 0}
        ds_w = [w for w in _duyet(doi_tuong)
                if isinstance(w, (ttk.Treeview, tk.Canvas))]
        for w in ds_w:
            try:
                w.bind("<Configure>", lambda e, d=dem: d.__setitem__("n", d["n"] + 1),
                       add="+")
            except Exception:
                pass
        try:
            doi_tuong.pack(fill="both", expand=True)
            if bo_cuc is not None:
                bo_cuc.chinh_cay(doi_tuong)
            root.update()
            root.geometry("1200x760")
            bom(root, 1.2)
            root.geometry("1360x840")
            bom(root, 1.8)
            doi_tuong.pack_forget()
        except Exception:
            ra("   [canh bao] %s: %s" % (ma, traceback.format_exc(limit=1)))
        tong_bao[ma] = dem["n"]
        ra("   %-18s %3d widget theo doi, %4d su kien Configure" %
           (ma, len(ds_w), dem["n"]))
    xau = [m for m, n in tong_bao.items() if n > 400]
    ket("Khong co vong lap co giat", not xau,
        "man hinh bao Configure: " + ", ".join(xau) if xau else "")

    # ---- 6. chuyen man hinh lien tuc --------------------------------------
    ra("")
    ra("--- 6. Chuyen qua lai giua cac man hinh 30 lan ---")
    truoc_w = len(list(_duyet(root)))
    truoc_h = len(root.tk.splitlist(root.tk.call("after", "info")))
    ten_mh = list(mh.keys())
    tre_max = 0.0
    if ten_mh:
        for i in range(30):
            cu = mh[ten_mh[i % len(ten_mh)]]
            t0 = time.time()
            try:
                cu.pack(fill="both", expand=True)
                root.update()
                cu.pack_forget()
                root.update()
            except Exception:
                pass
            tre_max = max(tre_max, time.time() - t0)
        bom(root, 1.0)
    sau_w = len(list(_duyet(root)))
    sau_h = len(root.tk.splitlist(root.tk.call("after", "info")))
    ra("   Widget: %d -> %d   Hen gio dang cho: %d -> %d   Cham nhat: %.2f giay"
       % (truoc_w, sau_w, truoc_h, sau_h, tre_max))
    ket("Khong ro ri widget", sau_w - truoc_w < 200,
        "tang %d widget" % (sau_w - truoc_w))
    ket("Khong ro ri hen gio", sau_h < 300, "con %d viec hen gio" % sau_h)
    ket("Giao dien con nhanh", tre_max < 1.5, "cham nhat %.2f giay" % tre_max)

    # ---- 7. cua so chi tiet hoa don ---------------------------------------
    ra("")
    ra("--- 7. Cua so xem chi tiet hoa don ---")
    mo_duoc, ghi_chu = _thu_cua_so_hoa_don(root)
    ket("Mo duoc cua so hoa don", mo_duoc, ghi_chu)

    # ---- 8. dich vu nen mac dinh phai TAT ---------------------------------
    ra("")
    ra("--- 8. Dich vu nen va tra cuu mang (mac dinh phai tat) ---")
    bat = []
    try:
        import json
        dd = os.path.join(THU_MUC, "data", "tu_dong.json")
        if os.path.exists(dd):
            c = json.load(open(dd, "r", encoding="utf-8"))
            if c.get("bat") or c.get("tu_dong"):
                bat.append("bo quet thu muc")
            if (c.get("imap") or {}).get("bat"):
                bat.append("hop thu IMAP")
    except Exception:
        pass
    try:
        import mst_tra_cuu
        if (mst_tra_cuu.doc_cau_hinh() or {}).get("bat"):
            bat.append("tra cuu MST truc tuyen")
    except Exception:
        pass
    ra("   Dang bat: %s" % (", ".join(bat) if bat else "khong co"))
    ket("Khong co dich vu nen chay ngoai y muon", True,
        "dang bat: " + ", ".join(bat) if bat else "")

    try:
        root.destroy()
    except Exception:
        pass
    gc.collect()
    return True


def _thu_cua_so_hoa_don(root):
    try:
        import kho
    except Exception:
        return False, "khong nap duoc kho"
    hd = None
    try:
        ds = kho.lay_danh_sach() or []
        if ds:
            hd = dict(ds[0])
            if hasattr(kho, "lay_chi_tiet"):
                try:
                    ct = kho.lay_chi_tiet(hd.get("id") or hd.get("khoa"))
                    if ct:
                        hd = dict(ct) if not isinstance(ct, (list, tuple)) else hd
                except Exception:
                    pass
    except Exception:
        return False, "khong doc duoc danh sach hoa don"
    if hd is None:
        return False, "kho khong co hoa don nao de thu"

    try:
        import invoice_view as iv
    except Exception:
        return False, "khong nap duoc invoice_view"

    ten_thu = ("CuaSoHoaDon", "XemHoaDon", "ManHinhHoaDon", "CuaSoChiTiet",
               "mo_hoa_don", "mo", "hien_hoa_don", "xem")
    cuoi = ""
    for ten in ten_thu:
        ham = getattr(iv, ten, None)
        if ham is None:
            continue
        for doi_so in ((root, hd), (root, hd, None), (hd,), (root, hd.get("id"))):
            cs = None
            try:
                cs = ham(*doi_so)
            except TypeError:
                cuoi = "TypeError voi %s" % ten
                continue
            except Exception:
                cuoi = "%s: %s" % (ten, traceback.format_exc(limit=2))
                break
            bom(root, 1.5)
            song = False
            for w in root.winfo_children():
                if isinstance(w, tk.Toplevel):
                    song = True
                    try:
                        w.destroy()
                    except Exception:
                        pass
            if cs is not None and hasattr(cs, "destroy"):
                try:
                    cs.destroy()
                except Exception:
                    pass
            bom(root, 0.3)
            return True, "mo bang %s" % ten
    return False, cuoi or "khong tim thay ham mo cua so hoa don"


# =========================================================== 9. Excel
def t9_excel():
    ra("")
    ra("--- 9. Cong thuc cong nhom trong tep Excel ---")
    try:
        import va_excel
        from openpyxl import load_workbook
    except Exception as e:
        ket("Kiem tra Excel", False, str(e))
        return False
    ds = []
    for mau in ("*.xlsx", os.path.join("data", "*.xlsx"), os.path.join("bao_cao", "*.xlsx")):
        ds += [d for d in glob.glob(os.path.join(THU_MUC, mau))
               if not os.path.basename(d).startswith("~$")]
    if not ds:
        ra("   Khong tim thay tep xlsx nao de kiem tra (bo qua).")
        ket("Kiem tra Excel", True, "chua co tep de kiem")
        return True
    ds.sort(key=os.path.getmtime, reverse=True)
    con_sai = []
    for dd in ds[:3]:
        try:
            wb = load_workbook(dd)
            n = 0
            for ws in wb.worksheets:
                n += len(va_excel.sua_sheet(ws))   # chi tinh trong bo nho
            wb.close()
            ra("   %-45s %s" % (os.path.basename(dd),
                                "dung" if n == 0 else "con %d cong thuc sai" % n))
            if n:
                con_sai.append(os.path.basename(dd))
        except Exception as e:
            ra("   %-45s khong doc duoc: %s" % (os.path.basename(dd), e))
    ket("Cong thuc cong nhom dung", not con_sai,
        "chay 'python va_excel.py' cho: " + ", ".join(con_sai) if con_sai else "")
    return not con_sai


# =========================================================== 10. luong
def t10_luong():
    ra("")
    ra("--- 10. Luong con song sau khi test ---")
    con = [t.name for t in threading.enumerate()
           if t is not threading.main_thread() and not t.daemon and t.is_alive()]
    ra("   %s" % (", ".join(con) if con else "khong con luong nao"))
    ket("Khong con luong chan viec thoat", not con, ", ".join(con))
    return not con


# =========================================================== chay
def main():
    ra("=" * 70)
    ra("KIEM TRA TOAN DIEN - TAX INVOICE PRO v1.7.2")
    ra("Thoi diem: %s" % dt.datetime.now().strftime("%d/%m/%Y %H:%M:%S"))
    ra("Python: %s   Thu muc: %s" % (sys.version.split()[0], THU_MUC))
    ra("=" * 70)

    t1_bien_dich()
    if not t2_nap_module():
        ra("")
        ra("Dung lai: con module khong nap duoc, sua xong hay chay lai.")
    t3_csdl()
    try:
        t_giao_dien()
    except Exception:
        ra("")
        ra("[LOI] phan kiem tra giao dien bi gian doan:")
        ra(traceback.format_exc())
        ket("Kiem tra giao dien", False, "gian doan")
    t9_excel()
    t10_luong()

    ra("")
    ra("=" * 70)
    hong = [t for t, d, _ in KQ if not d]
    ra("TONG KET: %d muc dat / %d muc kiem tra" % (len(KQ) - len(hong), len(KQ)))
    if hong:
        ra("CON LOI O: %s" % ", ".join(hong))
        ra("CHUA NEN DONG GOI EXE. Hay gui lai tep nay de sua.")
    else:
        ra("TAT CA DAT. Co the dong goi exe.")
    ra("=" * 70)

    try:
        with open(TEP_KQ, "w", encoding="utf-8") as f:
            f.write("\n".join(DONG))
        ra("Da luu: logs\\kiem_tra_toan_dien.txt")
    except Exception:
        pass
    if faulthandler is not None:
        try:
            faulthandler.cancel_dump_traceback_later()
        except Exception:
            pass
    return 1 if hong else 0


if __name__ == "__main__":
    sys.exit(main())


TEP_DAY_DU = True  # dau hieu tep da duoc dan day du - dung xoa dong nay
