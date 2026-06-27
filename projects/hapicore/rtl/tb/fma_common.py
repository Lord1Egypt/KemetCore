"""Shared helpers for the bf16/fp16 fused-multiply-add cocotb testbenches.

Each format's RTL (hapi_bf16_fma / hapi_fp16_fma) is checked bit-exact against the
single-rounded golden fp_fma (exact rational a*b+c, one rounding). NaN compared by
class; the sign of zero IS checked.
"""
import os
import random
import sys

import numpy as np
from cocotb.triggers import Timer

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "golden"))
import hapi_fpu as golden  # noqa: E402

# (exp_w, mant_w, bias)
PARAMS = {"bf16": (8, 7, 127), "fp16": (5, 10, 15)}


def bits_to_f(u, fmt):
    if fmt == "bf16":
        return float(np.uint32(u << 16).view(np.float32))
    return float(np.uint16(u).view(np.float16))


def f_to_bits(f, fmt):
    if fmt == "bf16":
        return (int(np.float32(golden.round_bf16(f)).view(np.uint32)) >> 16) & 0xFFFF
    return int(np.float16(f).view(np.uint16))


def is_nan_bits(u, fmt):
    ew, mw, _ = PARAMS[fmt]
    exp = (u >> mw) & ((1 << ew) - 1)
    return exp == (1 << ew) - 1 and (u & ((1 << mw) - 1)) != 0


async def check(dut, fmt, ab, bb, cb):
    dut.a.value = ab
    dut.b.value = bb
    dut.c.value = cb
    await Timer(1, units="ns")
    got = int(dut.y.value)

    af, bf, cf = bits_to_f(ab, fmt), bits_to_f(bb, fmt), bits_to_f(cb, fmt)
    res = golden.fp_fma(af, bf, cf, fmt)
    if isinstance(res, float) and res != res:           # NaN
        assert is_nan_bits(got, fmt), (
            f"{fmt} {ab:04x}*{bb:04x}+{cb:04x}: got {got:04x}, expected NaN")
        return
    exp = f_to_bits(res, fmt)
    assert got == exp, (
        f"{fmt} {ab:04x}*{bb:04x}+{cb:04x}: got {got:04x} expected {exp:04x} "
        f"({af} * {bf} + {cf} = {res})")


CORNERS = {
    "bf16": [0x0000, 0x8000, 0x3F80, 0xBF80, 0x4000, 0xC000, 0x3F00, 0x3FC0,
             0x7F80, 0xFF80, 0x7FC0, 0x7FA0, 0x0001, 0x8001, 0x007F, 0x0080,
             0x7F7F, 0xFF7F, 0x4049, 0xC049, 0x3F2B, 0x4B00],
    "fp16": [0x0000, 0x8000, 0x3C00, 0xBC00, 0x4000, 0xC000, 0x3800, 0x3E00,
             0x7C00, 0xFC00, 0x7E00, 0x7D00, 0x0001, 0x8001, 0x03FF, 0x0400,
             0x7BFF, 0xFBFF, 0x4248, 0xC248, 0x3555, 0x6400],
}


def _emax(fmt):
    return (1 << PARAMS[fmt][0]) - 1


async def run_corners(dut, fmt):
    cs = CORNERS[fmt]
    addends = cs[:1] + cs[2:4] + cs[8:9] + cs[12:13] + cs[15:17]
    n = 0
    for a in cs:
        for b in cs:
            for cc in addends:
                await check(dut, fmt, a, b, cc)
                n += 1
    dut._log.info(f"{fmt} fma: {n} directed corner FMAs verified bit-exact")


async def run_random(dut, fmt, n, seed):
    rng = random.Random(seed)
    for _ in range(n):
        await check(dut, fmt, rng.getrandbits(16), rng.getrandbits(16),
                    rng.getrandbits(16))
    dut._log.info(f"{fmt} fma: {n} random FMAs verified bit-exact")


async def run_cancellation(dut, fmt, n, seed):
    """a*b chosen to nearly cancel c (exact -> +0 too)."""
    rng = random.Random(seed)
    ew, mw, _ = PARAMS[fmt]
    cnt = 0
    for _ in range(n):
        a = rng.getrandbits(16)
        b = rng.getrandbits(16)
        ea = (a >> mw) & ((1 << ew) - 1)
        eb = (b >> mw) & ((1 << ew) - 1)
        if ea in (0, _emax(fmt)) or eb in (0, _emax(fmt)):
            continue
        prod = golden.fp_mul(bits_to_f(a, fmt), bits_to_f(b, fmt), fmt)
        pb = f_to_bits(prod, fmt)
        cbits = (pb ^ 0x8000)
        cbits = (cbits & ~((1 << mw) - 1)) | ((cbits + rng.randint(-2, 2)) & ((1 << mw) - 1))
        await check(dut, fmt, a, b, cbits)
        await check(dut, fmt, a, b, pb ^ 0x8000)
        cnt += 2
    dut._log.info(f"{fmt} fma: {cnt} cancellation FMAs verified")


async def run_opposite_sign_tail(dut, fmt, n, seed):
    """c opposite-sign to a*b, swept far below it -> sticky-borrow path."""
    rng = random.Random(seed)
    ew, mw, _ = PARAMS[fmt]
    emax = _emax(fmt)
    cnt = 0
    for _ in range(n):
        a = rng.getrandbits(16)
        b = rng.getrandbits(16)
        ea = (a >> mw) & ((1 << ew) - 1)
        eb = (b >> mw) & ((1 << ew) - 1)
        if ea in (0, emax) or eb in (0, emax):
            continue
        prod = golden.fp_mul(bits_to_f(a, fmt), bits_to_f(b, fmt), fmt)
        pb = f_to_bits(prod, fmt)
        pe = (pb >> mw) & (emax)
        ce = pe - rng.randint(1, mw + 6)
        if ce <= 0 or ce >= emax:
            continue
        cbits = ((pb ^ 0x8000) & 0x8000) | (ce << mw) | (rng.getrandbits(mw))
        await check(dut, fmt, a, b, cbits)
        cnt += 1
    dut._log.info(f"{fmt} fma: {cnt} opposite-sign far-tail FMAs verified")


async def run_subnormal_overflow(dut, fmt):
    cs = CORNERS[fmt]
    pool = [cs[12], cs[14], cs[15], cs[16], cs[2], cs[4], cs[3], cs[8], 0x0002]
    n = 0
    for a in pool:
        for b in pool:
            for cc in (0x0000, cs[12], cs[16], cs[2]):
                await check(dut, fmt, a, b, cc)
                await check(dut, fmt, a ^ 0x8000, b, cc)
                n += 2
    dut._log.info(f"{fmt} fma: {n} subnormal/overflow edge FMAs verified")
