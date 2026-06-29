// AtumCore — vector averaging add/sub with rounding (KemetCore Phase 2 RTL)
//
// RVV fixed-point averaging: VLMAX parallel lanes computing (a +/- b) >> 1 with
// round-to-nearest, ties up (vxrm rnu) — the sum/difference is formed one bit wider
// (so it never overflows) and then halved with rounding. op selects:
//   0 vaaddu : unsigned average  (a + b) >> 1
//   1 vaadd  : signed   average  (a + b) >> 1
//   2 vasub  : signed   average difference (a - b) >> 1
// The (SEW+1)-bit intermediate is held in `v`; the rounded halving is then uniform for
// both signednesses: result = v[ELEN:1] + v[0] — bits[ELEN:1] are the >>1 (the top bit
// is the carry for unsigned / the sign for signed, so the extraction is the right
// logical/arithmetic shift), and v[0] is the rnu rounding increment. (vasubu is omitted
// — its unsigned-underflow rounding semantics are a known RVV ambiguity.)
//
// Active-element semantics match atum_valu / golden _wr_int: a lane writes only when
// body-active (i < vl) AND mask-active; else the destination element is undisturbed.
// Operands cross the boundary packed little-endian by lane (element i at [i*ELEN +:
// ELEN]). Purely combinational — Yosys must report 0 latches. Verified vs the golden —
// see tb/test_vaadd.py.

module atum_vaadd #(
    parameter int VLMAX = 8,
    parameter int ELEN  = 32
) (
    input  logic [VLMAX*ELEN-1:0]      vs1,
    input  logic [VLMAX*ELEN-1:0]      vs2,
    input  logic [VLMAX*ELEN-1:0]      vd_old,
    input  logic [1:0]                 op,    // 0 vaaddu, 1 vaadd, 2 vasub
    input  logic [VLMAX-1:0]           mask,
    input  logic [$clog2(VLMAX+1)-1:0] vl,
    output logic [VLMAX*ELEN-1:0]      vd_new
);
    always_comb begin
        for (int i = 0; i < VLMAX; i++) begin
            logic [ELEN-1:0]        a, b, res;
            logic [ELEN:0]          usum, vsel;       // (SEW+1)-bit intermediates
            logic signed [ELEN:0]   ssum, sdiff;
            logic                   active;
            a = vs1[i*ELEN +: ELEN];
            b = vs2[i*ELEN +: ELEN];
            usum  = {1'b0, a} + {1'b0, b};                                  // unsigned a+b
            ssum  = $signed({a[ELEN-1], a}) + $signed({b[ELEN-1], b});      // signed a+b
            sdiff = $signed({a[ELEN-1], a}) - $signed({b[ELEN-1], b});      // signed a-b
            unique case (op)
                2'd0:    vsel = usum;
                2'd1:    vsel = ssum;
                2'd2:    vsel = sdiff;
                default: vsel = '0;
            endcase
            // (v >> 1) + rnu rounding increment; uniform for signed/unsigned.
            res = vsel[ELEN:1] + {{(ELEN-1){1'b0}}, vsel[0]};
            active = (i < vl) && mask[i];
            vd_new[i*ELEN +: ELEN] = active ? res : vd_old[i*ELEN +: ELEN];
        end
    end
endmodule
