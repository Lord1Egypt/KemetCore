# KemetCore — GDSII harden results

Signed-off ASAP7 7 nm layouts (routed GDSII, timing WNS 0.00 = closes, 0 antenna DRC),
produced locally via `flow/harden_train.sh`. WNS 0.00 ⇒ meets timing at the clock in
each design's `constraint.sdc`.

| design | GDS | area (µm²) | WNS (ps) | antenna DRC | RAM (MB) |
|--------|:---:|-----------:|---------:|:-----------:|---------:|
| `sha256_core` | ✅ 13M | 1286 | 0.00 | 4× clean | 20 |
| `seth_regfile` | ✅ 9.6M | 907 | 0.00 | 4× clean | 20 |
| `bast_mac` (BF16 MAC) | ✅ 6.8M | 499 | 0.00 | 4× clean | ~1850 |
| `ra_noc_arbiter` | ✅ 1.7M | 132 | 0.00 | 4× clean | 20 |
