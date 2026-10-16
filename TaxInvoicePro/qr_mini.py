# -*- coding: utf-8 -*-
"""
TAX INVOICE PRO - Bộ sinh mã QR tối giản (chuẩn QR Code Model 2, mức sửa lỗi M).
Tự cài hoàn toàn bằng Python thuần, không cần thư viện ngoài.
Hỗ trợ phiên bản 1..10 (tối đa 213 byte) - đủ cho chuỗi DLQRCode của hóa đơn điện tử.
Tác giả: TDA - Điện thoại: 0986509106
"""

# --- GF(256) ---------------------------------------------------------------
_EXP = [0] * 512
_LOG = [0] * 256
_x = 1
for _i in range(255):
    _EXP[_i] = _x
    _LOG[_x] = _i
    _x <<= 1
    if _x & 0x100:
        _x ^= 0x11D
for _i in range(255, 512):
    _EXP[_i] = _EXP[_i - 255]


def _mul(a, b):
    if a == 0 or b == 0:
        return 0
    return _EXP[_LOG[a] + _LOG[b]]


def _rs_gen(n):
    g = [1]
    for i in range(n):
        ng = [0] * (len(g) + 1)
        for j, c in enumerate(g):
            ng[j] ^= c
            ng[j + 1] ^= _mul(c, _EXP[i])
        g = ng
    return g


def _rs_ecc(data, n):
    gen = _rs_gen(n)
    res = list(data) + [0] * n
    for i in range(len(data)):
        c = res[i]
        if c:
            for j in range(1, len(gen)):
                res[i + j] ^= _mul(gen[j], c)
    return res[len(data):]


# --- Bảng thông số mức sửa lỗi M ------------------------------------------
# phiên bản: (tổng codeword, ecc/khối, [(số khối, data/khối), ...])
_SPEC = {
    1: (26, 10, [(1, 16)]),
    2: (44, 16, [(1, 28)]),
    3: (70, 26, [(1, 44)]),
    4: (100, 18, [(2, 32)]),
    5: (134, 24, [(2, 43)]),
    6: (172, 16, [(4, 27)]),
    7: (196, 18, [(4, 31)]),
    8: (242, 22, [(2, 38), (2, 39)]),
    9: (292, 22, [(3, 36), (2, 37)]),
    10: (346, 26, [(4, 43), (1, 44)]),
}
_ALIGN = {1: [], 2: [6, 18], 3: [6, 22], 4: [6, 26], 5: [6, 30], 6: [6, 34],
          7: [6, 22, 38], 8: [6, 24, 42], 9: [6, 26, 46], 10: [6, 28, 50]}


def _data_cw(v):
    return sum(b * d for b, d in _SPEC[v][2])


def _suc_chua(v):
    cnt_bits = 8 if v <= 9 else 16
    return (_data_cw(v) * 8 - 4 - cnt_bits) // 8


def _chon_phien_ban(n):
    for v in range(1, 11):
        if n <= _suc_chua(v):
            return v
    return None


# --- Mã hóa dữ liệu --------------------------------------------------------
def _bit_stream(payload, v):
    bits = []

    def push(val, n):
        for k in range(n - 1, -1, -1):
            bits.append((val >> k) & 1)

    push(0b0100, 4)                       # chế độ byte
    push(len(payload), 8 if v <= 9 else 16)
    for b in payload:
        push(b, 8)

    tong = _data_cw(v) * 8
    push(0, min(4, tong - len(bits)))
    while len(bits) % 8:
        bits.append(0)
    cws = [int("".join(str(b) for b in bits[i:i + 8]), 2) for i in range(0, len(bits), 8)]
    pad = [0xEC, 0x11]
    i = 0
    while len(cws) < _data_cw(v):
        cws.append(pad[i % 2])
        i += 1
    return cws


def _xen_khoi(cws, v):
    _, ecn, groups = _SPEC[v]
    khoi, pos = [], 0
    for sokhoi, dlen in groups:
        for _ in range(sokhoi):
            khoi.append(cws[pos:pos + dlen])
            pos += dlen
    ecc = [_rs_ecc(b, ecn) for b in khoi]

    ra = []
    for i in range(max(len(b) for b in khoi)):
        for b in khoi:
            if i < len(b):
                ra.append(b[i])
    for i in range(ecn):
        for e in ecc:
            ra.append(e[i])
    return ra


# --- Dựng ma trận ----------------------------------------------------------
def _khung(v):
    n = 4 * v + 17
    m = [[0] * n for _ in range(n)]
    rs = [[False] * n for _ in range(n)]

    def finder(r0, c0):
        for r in range(-1, 8):
            for c in range(-1, 8):
                rr, cc = r0 + r, c0 + c
                if 0 <= rr < n and 0 <= cc < n:
                    vung = (0 <= r <= 6 and c in (0, 6)) or (0 <= c <= 6 and r in (0, 6)) \
                           or (2 <= r <= 4 and 2 <= c <= 4)
                    m[rr][cc] = 1 if vung else 0
                    rs[rr][cc] = True

    finder(0, 0)
    finder(0, n - 7)
    finder(n - 7, 0)

    for i in range(8, n - 8):
        b = 1 if i % 2 == 0 else 0
        m[6][i] = b
        rs[6][i] = True
        m[i][6] = b
        rs[i][6] = True

    ap = _ALIGN[v]
    for r in ap:
        for c in ap:
            if (r < 9 and c < 9) or (r < 9 and c > n - 10) or (r > n - 10 and c < 9):
                continue
            for dr in range(-2, 3):
                for dc in range(-2, 3):
                    m[r + dr][c + dc] = 1 if (max(abs(dr), abs(dc)) != 1) else 0
                    rs[r + dr][c + dc] = True

    m[n - 8][8] = 1
    rs[n - 8][8] = True

    for i in range(9):
        if not rs[8][i]:
            rs[8][i] = True
        if not rs[i][8]:
            rs[i][8] = True
    for i in range(8):
        rs[8][n - 1 - i] = True
        rs[n - 1 - i][8] = True

    if v >= 7:
        for i in range(6):
            for j in range(3):
                rs[n - 11 + j][i] = True
                rs[i][n - 11 + j] = True
    return m, rs, n


def _bch(data, gen, bits):
    d = data << (bits - 1)
    g_len = gen.bit_length()
    while d.bit_length() >= g_len:
        d ^= gen << (d.bit_length() - g_len)
    return d


def _dat_format(m, n, mask):
    val = (0b00 << 3) | mask          # mức M = 00
    fmt = ((val << 10) | _bch(val, 0x537, 11)) ^ 0x5412
    for i in range(15):
        b = (fmt >> i) & 1
        if i < 6:
            m[8][i] = b
        elif i == 6:
            m[8][7] = b
        elif i == 7:
            m[8][8] = b
        elif i == 8:
            m[7][8] = b
        else:
            m[14 - i][8] = b
        if i < 8:
            m[n - 1 - i][8] = b
        else:
            m[8][n - 15 + i] = b


def _dat_version(m, n, v):
    if v < 7:
        return
    vi = (v << 12) | _bch(v, 0x1F25, 13)
    for i in range(18):
        b = (vi >> i) & 1
        m[i // 3][n - 11 + i % 3] = b
        m[n - 11 + i % 3][i // 3] = b


_MASKS = [
    lambda r, c: (r + c) % 2 == 0,
    lambda r, c: r % 2 == 0,
    lambda r, c: c % 3 == 0,
    lambda r, c: (r + c) % 3 == 0,
    lambda r, c: (r // 2 + c // 3) % 2 == 0,
    lambda r, c: (r * c) % 2 + (r * c) % 3 == 0,
    lambda r, c: ((r * c) % 2 + (r * c) % 3) % 2 == 0,
    lambda r, c: ((r + c) % 2 + (r * c) % 3) % 2 == 0,
]


def _dat_data(m, rs, n, bits, mask):
    fn = _MASKS[mask]
    idx = 0
    col = n - 1
    up = True
    while col > 0:
        if col == 6:
            col -= 1
        rows = range(n - 1, -1, -1) if up else range(n)
        for r in rows:
            for c in (col, col - 1):
                if rs[r][c]:
                    continue
                b = bits[idx] if idx < len(bits) else 0
                idx += 1
                m[r][c] = b ^ (1 if fn(r, c) else 0)
        up = not up
        col -= 2


def _phat(m, n):
    p = 0
    for line in list(m) + [[m[r][c] for r in range(n)] for c in range(n)]:
        run, prev = 1, line[0]
        for x in line[1:]:
            if x == prev:
                run += 1
            else:
                if run >= 5:
                    p += 3 + (run - 5)
                run, prev = 1, x
        if run >= 5:
            p += 3 + (run - 5)
    for r in range(n - 1):
        for c in range(n - 1):
            s = m[r][c] + m[r][c + 1] + m[r + 1][c] + m[r + 1][c + 1]
            if s in (0, 4):
                p += 3
    pat1 = [1, 0, 1, 1, 1, 0, 1, 0, 0, 0, 0]
    pat2 = list(reversed(pat1))
    for line in list(m) + [[m[r][c] for r in range(n)] for c in range(n)]:
        for i in range(n - 10):
            seg = line[i:i + 11]
            if seg == pat1 or seg == pat2:
                p += 40
    dark = sum(sum(r) for r in m)
    p += 10 * (abs(dark * 100 // (n * n) - 50) // 5)
    return p


def tao_ma_tran(text):
    """Trả về ma trận 0/1 của mã QR, hoặc None nếu chuỗi quá dài."""
    try:
        payload = str(text or "").encode("utf-8")
    except Exception:
        return None
    if not payload:
        return None
    v = _chon_phien_ban(len(payload))
    if v is None:
        return None

    cws = _xen_khoi(_bit_stream(payload, v), v)
    bits = []
    for cw in cws:
        for k in range(7, -1, -1):
            bits.append((cw >> k) & 1)

    tot, best = None, None
    for mask in range(8):
        m, rs, n = _khung(v)
        _dat_version(m, n, v)
        _dat_data(m, rs, n, bits, mask)
        _dat_format(m, n, mask)
        p = _phat(m, n)
        if tot is None or p < tot:
            tot, best = p, m
    return best


def ve_svg(text, px=4, quiet=4):
    """Sinh thẻ <svg> nhúng trực tiếp vào HTML. Trả về "" nếu không tạo được."""
    m = tao_ma_tran(text)
    if not m:
        return ""
    n = len(m)
    size = (n + quiet * 2) * px
    o = ['<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" '
         'shape-rendering="crispEdges">' % (size, size),
         '<rect width="%d" height="%d" fill="#fff"/>' % (size, size)]
    for r in range(n):
        c = 0
        while c < n:
            if m[r][c]:
                c2 = c
                while c2 < n and m[r][c2]:
                    c2 += 1
                o.append('<rect x="%d" y="%d" width="%d" height="%d" fill="#000"/>'
                         % ((c + quiet) * px, (r + quiet) * px, (c2 - c) * px, px))
                c = c2
            else:
                c += 1
    o.append('</svg>')
    return "".join(o)
