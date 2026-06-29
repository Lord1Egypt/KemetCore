import struct

import numpy as np

import ra_soc as r
from ra_soc_model import KaiAxpy, host_axpy, KAI_COUNT


def test_kai_conformance():
    scratch = r.Scratchpad()
    dev = KaiAxpy(scratch)
    # every mandatory KAI register must be readable
    for off in r.MANDATORY_REGS:
        _ = dev.mmio_read(off)
    # ID register must carry the KMT magic (low 24 bits) and the block id (top byte)
    idv = dev.mmio_read(r.KAI_ID)
    assert (idv & 0xFFFFFF) == r.KAI_MAGIC
    assert (idv >> 24) == KaiAxpy.BLOCK_ID


def test_kai_status_lifecycle():
    scratch = r.Scratchpad()
    dev = KaiAxpy(scratch)
    assert dev.mmio_read(r.KAI_STATUS) == 0
    scratch.write(0x100, struct.pack("<2f", 1.0, 2.0))
    scratch.write(0x200, struct.pack("<2f", 3.0, 4.0))
    dev.mmio_write(r.KAI_SRC, 0x100)
    dev.mmio_write(r.KAI_DST, 0x200)
    dev.mmio_write(KAI_COUNT, 2)
    dev.mmio_write(0x040, struct.unpack("<I", struct.pack("<f", 2.0))[0])
    dev.mmio_write(r.KAI_CTRL, r.CTRL_GO)
    assert dev.mmio_read(r.KAI_STATUS) & r.STATUS_DONE


def test_dma_2d():
    scratch = r.Scratchpad()
    dma = r.Dma(scratch)
    # source: 3 rows of 4 bytes, stride 8 (gaps); dst packed stride 4
    for i in range(3):
        scratch.write(0x100 + i * 8, bytes([i + 1, i + 1, i + 1, i + 1]))
    dma.copy_2d(0x100, 0x500, rows=3, row_bytes=4, src_stride=8, dst_stride=4)
    assert scratch.read(0x500, 12) == bytes([1, 1, 1, 1, 2, 2, 2, 2, 3, 3, 3, 3])
    assert dma.bytes_moved == 12


def test_noc_arbitration():
    xbar = r.NocCrossbar(n_masters=2)
    # both masters always request -> round-robin alternates fairly
    grants = [xbar.arbitrate([True, True]) for _ in range(100)]
    assert abs(grants.count(0) - grants.count(1)) <= 1
    # no requests -> no grant
    assert xbar.arbitrate([False, False]) is None


def test_axpy_end2end():
    rng = np.random.default_rng(0)
    n = 16
    x = rng.standard_normal(n).astype(np.float32).tolist()
    y = rng.standard_normal(n).astype(np.float32).tolist()
    a = 2.5
    out, dev, dma = host_axpy(a, x, y)
    expected = [np.float32(a) * np.float32(xi) + np.float32(yi)
                for xi, yi in zip(x, y)]
    assert np.allclose(out, expected, atol=1e-5)
    # operands flowed through the DMA, and the accelerator reported DONE
    assert dma.bytes_moved == 2 * 4 * n
    assert dev.mmio_read(r.KAI_PERF) == n


def test_kai_regs_model():
    import ra_soc as g
    r = g.KaiRegs(block_id=0x05)
    # ID is read-only magic with block id in top byte
    assert r.read(g.KAI_ID) == ((0x05 << 24) | g.KAI_MAGIC)
    # write/read descriptor
    r.write(g.KAI_SRC, 0x1000); r.write(g.KAI_DST, 0x2000); r.write(g.KAI_LEN, 64)
    assert r.read(g.KAI_SRC) == 0x1000 and r.read(g.KAI_DST) == 0x2000
    assert r.read(g.KAI_LEN) == 64
    # GO sets BUSY + pulses go
    r.write(g.KAI_CTRL, g.CTRL_GO)
    assert r.go == 1 and r.read(g.KAI_STATUS) == g.STATUS_BUSY
    # finish latches DONE + PERF
    r.finish(1234, err=0)
    assert r.read(g.KAI_STATUS) == g.STATUS_DONE and r.read(g.KAI_PERF) == 1234
    # error path
    r.finish(7, err=1)
    assert r.read(g.KAI_STATUS) == (g.STATUS_DONE | g.STATUS_ERR)
    # ABORT clears status; ID/STATUS not host-writable
    r.write(g.KAI_CTRL, 1 << 1)
    assert r.read(g.KAI_STATUS) == 0
    r.write(g.KAI_ID, 0xDEAD)
    assert r.read(g.KAI_ID) == ((0x05 << 24) | g.KAI_MAGIC)


def test_noc_crossbar():
    import ra_soc as g
    x = g.NocCrossbar(4)
    # no requests -> no grant
    assert x.arbitrate([False] * 4) is None
    # single requester always granted
    assert x.arbitrate([False, False, True, False]) == 2
    # round-robin: after granting 2, a 0&3 contest goes to 3 (next after 2)
    x2 = g.NocCrossbar(4)
    x2.arbitrate([False, False, True, False])     # last=2
    assert x2.arbitrate([True, False, False, True]) == 3
    # then from last=3, 0&1 contest -> 0
    assert x2.arbitrate([True, True, False, False]) == 0
    # grant counters accumulate
    assert x2.grants[2] == 1 and x2.grants[3] == 1 and x2.grants[0] == 1


def test_dma_copies():
    import ra_soc as g
    # 1D copy
    scr = g.Scratchpad(256)
    scr.write(0, bytes(range(32)))
    dma = g.Dma(scr); dma.copy(0, 100, 32)
    assert scr.read(100, 32) == bytes(range(32))
    assert dma.bytes_moved == 32
    # 2D strided copy
    scr2 = g.Scratchpad(256)
    scr2.write(0, bytes(range(64)))
    dma2 = g.Dma(scr2)
    dma2.copy_2d(0, 128, rows=4, row_bytes=4, src_stride=8, dst_stride=4)
    for r in range(4):
        assert scr2.read(128 + r * 4, 4) == bytes(range(r * 8, r * 8 + 4))
    assert dma2.bytes_moved == 16
