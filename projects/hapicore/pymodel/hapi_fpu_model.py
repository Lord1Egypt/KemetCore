"""HapiCore pymodel — cycle-level FPU pipeline (latency model).

Wraps the golden math and tracks pipeline latency so the cycle behaviour of the
future RTL is specified here. Values are bit-identical to the golden reference.
"""
import hapi_fpu as g

LATENCY = {"add": 2, "sub": 2, "mul": 2, "fma": 2, "cmp": 1, "div": 12, "sqrt": 14}


class FpuPipeline:
    def __init__(self, fmt="fp32"):
        self.fmt = fmt
        self.cycles = 0

    def _tick(self, op):
        self.cycles += LATENCY[op]

    def add(self, a, b):
        self._tick("add")
        return g.fp_add(a, b, self.fmt)

    def sub(self, a, b):
        self._tick("sub")
        return g.fp_sub(a, b, self.fmt)

    def mul(self, a, b):
        self._tick("mul")
        return g.fp_mul(a, b, self.fmt)

    def fma(self, a, b, c):
        self._tick("fma")
        return g.fp_fma(a, b, c, self.fmt)

    def cmp(self, a, b):
        self._tick("cmp")
        return g.fp_cmp(a, b, self.fmt)
