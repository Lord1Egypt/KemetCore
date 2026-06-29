"""AnubisCore golden reference — SHA-256 and SHA-3 (Keccak) in pure Python.

No hashlib in the implementation — these are independent from-scratch references
(hashlib is only used in the tests as the known-correct oracle). Optional
per-round callbacks let the pymodel count rounds/permutations.
"""
import struct

MASK64 = (1 << 64) - 1

# --------------------------------------------------------------------------- #
# SHA-256
# --------------------------------------------------------------------------- #
_K256 = [
    0x428a2f98, 0x71374491, 0xb5c0fbcf, 0xe9b5dba5, 0x3956c25b, 0x59f111f1,
    0x923f82a4, 0xab1c5ed5, 0xd807aa98, 0x12835b01, 0x243185be, 0x550c7dc3,
    0x72be5d74, 0x80deb1fe, 0x9bdc06a7, 0xc19bf174, 0xe49b69c1, 0xefbe4786,
    0x0fc19dc6, 0x240ca1cc, 0x2de92c6f, 0x4a7484aa, 0x5cb0a9dc, 0x76f988da,
    0x983e5152, 0xa831c66d, 0xb00327c8, 0xbf597fc7, 0xc6e00bf3, 0xd5a79147,
    0x06ca6351, 0x14292967, 0x27b70a85, 0x2e1b2138, 0x4d2c6dfc, 0x53380d13,
    0x650a7354, 0x766a0abb, 0x81c2c92e, 0x92722c85, 0xa2bfe8a1, 0xa81a664b,
    0xc24b8b70, 0xc76c51a3, 0xd192e819, 0xd6990624, 0xf40e3585, 0x106aa070,
    0x19a4c116, 0x1e376c08, 0x2748774c, 0x34b0bcb5, 0x391c0cb3, 0x4ed8aa4a,
    0x5b9cca4f, 0x682e6ff3, 0x748f82ee, 0x78a5636f, 0x84c87814, 0x8cc70208,
    0x90befffa, 0xa4506ceb, 0xbef9a3f7, 0xc67178f2,
]


def _rotr32(x, n):
    return ((x >> n) | (x << (32 - n))) & 0xFFFFFFFF


def sha256(data, on_round=None):
    h = [0x6a09e667, 0xbb67ae85, 0x3c6ef372, 0xa54ff53a,
         0x510e527f, 0x9b05688c, 0x1f83d9ab, 0x5be0cd19]
    msg = bytearray(data)
    ml = (8 * len(data)) & ((1 << 64) - 1)
    msg.append(0x80)
    while len(msg) % 64 != 56:
        msg.append(0x00)
    msg += struct.pack(">Q", ml)

    for off in range(0, len(msg), 64):
        w = list(struct.unpack(">16L", msg[off:off + 64]))
        for t in range(16, 64):
            s0 = _rotr32(w[t - 15], 7) ^ _rotr32(w[t - 15], 18) ^ (w[t - 15] >> 3)
            s1 = _rotr32(w[t - 2], 17) ^ _rotr32(w[t - 2], 19) ^ (w[t - 2] >> 10)
            w.append((w[t - 16] + s0 + w[t - 7] + s1) & 0xFFFFFFFF)
        a, b, c, d, e, f, g_, hh = h
        for t in range(64):
            S1 = _rotr32(e, 6) ^ _rotr32(e, 11) ^ _rotr32(e, 25)
            ch = (e & f) ^ (~e & g_)
            t1 = (hh + S1 + ch + _K256[t] + w[t]) & 0xFFFFFFFF
            S0 = _rotr32(a, 2) ^ _rotr32(a, 13) ^ _rotr32(a, 22)
            maj = (a & b) ^ (a & c) ^ (b & c)
            t2 = (S0 + maj) & 0xFFFFFFFF
            hh, g_, f, e, d, c, b, a = g_, f, e, (d + t1) & 0xFFFFFFFF, c, b, a, (t1 + t2) & 0xFFFFFFFF
            if on_round is not None:
                on_round(t, (a, b, c, d, e, f, g_, hh))
        h = [(x + y) & 0xFFFFFFFF for x, y in zip(h, (a, b, c, d, e, f, g_, hh))]
    return b"".join(struct.pack(">L", x) for x in h)


# --------------------------------------------------------------------------- #
# SHA-3 / Keccak-f[1600]
# --------------------------------------------------------------------------- #
_RC = [
    0x0000000000000001, 0x0000000000008082, 0x800000000000808A, 0x8000000080008000,
    0x000000000000808B, 0x0000000080000001, 0x8000000080008081, 0x8000000000008009,
    0x000000000000008A, 0x0000000000000088, 0x0000000080008009, 0x000000008000000A,
    0x000000008000808B, 0x800000000000008B, 0x8000000000008089, 0x8000000000008003,
    0x8000000000008002, 0x8000000000000080, 0x000000000000800A, 0x800000008000000A,
    0x8000000080008081, 0x8000000000008080, 0x0000000080000001, 0x8000000080008008,
]
_OFF = [
    [0, 36, 3, 41, 18],
    [1, 44, 10, 45, 2],
    [62, 6, 43, 15, 61],
    [28, 55, 25, 21, 56],
    [27, 20, 39, 8, 14],
]


def _rol64(v, n):
    n %= 64
    return ((v << n) | (v >> (64 - n))) & MASK64


def keccak_f1600(A, on_round=None):
    for rnd in range(24):
        C = [A[x][0] ^ A[x][1] ^ A[x][2] ^ A[x][3] ^ A[x][4] for x in range(5)]
        D = [C[(x - 1) % 5] ^ _rol64(C[(x + 1) % 5], 1) for x in range(5)]
        for x in range(5):
            for y in range(5):
                A[x][y] ^= D[x]
        B = [[0] * 5 for _ in range(5)]
        for x in range(5):
            for y in range(5):
                B[y][(2 * x + 3 * y) % 5] = _rol64(A[x][y], _OFF[x][y])
        for x in range(5):
            for y in range(5):
                A[x][y] = B[x][y] ^ ((~B[(x + 1) % 5][y]) & B[(x + 2) % 5][y])
        A[0][0] ^= _RC[rnd]
        if on_round is not None:
            on_round(rnd)
    return A


def sha3_384(data, on_round=None):
    rate = 104  # bytes (832 bits); capacity 768
    A = [[0] * 5 for _ in range(5)]
    padlen = rate - (len(data) % rate)
    pad = bytearray(padlen)
    pad[0] ^= 0x06
    pad[-1] ^= 0x80
    msg = bytes(data) + bytes(pad)
    for off in range(0, len(msg), rate):
        block = msg[off:off + rate]
        for i in range(rate // 8):
            lane = int.from_bytes(block[i * 8:i * 8 + 8], "little")
            A[i % 5][i // 5] ^= lane
        keccak_f1600(A, on_round=on_round)
    out = bytearray()
    while len(out) < 48:
        for i in range(rate // 8):
            out += A[i % 5][i // 5].to_bytes(8, "little")
            if len(out) >= 48:
                break
        if len(out) < 48:
            keccak_f1600(A, on_round=on_round)
    return bytes(out[:48])


def sha3_512(data, on_round=None):
    rate = 72  # bytes (576 bits); capacity 1024
    A = [[0] * 5 for _ in range(5)]
    padlen = rate - (len(data) % rate)
    pad = bytearray(padlen)
    pad[0] ^= 0x06
    pad[-1] ^= 0x80
    msg = bytes(data) + bytes(pad)
    for off in range(0, len(msg), rate):
        block = msg[off:off + rate]
        for i in range(rate // 8):
            lane = int.from_bytes(block[i * 8:i * 8 + 8], "little")
            A[i % 5][i // 5] ^= lane
        keccak_f1600(A, on_round=on_round)
    out = bytearray()
    while len(out) < 64:
        for i in range(rate // 8):
            out += A[i % 5][i // 5].to_bytes(8, "little")
            if len(out) >= 64:
                break
        if len(out) < 64:
            keccak_f1600(A, on_round=on_round)
    return bytes(out[:64])


def sha3_256(data, on_round=None):
    rate = 136  # bytes (1088 bits); capacity 512
    A = [[0] * 5 for _ in range(5)]
    padlen = rate - (len(data) % rate)
    pad = bytearray(padlen)
    pad[0] ^= 0x06
    pad[-1] ^= 0x80
    msg = bytes(data) + bytes(pad)
    for off in range(0, len(msg), rate):
        block = msg[off:off + rate]
        for i in range(rate // 8):
            lane = int.from_bytes(block[i * 8:i * 8 + 8], "little")
            A[i % 5][i // 5] ^= lane
        keccak_f1600(A, on_round=on_round)
    out = bytearray()
    while len(out) < 32:
        for i in range(rate // 8):
            out += A[i % 5][i // 5].to_bytes(8, "little")
            if len(out) >= 32:
                break
        if len(out) < 32:
            keccak_f1600(A, on_round=on_round)
    return bytes(out[:32])
