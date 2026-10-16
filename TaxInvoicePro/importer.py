# -*- coding: utf-8 -*-
"""
importer.py - TAX INVOICE PRO v1.2.0
Nap hoa don tu tep XML roi, thu muc, hoac goi ZIP tai ve tu Cong Thue.
KHONG ket noi may chu nao; chi doc tep da co san tren may.
Tac gia: TDA - 0986509106
"""

import os
import re
import shutil
import tempfile
import zipfile
from datetime import datetime

import kho
import xml_parser

log = kho.log
PHAN_MO_RONG = (".xml",)


# ----------------------------------------------------------------------
def _bao_cao(nguon, duong_dan=""):
    return {"nguon": nguon, "duong_dan": duong_dan, "tong_tep": 0,
            "hoa_don": 0, "them": 0, "trung": 0, "loi": 0,
            "tep_loi": [], "chi_tiet": [], "khoa_moi": []}


def _ds_xml(thu_muc, de_quy):
    ds = []
    if de_quy:
        for goc, _tm, tep in os.walk(thu_muc):
            for t in tep:
                if t.lower().endswith(PHAN_MO_RONG):
                    ds.append(os.path.join(goc, t))
    else:
        try:
            for t in sorted(os.listdir(thu_muc)):
                d = os.path.join(thu_muc, t)
                if os.path.isfile(d) and t.lower().endswith(PHAN_MO_RONG):
                    ds.append(d)
        except OSError as e:
            log.error("Không đọc được thư mục %s: %s", thu_muc, e)
    return sorted(ds)


def _ten_luu(inv):
    kh = re.sub(r"[^0-9A-Za-z]", "",
                (inv.get("ky_hieu_day_du") or inv.get("ky_hieu_hoa_don") or "HD"))
    so = re.sub(r"[^0-9A-Za-z]", "", str(inv.get("so_hoa_don") or "0"))
    return "HoaDon_%s_%s.xml" % (kh, so)


def chep_vao_kho(inv, goc_xml):
    """Chep tep XML vao thu muc luu tru: <kho>\\<MST ban>\\<nam>\\<ten>.xml"""
    ch = kho.doc_cau_hinh()
    if not ch.get("tu_chep_xml", True):
        return goc_xml
    goc = ch.get("thu_muc_luu_tru") or ""
    if not goc or not goc_xml or not os.path.isfile(goc_xml):
        return goc_xml
    nam = (inv.get("ngay_lap") or "")[:4] or "KhongRoNam"
    thu_muc = os.path.join(goc, inv.get("mst_nguoi_ban") or "KhongRoMST", nam)
    try:
        os.makedirs(thu_muc, exist_ok=True)
    except OSError as e:
        log.warning("Không tạo được thư mục lưu trữ %s: %s", thu_muc, e)
        return goc_xml
    dich = os.path.join(thu_muc, _ten_luu(inv))
    try:
        if os.path.abspath(dich) == os.path.abspath(goc_xml):
            return dich
        if os.path.exists(dich):
            try:
                if os.path.getsize(dich) == os.path.getsize(goc_xml):
                    return dich
            except OSError:
                pass
            t, d = os.path.splitext(dich)
            i = 1
            while os.path.exists(dich):
                dich = "%s_%d%s" % (t, i, d)
                i += 1
        shutil.copy2(goc_xml, dich)
        return dich
    except (OSError, shutil.Error) as e:
        log.warning("Không chép được %s: %s", goc_xml, e)
        return goc_xml


# ----------------------------------------------------------------------
def nap_tep(duong_dan, bc, ghi_de=False):
    """Nap mot tep XML (co the chua nhieu the <HDon>) vao kho."""
    ten = os.path.basename(duong_dan)
    bc["tong_tep"] += 1
    try:
        ds = xml_parser.doc_nhieu_tu_file(duong_dan)
    except Exception as e:                      # noqa: BLE001 - gom moi loi doc
        bc["loi"] += 1
        bc["tep_loi"].append(ten)
        bc["chi_tiet"].append("LỖI  %s — %s" % (ten, e))
        log.error("Lỗi đọc %s: %s", duong_dan, e)
        return
    for inv in ds:
        bc["hoa_don"] += 1
        inv["duong_dan_xml"] = chep_vao_kho(inv, duong_dan)
        inv["ten_tep"] = os.path.basename(inv["duong_dan_xml"])
        inv["da_tai"] = 1
        inv["nguon"] = bc["nguon"]
        inv["ngay_nap"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        kq = kho.them_hoa_don(inv, ghi_de=ghi_de, luu_ngay=False)
        mo_ta = "%s  số %s  ngày %s  %s" % (
            inv.get("ky_hieu_day_du"), inv.get("so_hoa_don"),
            kho.fmt_ngay(inv.get("ngay_lap")),
            kho.fmt_tien(inv.get("tong_tien")))
        if kq == "trung":
            bc["trung"] += 1
            bc["chi_tiet"].append("TRÙNG  " + mo_ta)
        else:
            bc["them"] += 1
            bc["khoa_moi"].append(inv.get("khoa") or kho.khoa_trung(inv))
            bc["chi_tiet"].append(
                ("CẬP NHẬT  " if kq == "cap_nhat" else "THÊM  ") + mo_ta)
            if inv.get("canh_bao"):
                bc["chi_tiet"].append("        ⚠ " + inv["canh_bao"][0])


def nap_danh_sach_tep(ds_tep, nguon="Tệp XML", ghi_de=False, duong_dan=""):
    bc = _bao_cao(nguon, duong_dan)
    for t in ds_tep:
        nap_tep(t, bc, ghi_de)
    kho.ket_noi().commit()
    kho.ghi_nhat_ky_nap(bc)
    log.info("Nạp %s: %d tệp, thêm %d, trùng %d, lỗi %d.",
             nguon, bc["tong_tep"], bc["them"], bc["trung"], bc["loi"])
    return bc


def nap_thu_muc(thu_muc, de_quy=False, ghi_de=False):
    nguon = "Thư mục XML (gồm thư mục con)" if de_quy else "Thư mục XML"
    ds = _ds_xml(thu_muc, de_quy)
    bc = nap_danh_sach_tep(ds, nguon, ghi_de, thu_muc)
    if not ds:
        bc["chi_tiet"].append("Không tìm thấy tệp .xml nào trong thư mục này.")
    return bc


def nap_zip(duong_dan_zip, ghi_de=False):
    """Giai nen goi ZIP tai tu Cong Thue vao thu muc tam roi nap."""
    bc = _bao_cao("Gói ZIP từ Cổng Thuế", duong_dan_zip)
    tam = tempfile.mkdtemp(prefix="taxinvoicepro_")
    try:
        try:
            _giai_nen(duong_dan_zip, tam, 0)
        except (zipfile.BadZipFile, OSError) as e:
            bc["loi"] += 1
            bc["chi_tiet"].append("Không mở được gói nén: %s" % e)
            kho.ghi_nhat_ky_nap(bc)
            return bc
        for t in _ds_xml(tam, True):
            nap_tep(t, bc, ghi_de)
        kho.ket_noi().commit()
        if bc["tong_tep"] == 0:
            bc["chi_tiet"].append("Gói nén không chứa tệp .xml nào.")
    finally:
        shutil.rmtree(tam, ignore_errors=True)
    kho.ghi_nhat_ky_nap(bc)
    log.info("Nạp ZIP %s: %d tệp, thêm %d, trùng %d, lỗi %d.",
             duong_dan_zip, bc["tong_tep"], bc["them"], bc["trung"], bc["loi"])
    return bc


def _giai_nen(duong_dan_zip, dich, muc):
    if muc > 3:
        return
    with zipfile.ZipFile(duong_dan_zip) as z:
        z.extractall(dich)
    for goc, _tm, tep in os.walk(dich):
        for t in tep:
            if t.lower().endswith(".zip"):
                con = os.path.join(goc, t)
                thu_muc_con = os.path.join(goc, os.path.splitext(t)[0] + "_giainen")
                try:
                    os.makedirs(thu_muc_con, exist_ok=True)
                    _giai_nen(con, thu_muc_con, muc + 1)
                except (zipfile.BadZipFile, OSError):
                    continue


def nap_nhieu_nguon(ds_duong_dan, ghi_de=False):
    """Nhan lan lon tep xml, tep zip va thu muc."""
    bc = _bao_cao("Nhiều nguồn")
    for d in ds_duong_dan:
        if os.path.isdir(d):
            con = nap_thu_muc(d, True, ghi_de)
        elif d.lower().endswith(".zip"):
            con = nap_zip(d, ghi_de)
        elif d.lower().endswith(".xml"):
            con = nap_danh_sach_tep([d], "Tệp XML", ghi_de, d)
        else:
            continue
        for k in ("tong_tep", "hoa_don", "them", "trung", "loi"):
            bc[k] += con[k]
        bc["chi_tiet"] += con["chi_tiet"]
        bc["tep_loi"] += con["tep_loi"]
        bc["khoa_moi"] += con["khoa_moi"]
    return bc


def tom_tat(bc):
    d = [
        "Nguồn nạp      : %s" % bc.get("nguon", ""),
        "Đường dẫn      : %s" % (bc.get("duong_dan") or "(nhiều nguồn)"),
        "Số tệp đã đọc  : %d" % bc.get("tong_tep", 0),
        "Số hóa đơn đọc : %d" % bc.get("hoa_don", 0),
        "Thêm mới       : %d" % bc.get("them", 0),
        "Bỏ qua do trùng: %d" % bc.get("trung", 0),
        "Tệp lỗi        : %d" % bc.get("loi", 0),
    ]
    return "\n".join(d)
