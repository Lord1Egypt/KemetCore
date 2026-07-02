# 🚀 Roadmap

> *"A journey of a thousand gates begins with a single flip-flop."*

The phased execution plan for all 10 KemetCore projects. Ordered for maximum skill/knowledge transfer — earlier projects build the tooling and expertise that later ones depend on.

---

## Execution Order

```
Phase 1 — Foundation (build the tooling)
  09. HapiCore ← no dependencies, pure arithmetic, creates FPU library
  06. AnubisCore ← no dependencies, pure crypto, creates hash library

Phase 2 — Compute Primitives (leverage FPU library)
  05. BastCore ← depends on HapiCore (BF16 multiply)
  01. SethCore ← depends on HapiCore (FPU for M extension)

Phase 3 — ML Accelerators (build on PtahCore patterns)
  02. PtahConv ← depends on BastCore (BF16 datapath)
  04. GebCore ← depends on BastCore (sparse BF16 matmul)
  03. ImentetCore ← depends on PtahConv + GebCore

Phase 4 — Advanced (graphics + post-quantum + vector)
  08. SobekCore ← independent, uses HapiCore
  07. NeithCore ← independent, standalone arithmetic
  10. AtumCore ← depends on SethCore (adds vector to scalar core)

Phase 5 — Capstone (integrate everything)
  00. RaCore ← depends on ALL blocks at Phase 2+; KAI-conformant
              RaCore-Lite first (laptop-feasible), then RaCore-Full
```

---

## Cross-Cutting: KAI Interface

From day one, the **KAI (Kemet Accelerator Interface)** spec — the register/DMA contract every block implements — is frozen in Phase 0 and becomes a per-block exit gate (`test_kai_conformance`). Retrofitting PtahCore to KAI validates the methodology before any new block is built.

---

## Target Timeline

### RaCore-Lite Capstone
When all 10 cores reach Phase 2+ and are KAI-conformant:
- NoC crossbar + descriptor DMA (8 days)
- Banked scratchpad + PLIC (4 days)
- RaCore-Lite top integration (6 days)
- Secure-boot enclave: AnubisCore + NeithCore (5 days)
- Synthesis: Lite ≤1.5M gates (2 days)
- P&R: Lite hierarchical GDSII (6 days)

---

## Key Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| RVV spec is 400+ pages | Implement subset first (VLEN=128, LMUL=1); extend later |
| Softmax hardware division is expensive | LUT-based + Newton iteration; verify error bounds |
| Sparse matmul throughput gain less than expected | Benchmark on real model weights before P&R |
| Single developer, projects take time | Prioritize by dependency graph; each project is independently shippable |
| RaCore-Full P&R exceeds laptop RAM | Ship RaCore-Lite; harden blocks to macros, route only top-level |
| KAI spec churns after blocks built | Frozen in Phase 0; gated by conformance test |
