"""cocotb testbench for NeithCore neith_ntt — bit-exact vs golden.ntt_cyclic.

Streams 256 coefficients into the engine, runs the multicycle forward NTT, reads
the 256 results back by address, and checks them against
golden.ntt_cyclic(vec, OMEGA) (q = 7681). Covers impulses, constants, ramps and
random vectors, including a back-to-back second transform.
"""
import os
import random
import sys

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, Timer

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "golden"))
import neith_mlkem as golden  # noqa: E402

Q = golden.Q
N = golden.N  # 256


async def reset(dut):
    dut.start.value = 0
    dut.mode.value = 0
    dut.nega.value = 0
    dut.in_valid.value = 0
    dut.in_data.value = 0
    dut.rd_addr.value = 0
    dut.rst_n.value = 0
    for _ in range(3):
        await RisingEdge(dut.clk)
    dut.rst_n.value = 1
    await RisingEdge(dut.clk)


async def run_ntt(dut, vec, mode=0, nega=0):
    # start pulse (engine -> LOAD), latch the transform direction + cyclic/negacyclic
    dut.start.value = 1
    dut.mode.value = mode
    dut.nega.value = nega
    dut.in_valid.value = 0
    await RisingEdge(dut.clk)
    dut.start.value = 0
    # stream 256 coefficients
    for j in range(N):
        dut.in_valid.value = 1
        dut.in_data.value = vec[j]
        await RisingEdge(dut.clk)
    dut.in_valid.value = 0
    # wait for completion
    for _ in range(2000):
        await RisingEdge(dut.clk)
        if dut.done.value == 1:
            break
    assert dut.done.value == 1, "engine did not assert done in time"
    # read results back by address (combinational)
    out = []
    for addr in range(N):
        dut.rd_addr.value = addr
        await Timer(1, units="ns")
        out.append(int(dut.out_data.value))
    return out


def inv_cyclic_ref(A):
    """Cyclic inverse: ntt_cyclic(A, OMEGA_INV) scaled by N_INV."""
    y = golden.ntt_cyclic(A, golden.OMEGA_INV)
    return [(y[i] * golden.N_INV) % Q for i in range(N)]


async def check_fwd(dut, vec):
    got = await run_ntt(dut, vec, mode=0)
    exp = golden.ntt_cyclic(vec, golden.OMEGA)
    assert got == exp, (
        f"forward NTT mismatch: "
        f"{next((i, got[i], exp[i]) for i in range(N) if got[i] != exp[i])}")


async def check_inv(dut, vec):
    got = await run_ntt(dut, vec, mode=1)
    exp = inv_cyclic_ref(vec)
    assert got == exp, (
        f"inverse NTT mismatch: "
        f"{next((i, got[i], exp[i]) for i in range(N) if got[i] != exp[i])}")


@cocotb.test()
async def test_directed_forward(dut):
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    await reset(dut)
    await check_fwd(dut, [5] + [0] * (N - 1))        # impulse
    await check_fwd(dut, [3] * N)                     # constant
    await check_fwd(dut, [(i * 37) % Q for i in range(N)])  # ramp
    await check_fwd(dut, [Q - 1] * N)                 # all max
    dut._log.info("neith_ntt: forward directed vectors verified bit-exact")


@cocotb.test()
async def test_random_forward(dut):
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    await reset(dut)
    rng = random.Random(0x117700)
    for _ in range(16):
        await check_fwd(dut, [rng.randrange(Q) for _ in range(N)])
    dut._log.info("neith_ntt: 16 random forward transforms verified bit-exact")


@cocotb.test()
async def test_inverse(dut):
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    await reset(dut)
    rng = random.Random(0x90D0C)
    for _ in range(16):
        await check_inv(dut, [rng.randrange(Q) for _ in range(N)])
    dut._log.info("neith_ntt: 16 random inverse transforms verified bit-exact")


@cocotb.test()
async def test_roundtrip(dut):
    """inverse(forward(a)) == a for random vectors — exercises both modes on the HW."""
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    await reset(dut)
    rng = random.Random(0x5EED)
    for _ in range(12):
        a = [rng.randrange(Q) for _ in range(N)]
        fwd = await run_ntt(dut, a, mode=0)
        rt = await run_ntt(dut, fwd, mode=1)
        assert rt == a, (
            f"roundtrip mismatch: "
            f"{next((i, rt[i], a[i]) for i in range(N) if rt[i] != a[i])}")
    dut._log.info("neith_ntt: 12 forward->inverse roundtrips recovered the input")


@cocotb.test()
async def test_negacyclic_forward(dut):
    """nega=1 forward must equal golden.ntt (psi pre-multiply + cyclic forward)."""
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    await reset(dut)
    rng = random.Random(0xACED)
    vecs = [[5] + [0] * (N - 1), [3] * N, [(i * 37) % Q for i in range(N)]]
    vecs += [[rng.randrange(Q) for _ in range(N)] for _ in range(16)]
    for vec in vecs:
        got = await run_ntt(dut, vec, mode=0, nega=1)
        exp = golden.ntt(vec)
        assert got == exp, (
            f"negacyclic forward mismatch: "
            f"{next((i, got[i], exp[i]) for i in range(N) if got[i] != exp[i])}")
    dut._log.info("neith_ntt: negacyclic forward (golden.ntt) verified bit-exact")


@cocotb.test()
async def test_negacyclic_inverse(dut):
    """nega=1 inverse must equal golden.intt (cyclic inverse + 1/N + psi^-i)."""
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    await reset(dut)
    rng = random.Random(0xBEEF)
    for _ in range(16):
        A = [rng.randrange(Q) for _ in range(N)]
        got = await run_ntt(dut, A, mode=1, nega=1)
        exp = golden.intt(A)
        assert got == exp, (
            f"negacyclic inverse mismatch: "
            f"{next((i, got[i], exp[i]) for i in range(N) if got[i] != exp[i])}")
    dut._log.info("neith_ntt: negacyclic inverse (golden.intt) verified bit-exact")


@cocotb.test()
async def test_negacyclic_polymul(dut):
    """The point of the negacyclic transform: intt(ntt(a)*ntt(b)) == schoolbook mod x^N+1."""
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    await reset(dut)
    rng = random.Random(0xF00D)
    for _ in range(8):
        a = [rng.randrange(Q) for _ in range(N)]
        b = [rng.randrange(Q) for _ in range(N)]
        A = await run_ntt(dut, a, mode=0, nega=1)
        B = await run_ntt(dut, b, mode=0, nega=1)
        C = [(A[i] * B[i]) % Q for i in range(N)]
        got = await run_ntt(dut, C, mode=1, nega=1)
        exp = golden.poly_mul_schoolbook(a, b)
        assert got == exp, (
            f"negacyclic poly-mul mismatch: "
            f"{next((i, got[i], exp[i]) for i in range(N) if got[i] != exp[i])}")
    dut._log.info("neith_ntt: HW negacyclic poly-mul matches schoolbook (mod x^256+1)")
