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


def test_cbd_coeff():
    # ETA=2: out in {0,1,2,Q-1,Q-2} per (a_bits, b_bits)
    assert g._cbd_coeff([0, 0], [0, 0]) == 0
    assert g._cbd_coeff([1, 1], [0, 0]) == 2
    assert g._cbd_coeff([0, 0], [1, 1]) == (g.Q - 2)
    assert g._cbd_coeff([1, 0], [0, 1]) == 0
    # _cbd uses _cbd_coeff and stays in the centered range
    import random as _r
    noise = g._cbd(_r.Random(3))
    assert all(c in (0, 1, 2, g.Q - 1, g.Q - 2) for c in noise)


def test_polymul_pipeline():
    # the hardware pipeline (ntt -> pointwise -> intt) equals both golden multipliers
    rng = random.Random(13)
    for _ in range(20):
        a = [rng.randrange(g.Q) for _ in range(g.N)]
        b = [rng.randrange(g.Q) for _ in range(g.N)]
        ref = g.poly_mul_schoolbook(a, b)
        assert g.intt(g.pointwise(g.ntt(a), g.ntt(b))) == ref
        assert g.poly_mul_ntt(a, b) == ref


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


def test_compress_decompress_roundtrip():
    """ML-KEM Compress_q/Decompress_q at Q=7681: compress maps [0,Q)->[0,2^d),
    decompress is its round-half-up inverse, and the round-trip error is bounded
    by ceil(Q/2^d) (the analysis bound that keeps decryption correct)."""
    import neith_mlkem as g

    # exact known values
    assert g.compress(0, 4) == 0 and g.decompress(0, 4) == 0
    assert g.decompress(1, 1) == (g.Q + 1) // 2          # round(Q/2)
    for d in (1, 4, 5, 10, 11):
        lim = 1 << d
        # compress lands in range
        for x in (0, 1, g.Q // 2, g.Q - 1):
            c = g.compress(x, d)
            assert 0 <= c < lim
        # decompress lands in the ring, and round-trips within the compression bound
        bound = (g.Q + lim - 1) // lim          # ceil(Q / 2^d)
        for x in range(0, g.Q, max(1, g.Q // 97)):
            c = g.compress(x, d)
            r = g.decompress(c, d)
            assert 0 <= r < g.Q
            diff = min((r - x) % g.Q, (x - r) % g.Q)
            assert diff <= bound, f"d={d} x={x}: round-trip err {diff} > {bound}"
