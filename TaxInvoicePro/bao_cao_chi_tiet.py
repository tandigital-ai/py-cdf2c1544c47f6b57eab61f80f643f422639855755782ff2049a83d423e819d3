# -*- coding: utf-8 -*-
"""
bao_cao_chi_tiet.py - TAX INVOICE PRO v1.4.0
Ket xuat chi tiet tung mat hang (bang phang, khong o trong),
Bang ke mua vao / ban ra phuc vu ke khai thue GTGT, va cac bang thong ke.
Tac gia: TDA - 0986509106
"""
import os
import re
import csv
import datetime

import doi_chieu as dc

TRONG_CHU = "KHÔNG CÓ"
TRONG_TS = "KHÔNG GHI"

# nhan thue suat chuan hoa -> (nhan hien thi, ty le thap phan hoac None)
BANG_TS = [
    (("0%", "0", "0.0", "thue suat 0"), ("0%", 0.0)),
    (("5%", "5", "0.05"), ("5%", 0.05)),
    (("8%", "8", "0.08"), ("8%", 0.08)),
    (("10%", "10", "0.1"), ("10%", 0.10)),
    (("kct", "khong chiu thue", "kcts"), ("KCT - không chịu thuế", None)),
    (("kkknt", "khong ke khai nop thue", "kkkn"),
     ("KKKNT - không kê khai nộp thuế", None)),
    (("khac", "khac:", "k"), ("KHÁC", None)),
]

COT_CHI_TIET = [
    ("ky", "Kỳ (yyyy-mm)", 12), ("nam", "Năm", 7), ("thang", "Tháng", 8),
    ("ngay_lap", "Ngày lập", 12), ("ngay_iso", "Ngày (yyyy-mm-dd)", 15),
    ("loai_gd", "Loại giao dịch", 14), ("mau_so", "Mẫu số", 8),
    ("ky_hieu", "Ký hiệu", 11), ("so_hd", "Số hóa đơn", 12),
    ("mst_ban", "MST người bán", 15), ("ten_ban", "Tên người bán", 40),
    ("mst_mua", "MST người mua", 15), ("ten_mua", "Tên người mua", 34),
    ("trang_thai", "Trạng thái HĐ", 13), ("loai_hd", "Loại hóa đơn", 18),
    ("stt_dong", "STT dòng", 9), ("ten_hang", "Tên hàng hóa, dịch vụ", 46),
    ("nhom_hang", "Nhóm hàng (chuẩn hóa)", 34), ("dvt", "ĐVT", 10),
    ("so_luong", "Số lượng", 12), ("don_gia", "Đơn giá", 15),
    ("thanh_tien", "Thành tiền chưa thuế", 18),
    ("ts_nhan", "Thuế suất", 24), ("ts_ty_le", "Tỷ lệ thuế", 11),
    ("tien_thue_dong", "Tiền thuế dòng", 16),
    ("tong_dong", "Tổng dòng có thuế", 18),
    ("tien_hang_hd", "Tiền hàng cả HĐ", 17),
    ("thue_hd", "Thuế GTGT cả HĐ", 17), ("tong_hd", "Tổng thanh toán HĐ", 18),
    ("so_dong_hd", "Số dòng của HĐ", 14),
    ("nguon_dong", "Nguồn dòng hàng", 22),
    ("khop_tong", "Đối chiếu tổng", 26),
    ("tep_xml", "Tệp XML gốc", 52), ("khoa", "Khóa hóa đơn", 30),
]


# ------------------------------------------------------------- tien ich
def _chu(v, md=TRONG_CHU):
    s = str(v).strip() if v is not None else ""
    return s if s else md


def chuan_thue_suat(v):
    t = dc.khong_dau(v).replace(" ", "")
    if not t:
        return TRONG_TS, None
    for khoa, kq in BANG_TS:
        if t in khoa:
            return kq
    g = re.search(r"(\d+(?:[.,]\d+)?)", t)
    if g:
        n = float(g.group(1).replace(",", "."))
        if n > 1:
            n = n / 100.0
        return ("%g%%" % round(n * 100, 2)), round(n, 4)
    return "KHÁC", None


def ts_tu_hoa_don(hd):
    if hd["tien_hang"] > 0 and hd["thue_gtgt"] > 0:
        return chuan_thue_suat("%g" % round(hd["thue_gtgt"] * 100.0
                                            / hd["tien_hang"]))
    if hd["thue_gtgt"] == 0 and hd["tien_hang"] > 0:
        return "KCT / 0% (hóa đơn không ghi thuế)", 0.0
    return TRONG_TS, None


def nhom_hang(ten):
    s = dc.khong_dau(ten).upper()
    s = re.sub(r"[0-9]{3,}", " ", s)
    s = re.sub(r"[^A-Z0-9 ]", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return (s[:34] or "KHONG CO TEN")


def phan_loai(hd, mst_don_vi):
    mdv = re.sub(r"[^0-9]", "", str(mst_don_vi or ""))
    if not mdv:
        return "Mua vào"
    ban = re.sub(r"[^0-9]", "", hd["mst_nguoi_ban"])
    mua = re.sub(r"[^0-9]", "", hd["mst_nguoi_mua"])
    if ban.startswith(mdv) or mdv.startswith(ban) and ban:
        return "Bán ra"
    if mua.startswith(mdv) or (mua and mdv.startswith(mua)):
        return "Mua vào"
    return "Khác"


# -------------------------------------------------- bang phang chi tiet
def _dong_cua_hd(hd, dongs, mst_dv):
    loai_gd = phan_loai(hd, mst_dv)
    iso = hd["ngay_lap"] or ""
    chung = {
        "ky": iso[:7] or TRONG_CHU,
        "nam": int(iso[:4]) if iso[:4].isdigit() else 0,
        "thang": int(iso[5:7]) if iso[5:7].isdigit() else 0,
        "ngay_lap": dc.ngay_vn(iso) or TRONG_CHU, "ngay_iso": iso or TRONG_CHU,
        "loai_gd": loai_gd, "mau_so": _chu(hd["ky_hieu_mau_so"], "0"),
        "ky_hieu": _chu(hd["ky_hieu_hoa_don"]), "so_hd": _chu(hd["so_hoa_don"]),
        "mst_ban": _chu(hd["mst_nguoi_ban"]), "ten_ban": _chu(hd["ten_nguoi_ban"]),
        "mst_mua": _chu(hd["mst_nguoi_mua"]), "ten_mua": _chu(hd["ten_nguoi_mua"]),
        "trang_thai": _chu(hd["trang_thai"], "Hợp lệ"),
        "loai_hd": _chu(hd["loai_hoa_don"]),
        "tien_hang_hd": hd["tien_hang"], "thue_hd": hd["thue_gtgt"],
        "tong_hd": hd["tong_tien"], "tep_xml": _chu(hd["duong_dan_xml"]),
        "khoa": _chu(hd.get("khoa_chuan")),
    }

    tho = []
    for i, d in enumerate(dongs or [], 1):
        sl = dc.so(d.get("so_luong"))
        dg = dc.so(d.get("don_gia"))
        tt = dc.so(d.get("thanh_tien"))
        if tt == 0 and sl and dg:
            tt = sl * dg
        if tt and sl == 0:
            sl, dg = 1.0, tt
        if tt and sl and dg == 0:
            dg = tt / sl
        nhan, ty_le = chuan_thue_suat(d.get("thue_suat"))
        tho.append({"stt": d.get("stt") or i, "ten": _chu(d.get("ten"),
                                                          "HÀNG HÓA, DỊCH VỤ"),
                    "dvt": _chu(d.get("dvt"), "KHÔNG"), "sl": sl, "dg": dg,
                    "tt": tt, "nhan": nhan, "ty_le": ty_le,
                    "thue": dc.so(d.get("tien_thue")), "nguon": "XML chi tiết"})

    if not tho:
        nhan, ty_le = ts_tu_hoa_don(hd)
        tt = float(hd["tien_hang"] or hd["tong_tien"])
        tho = [{"stt": 1,
                "ten": "HÀNG HÓA, DỊCH VỤ THEO HÓA ĐƠN (không có chi tiết dòng)",
                "dvt": "KHÔNG", "sl": 1.0, "dg": tt, "tt": tt, "nhan": nhan,
                "ty_le": ty_le, "thue": float(hd["thue_gtgt"]),
                "nguon": "Suy từ tổng hóa đơn"}]

    tong_tt = sum(x["tt"] for x in tho)
    co_thue_dong = any(x["thue"] > 0 for x in tho)
    if not co_thue_dong and hd["thue_gtgt"] > 0 and tong_tt > 0:
        con = float(hd["thue_gtgt"])
        for x in tho[:-1]:
            p = round(hd["thue_gtgt"] * x["tt"] / tong_tt)
            x["thue"] = float(p)
            con -= p
        tho[-1]["thue"] = max(con, 0.0)
    elif not co_thue_dong:
        for x in tho:
            x["thue"] = round(x["tt"] * x["ty_le"]) if x["ty_le"] else 0.0

    lech = round(tong_tt) - hd["tien_hang"]
    khop = ("Khớp tổng hóa đơn" if abs(lech) <= 1
            else "Lệch %s đ so với tiền hàng HĐ" % dc.fmt_tien(lech))

    kq = []
    for x in tho:
        r = dict(chung)
        r.update({
            "stt_dong": x["stt"], "ten_hang": x["ten"],
            "nhom_hang": nhom_hang(x["ten"]), "dvt": x["dvt"],
            "so_luong": round(x["sl"], 4), "don_gia": round(x["dg"], 2),
            "thanh_tien": round(x["tt"], 2), "ts_nhan": x["nhan"],
            "ts_ty_le": x["ty_le"] if x["ty_le"] is not None else 0,
            "tien_thue_dong": round(x["thue"], 2),
            "tong_dong": round(x["tt"] + x["thue"], 2),
            "so_dong_hd": len(tho), "nguon_dong": x["nguon"],
            "khop_tong": khop})
        kq.append(r)
    return kq


def bang_phang(ds, mst_don_vi=""):
    bang_dong = dc.doc_dong_hang()
    out = []
    for hd in ds:
        out.extend(_dong_cua_hd(hd, dc.dong_cua(hd, bang_dong), mst_don_vi))
    return out


def xuat_csv(dong, duong_dan):
    with open(duong_dan, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f, delimiter=";")
        w.writerow([n for _, n, _ in COT_CHI_TIET])
        for r in dong:
            w.writerow([r.get(m, "") for m, _, _ in COT_CHI_TIET])
    return duong_dan


# ----------------------------------------------------------- Excel
def _kieu():
    from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
    return {
        "dam": Font(bold=True, color="FFFFFF"),
        "nen": PatternFill("solid", fgColor="1565C0"),
        "nen2": PatternFill("solid", fgColor="0D47A1"),
        "tong": PatternFill("solid", fgColor="E3F0FD"),
        "nhom": PatternFill("solid", fgColor="FFF3CD"),
        "vien": Border(*[Side(style="thin", color="B8C6D6")] * 4),
        "giua": Alignment(horizontal="center", vertical="center",
                          wrap_text=True),
        "bold": Font(bold=True),
    }


def _sheet(wb, ten, cot, dau=True):
    from openpyxl.utils import get_column_letter
    k = _kieu()
    ws = wb.create_sheet(ten) if wb.sheetnames != ["Sheet"] else wb.active
    ws.title = ten
    if dau:
        ws.append([n for _, n, _ in cot])
        for i, (_, _, w) in enumerate(cot, 1):
            o = ws.cell(row=1, column=i)
            o.font, o.fill, o.alignment, o.border = (k["dam"], k["nen"],
                                                     k["giua"], k["vien"])
            ws.column_dimensions[get_column_letter(i)].width = w
        ws.freeze_panes = "A2"
    try:
        ws.page_setup.orientation = "landscape"
        ws.page_setup.fitToWidth = 1
        ws.page_setup.fitToHeight = 0
        ws.sheet_properties.pageSetUpPr.fitToPage = True
        ws.print_title_rows = "1:1"
    except Exception:
        pass
    return ws


def _tong_dong(ws, cot_so, dong_dau, dong_cuoi, nhan_cot=1, nhan="TỔNG CỘNG"):
    from openpyxl.utils import get_column_letter
    k = _kieu()
    if dong_cuoi < dong_dau:
        return None
    r = dong_cuoi + 1
    o = ws.cell(row=r, column=nhan_cot, value=nhan)
    o.font, o.fill = k["bold"], k["tong"]
    for c in cot_so:
        L = get_column_letter(c)
        o = ws.cell(row=r, column=c,
                    value="=SUM(%s%d:%s%d)" % (L, dong_dau, L, dong_cuoi))
        o.number_format, o.font, o.fill = '#,##0', k["bold"], k["tong"]
    return r


def xuat_chi_tiet_day_du(ds, duong_dan, mst_don_vi="", tu_ngay=None,
                         den_ngay=None):
    """Tao tep Excel nhieu sheet: chi tiet mat hang + bang ke + thong ke."""
    from openpyxl import Workbook
    from openpyxl.styles import Font
    from openpyxl.utils import get_column_letter

    k = _kieu()
    dong = bang_phang(ds, mst_don_vi)
    wb = Workbook()

    # ---------- sheet 0: thong tin
    ws0 = _sheet(wb, "Thông tin", [], dau=False)
    ws0.column_dimensions["A"].width = 32
    ws0.column_dimensions["B"].width = 66
    mua = [r for r in dong if r["loai_gd"] == "Mua vào"]
    ban = [r for r in dong if r["loai_gd"] == "Bán ra"]
    tt = [("BÁO CÁO CHI TIẾT HÓA ĐƠN ĐIỆN TỬ", ""),
          ("Phần mềm", "TAX INVOICE PRO v1.4.0"),
          ("Tác giả", "TDA - 0986509106"),
          ("Ngày lập", datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")),
          ("Kỳ dữ liệu", "%s - %s" % (dc.ngay_vn(tu_ngay) or "đầu kỳ",
                                      dc.ngay_vn(den_ngay) or "cuối kỳ")),
          ("MST đơn vị kê khai", mst_don_vi or "(chưa khai báo)"),
          ("Số hóa đơn", len(ds)),
          ("Số dòng mặt hàng", len(dong)),
          ("Dòng mua vào", len(mua)), ("Dòng bán ra", len(ban)),
          ("Tổng tiền hàng mua vào", round(sum(r["thanh_tien"] for r in mua))),
          ("Tổng thuế GTGT mua vào", round(sum(r["tien_thue_dong"] for r in mua))),
          ("Tổng tiền hàng bán ra", round(sum(r["thanh_tien"] for r in ban))),
          ("Tổng thuế GTGT bán ra", round(sum(r["tien_thue_dong"] for r in ban))),
          ("Chuẩn dữ liệu",
           "Nghị định 254/2026/NĐ-CP và Thông tư 91/2026/TT-BTC"),
          ("Quy ước điền dữ liệu",
           "Mọi ô đều có giá trị: chữ thiếu ghi 'KHÔNG CÓ', thuế suất thiếu "
           "ghi 'KHÔNG GHI', số thiếu ghi 0."),
          ("Lưu ý", "Số liệu dùng để đối chiếu nội bộ. Tệp XML là bản gốc có "
                    "giá trị pháp lý. Người lập tờ khai tự chịu trách nhiệm "
                    "về số liệu kê khai.")]
    for a, b in tt:
        ws0.append([a, b])
    ws0["A1"].font = Font(bold=True, size=15, color="1565C0")
    for r in range(2, len(tt) + 1):
        ws0.cell(row=r, column=1).font = k["bold"]
    for r in range(11, 15):
        ws0.cell(row=r, column=2).number_format = '#,##0'

    # ---------- sheet 1: chi tiet mat hang (bang phang)
    ws = _sheet(wb, "Chi tiết mặt hàng", COT_CHI_TIET)
    for r in dong:
        ws.append([r.get(m, "") for m, _, _ in COT_CHI_TIET])
    n = len(dong)
    chi_so = {m: i for i, (m, _, _) in enumerate(COT_CHI_TIET, 1)}
    for r in range(2, n + 2):
        for m in ("don_gia", "thanh_tien", "tien_thue_dong", "tong_dong",
                  "tien_hang_hd", "thue_hd", "tong_hd"):
            ws.cell(row=r, column=chi_so[m]).number_format = '#,##0'
        ws.cell(row=r, column=chi_so["so_luong"]).number_format = '#,##0.###'
        ws.cell(row=r, column=chi_so["ts_ty_le"]).number_format = '0.00%'
    if n:
        _tong_dong(ws, [chi_so[m] for m in ("thanh_tien", "tien_thue_dong",
                                            "tong_dong")], 2, n + 1,
                   chi_so["ten_hang"])
        ws.auto_filter.ref = "A1:%s%d" % (
            get_column_letter(len(COT_CHI_TIET)), n + 1)

    # ---------- sheet 2 & 3: bang ke mua vao / ban ra
    _bang_ke(wb, "Bảng kê mua vào", mua, "Tên người bán", "ten_ban",
             "mst_ban",
             "GIÁ TRỊ HÀNG HÓA, DỊCH VỤ MUA VÀO VÀ THUẾ GTGT ĐẦU VÀO")
    _bang_ke(wb, "Bảng kê bán ra", ban, "Tên người mua", "ten_mua", "mst_mua",
             "DOANH THU BÁN HÀNG HÓA, DỊCH VỤ VÀ THUẾ GTGT ĐẦU RA")

    # ---------- sheet 4: thong ke theo thang
    _thong_ke_thang(wb, dong)
    # ---------- sheet 5: theo doi tac
    _thong_ke_doi_tac(wb, dong)
    # ---------- sheet 6: theo mat hang
    _thong_ke_mat_hang(wb, dong)
    # ---------- sheet 7: theo thue suat
    _thong_ke_thue_suat(wb, dong)
    # ---------- sheet 8: tong hop ke khai
    _tong_hop_ke_khai(wb, mua, ban)

    thu_muc = os.path.dirname(os.path.abspath(duong_dan))
    if thu_muc and not os.path.isdir(thu_muc):
        os.makedirs(thu_muc, exist_ok=True)
    wb.save(duong_dan)
    return {"tep": duong_dan, "so_hoa_don": len(ds), "so_dong": len(dong),
            "mua": len(mua), "ban": len(ban)}


def _bang_ke(wb, ten_sheet, dong, nhan_dt, khoa_ten, khoa_mst, tieu_de_lon):
    """Bang ke theo mau ke khai: nhom theo thue suat, co dong tong tung nhom."""
    k = _kieu()
    cot = [("stt", "STT", 6), ("so_hd", "Số hóa đơn", 13),
           ("ngay_lap", "Ngày, tháng, năm lập", 18),
           ("ky_hieu", "Ký hiệu HĐ", 12), ("mau_so", "Mẫu số", 8),
           ("ten", nhan_dt, 44), ("mst", "Mã số thuế", 16),
           ("gia_tri", "Giá trị chưa thuế GTGT", 20),
           ("thue", "Thuế GTGT", 17), ("tong", "Tổng thanh toán", 18),
           ("ts", "Thuế suất", 22), ("ghi", "Ghi chú", 30)]
    ws = _sheet(wb, ten_sheet, cot)

    # gop ve muc hoa don + thue suat (mot hoa don co the co nhieu thue suat)
    gop = {}
    for r in dong:
        key = (r["khoa"], r["ts_nhan"])
        g = gop.setdefault(key, dict(r))
        if g is not r:
            g["thanh_tien"] = g.get("thanh_tien", 0)
        gop[key] = g
    tong_hop = {}
    for r in dong:
        key = (r["ts_nhan"], r["khoa"])
        g = tong_hop.setdefault(key, {"r": r, "tt": 0.0, "thue": 0.0})
        g["tt"] += r["thanh_tien"]
        g["thue"] += r["tien_thue_dong"]

    thu_tu = sorted({ts for ts, _ in tong_hop},
                    key=lambda x: (x.startswith("KHÔNG"), x))
    stt = 0
    cot_so = [8, 9, 10]
    for ts in thu_tu:
        ws.append(["", "", "", "", "", "NHÓM THUẾ SUẤT: %s" % ts, "", "", "",
                   "", "", ""])
        r_nhom = ws.max_row
        for c in range(1, len(cot) + 1):
            ws.cell(row=r_nhom, column=c).fill = k["nhom"]
        ws.cell(row=r_nhom, column=6).font = k["bold"]
        dau = ws.max_row + 1
        muc = [v for (t, _), v in tong_hop.items() if t == ts]
        muc.sort(key=lambda x: (x["r"]["ngay_iso"], x["r"]["so_hd"]))
        for v in muc:
            stt += 1
            r = v["r"]
            ws.append([stt, r["so_hd"], r["ngay_lap"], r["ky_hieu"],
                       r["mau_so"], r[khoa_ten], r[khoa_mst],
                       round(v["tt"]), round(v["thue"]),
                       round(v["tt"] + v["thue"]), ts,
                       "%s - %s" % (r["trang_thai"], r["nguon_dong"])])
        cuoi = ws.max_row
        for rr in range(dau, cuoi + 1):
            for c in cot_so:
                ws.cell(row=rr, column=c).number_format = '#,##0'
        _tong_dong(ws, cot_so, dau, cuoi, 6, "Cộng nhóm %s" % ts)
    if ws.max_row > 1:
        ws.append([])
        r = ws.max_row + 1
        ws.cell(row=r, column=6, value="TỔNG CỘNG TOÀN BẢNG KÊ").font = k["bold"]
        for c, m in zip(cot_so, ("tt", "thue", "tong")):
            v = sum(g["tt"] for g in tong_hop.values()) if m == "tt" else (
                sum(g["thue"] for g in tong_hop.values()) if m == "thue" else
                sum(g["tt"] + g["thue"] for g in tong_hop.values()))
            o = ws.cell(row=r, column=c, value=round(v))
            o.number_format, o.font, o.fill = '#,##0', k["bold"], k["tong"]
    else:
        ws.append(["", "", "", "", "", "Không có dữ liệu cho bảng kê này.",
                   "", 0, 0, 0, "", ""])
    ws.insert_rows(1)
    ws["A1"] = tieu_de_lon
    ws["A1"].font = Font_bold_blue()
    return ws


def Font_bold_blue():
    from openpyxl.styles import Font
    return Font(bold=True, size=13, color="0D47A1")


def _thong_ke_thang(wb, dong):
    k = _kieu()
    cot = [("ky", "Kỳ (tháng)", 14), ("loai", "Loại giao dịch", 15),
           ("shd", "Số hóa đơn", 12), ("sdong", "Số dòng hàng", 13),
           ("tt", "Tiền hàng", 18), ("thue", "Thuế GTGT", 17),
           ("tong", "Tổng thanh toán", 18)]
    ws = _sheet(wb, "Thống kê theo tháng", cot)
    g = {}
    for r in dong:
        key = (r["ky"], r["loai_gd"])
        d = g.setdefault(key, {"hd": set(), "n": 0, "tt": 0.0, "thue": 0.0})
        d["hd"].add(r["khoa"])
        d["n"] += 1
        d["tt"] += r["thanh_tien"]
        d["thue"] += r["tien_thue_dong"]
    for (ky, loai), d in sorted(g.items()):
        ws.append([ky, loai, len(d["hd"]), d["n"], round(d["tt"]),
                   round(d["thue"]), round(d["tt"] + d["thue"])])
    n = ws.max_row
    for r in range(2, n + 1):
        for c in (5, 6, 7):
            ws.cell(row=r, column=c).number_format = '#,##0'
    _tong_dong(ws, [3, 4, 5, 6, 7], 2, n, 1)
    return ws


def _thong_ke_doi_tac(wb, dong):
    cot = [("stt", "STT", 6), ("loai", "Loại", 12), ("mst", "Mã số thuế", 16),
           ("ten", "Tên đối tác", 46), ("shd", "Số hóa đơn", 12),
           ("sdong", "Số dòng hàng", 13), ("tt", "Tiền hàng", 18),
           ("thue", "Thuế GTGT", 17), ("tong", "Tổng thanh toán", 18),
           ("lan_dau", "Giao dịch đầu", 14), ("lan_cuoi", "Giao dịch cuối", 14)]
    ws = _sheet(wb, "Thống kê theo đối tác", cot)
    g = {}
    for r in dong:
        la_mua = r["loai_gd"] == "Mua vào"
        key = (r["loai_gd"], r["mst_ban"] if la_mua else r["mst_mua"],
               r["ten_ban"] if la_mua else r["ten_mua"])
        d = g.setdefault(key, {"hd": set(), "n": 0, "tt": 0.0, "thue": 0.0,
                               "ngay": []})
        d["hd"].add(r["khoa"])
        d["n"] += 1
        d["tt"] += r["thanh_tien"]
        d["thue"] += r["tien_thue_dong"]
        if r["ngay_iso"] != TRONG_CHU:
            d["ngay"].append(r["ngay_iso"])
    i = 0
    for (loai, mst, ten), d in sorted(g.items(), key=lambda x: -x[1]["tt"]):
        i += 1
        ng = sorted(d["ngay"]) or [""]
        ws.append([i, loai, mst, ten, len(d["hd"]), d["n"], round(d["tt"]),
                   round(d["thue"]), round(d["tt"] + d["thue"]),
                   dc.ngay_vn(ng[0]) or TRONG_CHU,
                   dc.ngay_vn(ng[-1]) or TRONG_CHU])
    n = ws.max_row
    for r in range(2, n + 1):
        for c in (7, 8, 9):
            ws.cell(row=r, column=c).number_format = '#,##0'
    _tong_dong(ws, [5, 6, 7, 8, 9], 2, n, 4)
    return ws


def _thong_ke_mat_hang(wb, dong):
    cot = [("stt", "STT", 6), ("nhom", "Nhóm hàng (chuẩn hóa)", 40),
           ("vd", "Tên xuất hiện gần nhất", 46), ("dvt", "ĐVT", 10),
           ("lan", "Số lần xuất hiện", 15), ("sl", "Tổng số lượng", 15),
           ("tt", "Tổng tiền hàng", 18), ("thue", "Tổng thuế", 16),
           ("dg_tb", "Đơn giá bình quân", 18),
           ("dg_min", "Đơn giá thấp nhất", 18),
           ("dg_max", "Đơn giá cao nhất", 18), ("ncc", "Số đối tác", 11)]
    ws = _sheet(wb, "Thống kê mặt hàng", cot)
    g = {}
    for r in dong:
        d = g.setdefault(r["nhom_hang"], {"vd": "", "dvt": r["dvt"], "lan": 0,
                                          "sl": 0.0, "tt": 0.0, "thue": 0.0,
                                          "dg": [], "ncc": set()})
        d["vd"] = r["ten_hang"]
        d["lan"] += 1
        d["sl"] += r["so_luong"]
        d["tt"] += r["thanh_tien"]
        d["thue"] += r["tien_thue_dong"]
        if r["don_gia"]:
            d["dg"].append(r["don_gia"])
        d["ncc"].add(r["mst_ban"])
    i = 0
    for nhom, d in sorted(g.items(), key=lambda x: -x[1]["tt"]):
        i += 1
        dg = d["dg"] or [0]
        ws.append([i, nhom, d["vd"], d["dvt"], d["lan"], round(d["sl"], 3),
                   round(d["tt"]), round(d["thue"]),
                   round(d["tt"] / d["sl"], 2) if d["sl"] else 0,
                   round(min(dg), 2), round(max(dg), 2), len(d["ncc"])])
    n = ws.max_row
    for r in range(2, n + 1):
        for c in (7, 8, 9, 10, 11):
            ws.cell(row=r, column=c).number_format = '#,##0'
        ws.cell(row=r, column=6).number_format = '#,##0.###'
    _tong_dong(ws, [5, 7, 8], 2, n, 2)
    return ws


def _thong_ke_thue_suat(wb, dong):
    cot = [("ts", "Thuế suất", 26), ("loai", "Loại giao dịch", 15),
           ("sdong", "Số dòng", 11), ("shd", "Số hóa đơn", 12),
           ("tt", "Tiền hàng", 18), ("thue", "Tiền thuế", 17),
           ("tong", "Tổng cộng", 18), ("tl", "Tỷ lệ thuế/tiền hàng", 20)]
    ws = _sheet(wb, "Thống kê thuế suất", cot)
    g = {}
    for r in dong:
        key = (r["ts_nhan"], r["loai_gd"])
        d = g.setdefault(key, {"n": 0, "hd": set(), "tt": 0.0, "thue": 0.0})
        d["n"] += 1
        d["hd"].add(r["khoa"])
        d["tt"] += r["thanh_tien"]
        d["thue"] += r["tien_thue_dong"]
    for (ts, loai), d in sorted(g.items()):
        ws.append([ts, loai, d["n"], len(d["hd"]), round(d["tt"]),
                   round(d["thue"]), round(d["tt"] + d["thue"]),
                   (d["thue"] / d["tt"]) if d["tt"] else 0])
    n = ws.max_row
    for r in range(2, n + 1):
        for c in (5, 6, 7):
            ws.cell(row=r, column=c).number_format = '#,##0'
        ws.cell(row=r, column=8).number_format = '0.00%'
    _tong_dong(ws, [3, 4, 5, 6, 7], 2, n, 1)
    return ws


def _tong_hop_ke_khai(wb, mua, ban):
    k = _kieu()
    cot = [("muc", "Nội dung", 56), ("gt", "Giá trị chưa thuế", 20),
           ("thue", "Thuế GTGT", 18), ("ghi", "Ghi chú", 46)]
    ws = _sheet(wb, "Tổng hợp kê khai", cot)

    def cong(ds, dieu_kien):
        a = sum(r["thanh_tien"] for r in ds if dieu_kien(r))
        b = sum(r["tien_thue_dong"] for r in ds if dieu_kien(r))
        return round(a), round(b)

    def la(ts):
        return lambda r: r["ts_nhan"].startswith(ts)

    hang = [("A. HÀNG HÓA, DỊCH VỤ MUA VÀO", None, None, ""),
            ("Tổng giá trị mua vào và thuế GTGT đầu vào",
             *cong(mua, lambda r: True),
             "Tương ứng chỉ tiêu [23], [24] trên tờ khai 01/GTGT"),
            ("  Trong đó: thuế suất 10%", *cong(mua, la("10%")), ""),
            ("  Trong đó: thuế suất 8%", *cong(mua, la("8%")), ""),
            ("  Trong đó: thuế suất 5%", *cong(mua, la("5%")), ""),
            ("  Trong đó: thuế suất 0%", *cong(mua, la("0%")), ""),
            ("  Trong đó: không chịu thuế / không kê khai",
             *cong(mua, lambda r: r["ts_nhan"].startswith("K")),
             "Không được khấu trừ thuế đầu vào"),
            ("", None, None, ""),
            ("B. HÀNG HÓA, DỊCH VỤ BÁN RA", None, None, ""),
            ("Tổng doanh thu bán ra và thuế GTGT đầu ra",
             *cong(ban, lambda r: True),
             "Tương ứng chỉ tiêu [32] + [33] (tùy thuế suất)"),
            ("  Doanh thu chịu thuế 10%", *cong(ban, la("10%")),
             "Chỉ tiêu [32] và [33]"),
            ("  Doanh thu chịu thuế 8%", *cong(ban, la("8%")),
             "Theo chính sách giảm thuế đang áp dụng"),
            ("  Doanh thu chịu thuế 5%", *cong(ban, la("5%")),
             "Chỉ tiêu [30] và [31]"),
            ("  Doanh thu thuế suất 0%", *cong(ban, la("0%")),
             "Chỉ tiêu [29]"),
            ("  Doanh thu không chịu thuế",
             *cong(ban, lambda r: r["ts_nhan"].startswith("K")),
             "Chỉ tiêu [26]"),
            ("", None, None, ""),
            ("C. CHÊNH LỆCH THUẾ (đầu ra − đầu vào)", None,
             round(sum(r["tien_thue_dong"] for r in ban)
                   - sum(r["tien_thue_dong"] for r in mua)),
             "Chỉ là phép trừ số học, chưa xét điều kiện khấu trừ")]
    for a, b, c, d in hang:
        ws.append([a, b if b is not None else "", c if c is not None else "", d])
        r = ws.max_row
        if a and b is None and c is None:
            ws.cell(row=r, column=1).font = k["bold"]
            for cc in range(1, 5):
                ws.cell(row=r, column=cc).fill = k["tong"]
        for cc in (2, 3):
            ws.cell(row=r, column=cc).number_format = '#,##0'
    ws.append([])
    ws.append(["LƯU Ý: Bảng này chỉ tổng hợp số liệu từ các tệp XML đang có "
               "trong kho để đối chiếu nội bộ, không thay thế tờ khai thuế. "
               "Điều kiện khấu trừ, thời điểm kê khai và việc loại trừ hóa đơn "
               "không hợp lệ do kế toán tự xác định và chịu trách nhiệm.",
               "", "", ""])
    ws.cell(row=ws.max_row, column=1).font = Font_bold_blue()
    return ws


if __name__ == "__main__":
    ds = dc.doc_hoa_don()
    r = xuat_chi_tiet_day_du(
        ds, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                         "BaoCaoChiTiet_test.xlsx"))
    print(r)
