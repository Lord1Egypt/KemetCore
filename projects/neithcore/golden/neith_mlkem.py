"""NeithCore golden reference — NTT + module-LWE KEM (Kyber-style).

Phase 0 scope:
  * A negacyclic NTT over Z_q (ring x^n + 1), with an O(n log n) fast transform
    cross-checked against an O(n^2) naive transform and against schoolbook
    polynomial multiplication.
  * A Kyber-style module-LWE KEM (keygen/encaps/decaps) built on that NTT.

NOTE: this is a *reference model*, not FIPS-203 certified ML-KEM. It uses an
NTT-friendly modulus (q = 7681) so a full negacyclic NTT exists; exact ML-KEM
parameters (q = 3329, incomplete NTT, ciphertext compression) arrive with RTL.
"""
import hashlib
import random

N = 256
Q = 7681          # NTT-friendly: q-1 = 7680 = 2^9 * 15, so a 2N-th root exists
K = 2             # module rank (Kyber-512-like)
ETA = 2           # centered-binomial noise parameter


def _find_psi(n, q):
    """Primitive 2n-th root of unity: psi^n == -1 (mod q)."""
    for c in range(2, q):
        if pow(c, n, q) == q - 1:
            return c
    raise RuntimeError("no 2n-th root of unity for these params")


PSI = _find_psi(N, Q)
OMEGA = PSI * PSI % Q                 # primitive n-th root
PSI_INV = pow(PSI, Q - 2, Q)
OMEGA_INV = pow(OMEGA, Q - 2, Q)
N_INV = pow(N, Q - 2, Q)
_PSI_POW = [pow(PSI, i, Q) for i in range(N)]
_PSI_INV_POW = [pow(PSI_INV, i, Q) for i in range(N)]


# --------------------------------------------------------------------------- #
# NTT
# --------------------------------------------------------------------------- #
def _bitrev(a):
    n = len(a)
    a = a[:]
    j = 0
    for i in range(1, n):
        bit = n >> 1
        while j & bit:
            j ^= bit
            bit >>= 1
        j |= bit
        if i < j:
            a[i], a[j] = a[j], a[i]
    return a


def ntt_cyclic(a, root):
    """Iterative radix-2 cyclic NTT: X[j] = sum_i a[i] root^(ij) mod Q."""
    n = len(a)
    A = _bitrev(a)
    length = 2
    while length <= n:
        wlen = pow(root, n // length, Q)
        for i in range(0, n, length):
            w = 1
            half = length // 2
            for k in range(half):
                u = A[i + k]
                v = A[i + k + half] * w % Q
                A[i + k] = (u + v) % Q
                A[i + k + half] = (u - v) % Q
                w = w * wlen % Q
        length <<= 1
    return A


def ntt_cyclic_naive(a, root):
    n = len(a)
    return [sum(a[i] * pow(root, i * j, Q) for i in range(n)) % Q for j in range(n)]


def ntt(a):
    """Forward negacyclic NTT (fast)."""
    pre = [a[i] * _PSI_POW[i] % Q for i in range(N)]
    return ntt_cyclic(pre, OMEGA)


def intt(A):
    """Inverse negacyclic NTT (fast)."""
    tmp = ntt_cyclic(A, OMEGA_INV)
    return [tmp[i] * N_INV % Q * _PSI_INV_POW[i] % Q for i in range(N)]


def pointwise(A, B):
    """NTT-domain pointwise modular multiply: C[i] = A[i]*B[i] mod Q. This is the middle
    stage of poly_mul_ntt (ntt -> pointwise -> intt)."""
    return [(A[i] * B[i]) % Q for i in range(len(A))]


def poly_mul_ntt(a, b):
    A, B = ntt(a), ntt(b)
    C = pointwise(A, B)
    return intt(C)


def poly_mul_schoolbook(a, b):
    """Negacyclic (mod x^N + 1) schoolbook multiplication."""
    res = [0] * (2 * N)
    for i in range(N):
        if a[i] == 0:
            continue
        for j in range(N):
            res[i + j] += a[i] * b[j]
    out = [0] * N
    for i in range(N):
        out[i] = (res[i] - res[i + N]) % Q
    return out


# --------------------------------------------------------------------------- #
# Polynomial / vector helpers
# --------------------------------------------------------------------------- #
def padd(a, b):
    return [(x + y) % Q for x, y in zip(a, b)]


def psub(a, b):
    return [(x - y) % Q for x, y in zip(a, b)]


def _cbd(rng):
    """Centered binomial noise polynomial in [-ETA, ETA]."""
    out = [0] * N
    for i in range(N):
        a_bits = [rng.getrandbits(1) for _ in range(ETA)]
        b_bits = [rng.getrandbits(1) for _ in range(ETA)]
        out[i] = _cbd_coeff(a_bits, b_bits)
    return out


def _cbd_coeff(a_bits, b_bits):
    """One CBD coefficient from 2*ETA bits: (popcount(a) - popcount(b)) mod Q."""
    return (sum(a_bits) - sum(b_bits)) % Q


def _uniform(rng):
    return [rng.randrange(Q) for _ in range(N)]


# --------------------------------------------------------------------------- #
# Module-LWE KEM
# --------------------------------------------------------------------------- #
def keygen(rng):
    A = [[_uniform(rng) for _ in range(K)] for _ in range(K)]   # K x K matrix of polys
    s = [_cbd(rng) for _ in range(K)]
    e = [_cbd(rng) for _ in range(K)]
    t = []
    for i in range(K):
        acc = [0] * N
        for j in range(K):
            acc = padd(acc, poly_mul_ntt(A[i][j], s[j]))
        t.append(padd(acc, e[i]))
    pk = (A, t)
    sk = s
    return pk, sk


def _encode(bits):
    return [(1 if bits[i] else 0) * (Q // 2) for i in range(N)]


def _decode(poly):
    q4, q34 = Q // 4, 3 * Q // 4
    return [1 if q4 < (c % Q) < q34 else 0 for c in poly]


def encrypt(pk, bits, rng):
    A, t = pk
    r = [_cbd(rng) for _ in range(K)]
    e1 = [_cbd(rng) for _ in range(K)]
    e2 = _cbd(rng)
    # u = A^T r + e1
    u = []
    for i in range(K):
        acc = [0] * N
        for j in range(K):
            acc = padd(acc, poly_mul_ntt(A[j][i], r[j]))
        u.append(padd(acc, e1[i]))
    # v = t^T r + e2 + encode(m)
    v = [0] * N
    for j in range(K):
        v = padd(v, poly_mul_ntt(t[j], r[j]))
    v = padd(padd(v, e2), _encode(bits))
    return (u, v)


def decrypt(sk, ct):
    s = sk
    u, v = ct
    su = [0] * N
    for j in range(K):
        su = padd(su, poly_mul_ntt(s[j], u[j]))
    m = psub(v, su)
    return _decode(m)


def encaps(pk, rng):
    bits = [rng.getrandbits(1) for _ in range(N)]
    ct = encrypt(pk, bits, rng)
    key = hashlib.sha256(bytes(bits)).digest()
    return ct, key


def decaps(sk, ct):
    bits = decrypt(sk, ct)
    return hashlib.sha256(bytes(bits)).digest()


# ---- ciphertext compression (ML-KEM Compress_q / Decompress_q) ---------------- #
# Lossy rounding of coefficients to d bits, exactly as in FIPS-203 but at this
# module's NTT-friendly Q=7681. These are the bit-exact goldens the neith_compress
# / neith_decompress RTL match.

def compress(x, d):
    """Compress_q(x, d) = round(2^d / Q * x) mod 2^d, for a coefficient x in
    [0, Q). Rounding is round-half-up via integer floor((2^d*x + Q//2) / Q)."""
    return (((x << d) + (Q // 2)) // Q) & ((1 << d) - 1)


def decompress(y, d):
    """Decompress_q(y, d) = round(Q / 2^d * y), for y in [0, 2^d). Rounding is
    round-half-up via floor((Q*y + 2^(d-1)) / 2^d) = (Q*y + 2^(d-1)) >> d."""
    return (Q * y + (1 << (d - 1))) >> d
