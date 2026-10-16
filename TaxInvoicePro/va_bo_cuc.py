# -*- coding: utf-8 -*-
"""
va_bo_cuc.py - TAX INVOICE PRO v1.7.1
Chen dong "import bo_cuc" vao khoi_dong.py de bo cuc moi, huong dan va
bo sua cong thuc Excel tu dong co hieu luc. Chay mot lan la du.
Tac gia: TDA - 0986509106
"""

import os
import sys
import shutil
import datetime as dt

THU_MUC = os.path.dirname(os.path.abspath(__file__))
os.chdir(THU_MUC)
if THU_MUC not in sys.path:
    sys.path.insert(0, THU_MUC)

TEP = "khoi_dong.py"
DONG = "import bo_cuc  # bo cuc keo gian + huong dan + sua cong thuc Excel"
CAN_CO = ("giao_dien.py", "bo_cuc.py", "huong_dan.py", "va_excel.py", "khoi_dong.py")


def main():
    print("=== VA BO CUC - TAX INVOICE PRO v1.7.1 ===")
    print("Thu muc: %s" % THU_MUC)
    thieu = [t for t in CAN_CO if not os.path.exists(os.path.join(THU_MUC, t))]
    if thieu:
        print("[LOI] chua co cac tep: %s" % ", ".join(thieu))
        print("      Hay tao du cac tep roi chay lai.")
        return 1

    for ten in ("va_excel", "huong_dan", "bo_cuc"):
        try:
            __import__(ten)
            print("[ok]   %s nap thu thanh cong." % ten)
        except Exception as e:
            print("[LOI]  %s khong nap duoc: %s" % (ten, e))
            import traceback
            traceback.print_exc()
            return 1

    with open(TEP, "r", encoding="utf-8") as f:
        src = f.read()

    if "import bo_cuc" in src:
        print("[=]    khoi_dong.py da co dong import bo_cuc, khong can chen lai.")
    else:
        moc = "import giao_dien as gd"
        if moc in src:
            src = src.replace(moc, moc + "\n" + DONG, 1)
        else:
            dong = src.split("\n")
            vt = 0
            for i, d in enumerate(dong):
                if d.startswith("import ") or d.startswith("from "):
                    vt = i + 1
            dong.insert(vt, DONG)
            src = "\n".join(dong)
        ban_sao = "%s.bak_%s" % (TEP, dt.datetime.now().strftime("%Y%m%d_%H%M%S"))
        shutil.copyfile(TEP, ban_sao)
        with open(TEP, "w", encoding="utf-8") as f:
            f.write(src)
        print("[+]    Da chen dong import bo_cuc vao khoi_dong.py")
        print("       Ban sao luu: %s" % ban_sao)

    print("")
    print("Tiep theo:")
    print("  1. python va_excel.py           (sua cong thuc cac tep Excel da xuat truoc day)")
    print("  2. python thu_man_hinh.py       (kiem tra lai toan bo)")
    print("  3. nhay dup ChayAppMoi.bat")
    return 0


if __name__ == "__main__":
    sys.exit(main())


TEP_DAY_DU = True  # dau hieu tep da duoc dan day du - dung xoa dong nay
