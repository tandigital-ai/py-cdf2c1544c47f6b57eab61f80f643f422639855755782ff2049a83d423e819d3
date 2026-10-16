# -*- coding: utf-8 -*-
"""
TAX INVOICE PRO - xslt_nhung.py (v1.6.1)
Trich va ap dung ban mau trinh bay (XSLT) nhung trong tep XML hoa don.
Khong bat buoc thu vien ngoai: neu co lxml thi dung, neu khong thi xuat cap
tep XML + XSL de mo bang trinh duyet, va luon co duong lui ve ban the hien
tu dung cua phan mem.
Tac gia: TDA - 0986509106
"""
import os
import io
import re
import gzip
import base64
import shutil
import zipfile
import datetime
import tempfile
import webbrowser

PHIEN_BAN = "1.6.1"
THU_MUC = os.path.dirname(os.path.abspath(__file__))
THU_MUC_RA = os.path.join(THU_MUC, "ban_the_hien")

DAU_XSL = (b"xsl:stylesheet", b"xsl:transform")
TEN_GOI_Y = ("xslt", "xsl", "banthehien", "bantheien", "mauhoadon", "mauhd",
             "template", "stylesheet", "dulieuxslt", "mausohoadon")


# ----------------------------------------------------------------------
def _doc_bytes(p):
    with open(p, "rb") as f:
        return f.read()


def _ve_chu(raw):
    if raw is None:
        return ""
    for ma in ("utf-8-sig", "utf-8", "utf-16", "cp1258", "latin-1"):
        try:
            return raw.decode(ma)
        except Exception:
            continue
    return raw.decode("utf-8", "replace")


def _go_nen(raw):
    """Mo goi neu XSLT bi nen zip hoac gzip."""
    if not raw:
        return None
    if raw[:2] == b"PK":
        try:
            zf = zipfile.ZipFile(io.BytesIO(raw))
            for n in zf.namelist():
                if n.lower().endswith((".xsl", ".xslt", ".xml")):
                    return zf.read(n)
            return zf.read(zf.namelist()[0]) if zf.namelist() else None
        except Exception:
            return None
    if raw[:2] == b"\x1f\x8b":
        try:
            return gzip.decompress(raw)
        except Exception:
            return None
    return raw


def _giai_b64(chuoi):
    s = re.sub(r"[^A-Za-z0-9+/=]", "", chuoi or "")
    if len(s) < 400:
        return None
    s += "=" * ((4 - len(s) % 4) % 4)
    try:
        raw = base64.b64decode(s)
    except Exception:
        return None
    return _go_nen(raw)


def _la_xslt(raw):
    if not raw:
        return False
    dau = raw[:4000].lower()
    return any(k in dau for k in DAU_XSL)


def _khong_dau(s):
    s = str(s or "").lower()
    return re.sub(r"[^a-z0-9]", "", s)


# ----------------------------------------------------------------------
def tim_xslt(duong_dan_xml):
    """Tra ve danh sach [(mo_ta_nguon, noi_dung_bytes)] cac ban mau tim duoc."""
    kq = []
    try:
        raw = _doc_bytes(duong_dan_xml)
    except Exception:
        return kq
    van = _ve_chu(raw)
    thu_muc = os.path.dirname(os.path.abspath(duong_dan_xml))

    # 1. XSLT viet thang trong tep (ke ca trong CDATA)
    for m in re.finditer(r"<(?:\w+:)?(?:stylesheet|transform)\b", van):
        i = m.start()
        j = van.find("stylesheet>", i)
        k = van.find("transform>", i)
        cuoi = max(j, k)
        if cuoi > i:
            doan = van[i:cuoi + 12]
            if "xsl" in doan[:200].lower() and len(doan) > 500:
                kq.append(("XSLT ghi thẳng trong tệp XML", doan.encode("utf-8")))
                break

    # 2. Chi dan xu ly <?xml-stylesheet href="..."?>
    for m in re.finditer(r'<\?xml-stylesheet[^>]*href\s*=\s*"([^"]+)"', van):
        ten = m.group(1)
        p = ten if os.path.isabs(ten) else os.path.join(thu_muc, ten)
        if os.path.exists(p):
            kq.append(("Tệp mẫu kèm theo: %s" % os.path.basename(p), _doc_bytes(p)))

    # 3. Chuoi base64 nam trong cac the co ten goi y
    for m in re.finditer(r"<([A-Za-z_][\w:.\-]*)[^>]*>([^<]{400,})</\1>", van):
        ten = _khong_dau(m.group(1).split(":")[-1])
        noi = m.group(2)
        hop = any(g in ten for g in TEN_GOI_Y)
        if not hop and len(noi) < 3000:
            continue
        d = _giai_b64(noi)
        if _la_xslt(d):
            kq.append(("Mẫu nhúng trong thẻ <%s>" % m.group(1), d))

    # 4. Cap TTruong / DLieu trong khoi TTKhac
    for m in re.finditer(
            r"<(?:\w+:)?TTruong>([^<]*)</(?:\w+:)?TTruong>\s*"
            r"<(?:\w+:)?DLieu>([^<]*)</(?:\w+:)?DLieu>", van, re.S):
        d = _giai_b64(m.group(2))
        if _la_xslt(d):
            kq.append(("Mẫu nhúng ở trường \"%s\"" % m.group(1).strip()[:40], d))

    # 5. Tep .xsl cung thu muc, trung ten voi tep XML
    goc = os.path.splitext(os.path.basename(duong_dan_xml))[0]
    for ten in os.listdir(thu_muc) if os.path.isdir(thu_muc) else []:
        if ten.lower().endswith((".xsl", ".xslt")):
            if goc.lower() in ten.lower() or len(os.listdir(thu_muc)) < 40:
                p = os.path.join(thu_muc, ten)
                kq.append(("Tệp mẫu cùng thư mục: %s" % ten, _doc_bytes(p)))

    # Bo trung
    thay, sach = set(), []
    for mo_ta, d in kq:
        if not _la_xslt(d):
            continue
        h = hash(d[:3000])
        if h in thay:
            continue
        thay.add(h)
        sach.append((mo_ta, d))
    return sach


def co_xslt(duong_dan_xml):
    try:
        return len(tim_xslt(duong_dan_xml)) > 0
    except Exception:
        return False


# ----------------------------------------------------------------------
def co_lxml():
    try:
        import lxml.etree  # noqa: F401
        return True
    except Exception:
        return False


def _than_xml(duong_dan_xml):
    """Tra ve bytes cua MOT hoa don dau tien (tep co the chua nhieu <HDon>)."""
    raw = _doc_bytes(duong_dan_xml)
    van = _ve_chu(raw)
    n = len(re.findall(r"<(?:\w+:)?HDon[\s>]", van))
    if n <= 1:
        return raw
    i = re.search(r"<(?:\w+:)?HDon[\s>]", van)
    j = van.lower().rfind("</hdon>", 0, len(van))
    j2 = van.lower().find("</hdon>", i.start())
    if i and j2 > 0:
        doan = van[i.start():j2 + 7]
        return ('<?xml version="1.0" encoding="UTF-8"?>' + doan).encode("utf-8")
    return raw


def ap_dung_lxml(duong_dan_xml, xsl_bytes):
    """Bien doi XML theo XSLT, tra ve chuoi HTML. Nem loi neu that bai."""
    from lxml import etree
    tai = etree.XMLParser(recover=True, huge_tree=True, resolve_entities=False)
    cay_xsl = etree.fromstring(xsl_bytes, parser=tai)
    bien = etree.XSLT(cay_xsl)
    cay_xml = etree.fromstring(_than_xml(duong_dan_xml), parser=tai)
    kq = bien(cay_xml)
    html = str(kq)
    if not html.strip():
        raise RuntimeError("Mẫu trả về nội dung rỗng.")
    return html


def _khung(html, mo_ta, ten_tep):
    bang = ("<div style=\"font:12px Segoe UI,Arial;background:#E3F0FD;"
            "border-bottom:2px solid #1565C0;padding:8px 14px;color:#0D47A1\">"
            "<b>Bản thể hiện theo mẫu của nhà cung cấp</b> — %s &nbsp;|&nbsp; "
            "Tệp: %s &nbsp;|&nbsp; Kết xuất %s bởi TAX INVOICE PRO v%s (TDA - "
            "0986509106). Bản gốc có giá trị pháp lý là tệp XML."
            "<style media=\"print\">div{display:none}</style></div>"
            % (mo_ta, ten_tep,
               datetime.datetime.now().strftime("%d/%m/%Y %H:%M"), PHIEN_BAN))
    thap = html.lower()
    i = thap.find("<body")
    if i >= 0:
        j = html.find(">", i)
        if j > 0:
            return html[:j + 1] + bang + html[j + 1:]
    return bang + html


def xuat_cap_tep(duong_dan_xml, xsl_bytes, thu_muc_ra=None):
    """Ghi ra cap tep XML + XSL de mo bang trinh duyet (Firefox doc duoc)."""
    thu_muc_ra = thu_muc_ra or os.path.join(THU_MUC_RA, "mau_ncc")
    os.makedirs(thu_muc_ra, exist_ok=True)
    goc = os.path.splitext(os.path.basename(duong_dan_xml))[0]
    p_xsl = os.path.join(thu_muc_ra, goc + ".xsl")
    with open(p_xsl, "wb") as f:
        f.write(xsl_bytes)
    van = _ve_chu(_than_xml(duong_dan_xml))
    van = re.sub(r"<\?xml-stylesheet[^>]*\?>", "", van)
    chi_dan = '<?xml-stylesheet type="text/xsl" href="%s.xsl"?>' % goc
    if van.lstrip().startswith("<?xml"):
        k = van.find("?>") + 2
        van = van[:k] + "\n" + chi_dan + van[k:]
    else:
        van = '<?xml version="1.0" encoding="UTF-8"?>\n' + chi_dan + "\n" + van
    p_xml = os.path.join(thu_muc_ra, goc + "_mauNCC.xml")
    with open(p_xml, "w", encoding="utf-8") as f:
        f.write(van)
    return p_xml, p_xsl


def ban_the_hien_ncc(duong_dan_xml, thu_muc_ra=None, chi_so=0):
    """Tra ve (duong_dan_html, mo_ta). Nem loi neu khong lam duoc."""
    ds = tim_xslt(duong_dan_xml)
    if not ds:
        raise RuntimeError("Tệp XML này không nhúng mẫu trình bày của nhà cung cấp.")
    mo_ta, xsl = ds[min(chi_so, len(ds) - 1)]
    if not co_lxml():
        raise RuntimeError(
            "Máy chưa cài thư viện lxml nên chưa dựng được mẫu của nhà cung cấp. "
            "Bấm nút \"Cài thư viện lxml\" một lần duy nhất, hoặc dùng nút "
            "\"Xuất cặp tệp XML + XSL\" rồi mở bằng Firefox.")
    html = _khung(ap_dung_lxml(duong_dan_xml, xsl), mo_ta,
                  os.path.basename(duong_dan_xml))
    thu_muc_ra = thu_muc_ra or THU_MUC_RA
    os.makedirs(thu_muc_ra, exist_ok=True)
    ten = "MauNCC_%s.html" % os.path.splitext(os.path.basename(duong_dan_xml))[0]
    p = os.path.join(thu_muc_ra, ten)
    with open(p, "w", encoding="utf-8") as f:
        f.write(html)
    return p, mo_ta


# ----------------------------------------------------------------------
def ban_the_hien_chuan(duong_dan_xml, thu_muc_ra=None):
    """Ban the hien tu dung cua phan mem (duong lui luon dung duoc)."""
    thu_muc_ra = thu_muc_ra or THU_MUC_RA
    os.makedirs(thu_muc_ra, exist_ok=True)
    import invoice_render as ir
    hd = None
    try:
        import xml_parser as xp
        for ten in ("doc_file_an_toan", "doc_file", "doc_mot_file"):
            if hasattr(xp, ten):
                r = getattr(xp, ten)(duong_dan_xml)
                hd = r[0] if isinstance(r, tuple) else r
                if isinstance(hd, list):
                    hd = hd[0] if hd else None
                if hd:
                    break
    except Exception:
        hd = None
    if hd is None:
        raise RuntimeError("Không đọc được dữ liệu hóa đơn từ tệp XML.")
    for ten in ("luu_html", "luu_ban_the_hien", "xuat_html"):
        if hasattr(ir, ten):
            kq = getattr(ir, ten)(hd, thu_muc_ra)
            if isinstance(kq, (list, tuple)):
                kq = kq[0]
            return str(kq)
    for ten in ("dung_html", "tao_html", "html_hoa_don", "render"):
        if hasattr(ir, ten):
            html = getattr(ir, ten)(hd)
            p = os.path.join(thu_muc_ra, "Chuan_%s.html"
                             % os.path.splitext(os.path.basename(duong_dan_xml))[0])
            with open(p, "w", encoding="utf-8") as f:
                f.write(html)
            return p
    raise RuntimeError("Không tìm thấy hàm dựng HTML trong invoice_render.py")


def so_sanh_canh_nhau(trai, phai, nhan_trai="", nhan_phai="", thu_muc_ra=None):
    """Tao trang HTML dat hai ban the hien canh nhau."""
    thu_muc_ra = thu_muc_ra or THU_MUC_RA
    os.makedirs(thu_muc_ra, exist_ok=True)
    p = os.path.join(thu_muc_ra, "SoSanh_%s.html"
                     % datetime.datetime.now().strftime("%Y%m%d_%H%M%S"))
    def u(x):
        return "file:///" + os.path.abspath(x).replace("\\", "/")
    html = """<!DOCTYPE html><html lang="vi"><head><meta charset="utf-8">
<title>So sánh hai hóa đơn - TAX INVOICE PRO</title><style>
body{margin:0;font:13px Segoe UI,Arial;background:#F4F7FB}
.dau{background:#1565C0;color:#fff;padding:10px 16px;font-size:15px;font-weight:bold}
.luoi{display:flex;gap:10px;padding:10px;height:calc(100vh - 92px)}
.cot{flex:1;display:flex;flex-direction:column;border:1px solid #D6E2F0;
background:#fff;border-radius:8px;overflow:hidden}
.nhan{background:#E3F0FD;color:#0D47A1;padding:8px 12px;font-weight:bold;
border-bottom:1px solid #D6E2F0}
iframe{flex:1;border:0;width:100%%}
.chan{padding:8px 16px;color:#546E7A;font-size:12px}
@media print{.dau,.chan,.nhan{display:none}.luoi{height:auto;display:block}}
</style></head><body>
<div class="dau">So sánh hai hóa đơn cạnh nhau — TAX INVOICE PRO v%s</div>
<div class="luoi">
 <div class="cot"><div class="nhan">%s</div><iframe src="%s"></iframe></div>
 <div class="cot"><div class="nhan">%s</div><iframe src="%s"></iframe></div>
</div>
<div class="chan">Dùng để đối chiếu hóa đơn gốc với hóa đơn điều chỉnh hoặc
thay thế. Bản gốc có giá trị pháp lý là tệp XML. Tác giả: TDA - 0986509106</div>
</body></html>""" % (PHIEN_BAN, nhan_trai or "Hóa đơn 1", u(trai),
                     nhan_phai or "Hóa đơn 2", u(phai))
    with open(p, "w", encoding="utf-8") as f:
        f.write(html)
    return p


def cai_lxml():
    """Cai thu vien lxml vao moi truong ao dang chay."""
    import subprocess
    import sys
    r = subprocess.run([sys.executable, "-m", "pip", "install", "lxml"],
                       capture_output=True, text=True)
    return (r.returncode == 0, (r.stdout or "") + (r.stderr or ""))


def mo(p):
    try:
        os.startfile(p)
    except Exception:
        webbrowser.open("file:///" + os.path.abspath(p).replace("\\", "/"))


# ----------------------------------------------------------------------
def _cli():
    import sys
    duong = sys.argv[1] if len(sys.argv) > 1 else os.path.join(THU_MUC, "XML_Test")
    ds = []
    if os.path.isdir(duong):
        for t in sorted(os.listdir(duong)):
            if t.lower().endswith(".xml"):
                ds.append(os.path.join(duong, t))
    elif os.path.exists(duong):
        ds = [duong]
    print("=== TIM BAN MAU XSLT NHUNG TRONG XML ===")
    print("lxml: %s" % ("da cai" if co_lxml() else "CHUA cai"))
    print("So tep: %d" % len(ds))
    for p in ds:
        print("")
        print("* %s" % os.path.basename(p))
        try:
            mau = tim_xslt(p)
        except Exception as e:
            print("  [LOI] %s" % e)
            continue
        if not mau:
            print("  Khong nhung ban mau -> dung ban the hien chuan cua phan mem.")
            continue
        for i, (mo_ta, d) in enumerate(mau):
            print("  [%d] %s (%d byte)" % (i, mo_ta, len(d)))
        try:
            p_html, mo_ta = ban_the_hien_ncc(p)
            print("  -> Da tao: %s" % p_html)
        except Exception as e:
            print("  -> Chua dung duoc: %s" % e)
            try:
                a, b = xuat_cap_tep(p, mau[0][1])
                print("     Da xuat cap tep: %s" % a)
            except Exception as e2:
                print("     Loi xuat cap tep: %s" % e2)
    print("")
    print("Thu muc ket qua: %s" % THU_MUC_RA)


if __name__ == "__main__":
    _cli()

TEP_DAY_DU = True  # dau hieu tep da duoc dan day du - dung xoa dong nay
