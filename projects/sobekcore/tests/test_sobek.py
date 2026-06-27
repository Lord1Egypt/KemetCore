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
