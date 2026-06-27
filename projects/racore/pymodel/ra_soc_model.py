"""RaCore pymodel — an example KAI accelerator + end-to-end driver.

KaiAxpy is a concrete accelerator that obeys the KAI contract: it reads x and y
fp32 vectors from the shared scratchpad and writes a*x+y back. host_axpy is the
SethCore-style driver that programs it entirely through MMIO + DMA, proving the
fabric works end to end.
"""
import struct

import ra_soc as r

KAI_SCALAR = 0x040     # block-specific descriptor: fp32 scalar 'a'
KAI_COUNT = 0x044      # element count


class KaiAxpy(r.KaiDevice):
    BLOCK_ID = 0xA1

    def execute(self):
        n = self.regs[KAI_COUNT]
        src = self.regs[r.KAI_SRC]      # x vector
        aux = self.regs[r.KAI_DST]      # y vector (in-place result)
        a = struct.unpack("<f", struct.pack("<I", self.regs[KAI_SCALAR]))[0]
        x = struct.unpack(f"<{n}f", self.scratch.read(src, 4 * n))
        y = struct.unpack(f"<{n}f", self.scratch.read(aux, 4 * n))
        out = [a * xi + yi for xi, yi in zip(x, y)]
        self.scratch.write(aux, struct.pack(f"<{n}f", *out))
        return n                         # 'cycles' ~ element count


def host_axpy(a, x, y, x_addr=0x1000, y_addr=0x2000):
    """Drive a KaiAxpy accelerator through the KAI fabric, as a host CPU would."""
    n = len(x)
    scratch = r.Scratchpad()
    dma = r.Dma(scratch)

    # host stages operands in DRAM image (here just buffers) then DMAs to scratchpad
    scratch.write(0x8000, struct.pack(f"<{n}f", *x))   # 'DRAM' staging
    scratch.write(0x9000, struct.pack(f"<{n}f", *y))
    dma.copy(0x8000, x_addr, 4 * n)
    dma.copy(0x9000, y_addr, 4 * n)

    dev = KaiAxpy(scratch)
    dev.mmio_write(r.KAI_SRC, x_addr)
    dev.mmio_write(r.KAI_DST, y_addr)
    dev.mmio_write(KAI_COUNT, n)
    dev.mmio_write(KAI_SCALAR, struct.unpack("<I", struct.pack("<f", a))[0])
    dev.mmio_write(r.KAI_CTRL, r.CTRL_GO)               # kick

    assert dev.mmio_read(r.KAI_STATUS) & r.STATUS_DONE
    result = struct.unpack(f"<{n}f", scratch.read(y_addr, 4 * n))
    return list(result), dev, dma
