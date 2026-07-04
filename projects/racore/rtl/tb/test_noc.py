"""cocotb testbench for RaCore ra_noc_arbiter — bit-exact vs golden NocCrossbar."""
import os
import random
import sys

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, Timer

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "golden"))
import ra_soc as g  # noqa: E402

N = 4


@cocotb.test()
async def test_noc(dut):
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    dut.rst.value = 1
    dut.requests.value = 0
    dut.advance.value = 0
    for _ in range(2):
        await RisingEdge(dut.clk)
    dut.rst.value = 0
    await RisingEdge(dut.clk)

    ref = g.NocCrossbar(N)

    # --- directed round-robin proof (the case a naive "always last+1" arbiter
    # would get wrong): after granting master 0, only a FARTHER master requests,
    # so the grant must skip the idle master at last+1, not stall on it. ---
    async def grant(req_mask):
        dut.requests.value = req_mask
        dut.advance.value = 1
        await Timer(1, units="ns")
        gi = int(dut.grant_idx.value) if int(dut.grant_valid.value) else None
        await RisingEdge(dut.clk)
        await Timer(1, units="ns")
        return gi

    # all four request: classic round-robin cycles 1,2,3,0 (last starts at N-1=3)
    seq = [await grant(0b1111) for _ in range(4)]
    assert seq == [0, 1, 2, 3], f"round-robin order broken: {seq}"
    # now last=3; only master 2 requests (1<<2). last+1=0 is idle, so it must
    # skip 0/1 and grant 2 — this is exactly what the auditor doubted.
    assert (await grant(0b0100)) == 2, "arbiter failed to skip idle masters (round-robin bug)"
    # only master 1 requests while last=2 -> wrap past 3,0 to 1
    assert (await grant(0b0010)) == 1, "arbiter wrap-around broken"
    # keep the reference model in lockstep for the random phase below
    ref.arbitrate([True, True, True, True]); ref.arbitrate([True, True, True, True])
    ref.arbitrate([True, True, True, True]); ref.arbitrate([True, True, True, True])
    ref.arbitrate([False, False, True, False])
    ref.arbitrate([False, True, False, False])

    rng = random.Random(0x404C)

    for _ in range(4000):
        req = rng.getrandbits(N)
        dut.requests.value = req
        dut.advance.value = 1
        await Timer(1, units="ns")
        reqs = [(req >> i) & 1 == 1 for i in range(N)]
        exp = ref.arbitrate(reqs)              # None if no request, else index (commits)
        if exp is None:
            assert int(dut.grant_valid.value) == 0, f"req={req:04b}: expected no grant"
        else:
            assert int(dut.grant_valid.value) == 1
            assert int(dut.grant_idx.value) == exp, \
                f"req={req:04b}: grant {int(dut.grant_idx.value)}!={exp}"
        await RisingEdge(dut.clk)               # commit (advance high)
        await Timer(1, units="ns")              # let the packed-counter assign settle
        # check the committed grant counters match
        flat = int(dut.grants_flat.value)
        for i in range(N):
            cnt = (flat >> (32 * i)) & 0xFFFFFFFF
            assert cnt == ref.grants[i], f"grants[{i}]: {cnt}!={ref.grants[i]}"
    dut._log.info("ra_noc_arbiter verified bit-exact vs golden NocCrossbar")
