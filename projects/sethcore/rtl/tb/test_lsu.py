"""cocotb testbench for SethCore seth_lsu — bit-exact vs golden load/store format."""
import os
import random
import sys

import cocotb
from cocotb.triggers import Timer

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "golden"))
import seth_rv32im as golden  # noqa: E402

LOADS = [0x0, 0x1, 0x2, 0x4, 0x5]
STORES = [0x0, 0x1, 0x2]


async def check(dut, f3, addr_lo, mem_word, store_data):
    dut.funct3.value = f3
    dut.addr_lo.value = addr_lo
    dut.mem_word.value = mem_word
    dut.store_data.value = store_data
    await Timer(1, units="ns")
    if f3 in LOADS:
        exp = golden.load_format(f3, addr_lo, mem_word)
        assert int(dut.load_data.value) == exp, \
            f"load f3={f3} off={addr_lo} w={mem_word:08x}: {int(dut.load_data.value):08x}!={exp:08x}"
    if f3 in STORES:
        sw, ws = golden.store_merge(f3, addr_lo, mem_word, store_data)
        assert int(dut.store_word.value) == sw, \
            f"store f3={f3} off={addr_lo} w={mem_word:08x} d={store_data:08x}: {int(dut.store_word.value):08x}!={sw:08x}"
        assert int(dut.wstrb.value) == ws, \
            f"wstrb f3={f3} off={addr_lo}: {int(dut.wstrb.value):04b}!={ws:04b}"


@cocotb.test()
async def test_lsu(dut):
    corners = [0, 0xFFFFFFFF, 0x80808080, 0x01020304, 0xDEADBEEF, 0x00FF00FF]
    for f3 in sorted(set(LOADS + STORES)):
        for off in range(4):
            for w in corners:
                for d in corners:
                    await check(dut, f3, off, w, d)
    for _ in range(8000):
        f3 = random.choice(LOADS + STORES)
        await check(dut, f3, random.randint(0, 3),
                    random.getrandbits(32), random.getrandbits(32))
    dut._log.info("seth_lsu verified bit-exact vs golden load_format/store_merge")
