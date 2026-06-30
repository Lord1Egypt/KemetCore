# 📊 Progress Tracker

> Auto-generated from the master manifest. Live data from the repository.

---

## Overall: Phase 0/1 Complete — RTL Actively Shipping

Legend: ✅ Complete · 🔧 In Progress · ⬜ Planned

---

## Master Matrix — All 11 Cores × 6 Phases

| # | Core | Domain | P0 Golden | P1 pymodel | P2 RTL | P3 Synth | P4 P&R | P5 Signoff |
|:-:|------|--------|:---------:|:----------:|:------:|:--------:|:------:|:----------:|
| 00 | **RaCore** | AI SoC capstone | ✅ | ✅ | 🔧 | ⬜ | ⬜ | ⬜ |
| 01 | **SethCore** | RV32IM CPU | ✅ | ✅ | 🔧 | 🔧 | ⬜ | ⬜ |
| 02 | **PtahConv** | Convolution | ✅ | ✅ | 🔧 | ⬜ | ⬜ | ⬜ |
| 03 | **ImentetCore** | Attention | ✅ | ✅ | ⬜ | ⬜ | ⬜ | ⬜ |
| 04 | **GebCore** | Sparse matmul | ✅ | ✅ | 🔧 | 🔧 | ⬜ | ⬜ |
| 05 | **BastCore** | BF16 tensor | ✅ | ✅ | 🔧 | 🔧 | ⬜ | ⬜ |
| 06 | **AnubisCore** | Hash engine | ✅ | ✅ | ✅ | 🔧 | ⬜ | ⬜ |
| 07 | **NeithCore** | ML-KEM | ✅ | ✅ | 🔧 | 🔧 | ⬜ | ⬜ |
| 08 | **SobekCore** | Ray tracer | ✅ | ✅ | ⬜ | ⬜ | ⬜ | ⬜ |
| 09 | **HapiCore** | FPU library | ✅ | ✅ | 🔧 | 🔧 | ⬜ | ⬜ |
| 10 | **AtumCore** | RVV vector | ✅ | ✅ | 🔧 | ⬜ | ⬜ | ⬜ |

---

## RTL Shipping Status (Phase 2)

| Core | RTL Modules Shipped | What's Done |
|------|:-------------------:|-------------|
| **AnubisCore** | sha256_core, sha3_256_core, sha3_384_core, sha3_512_core, sha512_core | Full SHA-2/SHA-3 family implemented + synthesis reports |
| **NeithCore** | neith_polymul, neith_cbd, neith_msgcodec, neith_polyaddsub, neith_pointwise | NTT + polynomial pipeline building |
| **AtumCore** | atum_vcore, atum_val, atum_vcompress, atum_vrgather, atum_vslide, atum_vmerge, atum_vfsgnj, atum_vfminmax, atum_vfclass, atum_vmsbf, atum_vmv, atum_vsx, atum_vdiv, atum_vfsqrt, atum_vfredsum, atum_vmulh, atum_vaadd, atum_vimac, atum_viota, atum_vmask, atum_vregfile, atum_vsetvl, atum_vfpu, atum_vmlogic, atum_vmpopc, atum_vredu, atum_vredminmax, atum_vslide1 | 20+ vector units! |
| **HapiCore** | hapi_fp32_minmax, hapi_fp32_cmp, hapi_fp32_class, hapi_int_to_fp32, hapi_fp32_to_int | FPU building block by block |
| **RaCore** | ra_kai_regs, ra_noc_arbiter, ra_dma, ra_kai_dma | SoC integration layer |
| **PtahConv** | ptah_conv2d | Direct 2D convolution engine |

---

## What "Done" Means

- **Phase 0 (Golden):** Architecture document reviewed + golden reference tested against known-correct output (PyTorch, hashlib, Spike, etc.)
- **Phase 1 (pymodel):** Cycle-level model passes all golden comparison tests
- **Phase 2 (RTL):** SystemVerilog with cocotb tests, 90%+ coverage, 0 latches
- **Phase 3 (Synth):** Yosys elaboration, gate count reported
- **Phase 4 (P&R):** DRC-clean GDSII with timing closure at target frequency
- **Phase 5 (Signoff):** CI pipeline passing, docs complete

---

## First Tape-Out Candidates

Based on area and dependency-free status, the first designs ready for GDSII tape-out:

1. **AnubisCore** (0.05 mm², 1 GHz, synthesis reports exist) — closest to done
2. **HapiCore** (0.1 mm², 500 MHz, no dependencies) — second closest
3. **SobekCore** (0.08 mm², 500 MHz, independent)
4. **NeithCore** (0.3 mm², 200 MHz, independent)
