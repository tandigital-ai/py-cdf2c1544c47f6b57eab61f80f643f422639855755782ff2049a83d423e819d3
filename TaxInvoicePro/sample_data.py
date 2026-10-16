# -*- coding: utf-8 -*-
"""
TAX INVOICE PRO v1.0.0
Dữ liệu hóa đơn mẫu cho lần chạy đầu tiên (hoàn toàn offline).
Tác giả: TDA - Điện thoại: 0986509106
"""

MST_MAC_DINH = "0101234567"


def tao_du_lieu_mau():
    """Trả về 12 hóa đơn mẫu, ngày trong tháng 09/2026, đủ 4 trạng thái.
    MST người mua 0101234567 xuất hiện ở 9 hóa đơn."""
    m = MST_MAC_DINH
    rows = [
        # ngay_lap, so_hd, mau_so, ky_hieu, mst_ban, ten_ban, mst_mua, cccd,
        # tien_hang, thue, tong, trang_thai, loai, da_tai
        ("2026-09-05", "0000125", "1C26TAA", "AA/26E", "0102223333",
         "CÔNG TY TNHH ABC", m, "", 10_000_000, 1_000_000, 11_000_000,
         "Hợp lệ", "Hóa đơn GTGT", True),
        ("2026-09-06", "0000126", "1C26TAA", "AA/26E", "0104445555",
         "CÔNG TY CP XYZ", m, "", 5_000_000, 500_000, 5_500_000,
         "Hợp lệ", "Hóa đơn GTGT", True),
        ("2026-09-10", "0000127", "1C26TAA", "AA/26E", "0106667777",
         "CÔNG TY TNHH DEF", m, "", 8_000_000, 800_000, 8_800_000,
         "Hợp lệ", "Hóa đơn GTGT", True),
        ("2026-09-12", "0000128", "1C26TAA", "AA/26E", "0108889999",
         "CÔNG TY CP GHI", m, "", 12_000_000, 1_200_000, 13_200_000,
         "Hợp lệ", "Hóa đơn GTGT", False),
        ("2026-09-15", "0000129", "1C26TAA", "AA/26E", "0111122222",
         "CÔNG TY TNHH KLM", m, "", 7_000_000, 700_000, 7_700_000,
         "Điều chỉnh", "Hóa đơn GTGT", False),
        ("2026-09-18", "0000130", "1C26TAA", "AA/26E", "0113344444",
         "CÔNG TY CP NOP", m, "", 20_000_000, 2_000_000, 22_000_000,
         "Thay thế", "Hóa đơn GTGT", False),
        ("2026-09-20", "0000131", "1C26TAA", "AA/26E", "0115566666",
         "CÔNG TY TNHH QRS", m, "", 3_000_000, 300_000, 3_300_000,
         "Hợp lệ", "Hóa đơn bán hàng", False),
        ("2026-09-25", "0000132", "1C26TAA", "AA/26E", "0117788888",
         "CÔNG TY CP TUV", m, "", 15_000_000, 1_500_000, 16_500_000,
         "Hủy", "Hóa đơn GTGT", False),
        ("2026-09-26", "0000133", "1C26TAA", "AA/26E", "0119900011",
         "CÔNG TY TNHH WX VIỆT NAM", m, "", 4_500_000, 450_000, 4_950_000,
         "Hợp lệ", "Hóa đơn GTGT", False),
        ("2026-09-27", "0000134", "2C26TAB", "AB/26E", "0121011122",
         "CÔNG TY CP YZ", "0109999888", "", 9_000_000, 900_000, 9_900_000,
         "Điều chỉnh", "Hóa đơn bán hàng", False),
        ("2026-09-28", "0000135", "2C26TAB", "AB/26E", "0122122233",
         "CÔNG TY TNHH AN KHANG", "0105554443", "001090012345",
         6_400_000, 640_000, 7_040_000, "Hợp lệ", "Hóa đơn GTGT", False),
        ("2026-09-30", "0000136", "2C26TAB", "AB/26E", "0123233344",
         "CÔNG TY CP MINH PHÁT", "0107778889", "", 25_000_000, 2_500_000,
         27_500_000, "Thay thế", "Hóa đơn GTGT", False),
    ]

    data = []
    for i, r in enumerate(rows, start=1):
        data.append({
            "id": "SEED%04d" % i,
            "ngay_lap": r[0],
            "so_hoa_don": r[1],
            "ky_hieu_mau_so": r[2],
            "ky_hieu_hoa_don": r[3],
            "mst_nguoi_ban": r[4],
            "ten_nguoi_ban": r[5],
            "mst_nguoi_mua": r[6],
            "cccd_nguoi_mua": r[7],
            "tien_hang": r[8],
            "thue_gtgt": r[9],
            "tong_tien": r[10],
            "trang_thai": r[11],
            "loai_hoa_don": r[12],
            "duong_dan_xml": "",
            "da_tai": r[13],
        })
    return data