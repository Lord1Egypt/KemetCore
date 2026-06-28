// AtumCore — vector slide-by-1 unit (KemetCore Phase 2 RTL)
//
// Slide elements by exactly one lane, inserting a scalar at the vacated end — the
// RVV vslide1up / vslide1down ops (used to shift a new element into a vector queue,
// e.g. building a sliding window):
//   op=0 vslide1up   -> vd[0] = x,      vd[i] = vs[i-1]  (0 < i < vl)
//   op=1 vslide1down -> vd[vl-1] = x,   vd[i] = vs[i+1]  (i < vl-1)
// Tail lanes (i >= vl) read 0. Mirrors golden VectorUnit.vslide1up / vslide1down
// exactly. Vectors are lane-packed LE. Purely combinational — Yosys must report 0
// latches. Verified vs the golden — see tb/test_vslide1.py.

module atum_vslide1 #(
    parameter int VLMAX = 8,
    parameter int ELEN  = 32
) (
    input  logic [VLMAX*ELEN-1:0]      vs,
    input  logic [ELEN-1:0]            x,       // scalar inserted at the vacated end
    input  logic                       op,      // 0 = slide1up, 1 = slide1down
    input  logic [$clog2(VLMAX+1)-1:0] vl,
    output logic [VLMAX*ELEN-1:0]      vd
);
    always_comb begin
        logic [ELEN-1:0] e;
        for (int i = 0; i < VLMAX; i++) begin
            if (op == 1'b0) begin
                // slide up: lane 0 gets x, others take the lane below
                e = (i == 0) ? x : vs[(i-1)*ELEN +: ELEN];
            end else begin
                // slide down: the top active lane (where i+1 is NOT active, i.e.
                // i+1 >= vl) gets x; others take the lane above. When i+1 < vl we
                // have i+1 <= vl-1 < VLMAX, so the part-select is always in range.
                if (!((i + 1) < vl)) e = x;
                else                 e = vs[(i+1)*ELEN +: ELEN];
            end
            vd[i*ELEN +: ELEN] = (i < vl) ? e : '0;
        end
    end
endmodule
