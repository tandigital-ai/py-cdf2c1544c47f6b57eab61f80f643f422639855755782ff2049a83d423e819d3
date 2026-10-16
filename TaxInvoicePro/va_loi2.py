# -*- coding: utf-8 -*-
"""
va_loi2.py - Chen lop va tuong thich ttk vao tep khoi dong app.py
Chay:  python va_loi2.py
Tac gia: TDA - 0986509106
"""
import io
import os
import shutil
import datetime

TEP = "app.py"
DONG = "import va_ttk  # va loi command=None cua ttk tren Python 3.12+"


def doc(ten):
    with io.open(ten, "r", encoding="utf-8") as f:
        return f.read()


def ghi(ten, noi_dung):
    with io.open(ten, "w", encoding="utf-8", newline="\n") as f:
        f.write(noi_dung)


def chen(src):
    if "import va_ttk" in src:
        return src, False
    dong = src.split("\n")
    vt = 0
    for i, d in enumerate(dong[:200]):
        s = d.strip()
        if s.startswith("def ") or s.startswith("class "):
            break
        if s.startswith("import ") or s.startswith("from "):
            vt = i + 1
    dong.insert(vt, DONG)
    return "\n".join(dong), True


def main():
    print("=" * 62)
    print(" VA LOI 2 - TAX INVOICE PRO")
    print(" Thu muc: %s" % os.getcwd())
    print("=" * 62)

    import sys
    print(" Python dang dung: %s" % sys.version.split()[0])

    if not os.path.exists("va_ttk.py"):
        print(" [X] Thieu tep va_ttk.py. Hay tao tep do truoc roi chay lai.")
        return
    if not os.path.exists(TEP):
        print(" [X] Khong thay app.py. Hay chay lenh nay trong thu muc du an.")
        return

    try:
        import va_ttk  # kiem tra tep va chay duoc
        _ = va_ttk
        print(" [ok] va_ttk.py nap thu thanh cong.")
    except Exception as e:
        print(" [X] va_ttk.py bi loi: %s" % e)
        return

    goc = doc(TEP)
    moi, da_chen = chen(goc)

    if not da_chen:
        print(" [ok] app.py da co san dong import va_ttk, khong can sua.")
    else:
        try:
            compile(moi, TEP, "exec")
        except SyntaxError as e:
            print(" [X] Sau khi sua bi loi cu phap dong %s: %s" % (e.lineno, e.msg))
            return
        nhan = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        shutil.copyfile(TEP, "%s.bak2_%s" % (TEP, nhan))
        ghi(TEP, moi)
        print(" [+] Da chen dong import va_ttk vao app.py (co ban sao luu).")

    dem = 0
    for ten in sorted(os.listdir(".")):
        if ten.endswith(".py"):
            try:
                dem += doc(ten).count("else None)")
            except Exception:
                pass
    print(" Da bao ve %d cho viet kieu 'command=... else None'." % dem)

    print("-" * 62)
    print(" Xong. Buoc tiep theo: chay ChayApp.bat")
    print("=" * 62)


if __name__ == "__main__":
    main()
