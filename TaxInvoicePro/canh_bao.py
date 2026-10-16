# -*- coding: utf-8 -*-
"""
TAX INVOICE PRO - canh_bao.py (v1.6.0)
Bo quy tac canh bao rui ro thue cho hoa don mua vao / ban ra.
DA BO quy tac "tinh lien tuc so hoa don theo nha cung cap" vi khong dung nghiep vu:
nha cung cap phat hanh cho nhieu khach hang nen so hoa don dut quang la binh thuong.
Quy tac nay chi dung khi soat hoa don BAN RA cua chinh don vi (co tuy chon rieng).
Tac gia: TDA - 0986509106
"""
import datetime
import os

import mst_tra_cuu as mst

CAO = "Cao"
TB = "Trung bình"
THAP = "Thấp"

THU_TU_MUC = {CAO: 0, TB: 1, THAP: 2}
DUNG_SAI = 1.0
NGUONG_KDTM = 5000000.0
TS_CHUAN = (0.0, 0.05, 0.08, 0.10)

LY_DO_BO_QUY_TAC = (
    "Đã bỏ cảnh báo \"thiếu số hóa đơn liên tục của nhà cung cấp\": một nhà cung "
    "cấp xuất hóa đơn cho rất nhiều khách hàng nên dãy số hóa đơn mà đơn vị nhận "
    "được luôn đứt quãng — đây là hiện tượng bình thường, không phải dấu hiệu rủi "
    "ro. Quy tắc này chỉ có ý nghĩa khi rà soát hóa đơn BÁN RA của chính đơn vị."
)


# ----------------------------------------------------------------------
def hom_nay():
    return datetime.date.today().strftime("%Y-%m-%d")


def ky_thang(ngay):
    return (ngay or "")[:7]


def ky_quy(ngay):
    if not ngay or len(ngay) < 7:
        return ""
    return "%s-Q%d" % (ngay[:4], (int(ngay[5:7]) - 1) // 3 + 1)


def han_nop_thang(ky):
    """Ho so khai thue GTGT thang: cham nhat ngay 20 thang sau."""
    try:
        nam, thang = int(ky[:4]), int(ky[5:7])
        thang += 1
        if thang > 12:
            thang, nam = 1, nam + 1
        return datetime.date(nam, thang, 20)
    except Exception:
        return None


def han_nop_quy(ky):
    """Khai theo quy: cham nhat ngay cuoi cung cua thang dau quy sau."""
    try:
        nam, q = int(ky[:4]), int(ky[-1])
        thang = q * 3 + 1
        if thang > 12:
            thang, nam = 1, nam + 1
        if thang == 12:
            return datetime.date(nam, 12, 31)
        return datetime.date(nam, thang + 1, 1) - datetime.timedelta(days=1)
    except Exception:
        return None


def phan_loai_gd(hd, mst_dv):
    dv = mst.mst_goc(mst_dv)
    if not dv:
        return "Mua vào"
    if mst.mst_goc(hd.get("mst_ban", "")) == dv:
        return "Bán ra"
    if mst.mst_goc(hd.get("mst_mua", "")) == dv:
        return "Mua vào"
    return "Khác"


def ty_le_thue(hd):
    th = hd.get("tien_hang", 0) or 0
    t = hd.get("thue", 0) or 0
    if th <= 0:
        return None
    return round(t / th, 4)


# ----------------------------------------------------------------------
def tong_hop(ds, mst_dv=""):
    kq = {"so_hd": len(ds), "mua_sl": 0, "mua_hang": 0.0, "mua_thue": 0.0,
          "mua_tong": 0.0, "ban_sl": 0, "ban_hang": 0.0, "ban_thue": 0.0,
          "ban_tong": 0.0, "khac_sl": 0, "huy_sl": 0, "ncc": set()}
    for hd in ds:
        loai = phan_loai_gd(hd, mst_dv)
        hd["_loai_gd"] = loai
        if mst.mst_goc(hd.get("mst_ban", "")) != mst.mst_goc(mst_dv):
            kq["ncc"].add(hd.get("mst_ban", ""))
        if "huy" in mst._kd(hd.get("trang_thai", "")):
            kq["huy_sl"] += 1
        if loai == "Mua vào":
            kq["mua_sl"] += 1
            kq["mua_hang"] += hd.get("tien_hang", 0)
            kq["mua_thue"] += hd.get("thue", 0)
            kq["mua_tong"] += hd.get("tong", 0)
        elif loai == "Bán ra":
            kq["ban_sl"] += 1
            kq["ban_hang"] += hd.get("tien_hang", 0)
            kq["ban_thue"] += hd.get("thue", 0)
            kq["ban_tong"] += hd.get("tong", 0)
        else:
            kq["khac_sl"] += 1
    kq["ncc"].discard("")
    kq["so_ncc"] = len(kq["ncc"])
    kq["chenh_thue"] = kq["ban_thue"] - kq["mua_thue"]
    return kq


# ----------------------------------------------------------------------
def _cb(ma, muc, nhom, tieu_de, ds, can_cu, xu_ly, tien_do=0.0):
    return {"ma": ma, "muc": muc, "nhom": nhom, "tieu_de": tieu_de,
            "so_luong": len(ds), "tien": tien_do, "can_cu": can_cu,
            "xu_ly": xu_ly, "danh_sach": ds}


def phan_tich(ds, mst_dv="", cache_ncc=None, ds_rui_ro=None, ngay=None):
    """Tra ve dict {kpi, canh_bao, chat_luong}."""
    ngay = ngay or hom_nay()
    cache_ncc = cache_ncc if cache_ncc is not None else mst.doc_cache_tat_ca()
    ds_rui_ro = ds_rui_ro if ds_rui_ro is not None else mst.doc_ds_rui_ro()
    kpi = tong_hop(ds, mst_dv)
    cb = []
    dv = mst.mst_goc(mst_dv)

    mua = [h for h in ds if h.get("_loai_gd") == "Mua vào"]

    # 1. Nguoi ban co MST khong con binh thuong
    x = []
    for h in mua:
        r = cache_ncc.get(h.get("mst_ban", ""))
        if r and r.get("muc_rui_ro") == mst.RUI_RO and h.get("mst_ban") not in ds_rui_ro:
            h["_ghi"] = r.get("trang_thai", "")
            x.append(h)
    if x:
        cb.append(_cb("ncc_ngung", CAO, "Người bán",
                      "Hóa đơn của nhà cung cấp có MST ngừng hoạt động / bỏ địa chỉ",
                      x,
                      "Luật Quản lý thuế 108/2025/QH15; Nghị định 254/2026/NĐ-CP",
                      "Đối chiếu ngày lập hóa đơn với thời điểm MST đổi trạng thái. "
                      "Nếu hóa đơn lập sau thời điểm đó thì không đủ điều kiện khấu "
                      "trừ và tính chi phí; in bản tra cứu tại tracuunnt.gdt.gov.vn "
                      "lưu hồ sơ.",
                      sum(h.get("tong", 0) for h in x)))

    # 2. Nguoi ban nam trong danh sach rui ro/vi pham da nap
    x = [h for h in mua if h.get("mst_ban") in ds_rui_ro]
    if x:
        cb.append(_cb("ncc_ds_rui_ro", CAO, "Người bán",
                      "Hóa đơn của doanh nghiệp thuộc danh sách rủi ro / vi phạm",
                      x,
                      "Danh sách doanh nghiệp rủi ro, vi phạm của cơ quan thuế "
                      "(tracuuhoadon.gdt.gov.vn/dnrrvp.html)",
                      "Rà soát hợp đồng, biên bản giao nhận, chứng từ thanh toán. "
                      "Cân nhắc loại khỏi số thuế được khấu trừ cho tới khi xác minh "
                      "được giao dịch là có thật.",
                      sum(h.get("tong", 0) for h in x)))

    # 3. Chua tra cuu tinh trang nguoi ban
    x = [h for h in mua if h.get("mst_ban") and
         not (cache_ncc.get(h.get("mst_ban")) or {}).get("ngay_tra_cuu")]
    if x:
        cb.append(_cb("ncc_chua_tra", TB, "Người bán",
                      "Chưa tra cứu tình trạng hoạt động của nhà cung cấp",
                      x, "Quy trình kiểm soát nội bộ rủi ro hóa đơn đầu vào",
                      "Mở màn hình \"Nhà cung cấp & Rủi ro\" và bấm TRA CỨU HÀNG LOẠT.",
                      sum(h.get("tong", 0) for h in x)))

    # 4. Hoa don tu 5 trieu chua co chung tu thanh toan khong dung tien mat
    x = [h for h in mua if h.get("tong", 0) >= NGUONG_KDTM and not h.get("tt_kdtm")]
    if x:
        cb.append(_cb("kdtm", CAO, "Điều kiện khấu trừ",
                      "Hóa đơn mua vào từ 5.000.000 đ chưa gắn chứng từ thanh toán "
                      "không dùng tiền mặt",
                      x,
                      "Luật Thuế GTGT 48/2024/QH15; Điều 26 Nghị định 181/2025/NĐ-CP",
                      "Bổ sung ủy nhiệm chi / sao kê / chứng từ bù trừ trước khi nộp "
                      "tờ khai, rồi đánh dấu lại trong phần mềm.",
                      sum(h.get("tong", 0) for h in x)))

    # 5. Lech so lieu
    x = [h for h in ds if abs((h.get("tien_hang", 0) + h.get("thue", 0)) -
                              h.get("tong", 0)) > DUNG_SAI]
    if x:
        cb.append(_cb("lech", CAO, "Số liệu",
                      "Tổng thanh toán khác tiền hàng cộng thuế GTGT", x,
                      "Phụ lục dữ liệu hóa đơn - Thông tư 91/2026/TT-BTC",
                      "Mở bản thể hiện, đối chiếu XML gốc. Nếu XML sai, yêu cầu người "
                      "bán lập hóa đơn điều chỉnh/thay thế.",
                      sum(h.get("tong", 0) for h in x)))

    # 6. Thue suat bat thuong
    x = []
    for h in ds:
        tl = ty_le_thue(h)
        if tl is None or h.get("thue", 0) == 0:
            continue
        if not any(abs(tl - c) <= 0.005 for c in TS_CHUAN):
            h["_ghi"] = "Tỷ lệ thuế/tiền hàng = %.2f%%" % (tl * 100)
            x.append(h)
    if x:
        cb.append(_cb("ts_la", TB, "Số liệu",
                      "Tỷ lệ thuế GTGT không khớp các mức 0% / 5% / 8% / 10%", x,
                      "Luật Thuế GTGT 48/2024/QH15 và văn bản giảm thuế hiện hành",
                      "Kiểm tra hóa đơn nhiều thuế suất hoặc hóa đơn có khoản không "
                      "chịu thuế; xem chi tiết dòng hàng ở màn hình Báo cáo.",
                      sum(h.get("thue", 0) for h in x)))

    # 7. Hoa don da huy / dieu chinh / thay the van dang hach toan
    x = [h for h in ds if "huy" in mst._kd(h.get("trang_thai", ""))]
    if x:
        cb.append(_cb("huy", CAO, "Hồ sơ",
                      "Hóa đơn ở trạng thái Hủy nhưng vẫn nằm trong kỳ kê khai", x,
                      "Nghị định 254/2026/NĐ-CP về xử lý hóa đơn sai sót",
                      "Loại khỏi số liệu kê khai; nếu đã kê khai thì khai bổ sung.",
                      sum(h.get("tong", 0) for h in x)))

    co = {h.get("khoa") for h in ds}
    x = []
    for h in ds:
        t = mst._kd(h.get("trang_thai", ""))
        if ("dieu chinh" in t or "thay the" in t) and h.get("mst_ban"):
            x.append(h)
    if x:
        cb.append(_cb("chuoi", TB, "Hồ sơ",
                      "Hóa đơn điều chỉnh / thay thế - cần kiểm tra hóa đơn gốc", x,
                      "Nghị định 254/2026/NĐ-CP; Thông tư 91/2026/TT-BTC",
                      "Mở màn hình Đối chiếu & Kiểm tra để nối chuỗi gốc → điều chỉnh "
                      "→ thay thế, bảo đảm không kê khai trùng.",
                      sum(h.get("tong", 0) for h in x)))

    # 8. Trung hoa don
    dem = {}
    for h in ds:
        dem.setdefault(h.get("khoa"), []).append(h)
    x = [h for k, v in dem.items() if len(v) > 1 for h in v]
    if x:
        cb.append(_cb("trung", CAO, "Số liệu",
                      "Hóa đơn trùng (cùng MST người bán, ký hiệu và số hóa đơn)", x,
                      "Nguyên tắc nhận dạng hóa đơn duy nhất",
                      "Xóa bản ghi thừa ở màn hình Tra cứu để tránh kê khai hai lần.",
                      sum(h.get("tong", 0) for h in x)))

    # 9. Thieu tep XML goc
    x = [h for h in ds if not h.get("xml") or not os.path.exists(h.get("xml", ""))]
    if x:
        cb.append(_cb("thieu_xml", TB, "Lưu trữ",
                      "Hóa đơn chưa có tệp XML gốc trên máy", x,
                      "XML là bản gốc có giá trị pháp lý, phải lưu trữ theo quy định",
                      "Tải lại XML từ hoadondientu.gdt.gov.vn hoặc từ email người bán "
                      "rồi nạp vào kho.",
                      sum(h.get("tong", 0) for h in x)))

    # 10. MST sai dinh dang
    x = [h for h in ds if h.get("mst_ban") and not mst.mst_hop_le(h["mst_ban"])]
    if x:
        cb.append(_cb("mst_sai", TB, "Số liệu",
                      "Mã số thuế người bán sai định dạng (phải 10, 12 hoặc 13 chữ số)",
                      x, "Quy định về cấu trúc mã số thuế",
                      "Mở XML kiểm tra lại; có thể do lỗi khi đọc tệp."))

    # 11. Hoa don khong thuoc don vi
    if dv:
        x = [h for h in ds if h.get("_loai_gd") == "Khác"]
        if x:
            cb.append(_cb("khong_thuoc", TB, "Hồ sơ",
                          "Hóa đơn không mang MST của đơn vị (có thể nạp nhầm)", x,
                          "Kiểm soát nội bộ",
                          "Kiểm tra lại MST đơn vị ở ô cấu hình hoặc xóa hóa đơn nạp "
                          "nhầm.",
                          sum(h.get("tong", 0) for h in x)))

    # 12. Hoa don ky truoc moi nap
    ky_nay = ky_thang(ngay)
    x = [h for h in mua if h.get("ngay_lap") and ky_thang(h["ngay_lap"]) < ky_nay]
    if x:
        cb.append(_cb("bo_sot", THAP, "Kê khai",
                      "Hóa đơn mua vào thuộc kỳ trước (kiểm tra đã kê khai chưa)", x,
                      "Hướng dẫn kê khai hóa đơn bỏ sót áp dụng từ 01/7/2026",
                      "Nếu chưa kê khai, kê vào kỳ phát hiện; nếu kê sai thì khai bổ "
                      "sung hồ sơ của kỳ có sai sót.",
                      sum(h.get("thue", 0) for h in x)))

    # 13. Ngay lap trong tuong lai
    x = [h for h in ds if h.get("ngay_lap") and h["ngay_lap"] > ngay]
    if x:
        cb.append(_cb("ngay_la", TB, "Số liệu",
                      "Hóa đơn có ngày lập sau ngày hôm nay", x,
                      "Kiểm soát dữ liệu",
                      "Kiểm tra lại dữ liệu nguồn hoặc đồng hồ hệ thống."))

    cb.sort(key=lambda c: (THU_TU_MUC.get(c["muc"], 9), -c["so_luong"]))

    tong_hd = max(1, len(ds))
    co_xml = sum(1 for h in ds if h.get("xml") and os.path.exists(h["xml"]))
    can_ct = [h for h in mua if h.get("tong", 0) >= NGUONG_KDTM]
    co_ct = sum(1 for h in can_ct if h.get("tt_kdtm"))
    ncc_list = [m for m in kpi["ncc"] if m]
    da_tra = sum(1 for m in ncc_list if (cache_ncc.get(m) or {}).get("ngay_tra_cuu"))
    chat_luong = {
        "xml": co_xml / tong_hd,
        "chung_tu": (co_ct / len(can_ct)) if can_ct else 1.0,
        "tra_ncc": (da_tra / len(ncc_list)) if ncc_list else 1.0,
        "so_ncc_rui_ro": sum(1 for m in ncc_list
                             if (cache_ncc.get(m) or {}).get("muc_rui_ro") == mst.RUI_RO
                             or m in ds_rui_ro),
    }
    kpi["cao"] = sum(c["so_luong"] for c in cb if c["muc"] == CAO)
    kpi["so_canh_bao"] = len(cb)
    return {"kpi": kpi, "canh_bao": cb, "chat_luong": chat_luong}


# ----------------------------------------------------------------------
def kiem_tra_lien_tuc_ban_ra(ds, mst_dv, nguong=500):
    """Chi ap dung cho hoa don BAN RA cua chinh don vi."""
    dv = mst.mst_goc(mst_dv)
    if not dv:
        return []
    gom = {}
    for h in ds:
        if mst.mst_goc(h.get("mst_ban", "")) != dv:
            continue
        gom.setdefault(h.get("ky_hieu", ""), []).append(h)
    kq = []
    for kh, v in gom.items():
        sos = sorted({int(x["so_hd"]) for x in v if str(x.get("so_hd", "")).isdigit()})
        if len(sos) < 2:
            continue
        thieu = []
        for a, b in zip(sos, sos[1:]):
            if 1 < b - a <= nguong:
                thieu.append("%d-%d" % (a + 1, b - 1))
        if thieu:
            kq.append({"ky_hieu": kh, "thieu": thieu, "tu": sos[0], "den": sos[-1]})
    return kq
