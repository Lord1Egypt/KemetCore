# 𓆣 AtumCore — RISC-V Vector Extension v1.0 Unit

> **Deity:** Atum (𓆣, the creator god — synthesized all the others into being, just as vector processing synthesizes scalar operations into parallel computation)
> **Domain:** CPU — SIMD/Vector Processing
> **Status:** Phase 0 — Spec & Golden
> **Target Fmax:** 500 MHz on ASAP7
> **Est. Gates:** ~100K+ (largest KemetCore project)
> **Complexity:** ★★★★★

---

## 1. Technical Overview

AtumCore is a **RISC-V Vector Extension (RVV v1.0) coprocessor** that plugs into SethCore (Project 01) to provide vector processing capabilities. It implements a decoupled vector execution unit with a dedicated vector register file, vector ALU lanes, and a vector memory unit for strided/indexed/unit-stride access patterns.

### Why RVV?

RVV is the RISC-V standard for data-parallel computing — the equivalent of ARM SVE or Intel AVX. It is inherently **length-agnostic**: software written for RVV runs on any implementation with any VLEN, from 128 to 65536 bits. This makes it ideal for everything from embedded SIMD to HPC vector processors.

### Key Specifications

| Parameter | Target | Notes |
|-----------|--------|-------|
| VLEN | 256 bits | Implementation-defined |
| ELEN | 64 bits | All standard types |
| LMUL | 1, 2, 4, 8 | Fractional not required |
| Vector registers | 32 × VLEN | 1 KiB total |
| Mask registers | 8 × VLEN/8 | 32 bytes total |
| Strip mining | Full support | vsetvl* instructions |

### Supported RVV v1.0 Instruction Groups

| Group | Instructions | Priority | Notes |
|-------|-------------|:--------:|-------|
| Configuration | vsetvli, vsetivli, vsetvl | ✅ Required | VLEN/ELEN discovery |
| Vector load/store | vlb, vlh, vlw, vle, vsb, vsh, vsw, vse | ✅ Required | Unit-stride |
| Strided load/store | vlsb, vlsh, vlsw, vlse, vssb, vssh, vssw, vsse | ✅ Required | Strided |
| Indexed load/store | vlxb, vlxh, vlxw, vlxe, vsxb, vsxh, vsxw, vsxe | ✅ Required | Scatter/gather |
| Integer arithmetic | vadd, vsub, vand, vor, vxor, vsll, vsrl, vsra | ✅ Required | |
| Integer multiply | vmul, vmh, vmacc | ✅ Required | |
| Integer compare | vmseq, vmsne, vmslt, vmsleu | ✅ Required | |
| Shift/permute | vslideup, vslidedown, vrgather, vcompress | 🎯 Target | Complex datapath |
| Reduction | vredsum, vredmax, vfredusum | 🎯 Target | |
| Floating-point | vfadd, vfmul, vffma | 🎯 Target | Uses HapiCore |

---

## 2. Architecture

### Vector Coprocessor Block Diagram

```
SethCore (scalar core)
     │
     ├─── vector instructions via custom opcode ───▶ atumcore/
     │                                                    │
     │                                              ┌─────▼──────┐
     │                                              │ Command Q   │
     │                                              │ (8 entries) │
     │                                              └─────┬──────┘
     │                                                    │
     │                                              ┌─────▼──────┐
     │                                              │ Decode +    │
     │                                              │ Sequence    │
     │                                              └──┬───┬─────┘
     │                                                 │   │
     │                                        ┌────────┘   └────────┐
     │                                        ▼                     ▼
     │                                ┌──────────────┐    ┌──────────────┐
     │                                │ Vector ALU   │    │ Vector LSU   │
     │                                │ (8 lanes)    │    │ (10 stages)  │
     │                                │              │    │              │
     │                                │ · VADD/VSUB  │    │ · Unit-strid │
     │                                │ · VMUL/VFMUL │    │ · Strided    │
     │                                │ · Compare    │    │ · Indexed    │
     │                                │ · Shift      │    │              │
     │                                └──────┬───────┘    └──────┬───────┘
     │                                       │                   │
     │                                ┌──────▼───────────────────▼───────┐
     │                                │     Vector Register File        │
     │                                │     32 × 256-bit = 1,024 bytes  │
     │                                │                                  │
     │                                │     Mask Reg File               │
     │                                │     8 × 32-bit = 32 bytes       │
     │                                └──────────────────────────────────┘
```

### Module Hierarchy

```
atumcore/
├── atum_top.sv                 # Top-level: command interface + dispatch
├── atum_command_queue.sv       # In-order command queue (8 entries)
├── atum_decode.sv              # RVV instruction decoder (all groups)
├── atum_sequencer.sv           # Strip-mining + LMUL sequencer
├── atum_regfile.sv             # 32×VLEN vector register file
├── atum_mask_regfile.sv        # 8×VLEN/8 mask register file
├── atum_alu_lane.sv            # Single vector ALU lane
├── atum_alu_lane_group.sv      # 8 ALU lanes in parallel
├── atum_int_add.sv             # Integer add/sub per lane
├── atum_int_mul.sv             # Integer multiply per lane
├── atum_int_shift.sv           # Shift per lane
├── atum_int_cmp.sv             # Integer compare per lane
├── atum_fp_add.sv              # FP add (from HapiCore)
├── atum_fp_mul.sv              # FP mul (from HapiCore)
├── atum_fp_fma.sv              # FP FMA (from HapiCore)
├── atum_lsu.sv                 # Vector load/store unit
├── atum_lsu_unit_stride.sv     # Unit-stride access
├── atum_lsu_strided.sv         # Strided access
├── atum_lsu_indexed.sv         # Indexed (scatter/gather)
├── atum_permute.sv             # Vector permute unit
├── atum_reduce.sv              # Reduction unit
├── atum_mask_logic.sv          # Mask generation/combination
└── atum_controller.sv          # Main vector controller FSM
```

### Vector ALU Datapath

```
VLEN = 256 bits, 8 lanes × 32 bits per lane

                          Lane 0      Lane 1  ...  Lane 7
                         ┌────────┐  ┌────────┐    ┌────────┐
    vs1[VLEN-1:0] ───────▶│        │  │        │    │        │
                          │  ALU   │  │  ALU   │    │  ALU   │
    vs2[VLEN-1:0] ───────▶│ Lane 0 │  │ Lane 1 │    │ Lane 7 │
                          │        │  │        │    │        │
    vd[VLEN-1:0] ◀────────│        │◀─│        │◀───│        │
                          └────────┘  └────────┘    └────────┘
                            ELEN=32    ELEN=32       ELEN=32

Each lane contains:
  - 32-bit integer ALU (add/sub/shift/logic)
  - 32-bit integer multiplier
  - 32-bit FP adder (from HapiCore fp_add)
  - 32-bit FP multiplier (from HapiCore fp_mul)
  - Local register file slice
```

---

## 3. Golden Reference

```
golden/
├── rvv_instructions.py        # All RVV v1.0 instruction definitions
├── rvv_register_file.py       # Vector + mask register file model
├── rvv_alu.py                 # Vector ALU (per-lane, all ops)
├── rvv_lsu.py                 # Vector LSU (all 3 access patterns)
├── rvv_strip_mining.py        # Strip-mining semantics
├── rvv_decoder.py             # Instruction decoder
├── rvv_simulator.py           # Full RVV simulator
├── riscv_vector_test.py       # Compare vs Spike (vector extension)
└── tests/
    ├── test_vsetvl.py         # VLEN/ELEN discovery
    ├── test_alu.py            # All integer instructions
    ├── test_lsu.py            # All 3 access patterns
    ├── test_masked.py         # Masked operations
    ├── test_reduction.py      # Vector reduction
    ├── test_permute.py        # Slide, gather, compress
    ├── test_fp.py             # Float-point instructions
    └── test_spike.py          # Random programs vs Spike
```

### Spike Comparison

AtumCore's golden simulator must match **Spike with the `--isa=RV64GV` extension** on every instruction. Same methodology as SethCore:

1. Generate random RISC-V binary with vector instructions
2. Run on golden simulator → capture register state
3. Run on Spike → capture register state
4. Assert bit-exact match

---

## 4. Testing Strategy

| Test | Count | What It Verifies |
|------|:-----:|------------------|
| Golden: vs Spike | 20 | Random vector programs |
| Golden: masked ops | 8 | All mask register combos |
| Golden: LMUL variants | 6 | LMUL=1,2,4,8 + fractional |
| pymodel: ALU lanes | 8 | Each instruction per lane |
| pymodel: LSU | 6 | Strided/indexed boundary cases |
| pymodel: full chip | 6 | Strip-mined loops |
| RTL: lane group | 8 | VADD→VMUL→VFADD chain |
| RTL: LSU unit-stride | 6 | Alignment, misalignment, wrap |
| RTL: LSU strided | 6 | Various strides, overlaps |
| RTL: LSU indexed | 6 | Scatter/gather correctness |
| RTL: mask logic | 4 | All mask operations |
| RTL: reduction | 4 | All reduction types |
| RTL: full chip | 6 | Vector program vs Spike |
| RTL: SethCore integration | 6 | Scalar→vector→scalar data |
| **Total** | **~96** | |

---

## 5. Dependencies

| Dependency | Why | Project |
|------------|-----|---------|
| SethCore | Scalar core that issues vector instructions | [docs/01_SethCore_RV32IM_CPU.md](01_SethCore_RV32IM_CPU.md) |
| HapiCore | FP32 add/mul/FMA for vector FP opcodes | [docs/09_HapiCore_FPU.md](09_HapiCore_FPU.md) |

---

## 6. Physical Design

| Parameter | Target |
|-----------|--------|
| VLEN | 256 bits (8 × 32-bit lanes) |
| ALU lanes | 8 (fully parallel) |
| Lane width | 32 bits |
| Fmax | 500 MHz |
| Vector RF | 1,024 bytes (32 × 256 bits) |
| Mask RF | 32 bytes (8 × 32 bits) |
| LSU pipe depth | 10 stages |
| ALU pipe depth | 4 stages |
| FP pipe depth | 4 stages |
| Area | ~0.5 mm² |
| Gates | ~100K+ |

---

## 7. Challenges & Design Decisions

### Challenge 1: RVV Spec Complexity

The RVV v1.0 spec is ~400 pages. AtumCore implements a pragmatic subset:

| Priority | Groups | Reason |
|:--------:|--------|--------|
| P0 (required) | vsetvl, load/store (all patterns), integer ALU | Core functionality |
| P1 (target) | Shift/permute, reduction, FP | ML workload support |
| P2 (future) | Segment load/store, crypto extensions | Niche use cases |

### Challenge 2: LMUL and Strip Mining

LMUL (length multiplier) allows grouping registers for longer vectors. AtumCore supports LMUL=1,2,4,8 by fetching multiple register file entries per operation. Strip mining is handled by the sequencer using `vsetvl`.

### Challenge 3: Scalar-Vector Coupling

AtumCore communicates with SethCore via:
- **Command queue** — SethCore writes vector opcodes into an 8-entry FIFO
- **Register mapping** — SethCore's integer registers are visible for scalar operands
- **Exception handling** — Vector exceptions propagate to SethCore's trap handler

---

## 8. Comparison with Prior Art

| Design | VLEN | Lanes | Fmax | FP | Area | Verification |
|--------|:----:|:-----:|:----:|:--:|:----:|:------------|
| **AtumCore** | **256** | **8** | **500 MHz** | **Yes** | **~0.5 mm²** | **vs Spike** |
| Ara (ETH) | 256 | 4 | 500 MHz | Yes | ~1.0 mm² | vs Spike |
| Vitruvius | 256 | 8 | 1 GHz | Yes | ~2.0 mm² | Formal |
| Spatz (BSC) | 512 | 4 | 400 MHz | No | ~0.4 mm² | vs Spike |
| Xuantie C910 | 128 | 4 | 1.2 GHz | Yes | ~1.5 mm² | Commercial |

AtumCore targets the sweet spot: **same performance as Ara** in **half the area**, by using a simpler decoupled design rather than a tightly-coupled multi-issue vector unit.

---

## 9. Checkpoints

| # | Checkpoint | Deliverable |
|:-:|------------|-------------|
| AT.1 | Golden: RVV simulator | Matches Spike |
| AT.2 | Golden: LMUL + strip mining | Correct semantics |
| AT.3 | pymodel: ALU lanes | 8-lane operation |
| AT.4 | pymodel: LSU | All access patterns |
| AT.5 | RTL: command queue + decode | Instruction dispatch |
| AT.6 | RTL: ALU lane group | 8-lane integer ALU |
| AT.7 | RTL: FP lanes (from HapiCore) | Vector FP operations |
| AT.8 | RTL: LSU unit-stride | Vector memory access |
| AT.9 | RTL: LSU strided + indexed | Complex patterns |
| AT.10 | RTL: mask + reduction | Masked operations |
| AT.11 | RTL: SethCore integration | Scalar→vector→scalar |
| AT.12 | Synthesis | Gate count ≤ 150K |
| AT.13 | P&R | DRC clean at 500 MHz |

---

## 10. Example: Vector Axpy

```python
# C code:
# void axpy(int n, float a, float *x, float *y) {
#     for (int i = 0; i < n; i++) y[i] += a * x[i];
# }

# RVV assembly (VLEN=256, 8×float32 per iteration):
axpy:
    vsetvli t0, a0, e32, m1, ta, ma     # VL = min(n, 8/LMUL=1)
loop:
    vle32.v v0, (a2)                     # Load 8 floats from x
    vfmacc.vf v1, fa0, v0               # v1 += a * v0 (fused)
    vse32.v v1, (a3)                     # Store to y
    add     a2, a2, t0, sll 2            # x += VL
    add     a3, a3, t0, sll 2            # y += VL
    sub     a0, a0, t0                   # n -= VL
    vsetvli t0, a0, e32, m1, ta, ma     # Reload VL
    bnez    a0, loop                     # Repeat
```

AtumCore processes **8 float32 elements per iteration** with fully pipelined FMA — effectively **4 GFLOPS at 500 MHz per lane × 8 lanes = 16 GFLOPS peak**.

---

*Prev: [HapiCore](09_HapiCore_FPU.md) · Back to [README](../README.md)*
