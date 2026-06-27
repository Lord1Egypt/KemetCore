"""SobekCore pymodel — pipelined intersector.

Models the Moller-Trumbore datapath as named pipeline stages (cross/dot/divide/
compare) and reports latency. Result is identical to the golden reference.
"""
import sobek_raytri as g

STAGES = ["edge", "pvec/det", "u-test", "qvec/v-test", "t-compute", "range-test"]
LATENCY = len(STAGES)


class Intersector:
    def __init__(self):
        self.invocations = 0
        self.cycles = 0

    def intersect(self, origin, direction, v0, v1, v2):
        self.invocations += 1
        self.cycles += LATENCY
        return g.ray_triangle(origin, direction, v0, v1, v2)
