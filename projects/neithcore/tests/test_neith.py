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
