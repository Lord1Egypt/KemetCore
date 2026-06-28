// AtumCore — vector mask set-before/including/only-first unit (KemetCore Phase 2 RTL)
//
// RVV mask-manipulation relative to the first set bit f of the source mask (within
// vl):
//   op=0 vmsbf -> set bits strictly before f
//   op=1 vmsif -> set bits up to and including f
//   op=2 vmsof -> set only f
// If no source bit is set: vmsbf/vmsif fill the whole body (i < vl) with 1, vmsof
// yields all 0. Tail lanes (i >= vl) read 0. These complete the RVV mask-manip set
// (used to build leading/trailing predicates from a found element).
//
// A priority scan finds f; a per-lane compare then forms the result. Mirrors golden
// VectorUnit.vmsbf/vmsif/vmsof exactly. Purely combinational — Yosys must report 0
// latches. Verified vs the golden — see tb/test_vmsbf.py.

module atum_vmsbf #(
    parameter int VLMAX = 8
) (
    input  logic [VLMAX-1:0]           m,
    input  logic [1:0]                 op,      // 0 sbf, 1 sif, 2 sof
    input  logic [$clog2(VLMAX+1)-1:0] vl,
    output logic [VLMAX-1:0]           vd_mask
);
    always_comb begin
        logic found;
        int   f;
        found = 1'b0;
        f     = 0;
        // first set bit within vl (lowest index wins)
        for (int i = 0; i < VLMAX; i++) begin
            if (!found && (i < vl) && m[i]) begin
                f     = i;
                found = 1'b1;
            end
        end
        for (int i = 0; i < VLMAX; i++) begin
            logic r;
            if (i >= vl) r = 1'b0;
            else unique case (op)
                2'd0:    r = (!found) || (i <  f);     // vmsbf
                2'd1:    r = (!found) || (i <= f);     // vmsif
                2'd2:    r = found && (i == f);        // vmsof
                default: r = 1'b0;
            endcase
            vd_mask[i] = r;
        end
    end
endmodule
