"""RaCore golden reference — the KAI SoC fabric (capstone).

Models the system that ties all KemetCore blocks together:
  * KAI: the Kemet Accelerator Interface — a memory-mapped register contract every
    accelerator implements (ID/CTRL/STATUS/SRC/DST/LENGTH/...).
  * A shared scratchpad memory.
  * A descriptor DMA engine (1D + 2D/strided copies).
  * A NoC crossbar with round-robin arbitration.
  * An end-to-end axpy that drives a KAI accelerator entirely through the fabric.
"""

# --- KAI register offsets (the contract) ----------------------------------- #
KAI_ID = 0x000
KAI_CAPS = 0x004
KAI_CTRL = 0x008      # bit0 GO, bit1 ABORT, bit2 IRQ_EN, bit3 SOFT_RST
KAI_STATUS = 0x00C    # bit0 BUSY, bit1 DONE, bit2 ERR
KAI_SRC = 0x020
KAI_DST = 0x028
KAI_LEN = 0x030
KAI_PERF = 0xF00
KAI_MAGIC = 0x4B4D54           # 'KMT' in the low 24 bits; block id in the top byte

CTRL_GO = 1 << 0
STATUS_BUSY = 1 << 0
STATUS_DONE = 1 << 1
STATUS_ERR = 1 << 2

MANDATORY_REGS = [KAI_ID, KAI_CAPS, KAI_CTRL, KAI_STATUS, KAI_SRC, KAI_DST,
                  KAI_LEN, KAI_PERF]


class Scratchpad:
    """Byte-addressable shared memory."""
    def __init__(self, size=1 << 20):
        self.mem = bytearray(size)

    def read(self, addr, n):
        return bytes(self.mem[addr:addr + n])

    def write(self, addr, data):
        self.mem[addr:addr + len(data)] = data


class KaiDevice:
    """Base class: any accelerator that obeys KAI subclasses this."""
    BLOCK_ID = 0x00

    def __init__(self, scratch):
        self.scratch = scratch
        self.regs = {KAI_ID: (self.BLOCK_ID << 24) | KAI_MAGIC,
                     KAI_CAPS: 0, KAI_CTRL: 0, KAI_STATUS: 0,
                     KAI_SRC: 0, KAI_DST: 0, KAI_LEN: 0, KAI_PERF: 0}

    def mmio_read(self, off):
        return self.regs.get(off, 0)

    def mmio_write(self, off, val):
        self.regs[off] = val & 0xFFFFFFFF
        if off == KAI_CTRL and (val & CTRL_GO):
            self._run()

    def _run(self):
        self.regs[KAI_STATUS] = STATUS_BUSY
        cycles = self.execute()
        self.regs[KAI_PERF] = cycles
        self.regs[KAI_STATUS] = STATUS_DONE

    def execute(self):
        raise NotImplementedError


class Dma:
    """Descriptor DMA: 1D and 2D/strided copies within the scratchpad."""
    def __init__(self, scratch):
        self.scratch = scratch
        self.bytes_moved = 0

    def copy(self, src, dst, length):
        self.scratch.write(dst, self.scratch.read(src, length))
        self.bytes_moved += length

    def copy_2d(self, src, dst, rows, row_bytes, src_stride, dst_stride):
        for r in range(rows):
            s = src + r * src_stride
            d = dst + r * dst_stride
            self.scratch.write(d, self.scratch.read(s, row_bytes))
            self.bytes_moved += row_bytes


class NocCrossbar:
    """N-master x M-slave crossbar with round-robin arbitration."""
    def __init__(self, n_masters):
        self.n = n_masters
        self.grants = [0] * n_masters
        self._last = -1

    def arbitrate(self, requests):
        """requests: list of bools. Returns granted master index (round-robin)."""
        if not any(requests):
            return None
        for k in range(1, self.n + 1):
            cand = (self._last + k) % self.n
            if requests[cand]:
                self._last = cand
                self.grants[cand] += 1
                return cand
        return None
