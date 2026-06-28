// AtumCore — vector fp32 compare-to-mask unit (KemetCore Phase 2 RTL)
//
// The fp predication datapath of the RVV unit: VLMAX parallel fp32 comparators that
// evaluate one element-wise floating-point compare (vd_mask[i] = vs1[i] CMP vs2[i])
// in a single combinational pass. The destination is a MASK register (one bit per
// lane) — what RVV vmfeq/vmflt/... write and what masked execution consumes. The fp
// analog of atum_vmask.
//
// IEEE-754 ordered/unordered semantics: if either operand is NaN the compare is
// UNORDERED -> every relation is false except vmfne, which is true. +0 and -0 compare
// EQUAL. Ordering of finite/Inf values uses a monotonic sign-magnitude key (negatives
// reversed) so an unsigned key compare matches real-value order; the both-zero case
// is forced equal so +0/-0 don't split. Mirrors golden VectorUnit._fcmp (numpy fp
// compare) exactly.
//
// A lane bit is set only when body-active (i < vl) AND mask-active (mask[i]) AND the
// relation holds; otherwise 0. Operands cross the boundary packed little-endian by
// lane: element i at [i*ELEN +: ELEN]. Purely combinational — Yosys must report 0
// latches. Verified vs the golden — see tb/test_vmfcmp.py.

module atum_vmfcmp #(
    parameter int VLMAX = 8,
    parameter int ELEN  = 32
) (
    input  logic [VLMAX*ELEN-1:0]      vs1,
    input  logic [VLMAX*ELEN-1:0]      vs2,
    input  logic [2:0]                 op,
    input  logic [VLMAX-1:0]           mask,
    input  logic [$clog2(VLMAX+1)-1:0] vl,
    output logic [VLMAX-1:0]           vd_mask
);
    // op encoding (matches golden compare method order)
    localparam logic [2:0] OP_EQ = 3'd0,   // ==
                           OP_NE = 3'd1,   // !=
                           OP_LT = 3'd2,   // <
                           OP_LE = 3'd3,   // <=
                           OP_GT = 3'd4,   // >
                           OP_GE = 3'd5;   // >=

    function automatic logic is_nan(input logic [ELEN-1:0] x);
        is_nan = (x[30:23] == 8'hFF) && (x[22:0] != 23'd0);
    endfunction

    function automatic logic is_zero(input logic [ELEN-1:0] x);
        is_zero = (x[30:23] == 8'd0) && (x[22:0] == 23'd0);  // +0 / -0
    endfunction

    always_comb begin
        for (int i = 0; i < VLMAX; i++) begin
            logic [ELEN-1:0] a, b, ka, kb;
            logic            unordered, both_zero, eq_ord, lt_ord, gt_ord, cmp, active;
            a = vs1[i*ELEN +: ELEN];
            b = vs2[i*ELEN +: ELEN];
            unordered = is_nan(a) | is_nan(b);
            both_zero = is_zero(a) & is_zero(b);
            // monotonic key: negatives -> bitwise NOT; non-negatives -> set MSB.
            ka = a[31] ? ~a : (a | 32'h8000_0000);
            kb = b[31] ? ~b : (b | 32'h8000_0000);
            eq_ord = both_zero | (ka == kb);
            lt_ord = ~both_zero & (ka <  kb);
            gt_ord = ~both_zero & (ka >  kb);
            unique case (op)
                OP_EQ:   cmp = unordered ? 1'b0 : eq_ord;
                OP_NE:   cmp = unordered ? 1'b1 : ~eq_ord;
                OP_LT:   cmp = unordered ? 1'b0 : lt_ord;
                OP_LE:   cmp = unordered ? 1'b0 : (eq_ord | lt_ord);
                OP_GT:   cmp = unordered ? 1'b0 : gt_ord;
                OP_GE:   cmp = unordered ? 1'b0 : (eq_ord | gt_ord);
                default: cmp = 1'b0;
            endcase
            active = (i < vl) && mask[i];
            vd_mask[i] = active && cmp;
        end
    end
endmodule
