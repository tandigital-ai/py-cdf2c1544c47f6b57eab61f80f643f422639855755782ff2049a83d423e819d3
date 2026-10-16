# -*- coding: utf-8 -*-
"""
kiem_tra_xml.py - TAX INVOICE PRO
Cong cu kiem tra nhanh bo doc XML voi hoa don that, chay doc lap voi giao dien.

Cach dung (trong cua so Command Prompt da bat moi truong ao):
    python kiem_tra_xml.py "D:\\HoaDon_TCT"            -> quet ca thu muc
    python kiem_tra_xml.py "D:\\HoaDon_TCT\\abc.xml"   -> doc mot tep
    python kiem_tra_xml.py "D:\\HoaDon_TCT" --html     -> xuat them ban the hien HTML
Tac gia: TDA - 0986509106
"""

import os
import sys

import invoice_render
import xml_parser


def _ds_tep(duong_dan):
    if os.path.isfile(duong_dan):
        return [duong_dan]
    ds = []
    for goc, _thu_muc, tep in os.walk(duong_dan):
        for t in tep:
            if t.lower().endswith(".xml"):
                ds.append(os.path.join(goc, t))
    return sorted(ds)


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return 1
    muc_tieu = sys.argv[1]
    xuat_html = "--html" in sys.argv
    if not os.path.exists(muc_tieu):
        print("Không tìm thấy: %s" % muc_tieu)
        return 1

    tep = _ds_tep(muc_tieu)
    if not tep:
        print("Không có tệp .xml nào trong: %s" % muc_tieu)
        return 1

    thu_muc_html = os.path.join(os.getcwd(), "ban_the_hien")
    tong, ok, loi, canh_bao = 0, 0, 0, 0
    print("=" * 78)
    print("KIỂM TRA BỘ ĐỌC XML — %d tệp" % len(tep))
    print("Chuẩn: %s" % __import__("tt91").VAN_BAN_AP_DUNG)
    print("=" * 78)

    for t in tep:
        try:
            ds = xml_parser.doc_nhieu_tu_file(t)
        except Exception as e:
            loi += 1
            print("\n[LỖI] %s\n       %s" % (os.path.basename(t), e))
            continue
        for inv in ds:
            tong += 1
            ok += 1
            gm = inv.get("giai_ma_ky_hieu", {})
            print("\n[%d] %s" % (tong, os.path.basename(t)))
            print("    Ký hiệu       : %s   (%s)"
                  % (inv["ky_hieu_day_du"], gm.get("mo_ta", "")))
            print("    Số / Ngày lập : %s   %s"
                  % (inv["so_hoa_don"], invoice_render.fmt_ngay(inv["ngay_lap"])))
            print("    Người bán     : %s — MST %s"
                  % (inv["ten_nguoi_ban"], inv["mst_nguoi_ban"]))
            print("    Người mua     : %s — MST %s"
                  % (inv["ten_nguoi_mua"] or "(không có)",
                     inv["mst_nguoi_mua"] or "(không có)"))
            print("    Tiền hàng     : %15s" % invoice_render.fmt_tien(inv["tien_hang"]))
            print("    Thuế GTGT     : %15s" % invoice_render.fmt_tien(inv["thue_gtgt"]))
            print("    Tổng thanh toán:%15s %s"
                  % (invoice_render.fmt_tien(inv["tong_tien"]), inv["don_vi_tien_te"]))
            print("    Số dòng hàng  : %d | Mã CQT: %s | QR: %s | Chữ ký: %d"
                  % (len(inv["dong_hang"]), inv["ma_cqt"] or "(không)",
                     "có" if inv["ma_qr"] else "không", len(inv["chu_ky"])))
            if inv["canh_bao"]:
                canh_bao += 1
                for c in inv["canh_bao"]:
                    print("    * Cảnh báo   : %s" % c)
            else:
                print("    * Số liệu khớp, không có cảnh báo.")
            if xuat_html:
                d = invoice_render.luu_html(inv, thu_muc_html)
                print("    -> Bản thể hiện: %s" % d)

    print("\n" + "=" * 78)
    print("KẾT QUẢ: đọc được %d hóa đơn, %d tệp lỗi, %d hóa đơn có cảnh báo."
          % (ok, loi, canh_bao))
    if xuat_html:
        print("Bản thể hiện HTML lưu tại: %s" % thu_muc_html)
    print("TAX INVOICE PRO — Tác giả TDA — 0986509106")
    print("=" * 78)
    return 0


if __name__ == "__main__":
    sys.exit(main())
