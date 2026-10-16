# -*- coding: utf-8 -*-
"""
thu_man_hinh.py - TAX INVOICE PRO v1.7.0
Kiem tra: tep co bi cat khi dan khong, va tung man hinh co dung duoc khong.
Tac gia: TDA - 0986509106
"""

import os
import sys
import traceback
import datetime as dt

THU_MUC = os.path.dirname(os.path.abspath(__file__))
if THU_MUC not in sys.path:
    sys.path.insert(0, THU_MUC)
os.chdir(THU_MUC)
os.makedirs(os.path.join(THU_MUC, "logs"), exist_ok=True)
TEP_LOG = os.path.join(THU_MUC, "logs", "thu_man_hinh.txt")

DONG = []


def ra(s=""):
    print(s)
    DONG.append(s)


TEP_KIEM = ["giao_dien.py", "mst_tra_cuu.py", "canh_bao.py", "trang_chu_pro.py",
            "man_hinh_ncc.py", "man_hinh_moi.py", "khoi_dong.py",
            "doi_chieu.py", "bao_cao.py", "bao_cao_chi_tiet.py",
            "theo_doi.py", "hop_thu.py", "xslt_nhung.py", "xem_mau.py"]


def kiem_tep():
    ra("--- Kiem tra tep co bi cat khi dan hay khong ---")
    loi = []
    for ten in TEP_KIEM:
        dd = os.path.join(THU_MUC, ten)
        if not os.path.exists(dd):
            ra("[bo qua] %s chua co" % ten)
            continue
        try:
            with open(dd, "r", encoding="utf-8", errors="replace") as f:
                src = f.read()
        except Exception as e:
            ra("[LOI]  %s khong doc duoc: %s" % (ten, e))
            loi.append(ten)
            continue
        so_dong = src.count("\n") + 1
        try:
            compile(src, ten, "exec")
        except SyntaxError as e:
            ra("[LOI]  %s loi cu phap dong %s: %s" % (ten, e.lineno, e.msg))
            ra("       -> Tep bi cat hoac dan thieu. Hay dan lai TOAN BO tep nay.")
            loi.append(ten)
            continue
        if "TEP_DAY_DU" in src:
            ra("[ok]   %s day du (%d dong, co dau hieu TEP_DAY_DU)" % (ten, so_dong))
        else:
            ra("[ok]   %s dung cu phap (%d dong)" % (ten, so_dong))
    return loi


def thu_dung():
    ra("")
    ra("--- Thu dung tung man hinh ---")
    loi = []
    try:
        import giao_dien as gd
        gd.bat_dpi()
        import customtkinter as ctk
    except Exception:
        ra("[LOI]  khong nap duoc customtkinter / giao_dien")
        ra(traceback.format_exc())
        return ["moi truong"]

    root = ctk.CTk()
    root.withdraw()
    try:
        gd.ap_dung(root)
    except Exception:
        ra("[canh bao] khong ap dung duoc ty le hien thi")
        ra(traceback.format_exc())

    import khoi_dong
    bang = khoi_dong.nap_lop()
    for ten, noi_dung in khoi_dong.LOI_NAP.items():
        ra("[LOI]  khong nap duoc module %s" % ten)
        ra(noi_dung)
        loi.append(ten)

    khung = ctk.CTkFrame(root)
    for ma, lop in sorted(bang.items()):
        mh = None
        vet = ""
        for doi_so in ((khung, None), (khung,)):
            try:
                mh = lop(*doi_so)
                break
            except TypeError:
                vet = traceback.format_exc()
                continue
            except Exception:
                vet = traceback.format_exc()
                break
        if mh is None:
            ra("[LOI]  %s KHONG dung duoc" % ma)
            ra(vet)
            loi.append(ma)
        else:
            ra("[ok]   %s dung duoc (%s)" % (ma, lop.__name__))
            try:
                mh.destroy()
            except Exception:
                pass
    try:
        root.destroy()
    except Exception:
        pass
    return loi


def main():
    ra("=== THU DUNG MAN HINH - TAX INVOICE PRO v1.7.0 ===")
    ra("Thoi diem: %s" % dt.datetime.now().strftime("%d/%m/%Y %H:%M:%S"))
    ra("Python: %s" % sys.version.split()[0])
    ra("Thu muc: %s" % THU_MUC)
    ra("")
    l1 = kiem_tep()
    l2 = thu_dung()
    ra("")
    tat_ca = sorted(set(l1 + l2))
    if tat_ca:
        ra("KET LUAN: con loi o -> %s" % ", ".join(tat_ca))
        ra("Hay chup toan bo cua so nay gui lai.")
    else:
        ra("KET LUAN: tat ca deu tot. Hay chay ChayAppMoi.bat.")
    try:
        with open(TEP_LOG, "w", encoding="utf-8") as f:
            f.write("\n".join(DONG))
        ra("Da luu: logs\\thu_man_hinh.txt")
    except Exception:
        pass


if __name__ == "__main__":
    main()


TEP_DAY_DU = True  # dau hieu tep da duoc dan day du - dung xoa dong nay
