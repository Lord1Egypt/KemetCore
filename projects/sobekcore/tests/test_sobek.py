import numpy as np

import sobek_raytri as g
from sobek_raytri_model import Intersector, LATENCY

# unit triangle in the z=0 plane
V0 = [0.0, 0.0, 0.0]
V1 = [1.0, 0.0, 0.0]
V2 = [0.0, 1.0, 0.0]


def test_hit_center():
    # ray from above the centroid, pointing down
    hit = g.ray_triangle([0.25, 0.25, 1.0], [0, 0, -1], V0, V1, V2)
    assert hit is not None
    assert np.isclose(hit["t"], 1.0)
    assert np.isclose(hit["u"], 0.25) and np.isclose(hit["v"], 0.25)


def test_miss():
    hit = g.ray_triangle([2.0, 2.0, 1.0], [0, 0, -1], V0, V1, V2)
    assert hit is None


def test_parallel():
    # ray travelling in-plane never hits
    hit = g.ray_triangle([0.25, 0.25, 1.0], [1, 0, 0], V0, V1, V2)
    assert hit is None


def test_behind_origin():
    # triangle is behind the ray (ray points up, away from z=0)
    hit = g.ray_triangle([0.25, 0.25, 1.0], [0, 0, 1], V0, V1, V2)
    assert hit is None


def test_barycentric():
    hit = g.ray_triangle([0.1, 0.2, 1.0], [0, 0, -1], V0, V1, V2)
    assert hit is not None
    for c in ("u", "v", "w"):
        assert -1e-9 <= hit[c] <= 1.0 + 1e-9
    assert np.isclose(hit["u"] + hit["v"] + hit["w"], 1.0)


def test_pymodel_equals_golden():
    it = Intersector()
    a = it.intersect([0.25, 0.25, 1.0], [0, 0, -1], V0, V1, V2)
    b = g.ray_triangle([0.25, 0.25, 1.0], [0, 0, -1], V0, V1, V2)
    assert a == b
    assert it.cycles == LATENCY


def test_fp32_dot3_order_and_bits():
    """sobek_fp32.dot3 is the fixed-order fp32 datapath the sobek_dot3 RTL
    matches: p_i = a_i*b_i, then ((p0+p1)+p2), all round-to-nearest fp32."""
    import sobek_fp32 as f

    # exact small-integer case
    assert f.dot3([1.0, 2.0, 3.0], [4.0, 5.0, 6.0]) == np.float32(32.0)
    # matches an explicit left-to-right fp32 evaluation
    a, b = [0.1, 0.2, 0.3], [0.4, 0.5, 0.6]
    p0 = np.float32(a[0]) * np.float32(b[0])
    p1 = np.float32(a[1]) * np.float32(b[1])
    p2 = np.float32(a[2]) * np.float32(b[2])
    expect = np.float32(np.float32(p0 + p1) + p2)
    assert f.dot3(a, b) == expect
    # bit round-trip helpers are consistent
    for x in (0.0, 1.0, -3.5, 1e20, -1e-20):
        assert f.frombits(f.bits(x)) == np.float32(x)
    # dot3_bits agrees with dot3 on patterns
    ab = [f.bits(v) for v in a]
    bb = [f.bits(v) for v in b]
    assert f.dot3_bits(ab, bb) == f.bits(expect)
