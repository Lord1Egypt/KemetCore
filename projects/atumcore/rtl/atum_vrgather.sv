// AtumCore — vector register gather unit (KemetCore Phase 2 RTL)
//
// Arbitrary permutation / table lookup: vd[i] = vs[idx[i]], where idx is a vector of
// per-lane source indices. An index >= vl reads 0; tail lanes (i >= vl) read 0.
// This is the general data-motion primitive (shuffle / permute / gather) — the
// counterpart to atum_vcompress (which packs by mask, this routes by explicit
// index).
//
// Each output lane is a full VLMAX:1 mux selecting a source lane by its index. The
// index is compared full-width against vl so any value >= vl (incl >= VLMAX) yields
// 0, matching golden VectorUnit.vrgather exactly. Vectors cross the boundary packed
// little-endian by lane (element i at bits [i*ELEN +: ELEN]). Purely combinational —
// Yosys must report 0 latches. Verified vs the golden — see tb/test_vrgather.py.

module atum_vrgather #(
    parameter int VLMAX = 8,
    parameter int ELEN  = 32
) (
    input  logic [VLMAX*ELEN-1:0]      vs,      // source vector (lane-packed LE)
    input  logic [VLMAX*ELEN-1:0]      idx,     // per-lane source indices
    input  logic [$clog2(VLMAX+1)-1:0] vl,
    output logic [VLMAX*ELEN-1:0]      vd
);
    always_comb begin
        logic [ELEN-1:0] k;
        logic [ELEN-1:0] sel;
        for (int i = 0; i < VLMAX; i++) begin
            k   = idx[i*ELEN +: ELEN];
            sel = '0;
            // full VLMAX:1 mux; an index >= vl (incl >= VLMAX) selects nothing -> 0
            for (int j = 0; j < VLMAX; j++)
                if ((k == ELEN'(j)) && (j < vl))
                    sel = vs[j*ELEN +: ELEN];
            vd[i*ELEN +: ELEN] = (i < vl) ? sel : '0;
        end
    end
endmodule
