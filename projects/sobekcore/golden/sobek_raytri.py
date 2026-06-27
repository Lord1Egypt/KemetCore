"""SobekCore golden reference — Moller-Trumbore ray-triangle intersection.

ray_triangle(origin, direction, v0, v1, v2) -> hit record or None.
Returns t (distance along the ray) and barycentric coords (u, v, w), with w = 1-u-v.
Watertight in the sense of consistent edge handling; uses a small epsilon for the
parallel test.
"""
import numpy as np

EPS = 1e-7


def ray_triangle(origin, direction, v0, v1, v2):
    o = np.asarray(origin, np.float64)
    d = np.asarray(direction, np.float64)
    v0 = np.asarray(v0, np.float64)
    v1 = np.asarray(v1, np.float64)
    v2 = np.asarray(v2, np.float64)

    e1 = v1 - v0
    e2 = v2 - v0
    pvec = np.cross(d, e2)
    det = np.dot(e1, pvec)
    if abs(det) < EPS:
        return None                      # ray parallel to triangle plane
    inv_det = 1.0 / det
    tvec = o - v0
    u = np.dot(tvec, pvec) * inv_det
    if u < 0.0 or u > 1.0:
        return None
    qvec = np.cross(tvec, e1)
    v = np.dot(d, qvec) * inv_det
    if v < 0.0 or u + v > 1.0:
        return None
    t = np.dot(e2, qvec) * inv_det
    if t < EPS:
        return None                      # intersection behind the ray origin
    return {"t": t, "u": u, "v": v, "w": 1.0 - u - v}
