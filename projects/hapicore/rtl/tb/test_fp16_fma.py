"""cocotb testbench for hapi_fp16_fma — bit-exact vs single-rounded golden fp_fma."""
import cocotb

import fma_common as fc

FMT = "fp16"


@cocotb.test()
async def test_corners(dut):
    await fc.run_corners(dut, FMT)


@cocotb.test()
async def test_random(dut):
    await fc.run_random(dut, FMT, 25000, 0xF16FA0)


@cocotb.test()
async def test_cancellation(dut):
    await fc.run_cancellation(dut, FMT, 12000, 0xF16CA7)


@cocotb.test()
async def test_opposite_sign_tail(dut):
    await fc.run_opposite_sign_tail(dut, FMT, 16000, 0xF16077)


@cocotb.test()
async def test_subnormal_and_overflow(dut):
    await fc.run_subnormal_overflow(dut, FMT)
