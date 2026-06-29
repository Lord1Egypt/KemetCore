// AtumCore — vector integer divide / remainder (KemetCore Phase 2 RTL)
//
// RVV vdivu / vdiv / vremu / vrem: VLMAX parallel lanes computing element-wise integer
// division or remainder, with the RVV special cases (no traps), selected by op:
//   0 vdivu : unsigned quotient   a / b
//   1 vdiv  : signed   quotient   a / b   (truncated toward zero)
//   2 vremu : unsigned remainder  a % b
//   3 vrem  : signed   remainder  a % b   (remainder takes the sign of a)
// Special cases per the RVV spec (no divide-by-zero trap):
//   * b == 0           -> quotient = all-ones (= -1 / UINT_MAX); remainder = a
//   * signed overflow  -> a == INT_MIN, b == -1: quotient = INT_MIN; remainder = 0
// Otherwise SystemVerilog $div/$mod give C-style truncate-toward-zero with the
// remainder sign = dividend, matching RVV. Active-element semantics match atum_valu /
// golden _wr_int: a lane writes only when body-active (i < vl) AND mask-active; else the
// destination element is undisturbed. Operands cross the boundary packed little-endian
// by lane (element i at [i*ELEN +: ELEN]). Purely combinational — Yosys must report 0
// latches. Verified vs the golden — see tb/test_vdiv.py.

module atum_vdiv #(
    parameter int VLMAX = 8,
    parameter int ELEN  = 32
) (
    input  logic [VLMAX*ELEN-1:0]      vs1,
    input  logic [VLMAX*ELEN-1:0]      vs2,
    input  logic [VLMAX*ELEN-1:0]      vd_old,
    input  logic [1:0]                 op,    // 0 vdivu, 1 vdiv, 2 vremu, 3 vrem
    input  logic [VLMAX-1:0]           mask,
    input  logic [$clog2(VLMAX+1)-1:0] vl,
    output logic [VLMAX*ELEN-1:0]      vd_new
);
    localparam logic [ELEN-1:0] IMIN = {1'b1, {(ELEN-1){1'b0}}};   // INT_MIN
    localparam logic [ELEN-1:0] MONE = {ELEN{1'b1}};               // -1 / UINT_MAX

    always_comb begin
        for (int i = 0; i < VLMAX; i++) begin
            logic [ELEN-1:0]      a, b, res;
            logic [ELEN-1:0]      udiv, umod, sdiv, smod;
            logic signed [ELEN-1:0] sa, sb, sq, sr;
            logic                 div0, ovf, active;
            a = vs1[i*ELEN +: ELEN];
            b = vs2[i*ELEN +: ELEN];
            div0 = (b == '0);
            ovf  = (a == IMIN) && (b == MONE);               // signed INT_MIN / -1
            // compute signed quotient/remainder in dedicated signed nets so the
            // special-case muxes (which mix in unsigned constants) can't coerce the
            // division back to unsigned (the classic ?: signedness trap)
            sa = $signed(a);
            sb = $signed(b);
            sq = sa / sb;
            sr = sa % sb;
            udiv = div0 ? MONE : (a / b);
            umod = div0 ? a    : (a % b);
            sdiv = div0 ? MONE : (ovf ? IMIN : sq);
            smod = div0 ? a    : (ovf ? '0   : sr);
            unique case (op)
                2'd0:    res = udiv;
                2'd1:    res = sdiv;
                2'd2:    res = umod;
                2'd3:    res = smod;
                default: res = '0;
            endcase
            active = (i < vl) && mask[i];
            vd_new[i*ELEN +: ELEN] = active ? res : vd_old[i*ELEN +: ELEN];
        end
    end
endmodule
