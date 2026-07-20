# KemetCore — GDSII harden results

Signed-off ASAP7 7 nm layouts (routed GDSII), produced locally via `flow/harden.sh`. **WNS ≥ 0 ⇒ timing closes** at the clock in each design's `constraint.sdc`; the Fmax column is that clock. Deep single-cycle combinational blocks (dot3, attention score) close at a low clock by design — they are one giant unpipelined path.

**71 blocks across 11 cores** carried to routed GDSII with timing closed and 0 routing-DRC violations.

| # | design | core | GDS (MB) | area (µm²) | util | Fmax (MHz) | WNS (ps) | route DRC | closes |
|:-:|--------|------|---------:|-----------:|:----:|-----------:|---------:|:---------:|:------:|
| 1 | `ra_noc_arbiter` | RaCore | 1.7 | 132.0 | 40.0% | 667 | 0.00 | 0 viol | ✅ |
| 2 | `ra_kai_regs` | RaCore | 1.8 | 158.0 | 41.0% | 667 | 0.00 | 0 viol | ✅ |
| 3 | `seth_regfile` | SethCore | 10.0 | 907.0 | 36.0% | 1000 | 0.00 | 0 viol | ✅ |
| 4 | `seth_alu` | SethCore | 2.5 | 188.0 | 37.0% | 400 | 0.00 | 0 viol | ✅ |
| 5 | `seth_muldiv` | SethCore | 24.0 | 2154.0 | 36.0% | 100 | 0.00 | 0 viol | ✅ |
| 6 | `seth_branch` | SethCore | 0.5 | 46.0 | 43.0% | 400 | 0.00 | 0 viol | ✅ |
| 7 | `seth_imm` | SethCore | 0.5 | 43.0 | 46.0% | 400 | 0.00 | 0 viol | ✅ |
| 8 | `seth_aluctl` | SethCore | 0.3 | 14.0 | 46.0% | 400 | 0.00 | 0 viol | ✅ |
| 9 | `seth_decode` | SethCore | 0.3 | 16.0 | 45.0% | 400 | 0.00 | 0 viol | ✅ |
| 10 | `seth_trap` | SethCore | 1.9 | 212.0 | 46.0% | 400 | 0.00 | 0 viol | ✅ |
| 11 | `ptah_mac` | PtahConv | 12.6 | 940.0 | 35.0% | 167 | 0.00 | 0 viol | ✅ |
| 12 | `ptah_bias_relu` | PtahConv | 41.3 | 3328.0 | 35.0% | 167 | 0.00 | 0 viol | ✅ |
| 13 | `ptah_avgpool` | PtahConv | 21.5 | 1468.0 | 35.0% | 100 | 0.00 | 0 viol | ✅ |
| 14 | `ptah_maxpool` | PtahConv | 1.7 | 173.0 | 47.0% | 500 | 0.00 | 0 viol | ✅ |
| 15 | `imentet_qk_score` | ImentetCore | 89.7 | 7757.0 | 39.0% | 50 | 0.00 | 0 viol | ✅ |
| 16 | `imentet_mask_add` | ImentetCore | 47.8 | 3455.0 | 15.0% | 50 | 0.00 | 0 viol | ✅ |
| 17 | `imentet_rowmax_sub` | ImentetCore | 47.6 | 3543.0 | 40.0% | 50 | 0.00 | 0 viol | ✅ |
| 18 | `imentet_av_context` | ImentetCore | 142.2 | 12153.0 | 39.0% | 50 | 0.00 | 0 viol | ✅ |
| 19 | `geb_spmac` | GebCore | 12.7 | 948.0 | 35.0% | 50 | 0.00 | 0 viol | ✅ |
| 20 | `geb_spmac_grid` | GebCore | 184.2 | 15853.0 | 40.0% | 50 | 0.00 | 0 viol | ✅ |
| 21 | `bast_mac` | BastCore | 7.1 | 499.0 | 36.0% | 250 | 0.00 | 0 viol | ✅ |
| 22 | `bast_mac_grid` | BastCore | 102.8 | 7905.0 | 35.0% | 222 | 0.00 | 0 viol | ✅ |
| 23 | `bast_int8_mac` | BastCore | 1.0 | 86.0 | 40.0% | 667 | 0.00 | 0 viol | ✅ |
| 24 | `sha256_core` | AnubisCore | 12.9 | 1286.0 | 41.0% | 500 | 0.00 | 0 viol | ✅ |
| 25 | `neith_ntt` | NeithCore | 100.5 | 5817.0 | 37.0% | 250 | 0.00 | 0 viol | ✅ |
| 26 | `neith_butterfly` | NeithCore | 2.8 | 264.0 | 32.0% | 100 | 0.00 | 0 viol | ✅ |
| 27 | `neith_polyaddsub` | NeithCore | 27.9 | 2624.0 | 43.0% | 100 | 0.00 | 0 viol | ✅ |
| 28 | `neith_modmul` | NeithCore | 2.3 | 219.0 | 41.0% | 100 | 0.00 | 0 viol | ✅ |
| 29 | `neith_pointwise` | NeithCore | 28.8 | 2679.0 | 43.0% | 100 | 0.00 | 0 viol | ✅ |
| 30 | `neith_compress` | NeithCore | 1.6 | 113.0 | 41.0% | 100 | 0.00 | 0 viol | ✅ |
| 31 | `sobek_dot3` | SobekCore | 29.7 | 2352.0 | 35.0% | 111 | 0.00 | 0 viol | ✅ |
| 32 | `sobek_lerp` | SobekCore | 52.7 | 3777.0 | 15.0% | 100 | 0.00 | 0 viol | ✅ |
| 33 | `sobek_ray_point` | SobekCore | 35.6 | 2773.0 | 20.0% | 100 | 0.00 | 0 viol | ✅ |
| 34 | `sobek_faceforward` | SobekCore | 31.9 | 2395.0 | 15.0% | 100 | 0.00 | 0 viol | ✅ |
| 35 | `sobek_cross` | SobekCore | 49.7 | 4213.0 | 34.0% | 111 | 0.00 | 0 viol | ✅ |
| 36 | `sobek_scale` | SobekCore | 17.1 | 1548.0 | 35.0% | 111 | 0.00 | 0 viol | ✅ |
| 37 | `sobek_distance` | SobekCore | 55.7 | 4312.0 | 40.0% | 50 | 0.00 | 0 viol | ✅ |
| 38 | `hapi_fp32_mul` | HapiCore | 6.1 | 531.0 | 35.0% | 286 | 0.00 | 0 viol | ✅ |
| 39 | `hapi_fp16_mul` | HapiCore | 2.1 | 166.0 | 36.0% | 286 | 0.00 | 0 viol | ✅ |
| 40 | `hapi_bf16_mul` | HapiCore | 1.6 | 119.0 | 37.0% | 286 | 0.00 | 0 viol | ✅ |
| 41 | `hapi_fp16_add` | HapiCore | 2.5 | 179.0 | 36.0% | 286 | 0.00 | 0 viol | ✅ |
| 42 | `hapi_bf16_add` | HapiCore | 2.1 | 151.0 | 37.0% | 286 | 0.00 | 0 viol | ✅ |
| 43 | `hapi_fp32_add` | HapiCore | 5.8 | 437.0 | 35.0% | 286 | 0.00 | 0 viol | ✅ |
| 44 | `hapi_fp32_to_int` | HapiCore | 2.5 | 165.0 | 21.0% | 100 | 0.00 | 0 viol | ✅ |
| 45 | `hapi_int_to_fp32` | HapiCore | 2.4 | 175.0 | 36.0% | 286 | 0.00 | 0 viol | ✅ |
| 46 | `hapi_fp32_sgnj` | HapiCore | 0.3 | 32.0 | 50.0% | 286 | 0.00 | 0 viol | ✅ |
| 47 | `hapi_fp32_cmp` | HapiCore | 0.7 | 59.0 | 31.0% | 286 | 0.00 | 0 viol | ✅ |
| 48 | `hapi_fp32_class` | HapiCore | 0.3 | 22.0 | 35.0% | 286 | 0.00 | 0 viol | ✅ |
| 49 | `hapi_fp32_minmax` | HapiCore | 0.9 | 73.0 | 30.0% | 286 | 0.00 | 0 viol | ✅ |
| 50 | `hapi_fp16_class` | HapiCore | 0.2 | 14.0 | 35.0% | 286 | 0.00 | 0 viol | ✅ |
| 51 | `hapi_fp16_cmp` | HapiCore | 0.4 | 30.0 | 31.0% | 286 | 0.00 | 0 viol | ✅ |
| 52 | `hapi_fp16_minmax` | HapiCore | 0.6 | 38.0 | 30.0% | 286 | 0.00 | 0 viol | ✅ |
| 53 | `hapi_fp16_sgnj` | HapiCore | 0.2 | 17.0 | 56.0% | 286 | 0.00 | 0 viol | ✅ |
| 54 | `hapi_bf16_class` | HapiCore | 0.2 | 14.0 | 35.0% | 286 | 0.00 | 0 viol | ✅ |
| 55 | `hapi_bf16_cmp` | HapiCore | 0.4 | 30.0 | 31.0% | 286 | 0.00 | 0 viol | ✅ |
| 56 | `hapi_bf16_minmax` | HapiCore | 0.5 | 37.0 | 30.0% | 286 | 0.00 | 0 viol | ✅ |
| 57 | `hapi_bf16_sgnj` | HapiCore | 0.2 | 17.0 | 36.0% | 286 | 0.00 | 0 viol | ✅ |
| 58 | `hapi_fp32_to_bf16` | HapiCore | 0.4 | 27.0 | 46.0% | 286 | 0.00 | 0 viol | ✅ |
| 59 | `hapi_fp32_to_fp16` | HapiCore | 1.2 | 81.0 | 37.0% | 286 | 0.00 | 0 viol | ✅ |
| 60 | `hapi_bf16_to_fp32` | HapiCore | 0.2 | 17.0 | 47.0% | 286 | 0.00 | 0 viol | ✅ |
| 61 | `hapi_fp16_to_fp32` | HapiCore | 0.6 | 30.0 | 42.0% | 286 | 0.00 | 0 viol | ✅ |
| 62 | `atum_valu` | AtumCore | 39.1 | 3702.0 | 36.0% | 200 | 0.00 | 0 viol | ✅ |
| 63 | `atum_vredu` | AtumCore | 4.6 | 436.0 | 38.0% | 200 | 0.00 | 0 viol | ✅ |
| 64 | `atum_vsadd` | AtumCore | 14.0 | 1243.0 | 17.0% | 111 | 0.00 | 0 viol | ✅ |
| 65 | `atum_vcompress` | AtumCore | 5.8 | 471.0 | 22.0% | 100 | 0.00 | 0 viol | ✅ |
| 66 | `atum_viota` | AtumCore | 0.7 | 44.0 | 41.0% | 100 | 0.00 | 0 viol | ✅ |
| 67 | `atum_vmask` | AtumCore | 2.3 | 302.0 | 50.0% | 100 | 0.00 | 0 viol | ✅ |
| 68 | `atum_vsetvl` | AtumCore | 0.3 | 18.0 | 36.0% | 500 | 0.00 | 0 viol | ✅ |
| 69 | `atum_vfpu` | AtumCore | 70.9 | 6116.0 | 40.0% | 200 | 0.00 | 0 viol | ✅ |
| 70 | `atum_vregfile` | AtumCore | 97.3 | 8898.0 | 38.0% | 500 | 0.00 | 0 viol | ✅ |
| 71 | `atum_vimac` | AtumCore | 39.4 | 4433.0 | 41.0% | 200 | 0.00 | 0 viol | ✅ |

_Auto-generated by `flow/gen_harden_results.py` from the ORFS reports. Every core (00–10) has at least one representative block on 7 nm silicon._
