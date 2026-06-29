import random

import neith_mlkem as g
from neith_ntt_model import NttPipeline, LOG2N, BUTTERFLIES_PER_STAGE


def test_ntt_roundtrip():
    rng = random.Random(0)
    for _ in range(20):
        a = [rng.randrange(g.Q) for _ in range(g.N)]
        assert g.intt(g.ntt(a)) == a


def test_ntt_fast_equals_naive():
    rng = random.Random(1)
    a = [rng.randrange(g.Q) for _ in range(g.N)]
    assert g.ntt_cyclic(a, g.OMEGA) == g.ntt_cyclic_naive(a, g.OMEGA)


def test_ntt_polymult():
    rng = random.Random(2)
    for _ in range(20):
        a = [rng.randrange(g.Q) for _ in range(g.N)]
        b = [rng.randrange(g.Q) for _ in range(g.N)]
        assert g.poly_mul_ntt(a, b) == g.poly_mul_schoolbook(a, b)


def test_pointwise():
    rng = random.Random(7)
    for _ in range(20):
        A = [rng.randrange(g.Q) for _ in range(g.N)]
        B = [rng.randrange(g.Q) for _ in range(g.N)]
        assert g.pointwise(A, B) == [(A[i] * B[i]) % g.Q for i in range(g.N)]
    # pointwise is exactly the middle of poly_mul_ntt
    a = [rng.randrange(g.Q) for _ in range(g.N)]
    b = [rng.randrange(g.Q) for _ in range(g.N)]
    assert g.intt(g.pointwise(g.ntt(a), g.ntt(b))) == g.poly_mul_ntt(a, b)


def test_polyaddsub():
    rng = random.Random(9)
    for _ in range(20):
        a = [rng.randrange(g.Q) for _ in range(g.N)]
        b = [rng.randrange(g.Q) for _ in range(g.N)]
        assert g.padd(a, b) == [(a[i] + b[i]) % g.Q for i in range(g.N)]
        assert g.psub(a, b) == [(a[i] - b[i]) % g.Q for i in range(g.N)]


def test_msgcodec():
    rng = random.Random(11)
    for _ in range(20):
        bits = [rng.getrandbits(1) for _ in range(g.N)]
        assert g._decode(g._encode(bits)) == bits          # round trip
    # decode threshold: q4 and 3q4 are excluded (strict)
    q4, q34 = g.Q // 4, 3 * g.Q // 4
    poly = [q4, q4 + 1, q34 - 1, q34] + [0] * (g.N - 4)
    assert g._decode(poly)[:4] == [0, 1, 1, 0]


def test_kem_correctness():
    for seed in range(30):
        rng = random.Random(seed)
        pk, sk = g.keygen(rng)
        ct, key_enc = g.encaps(pk, rng)
        key_dec = g.decaps(sk, ct)
        assert key_enc == key_dec, f"KEM mismatch at seed {seed}"


def test_pymodel_ntt():
    rng = random.Random(3)
    a = [rng.randrange(g.Q) for _ in range(g.N)]
    p = NttPipeline()
    assert p.forward(a) == g.ntt(a)
    assert p.stages == LOG2N
    assert p.butterflies == LOG2N * BUTTERFLIES_PER_STAGE
