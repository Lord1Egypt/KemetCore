# 𓆋 SobekCore — Hardware Ray-Triangle Intersector

> **Deity:** Sobek (𓆋, god of the Nile, crocodiles, and pharaonic power — ambush predator, like a ray "hitting" its target)
> **Domain:** Computer Graphics — Ray Tracing
> **Status:** Phase 0 — Spec & Golden
> **Target Fmax:** 500 MHz on ASAP7
> **Est. Gates:** ~30K
> **Complexity:** ★★★☆☆

---

## 1. Technical Overview

SobekCore is a **hardware ray-triangle intersection unit** — the core compute primitive of any hardware ray tracer. It implements the Möller-Trumbore intersection algorithm in a fully pipelined datapath, producing hit distance (t), barycentric coordinates (u, v), and instance ID per cycle.

### Why Ray-Triangle Intersection Hardware?

Ray tracing is a rendering technique that simulates light transport by casting rays through each pixel and testing them against scene geometry. The bottleneck is always ray-primitive intersection. A hardware intersector can test **1 ray against 1 triangle per cycle**, which is the throughput required for real-time ray tracing (e.g., RT Cores in NVIDIA GPUs).

### Key Innovations

| Feature | SobekCore | Software (Embree) | NVIDIA RT Core |
|---------|:---------:|:-----------------:|:--------------:|
| **Ray-triangle/cycle** | 1 | 0.01 (SIMD) | 1 (guessed) |
| **Watertight** | ✅ Yes | ✅ Yes | ❓ Unknown |
| **FP32 precision** | Full | Full | Likely FP32 |
| **BVH integrated** | External stack | CPU-managed | Internal |
| **Open source** | ✅ Yes | ✅ (partial) | ❌ No |

---

## 2. Architecture

### Möller-Trumbore Algorithm

```
Ray:     O + t·D (origin, direction, distance)
Triangle: V0, V1, V2 (three vertices in 3D)

Step 1:  E1 = V1 − V0,  E2 = V2 − V0
Step 2:  P = D × E2                   (cross product)
Step 3:  det = E1 · P                 (dot product)
Step 4:  inv_det = 1.0 / det
Step 5:  T = O − V0
Step 6:  u = (T · P) × inv_det       (barycentric u)
Step 7:  Q = T × E1
Step 8:  v = (D · Q) × inv_det       (barycentric v)
Step 9:  t = (E2 · Q) × inv_det      (hit distance)
Step 10: hit = (u ≥ 0, v ≥ 0, u+v ≤ 1, t in [t_min, t_max])
```

### Pipelined Datapath

```
              ┌─────────┐     ┌─────────┐     ┌─────────┐
  V0,V1,V2 ──▶│  SUB    │────▶│  CROSS  │────▶│  DOT    │────▶  det
  O,D         │  (E1,E2)│     │  (P,D×E2)│     │  (E1·P) │
              └─────────┘     └─────────┘     └────┬────┘
                                                    │
              ┌─────────┐     ┌─────────┐          │
  O,V0 ──────▶│  SUB    │────▶│  DOT    │          │
              │  (T)    │     │  (T·P)  │── u ─────┤
              └─────────┘     └─────────┘          │
                                                    │
              ┌─────────┐     ┌─────────┐     ┌────▼────┐
  T,E1 ──────▶│  CROSS  │────▶│  DOT    │────▶│  MULT   │── t, v
              │  (Q)    │     │  (D·Q)  │     │ (×inv)  │
              └─────────┘     └─────────┘     └─────────┘

Depth: 5 pipeline stages (SUB→CROSS→DOT→RECIP→MULT)
```

### Module Hierarchy

```
sobekcore/
├── sobek_top.sv               # Top-level + pipeline controller
├── sobek_stage1_sub.sv        # E1 = V1-V0, E2 = V2-V0, T = O-V0
├── sobek_stage2_cross.sv      # P = D×E2, Q = T×E1
├── sobek_stage3_dot.sv        # det = E1·P, T·P, D·Q
├── sobek_stage4_recip.sv      # inv_det = 1/det (Newton-Raphson)
├── sobek_stage5_mult.sv       # t, u, v × inv_det
├── sobek_watertight.sv        # Watertight edge handling
├── sobek_test.sv              # Hit test: u≥0, v≥0, u+v≤1, t∈[min,max]
├── sobek_bvh_stack.sv         # BVH traversal stack (external)
├── sobek_ray_input.sv         # Ray formatting + denorm handling
└── sobek_hit_output.sv       # Hit record (t, u, v, tri_id)
```

### Watertight Intersection

Watertightness ensures that rays hitting shared edges between triangles don't slip through due to floating-point rounding. SobekCore implements:

1. **Edge classification** — Each edge uses a tie-breaker rule based on the edge's orientation
2. **Sheared arithmetic** — Subtract scaled ray direction to reduce cancellation
3. **Double-hit prevention** — Always report the closest hit (t-minimum)

---

## 3. Golden Reference

```
golden/
├── moeller_trumbore.py        # Möller-Trumbore reference (numpy float64)
├── watertight.py              # Watertight edge handling
├── bvh.py                     # BVH construction and traversal
├── scene_generator.py         # Random triangle scene generator
├── ray_gen.py                 # Random ray generator
└── tests/
    ├── test_intersection.py   # Random rays vs known intersections
    ├── test_watertight.py     # Edge-cases: shared edges, vertices
    ├── test_parallel.py       # Ray parallel to triangle → no hit
    ├── test_degenerate.py     # Degenerate triangles (zero area)
    └── test_backface.py       # Backface culling if enabled
```

---

## 4. Testing Strategy

| Test | Count | What It Verifies |
|------|:-----:|------------------|
| Golden: random intersection | 6 | Random rays, random triangles, compare |
| Golden: watertight edges | 4 | Rays along shared edges (must hit one) |
| Golden: parallel rays | 3 | Must return no hit |
| Golden: degenerate | 3 | Zero-area triangles |
| pymodel: pipeline stages | 6 | Each stage bit-accurate |
| RTL: stage1_sub | 4 | E1, E2, T correctness |
| RTL: stage2_cross | 4 | P, Q cross products |
| RTL: stage3_dot | 4 | det, T·P, D·Q |
| RTL: stage4_recip | 4 | 1/det ULP error ≤ 1 |
| RTL: full pipeline | 6 | Complete intersection vs golden |
| **Total** | **~44** | |

---

## 5. Dependencies

| Dependency | Why | Project |
|------------|-----|---------|
| HapiCore | FP32 mul, add, sub, reciprocal | [docs/09_HapiCore_FPU.md](09_HapiCore_FPU.md) |

---

## 6. Physical Design

| Parameter | Target |
|-----------|--------|
| Pipeline depth | 5 stages |
| Throughput | 1 ray-triangle/cycle |
| Clock | 500 MHz |
| Ray-triangle throughput | 500M intersections/sec |
| Latency | 5 cycles (10 ns) |
| Gates | ~30K |
| Area | ~0.08 mm² |
| FP units | 6×FP32 FMAs |

---

## 7. Performance Context

| Scene | Triangles | Rays | SobekCore (500 MHz) | Embree (1 core, 4 GHz) |
|-------|:---------:|:----:|:-------------------:|:----------------------:|
| Cornell box | 32 | 1M | 62.5 μs | ~10 ms |
| Bunny (5K) | ~10K | 1M | 20 ms | ~50 ms |
| Sponza | ~66K | 1M | 132 ms | ~200 ms |
| Classroom | ~1M | 1M | 2 sec | ~3 sec |

Performance assumes BVH reduces to ~10 tests/ray. Each test = 1 cycle.

---

## 8. Checkpoints

| # | Checkpoint | Deliverable |
|:-:|------------|-------------|
| SO.1 | Golden: Möller-Trumbore | Bit-exact vs numpy float64 |
| SO.2 | Golden: watertight | Edge cases handled |
| SO.3 | pymodel: pipeline | 5-stage cycle-level |
| SO.4 | RTL: stage 1–3 | Subtract + cross + dot |
| SO.5 | RTL: stage 4 (recip) | Newton accurate to 1 ULP |
| SO.6 | RTL: stage 5 + hit test | Hit/miss correct |
| SO.7 | RTL: full pipeline | 1 intersection/cycle |
| SO.8 | RTL: watertight mode | Edge-handling fp-correct |
| SO.9 | Synthesis | ≤ 40K gates |
| SO.10 | P&R at 500 MHz | DRC clean |

---

*Prev: [NeithCore](07_NeithCore_MLKEM.md) · Next: [HapiCore — FPU Generator](09_HapiCore_FPU.md)*
