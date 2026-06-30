# 🧠 KemetCore FAQ

## What is KemetCore?

An open-source collection of 10 hardware accelerator projects + 1 capstone AI SoC — from RTL to GDSII on ASAP7 7nm. CPUs, ML accelerators, cryptographic engines, graphics, and arithmetic libraries.

## Why "Kemet"?

**Kemet** (𓆎𓅓𓏏𓊖) was the ancient Egyptian name for Egypt, meaning "the black land." Each core is named after an Egyptian deity whose domain matches the core's function: Seth (chaos) for the CPU, Anubis (embalming) for hashing, Sobek (crocodile) for the ray-tracer that "strikes" its target, etc.

## Is this real hardware?

Yes. Every project targets actual GDSII layout on ASAP7 7nm PDK through Yosys synthesis and OpenROAD place-and-route. PtahCore (the FP8 tensor accelerator that serves as the blueprint) already has **5 GDSII macros** completed — a 32×32 array at 2.27 mm², DRC clean, timing closed.

## What's done today?

- **All 11 cores:** Phase 0/1 complete (golden reference + pymodel in Python)
- **AnubisCore:** Full RTL + synthesis reports for SHA-256, SHA-3
- **NeithCore:** RTL for polynomial arithmetic, CBD sampler, message codec
- **AtumCore:** 20+ RVV vector unit RTL modules
- **HapiCore:** FP32 comparison, classification, conversion RTL
- **RaCore:** KAI registers, NoC arbiter, DMA engine RTL
- **PtahConv:** 2D convolution engine RTL

## Can I run this on my laptop?

**Phase 0/1 (Python):** Yes. `pip install numpy pytest && pytest projects/ -q`. <0.5 GB RAM.  
**Phase 2 (RTL + cocotb):** Yes. Needs Verilator 5 + cocotb 1.9+.  
**Phase 4 (P&R):** Depends on core size. Everything ≤0.5 mm² fits on 16 GB. Use tile-abutment for bigger blocks.

## What RISC-V specification is implemented?

**SethCore:** RV32IM (base integer + multiply/divide) + Zicsr + Zifencei.  
**AtumCore:** RISC-V Vector Extension v1.0 (VLEN=256, ELEN=64).

## What crypto standards are implemented?

**AnubisCore:** FIPS 180-4 (SHA-256 family), FIPS 202 (SHA-3/Keccak).  
**NeithCore:** FIPS 203 (ML-KEM, formerly CRYSTALS-Kyber). NIST post-quantum standard.

## How do I contribute?

This is a solo developer project actively shipping. If you find a bug or want to propose an enhancement:
1. Open an issue on GitHub
2. Read the architecture spec for the relevant core in `docs/`
3. Follow the 6-phase methodology
4. Submit a PR with passing tests (CI must be green)

## Where's the LICENSE?

MIT. See the LICENSE file in the repository root.

## What's next?

The priority order is:
1. Complete AnubisCore tape-out (closest to GDSII)
2. Complete HapiCore RTL (foundation for all other cores)
3. Complete SethCore RTL (the CPU that powers RaCore)
4. RaCore-Lite integration (the capstone demo)
