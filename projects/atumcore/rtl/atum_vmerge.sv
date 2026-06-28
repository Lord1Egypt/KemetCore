// AtumCore — vector merge / select unit (KemetCore Phase 2 RTL)
//
// Mask-driven element select: vd[i] = m[i] ? vs1[i] : vs2[i] for i < vl (tail reads
// 0). This is the DATA consumer of the mask toolkit — it picks between two source
// vectors per lane, the standard way to apply a predicated result (e.g. blend the
// output of an operation only where a vms* compare held).
//
// A per-lane 2:1 mux gated by the body-active condition. Mirrors golden
// VectorUnit.vmerge exactly. Vectors cross the boundary packed little-endian by lane
// (element i at bits [i*ELEN +: ELEN]). Purely combinational — Yosys must report 0
// latches. Verified vs the golden — see tb/test_vmerge.py.

module atum_vmerge #(
    parameter int VLMAX = 8,
    parameter int ELEN  = 32
) (
    input  logic [VLMAX*ELEN-1:0]      vs1,     // taken where m[i] = 1
    input  logic [VLMAX*ELEN-1:0]      vs2,     // taken where m[i] = 0
    input  logic [VLMAX-1:0]           m,       // select mask
    input  logic [$clog2(VLMAX+1)-1:0] vl,
    output logic [VLMAX*ELEN-1:0]      vd
);
    always_comb begin
        for (int i = 0; i < VLMAX; i++) begin
            logic [ELEN-1:0] sel;
            sel = m[i] ? vs1[i*ELEN +: ELEN] : vs2[i*ELEN +: ELEN];
            vd[i*ELEN +: ELEN] = (i < vl) ? sel : '0;
        end
    end
endmodule
