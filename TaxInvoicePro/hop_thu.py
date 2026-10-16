# -*- coding: utf-8 -*-
"""
hop_thu.py - TAX INVOICE PRO v1.5.0 - Giai doan 3 (kenh B)
Lay tep dinh kem .xml/.zip tu hop thu IMAP cua ke toan.
Mat khau ung dung luu trong Windows Credential Manager (khong ghi ra tep).
Khong ket noi may chu co quan thue.
Tac gia: TDA - 0986509106
"""
import os
import json
import email
import imaplib
import datetime
from email.header import decode_header, make_header

import theo_doi

THU_MUC = os.path.dirname(os.path.abspath(__file__))
THU_MUC_TAI = os.path.join(THU_MUC, "data", "hop_thu")
TEP_UID = os.path.join(THU_MUC, "data", "hop_thu_uid.json")
DUOI_NHAN = (".xml", ".zip")

imaplib._MAXLINE = max(getattr(imaplib, "_MAXLINE", 10000), 1000000)


# ------------------------------------ Windows Credential Manager (ctypes)
def _api():
    import ctypes
    from ctypes import wintypes
    adv = ctypes.WinDLL("advapi32", use_last_error=True)

    class CREDENTIAL(ctypes.Structure):
        _fields_ = [("Flags", wintypes.DWORD), ("Type", wintypes.DWORD),
                    ("TargetName", wintypes.LPWSTR),
                    ("Comment", wintypes.LPWSTR),
                    ("LastWritten", wintypes.FILETIME),
                    ("CredentialBlobSize", wintypes.DWORD),
                    ("CredentialBlob", ctypes.POINTER(ctypes.c_char)),
                    ("Persist", wintypes.DWORD),
                    ("AttributeCount", wintypes.DWORD),
                    ("Attributes", ctypes.c_void_p),
                    ("TargetAlias", wintypes.LPWSTR),
                    ("UserName", wintypes.LPWSTR)]

    adv.CredWriteW.argtypes = [ctypes.POINTER(CREDENTIAL), wintypes.DWORD]
    adv.CredWriteW.restype = wintypes.BOOL
    adv.CredReadW.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD,
                              ctypes.POINTER(ctypes.POINTER(CREDENTIAL))]
    adv.CredReadW.restype = wintypes.BOOL
    adv.CredDeleteW.argtypes = [wintypes.LPCWSTR, wintypes.DWORD,
                                wintypes.DWORD]
    adv.CredDeleteW.restype = wintypes.BOOL
    adv.CredFree.argtypes = [ctypes.c_void_p]
    return ctypes, adv, CREDENTIAL


def ten_kho_khoa(may_chu, tai_khoan):
    return "TaxInvoicePro:IMAP:%s@%s" % (tai_khoan or "", may_chu or "")


def luu_mat_khau(may_chu, tai_khoan, mat_khau):
    ctypes, adv, CREDENTIAL = _api()
    blob = (mat_khau or "").encode("utf-16-le")
    c = CREDENTIAL()
    c.Flags = 0
    c.Type = 1                      # CRED_TYPE_GENERIC
    c.TargetName = ten_kho_khoa(may_chu, tai_khoan)
    c.Comment = "TAX INVOICE PRO - mật khẩu ứng dụng hộp thư"
    c.CredentialBlobSize = len(blob)
    c.CredentialBlob = ctypes.cast(ctypes.c_char_p(blob),
                                   ctypes.POINTER(ctypes.c_char))
    c.Persist = 2                   # CRED_PERSIST_LOCAL_MACHINE
    c.UserName = tai_khoan
    if not adv.CredWriteW(ctypes.byref(c), 0):
        raise OSError("Không lưu được mật khẩu (mã lỗi %d)"
                      % ctypes.get_last_error())
    return True


def doc_mat_khau(may_chu, tai_khoan):
    try:
        ctypes, adv, CREDENTIAL = _api()
        con = ctypes.POINTER(CREDENTIAL)()
        if not adv.CredReadW(ten_kho_khoa(may_chu, tai_khoan), 1, 0,
                             ctypes.byref(con)):
            return ""
        try:
            n = con.contents.CredentialBlobSize
            raw = ctypes.string_at(con.contents.CredentialBlob, n)
            return raw.decode("utf-16-le")
        finally:
            adv.CredFree(con)
    except Exception:
        return ""


def xoa_mat_khau(may_chu, tai_khoan):
    try:
        _, adv, _ = _api()
        return bool(adv.CredDeleteW(ten_kho_khoa(may_chu, tai_khoan), 1, 0))
    except Exception:
        return False


# ------------------------------------------------------------- UID da xu ly
def _doc_uid():
    try:
        with open(TEP_UID, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def _ghi_uid(d):
    os.makedirs(os.path.dirname(TEP_UID), exist_ok=True)
    with open(TEP_UID, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=1)


# ------------------------------------------------------------------ IMAP
def _ket_noi(ch, mat_khau):
    cong = int(ch.get("cong") or (993 if ch.get("ssl", True) else 143))
    if ch.get("ssl", True):
        m = imaplib.IMAP4_SSL(ch["may_chu"], cong)
    else:
        m = imaplib.IMAP4(ch["may_chu"], cong)
    m.login(ch["tai_khoan"], mat_khau)
    return m


def kiem_tra_ket_noi(ch, mat_khau):
    try:
        m = _ket_noi(ch, mat_khau)
        try:
            typ, hop = m.list()
            ten = []
            for d in (hop or [])[:40]:
                s = d.decode("utf-8", "ignore") if isinstance(d, bytes) else str(d)
                ten.append(s.split(' "/" ')[-1].strip('"'))
            return True, ("Đăng nhập thành công. Các hộp thư: %s"
                          % ", ".join(ten[:12]))
        finally:
            try:
                m.logout()
            except Exception:
                pass
    except imaplib.IMAP4.error as e:
        return False, ("Máy chủ từ chối đăng nhập: %s. Với Gmail/Outlook bạn "
                       "phải dùng 'mật khẩu ứng dụng', không dùng mật khẩu "
                       "thường." % e)
    except Exception as e:
        return False, "Không kết nối được: %s" % e


def _ten_tep(phan):
    ten = phan.get_filename()
    if not ten:
        return ""
    try:
        ten = str(make_header(decode_header(ten)))
    except Exception:
        pass
    return "".join(c for c in ten if c not in '\\/:*?"<>|').strip()


def tai_dinh_kem(ch, mat_khau, bao=None):
    """Tai dinh kem .xml/.zip moi ve data\\hop_thu. Tra ve dict ket qua."""
    kq = {"thu": 0, "tep": [], "bo_qua": 0, "loi": ""}
    ngay = max(1, int(ch.get("so_ngay", 30)))
    tu = (datetime.date.today() - datetime.timedelta(days=ngay)) \
        .strftime("%d-%b-%Y")
    da_xu_ly = _doc_uid()
    khoa_hop = "%s|%s|%s" % (ch.get("may_chu"), ch.get("tai_khoan"),
                             ch.get("hop_thu", "INBOX"))
    cu = set(da_xu_ly.get(khoa_hop, []))

    m = _ket_noi(ch, mat_khau)
    try:
        m.select(ch.get("hop_thu", "INBOX"), readonly=True)
        typ, dl = m.uid("search", None, '(SINCE "%s")' % tu)
        uids = (dl[0].split() if dl and dl[0] else [])
        if bao:
            bao("Hộp thư có %d thư từ %s." % (len(uids), tu))
        thu_muc = os.path.join(THU_MUC_TAI,
                               datetime.date.today().strftime("%Y%m"))
        os.makedirs(thu_muc, exist_ok=True)
        for u in uids:
            uid = u.decode() if isinstance(u, bytes) else str(u)
            if uid in cu:
                kq["bo_qua"] += 1
                continue
            typ, data = m.uid("fetch", uid, "(RFC822)")
            if typ != "OK" or not data or not isinstance(data[0], tuple):
                continue
            msg = email.message_from_bytes(data[0][1])
            co_tep = False
            for phan in msg.walk():
                if phan.get_content_maintype() == "multipart":
                    continue
                ten = _ten_tep(phan)
                if not ten or not ten.lower().endswith(DUOI_NHAN):
                    continue
                noi_dung = phan.get_payload(decode=True)
                if not noi_dung:
                    continue
                d = os.path.join(thu_muc, "%s_%s" % (uid, ten))
                with open(d, "wb") as f:
                    f.write(noi_dung)
                kq["tep"].append(d)
                co_tep = True
                if bao:
                    bao("Đã tải đính kèm: %s" % ten)
            cu.add(uid)
            if co_tep:
                kq["thu"] += 1
        da_xu_ly[khoa_hop] = sorted(cu)[-5000:]
        _ghi_uid(da_xu_ly)
    finally:
        try:
            m.close()
        except Exception:
            pass
        try:
            m.logout()
        except Exception:
            pass
    return kq


def tai_va_nap(ch, mat_khau, bao=None):
    """Tai dinh kem roi nap vao kho. Chi goi tu luong giao dien."""
    kq = tai_dinh_kem(ch, mat_khau, bao)
    if kq["tep"]:
        nap = theo_doi.nap_nhieu_tep(kq["tep"], bao=bao)
        kq.update(nap)
    else:
        kq.update({"them": 0, "trung": 0, "loi": 0})
    return kq
