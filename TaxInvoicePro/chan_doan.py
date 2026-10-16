# -*- coding: utf-8 -*-
"""
TAX INVOICE PRO - chan_doan.py (v1.6.0)
Cong cu tu chan doan: kiem tra import tung module, cau truc CSDL, menu, mang.
Chi in chu khong dau de khong loi font tren Command Prompt.
Tac gia: TDA - 0986509106
"""
import os
import sys
import json
import sqlite3
import traceback
import datetime

THU_MUC = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, THU_MUC)

MODULE = [
    "kho", "tt91", "xml_parser", "invoice_render", "qr_mini", "importer",
    "exporter", "invoice_view", "man_hinh_phu", "doi_chieu", "bao_cao",
    "bao_cao_chi_tiet", "theo_doi", "hop_thu", "mst_tra_cuu", "canh_bao",
    "trang_chu_pro", "man_hinh_ncc", "man_hinh_moi", "app",
]

BAO_CAO = []


def ghi(dong=""):
    print(dong)
    BAO_CAO.append(dong)


def thu_import(ten):
    try:
        __import__(ten)
        ghi("[ok]   %s" % ten)
        return True
    except Exception:
        ghi("[LOI]  %s" % ten)
        for d in traceback.format_exc().splitlines():
            ghi("       " + d)
        return False


def kiem_tra_db():
    duong = os.path.join(THU_MUC, "data", "taxinvoice.db")
    try:
        import mst_tra_cuu
        duong = mst_tra_cuu.duong_dan_db()
    except Exception:
        pass
    ghi("")
    ghi("CSDL: %s" % duong)
    if not os.path.exists(duong):
        ghi("[LOI]  Khong tim thay tep CSDL.")
        return
    try:
        conn = sqlite3.connect(duong)
        bang = [r[0] for r in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")]
        ghi("Cac bang: %s" % ", ".join(bang))
        for b in ("hoa_don", "invoices"):
            if b in bang:
                n = conn.execute("SELECT COUNT(*) FROM %s" % b).fetchone()[0]
                cot = [r[1] for r in conn.execute("PRAGMA table_info(%s)" % b)]
                ghi("  %s: %d dong" % (b, n))
                ghi("  cot: %s" % ", ".join(cot))
        conn.close()
    except Exception:
        ghi("[LOI]  Doc CSDL that bai")
        for d in traceback.format_exc().splitlines():
            ghi("       " + d)


def kiem_tra_menu():
    ghi("")
    try:
        import kho
        ds = getattr(kho, "MENU_TRAI", None)
        ghi("MENU_TRAI (%d muc): %s" % (len(ds or []), ds))
    except Exception:
        ghi("[LOI]  Khong doc duoc kho.MENU_TRAI")


def kiem_tra_app():
    ghi("")
    try:
        import app
        lop = getattr(app, "UngDung", None)
        ghi("app.UngDung: %s" % ("co" if lop else "KHONG CO"))
        ghi("app.UngDung.hien_man_hinh: %s" %
            ("co" if hasattr(lop, "hien_man_hinh") else "KHONG CO"))
    except Exception:
        ghi("[LOI]  Khong nap duoc app.py")


def kiem_tra_mang():
    ghi("")
    ghi("Thu goi API tra cuu MST (chi gui ma so thue):")
    try:
        import urllib.request
        req = urllib.request.Request(
            "https://api.vietqr.io/v2/business/0314434449",
            headers={"User-Agent": "TaxInvoicePro/1.6", "Accept": "application/json"})
        with urllib.request.urlopen(req, timeout=12) as r:
            js = json.loads(r.read().decode("utf-8", "replace"))
        d = js.get("data") or {}
        ghi("[ok]   code=%s status=%s" % (js.get("code"), d.get("status")))
    except Exception as e:
        ghi("[LOI]  %s" % e)
        ghi("       May khong ra duoc Internet hoac bi tuong lua chan.")


def main():
    ghi("=== TAX INVOICE PRO - CHAN DOAN ===")
    ghi("Thoi diem : %s" % datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S"))
    ghi("Python    : %s" % sys.version.replace("\n", " "))
    ghi("Thu muc   : %s" % THU_MUC)
    ghi("")
    ghi("--- Kiem tra nap module ---")
    hong = [t for t in MODULE
            if os.path.exists(os.path.join(THU_MUC, t + ".py")) and not thu_import(t)]
    thieu = [t for t in MODULE if not os.path.exists(os.path.join(THU_MUC, t + ".py"))]
    if thieu:
        ghi("")
        ghi("Chua co tep: %s" % ", ".join(thieu))
    kiem_tra_menu()
    kiem_tra_app()
    kiem_tra_db()
    if "--mang" in sys.argv:
        kiem_tra_mang()
    ghi("")
    if hong:
        ghi("KET LUAN: %d module bi loi -> %s" % (len(hong), ", ".join(hong)))
        ghi("Hay gui phan [LOI] o tren de duoc sua.")
    else:
        ghi("KET LUAN: tat ca module hien co deu nap duoc.")
    try:
        os.makedirs(os.path.join(THU_MUC, "logs"), exist_ok=True)
        with open(os.path.join(THU_MUC, "logs", "chan_doan.txt"), "w",
                  encoding="utf-8") as f:
            f.write("\n".join(BAO_CAO))
        ghi("Da luu bao cao: logs\\chan_doan.txt")
    except Exception:
        pass


if __name__ == "__main__":
    main()
