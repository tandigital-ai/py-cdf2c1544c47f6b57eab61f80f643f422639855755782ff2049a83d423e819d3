# -*- coding: utf-8 -*-
"""
dong_goi.py - TAX INVOICE PRO v1.5.0 - Giai doan 7
Dong goi ung dung thanh tep .exe bang PyInstaller, kem icon tu sinh.
Chay:  python dong_goi.py            (mot thu muc - khuyen dung, chay nhanh)
       python dong_goi.py --onefile  (mot tep .exe duy nhat)
Tac gia: TDA - 0986509106
"""
import os
import sys
import shutil
import struct
import subprocess

GOC = os.path.dirname(os.path.abspath(__file__))
TEN = "TaxInvoicePro"
ICON = os.path.join(GOC, "taxinvoicepro.ico")


def tao_icon(duong_dan=ICON, n=64):
    """Sinh tep .ico 64x64: nen xanh bo tron, hinh thoi trang o giua."""
    xanh = (0xC0, 0x65, 0x15, 255)      # BGRA cua #1565C0
    trang = (255, 255, 255, 255)
    trong = (0, 0, 0, 0)
    r, cx, cy = 12, (n - 1) / 2.0, (n - 1) / 2.0
    hang = []
    for y in range(n):
        d = []
        for x in range(n):
            gx = min(x, n - 1 - x)
            gy = min(y, n - 1 - y)
            if gx < r and gy < r and ((r - gx) ** 2 + (r - gy) ** 2) > r * r:
                d.append(trong)
                continue
            if abs(x - cx) / 17.0 + abs(y - cy) / 20.0 <= 1.0:
                d.append(trang)
            else:
                d.append(xanh)
        hang.append(d)
    xor = b"".join(bytes(bytearray(
        [c for px in hang[y] for c in px])) for y in range(n - 1, -1, -1))
    rong_mask = ((n + 31) // 32) * 4
    mask = b"\x00" * rong_mask * n
    bmp = struct.pack("<IiiHHIIiiII", 40, n, n * 2, 1, 32, 0,
                      len(xor) + len(mask), 0, 0, 0, 0)
    du_lieu = bmp + xor + mask
    ico = (struct.pack("<HHH", 0, 1, 1)
           + struct.pack("<BBBBHHII", n % 256, n % 256, 0, 0, 1, 32,
                         len(du_lieu), 22) + du_lieu)
    with open(duong_dan, "wb") as f:
        f.write(ico)
    return duong_dan


def co_pyinstaller():
    try:
        import PyInstaller  # noqa: F401
        return True
    except Exception:
        return False


def cai_pyinstaller():
    print("Đang cài PyInstaller (cần mạng một lần)…")
    return subprocess.call([sys.executable, "-m", "pip", "install",
                            "--upgrade", "pyinstaller"]) == 0


def chep_du_lieu(dich):
    for ten in ("data", "config.json"):
        n = os.path.join(GOC, ten)
        d = os.path.join(dich, ten)
        if not os.path.exists(n) or os.path.exists(d):
            continue
        try:
            if os.path.isdir(n):
                shutil.copytree(n, d)
            else:
                shutil.copy2(n, d)
            print("  đã chép %s" % ten)
        except Exception as e:
            print("  không chép được %s: %s" % (ten, e))


def main():
    os.chdir(GOC)
    mot_tep = "--onefile" in sys.argv
    print("=" * 64)
    print(" ĐÓNG GÓI TAX INVOICE PRO v1.5.0 — tác giả TDA 0986509106")
    print(" Python: %s" % sys.version.split()[0])
    print(" Kiểu: %s" % ("một tệp .exe" if mot_tep else "một thư mục"))
    print("=" * 64)

    if not os.path.exists(os.path.join(GOC, "khoi_dong.py")):
        print("Thiếu khoi_dong.py — hãy chạy lệnh này trong thư mục dự án.")
        return
    if not co_pyinstaller() and not cai_pyinstaller():
        print("Không cài được PyInstaller. Hãy chạy: pip install pyinstaller")
        return

    print("Đang tạo biểu tượng…")
    tao_icon()

    lenh = [sys.executable, "-m", "PyInstaller", "--noconfirm", "--clean",
            "--name", TEN, "--windowed", "--icon", ICON,
            "--collect-all", "customtkinter",
            "--hidden-import", "openpyxl",
            "--hidden-import", "imaplib",
            "--hidden-import", "email",
            "--hidden-import", "sqlite3"]
    for m in ("kho", "app", "man_hinh_phu", "man_hinh_moi", "doi_chieu",
              "bao_cao", "bao_cao_chi_tiet", "theo_doi", "hop_thu",
              "importer", "exporter", "invoice_view", "invoice_render",
              "xml_parser", "qr_mini", "tt91", "sample_data", "va_ttk"):
        if os.path.exists(os.path.join(GOC, m + ".py")):
            lenh += ["--hidden-import", m]
    lenh += ["--onefile"] if mot_tep else ["--onedir"]
    lenh += ["khoi_dong.py"]

    print("Đang đóng gói, bước này mất vài phút…\n")
    ma = subprocess.call(lenh)
    if ma != 0:
        print("\nĐóng gói thất bại (mã %d). Xem thông báo lỗi phía trên." % ma)
        return

    dich = os.path.join(GOC, "dist", TEN if not mot_tep else "")
    exe = (os.path.join(GOC, "dist", TEN + ".exe") if mot_tep
           else os.path.join(dich, TEN + ".exe"))
    print("\nĐã tạo: %s" % exe)
    if not mot_tep:
        print("Đang chép dữ liệu hiện có sang thư mục cài đặt…")
        chep_du_lieu(dich)
    else:
        print("Lưu ý: bản một tệp sẽ tạo thư mục data cạnh tệp .exe khi "
              "chạy lần đầu.")
    print("\nXong. Chép cả thư mục dist\\%s sang máy khác là chạy được, "
          "không cần cài Python." % TEN)


if __name__ == "__main__":
    main()
