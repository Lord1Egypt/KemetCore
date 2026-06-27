# 𓇳 RaCore — The Kemet Heterogeneous AI SoC (Capstone)

> **Deity:** Ra (𓇳, the sun god — the supreme creator the entire pantheon orbits and serves). Just as every other deity derives meaning from Ra, every KemetCore accelerator finds its purpose when integrated into RaCore.
> **Domain:** System-on-Chip — full-chip integration
> **Status:** Phase 0 — Spec & Golden (capstone; unblocks only after its building blocks reach Phase 2)
> **Target Fmax:** 500 MHz system clock (multi-clock domains; crypto enclave at 1 GHz)
> **Est. Gates:** RaCore-Lite ~1.5M · RaCore-Full ~26M
> **Complexity:** ★★★★★ (integration, not invention — the hard part is making 11 cores agree)

---

## 1. Why a Capstone Exists

The other ten projects (plus the already-complete **PtahCore**) are each a *correct, verified, taped-out block*. But ten blocks are not a chip. **RaCore is the project that makes KemetCore a coherent computer instead of a parts catalogue.**

RaCore answers the question every accelerator project eventually has to answer: *how does a host actually drive you, feed you data, and read your results — and how do you share silicon with your neighbours?*

It contributes three things that do not exist in any single block:

1. **KAI — the Kemet Accelerator Interface.** A single, documented register + DMA contract that every accelerator implements. Once a block speaks KAI, it drops into the SoC with zero glue logic. This is the difference between "10 demos" and "a composable IP library."
2. **A real interconnect + memory hierarchy.** A lightweight NoC, a shared on-chip scratchpad, and a DMA engine — RTL that lives nowhere else and is the actual scaling story.
3. **A post-quantum root of trust.** AnubisCore (hashing) + NeithCore (ML-KEM) compose into a secure-boot + attestation enclave, turning two crypto blocks into a security *subsystem*.

---

## 2. System Architecture

```
                         ┌──────────────────────────────────────────────┐
                         │                  RaCore SoC                     │
                         │                                                 │
   off-chip DRAM ◀──────▶│  ┌─────────────┐        ┌──────────────────┐  │
   (AXI / LPDDR)         │  │  CPU COMPLEX │        │  SECURITY ENCLAVE │  │
                         │  │             │        │  (1 GHz domain)   │  │
                         │  │  SethCore   │        │  AnubisCore (hash)│  │
                         │  │  (RV32IM)   │        │  NeithCore (MLKEM)│  │
                         │  │     +       │        │  → secure boot,   │  │
                         │  │  AtumCore   │        │    attestation,   │  │
                         │  │  (RVV vec)  │        │    key wrap       │  │
                         │  └──────┬──────┘        └─────────┬────────┘  │
                         │         │                         │           │
                         │    ┌────▼─────────────────────────▼──────┐    │
                         │    │        KEMET NoC (KAI fabric)        │    │
                         │    │   AXI-lite crossbar + DMA engine     │    │
                         │    └──┬───────┬───────┬───────┬───────┬──┘    │
                         │       │       │       │       │       │       │
                         │  ┌────▼──┐ ┌──▼───┐ ┌─▼────┐ ┌▼─────┐ ┌▼────┐ │
                         │  │ ML CLUSTER                    │ │GFX  │ │FPU │ │
                         │  │ PtahCore  (FP8 tensor)        │ │Sobek│ │Hapi│ │
                         │  │ BastCore  (BF16 tensor)       │ │ raytr│ │shar│ │
                         │  │ PtahConv  (convolution)       │ └─────┘ │ed  │ │
                         │  │ GebCore   (2:4 sparse matmul) │         └────┘ │
                         │  │ ImentetCore (attention)       │                │
                         │  └───────────────┬───────────────┘                │
                         │                  │                                 │
                         │           ┌──────▼───────┐                         │
                         │           │ SHARED SRAM  │  (banked scratchpad,    │
                         │           │  scratchpad  │   software-managed)     │
                         │           └──────────────┘                         │
                         └──────────────────────────────────────────────────┘
```

**Programming model.** SethCore runs the control program. It configures an accelerator over KAI (write descriptor registers), kicks the DMA engine to stream operands from DRAM into the shared scratchpad, sets the accelerator's `GO` bit, and either polls `DONE` or takes an interrupt. AtumCore handles the data-parallel glue (layout, activation, elementwise) that doesn't deserve a dedicated accelerator. The ML cluster does the heavy tensor math; the security enclave gates boot and protects keys.

---

## 3. KAI — The Kemet Accelerator Interface

KAI is the contract. **Every** KemetCore accelerator (including PtahCore, retrofitted) exposes the same memory-mapped register block so the host driver, the DMA engine, and the verification harness are written **once**.

### 3.1 Mandatory register map (per accelerator, 4 KiB MMIO window)

| Offset | Name | Access | Meaning |
|-------:|------|:------:|---------|
| `0x000` | `ID` | RO | Magic (`'KEMT'`) + block ID + version |
| `0x004` | `CAPS` | RO | Feature bits (formats, max tile, DMA channels) |
| `0x008` | `CTRL` | RW | `[0]=GO`, `[1]=ABORT`, `[2]=IRQ_EN`, `[3]=SOFT_RST` |
| `0x00C` | `STATUS` | RO | `[0]=BUSY`, `[1]=DONE`, `[2]=ERR`, `[7:4]=errcode` |
| `0x010` | `IRQ` | W1C | Interrupt status, write-1-to-clear |
| `0x020` | `SRC_ADDR` | RW | Scratchpad/DRAM source base |
| `0x028` | `DST_ADDR` | RW | Destination base |
| `0x030` | `LENGTH` | RW | Transfer/compute length |
| `0x040`+ | `DESC[…]` | RW | Block-specific descriptor (tile dims, strides, opcode) |
| `0xF00` | `PERF` | RO | Cycle counter + utilization (for honest benchmarking) |

### 3.2 Why this matters
- **One driver.** `kai_run(block, descriptor)` works for every accelerator.
- **One testbench skeleton.** cocotb `KaiDriver` class is reused across all 11 cores → far fewer than the ~500 total tests are bespoke.
- **Composability is provable.** "Does block X obey KAI?" becomes a conformance test suite (`test_kai_conformance.py`) every block must pass — a new CI gate.

This is a genuinely new idea relative to the current repo: today each block defines its own ad-hoc ports. KAI is the standardization layer that makes a *system* possible.

---

## 4. The Interconnect & Memory Hierarchy (new RTL)

| Module | Role | Notes |
|--------|------|-------|
| `kemet_noc_xbar.sv` | AXI-lite crossbar, N masters × M slaves | Round-robin arbiter; parametric width |
| `kemet_dma.sv` | Multi-channel descriptor DMA | DRAM ⇄ scratchpad; 2D/strided modes for tensors |
| `kemet_scratchpad.sv` | Banked SRAM, software-managed | Bank-per-port to avoid the ML cluster starving the CPU |
| `kemet_clk_rst.sv` | Clock/reset + CDC for the 1 GHz crypto enclave | Async FIFOs at the boundary |
| `kemet_plic.sv` | Platform interrupt controller | Aggregates per-block `DONE`/`ERR` to SethCore |

The scratchpad + DMA are the **scaling lever**: throughput is bounded by how fast operands reach the MAC arrays, not by the arrays themselves. This is the system-level lesson PtahCore (a bare array) cannot teach on its own.

---

## 5. Two Honest Build Tiers

KemetCore's "Silicon or Bust" principle collides with reality: a full 26M-gate SoC needs detailed-route memory far beyond a 16 GB laptop (the exact wall PtahCore's 6th GDS hit). RaCore is therefore specified in **two configurations**, and we are honest about which is buildable where.

| | **RaCore-Lite** | **RaCore-Full** |
|---|---|---|
| CPU | SethCore | SethCore + AtumCore |
| ML | PtahCore (FP8) only | PtahCore + BastCore + PtahConv + GebCore + ImentetCore |
| Crypto | AnubisCore | AnubisCore + NeithCore (PQ enclave) |
| Graphics | — | SobekCore |
| FPU | HapiCore | HapiCore |
| Interconnect | 4-port xbar + 1 DMA ch | NoC + multi-channel DMA |
| Scratchpad | 256 KiB | 4 MiB banked |
| Est. gates | **~1.5M** | **~26M** |
| Est. area (ASAP7) | **~3.5 mm²** | **~16 mm²** |
| **GDSII feasible on** | **16 GB laptop** (hierarchical, blocks pre-hardened) | **≥64 GB box / shuttle flow** |

**Lite is the actual capstone deliverable for a single developer on a laptop.** Full is the aspirational tape-out target, documented honestly as "needs real iron" — same discipline as `docs/FINISH_DRT_BIGRAM.md` in PtahCore.

---

## 6. Hierarchical Physical Design

RaCore does **not** flatten 26M gates into one P&R run (that's what melts the laptop). It reuses PtahCore's proven **abutted-macro** methodology at the next level up:

1. Each accelerator is hardened **once** into a fixed LEF/DEF macro with its own DRC-clean GDSII (already the per-project deliverable).
2. RaCore's top level places those macros + the NoC/SRAM as a **floorplan of black boxes** and routes only the top-level KAI/AXI nets.
3. Top-level detail route handles ~thousands of inter-block wires, not millions of intra-block ones → memory stays bounded.

This is the single most important scaling decision: **integration cost is O(blocks), not O(gates).**

---

## 7. Golden Reference & Verification

```
golden/
├── racore_soc.py           # Full SoC functional model (instantiates all block goldens)
├── kai.py                  # KAI register model + driver
├── noc_model.py            # Crossbar + arbitration timing model
├── dma_model.py            # Descriptor DMA (2D/strided)
├── secure_boot.py          # Anubis+Neith root-of-trust flow
└── tests/
    ├── test_kai_conformance.py   # Every block obeys the KAI contract
    ├── test_axpy_end2end.py      # CPU → DMA → AtumCore → result
    ├── test_resnet_tile.py       # CPU → DMA → PtahConv/Bast → scratchpad
    ├── test_attention_block.py   # ImentetCore driven over KAI
    ├── test_secure_boot.py       # PQ attestation handshake
    └── test_concurrency.py       # Two accelerators sharing scratchpad+NoC
```

| Layer | What RaCore adds beyond the per-block tests |
|-------|---------------------------------------------|
| Golden | An *end-to-end* workload model: a real op (axpy, a conv layer, an attention block) flowing host→DMA→accelerator→host |
| pymodel | NoC arbitration + DMA timing, so contention bugs surface in Python first |
| RTL | KAI conformance + multi-master NoC stress + CDC into the crypto enclave |
| Silicon | Top-level hierarchical GDSII (Lite); macro-abutment timing closure |

---

## 8. Flagship Demo — "Run a real model on open silicon"

The capstone proof: load a small INT8/FP8 CNN, run one inference, attest the result.

```
1. Secure boot: NeithCore verifies firmware signature (ML-KEM) ─┐
2. SethCore loads weights from DRAM via kemet_dma ──────────────┤
3. PtahConv runs conv layers (KAI: SRC=ifmap, DST=ofmap, GO) ───┤  all over
4. AtumCore applies ReLU + bias (vector elementwise) ───────────┤  the KAI
5. ImentetCore runs the classifier head's attention ───────────┤  fabric
6. AnubisCore hashes the output tensor → attestation tag ───────┘
7. SethCore prints class + attestation hash
```

A single program, six accelerators, one chip. That is the difference between KemetCore-the-catalogue and KemetCore-the-computer.

---

## 9. Dependencies

| Dependency | Why | Gate |
|------------|-----|------|
| All 11 blocks at Phase 2+ | RaCore integrates verified RTL; it does not invent compute | Hard |
| KAI conformance per block | Each block must pass `test_kai_conformance` before integration | Hard |
| PtahCore macro (exists) | First block retrofitted to KAI; proves the methodology | Done-ish |

---

## 10. Checkpoints

| # | Checkpoint | Deliverable |
|:-:|------------|-------------|
| RA.1 | KAI spec frozen | Register map + conformance suite |
| RA.2 | Retrofit PtahCore to KAI | Existing block passes conformance |
| RA.3 | Golden: NoC + DMA model | Contention-accurate Python |
| RA.4 | Golden: end-to-end axpy | host→DMA→Atum→host bit-exact |
| RA.5 | RTL: NoC crossbar + DMA | Multi-master stress passes |
| RA.6 | RTL: scratchpad + PLIC | Banked, no starvation |
| RA.7 | RTL: RaCore-Lite top | SethCore+PtahCore+Anubis+Hapi integrated |
| RA.8 | Secure boot enclave | Anubis+Neith attestation flow |
| RA.9 | Synthesis: Lite | ≤1.5M gates, 0 latches |
| RA.10 | P&R: Lite hierarchical GDSII | Macro-abutment, DRC clean, 16 GB-feasible |
| RA.11 | Flagship demo | CNN inference + attestation on Lite |
| RA.12 | RaCore-Full floorplan | Documented; tape-out target on real iron |

---

## 11. Comparison with Prior Art

| SoC | Cores integrated | Interconnect | Open RTL→GDSII | PQ security | Verification |
|-----|:----------------:|:------------:|:--------------:|:-----------:|:------------|
| **RaCore** | **11 (CPU+vec+5 ML+2 crypto+gfx+FPU)** | **KAI NoC** | **Yes (ASAP7)** | **Yes (ML-KEM)** | **bit-exact golden + KAI conformance** |
| OpenTitan | RV32 + crypto | TL-UL | Yes | No (classical) | DV (UVM) |
| ESP (Columbia) | Tiles + NoC | NoC | Partial | No | Per-tile |
| Chipyard/Rocket | RV + accels | TileLink | Mostly | No | Mixed |
| BlackParrot | RV multicore | BedRock | Yes | No | Trace |

RaCore's distinctive bet: **a uniform, dead-simple accelerator interface (KAI) + a post-quantum root of trust + bit-exact golden verification across the entire heterogeneous stack** — and an honest two-tier build so it actually closes on hardware a single developer can afford.

---

*The capstone. Prev: [AtumCore — RVV](10_AtumCore_RVV.md) · Back to [README](../README.md) · [ROADMAP](../ROADMAP.md)*
