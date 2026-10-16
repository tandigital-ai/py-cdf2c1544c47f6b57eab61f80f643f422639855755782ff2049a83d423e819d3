# -*- coding: utf-8 -*-
"""
va_loi.py - Cong cu va loi tu dong cho TAX INVOICE PRO
Sua loi: 'bind_all' is not allowed, could result in undefined behavior
Tac gia: TDA - 0986509106
Cach chay:  python va_loi.py
"""
import io
import os
import re
import shutil
import datetime

TEN_TOI = os.path.basename(__file__)
DONG_IMPORT = "import tkinter as _tkbase  # va loi bind_all cua customtkinter"

RE_BIND = re.compile(r"\bself((?:\.[A-Za-z_]\w*)*)\.bind_all\(")
RE_UNBIND = re.compile(r"\bself((?:\.[A-Za-z_]\w*)*)\.unbind_all\(")


def danh_sach_tep():
    ds = []
    for ten in sorted(os.listdir(".")):
        if ten.endswith(".py") and ten != TEN_TOI:
            ds.append(ten)
    return ds


def doc(ten):
    with io.open(ten, "r", encoding="utf-8") as f:
        return f.read()


def ghi(ten, noi_dung):
    with io.open(ten, "w", encoding="utf-8", newline="\n") as f:
        f.write(noi_dung)


def chen_import(src):
    """Chen 'import tkinter as _tkbase' vao cuoi khoi import dau tep."""
    if DONG_IMPORT in src or "import tkinter as _tkbase" in src:
        return src, False
    dong = src.split("\n")
    vi_tri = 0
    for i, d in enumerate(dong[:150]):
        s = d.strip()
        if s.startswith("def ") or s.startswith("class "):
            break
        if s.startswith("import ") or s.startswith("from "):
            vi_tri = i + 1
    dong.insert(vi_tri, DONG_IMPORT)
    return "\n".join(dong), True


def va_mot_tep(ten):
    """Tra ve (da_sua, so_cho_sua, loi_cu_phap)."""
    goc = doc(ten)
    so = len(RE_BIND.findall(goc)) + len(RE_UNBIND.findall(goc))
    if so == 0:
        return False, 0, kiem_tra_cu_phap(ten, goc)

    moi = RE_UNBIND.sub(r"_tkbase.Misc.unbind_all(self\1, ", goc)
    moi = RE_BIND.sub(r"_tkbase.Misc.bind_all(self\1, ", moi)
    moi, _ = chen_import(moi)

    loi = kiem_tra_cu_phap(ten, moi)
    if loi:
        return False, so, loi

    nhan = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    shutil.copyfile(ten, "%s.bak_%s" % (ten, nhan))
    ghi(ten, moi)
    return True, so, None


def kiem_tra_cu_phap(ten, src):
    try:
        compile(src, ten, "exec")
        return None
    except SyntaxError as e:
        return "dong %s: %s" % (e.lineno, e.msg)


def main():
    print("=" * 62)
    print(" CONG CU VA LOI - TAX INVOICE PRO")
    print(" Thu muc: %s" % os.getcwd())
    print("=" * 62)

    tep = danh_sach_tep()
    if not tep:
        print("Khong tim thay tep .py nao. Hay chay lenh nay trong thu muc du an.")
        return

    tong_sua = 0
    hong = []
    for ten in tep:
        try:
            da_sua, so, loi = va_mot_tep(ten)
        except Exception as e:
            print("  [!] %-22s doc tep that bai: %s" % (ten, e))
            hong.append(ten)
            continue

        dem_dong = len(doc(ten).split("\n"))
        if loi:
            print("  [X] %-22s CU PHAP HONG -> %s" % (ten, loi))
            hong.append(ten)
        elif da_sua:
            tong_sua += so
            print("  [+] %-22s da sua %d cho bind_all  (%d dong)" % (ten, so, dem_dong))
        else:
            print("  [ok] %-21s khong can sua        (%d dong)" % (ten, dem_dong))

    print("-" * 62)
    if hong:
        print("CAC TEP CAN DAN LAI (bi dut hoac sai cu phap):")
        for t in hong:
            print("   - %s" % t)
    else:
        print("Tat ca tep deu dung cu phap, khong co tep nao bi dut.")
    print("Da sua tong cong %d cho goi bind_all/unbind_all." % tong_sua)
    print("Ban sao luu duoc luu cung thu muc voi duoi .bak_<ngay_gio>")
    print("")
    print("Buoc tiep theo: chay ChayApp.bat")
    print("=" * 62)


if __name__ == "__main__":
    main()
