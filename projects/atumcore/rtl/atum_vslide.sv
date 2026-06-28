// AtumCore — vector slide unit (KemetCore Phase 2 RTL)
//
// Slides vector elements across lanes by a scalar offset — a fundamental data-motion
// op for stencils, shifts and reduction trees:
//   op=0 vslideup   -> vd[i] = vs[i-off] for off <= i < vl (lanes below off and the
//                      tail read 0).
//   op=1 vslidedown -> vd[i] = vs[i+off] for i < vl when i+off < vl, else 0.
//
// Each output lane is a VLMAX:1 mux selecting the source lane at the slid index;
// offsets are compared full-width so an out-of-range slide yields 0. Mirrors golden
// VectorUnit.vslideup / vslidedown exactly. Vectors cross the boundary packed
// little-endian by lane (element i at bits [i*ELEN +: ELEN]). Purely combinational —
// Yosys must report 0 latches. Verified vs the golden — see tb/test_vslide.py.

module atum_vslide #(
    parameter int VLMAX = 8,
    parameter int ELEN  = 32
) (
    input  logic [VLMAX*ELEN-1:0]      vs,      // source vector (lane-packed LE)
    input  logic [ELEN-1:0]            off,     // scalar slide offset
    input  logic                       op,      // 0 = slideup, 1 = slidedown
    input  logic [$clog2(VLMAX+1)-1:0] vl,
    output logic [VLMAX*ELEN-1:0]      vd
);
    always_comb begin
        logic [ELEN-1:0] sel;
        for (int i = 0; i < VLMAX; i++) begin
            sel = '0;
            for (int j = 0; j < VLMAX; j++) begin
                if (op == 1'b0) begin
                    // slideup: src lane j lands at lane j+off  (i = j+off), i < vl
                    if ((ELEN'(j) + off == ELEN'(i)) && (i < vl))
                        sel = vs[j*ELEN +: ELEN];
                end else begin
                    // slidedown: lane i takes src lane i+off (j = i+off), j < vl
                    if ((ELEN'(i) + off == ELEN'(j)) && (j < vl) && (i < vl))
                        sel = vs[j*ELEN +: ELEN];
                end
            end
            vd[i*ELEN +: ELEN] = sel;
        end
    end
endmodule
