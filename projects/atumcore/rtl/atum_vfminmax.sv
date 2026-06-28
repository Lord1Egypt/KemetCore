// AtumCore — vector floating-point min/max unit (KemetCore Phase 2 RTL)
//
// IEEE-style fp32 vfmin (op=0) / vfmax (op=1) per lane, with proper NaN handling:
//   * both operands NaN        -> canonical quiet NaN (0x7FC00000)
//   * exactly one operand NaN  -> the other (number) operand  (NaN propagation rule)
//   * otherwise                -> the smaller (min) / larger (max) value
//
// Ordering uses a monotonic float->key transform: key(x) = x[31] ? ~x : (x|msb).
// Under an UNSIGNED key compare this reproduces real-value order AND places -0 below
// +0, so min/max return the IEEE-recommended signed-zero result with no special case.
// Mirrors golden VectorUnit.vfmin / vfmax exactly. Vectors are lane-packed LE
// (element i at [i*ELEN +: ELEN]). Purely combinational — Yosys must report 0
// latches. Verified vs the golden — see tb/test_vfminmax.py.

module atum_vfminmax #(
    parameter int VLMAX = 8,
    parameter int ELEN  = 32          // fp32 lanes
) (
    input  logic [VLMAX*ELEN-1:0]      vs1,
    input  logic [VLMAX*ELEN-1:0]      vs2,
    input  logic                       op,      // 0 = vfmin, 1 = vfmax
    input  logic [$clog2(VLMAX+1)-1:0] vl,
    output logic [VLMAX*ELEN-1:0]      vd
);
    localparam logic [ELEN-1:0] CANON_NAN = 32'h7FC00000;

    // MSB-only constant for the monotonic float->uint key (no sized cast / function,
    // which the apt/conda Yosys frontends reject).
    localparam logic [ELEN-1:0] MSB = {1'b1, {(ELEN-1){1'b0}}};

    always_comb begin
        logic [ELEN-1:0] a, b, r, ka, kb;
        logic            an, bn, pick_a;
        for (int i = 0; i < VLMAX; i++) begin
            a  = vs1[i*ELEN +: ELEN];
            b  = vs2[i*ELEN +: ELEN];
            // NaN test ignores the sign bit (used elsewhere via a/b), inlined to keep
            // every temporary assigned on all paths (no latch inference).
            an = (a[30:23] == 8'hFF) && (a[22:0] != 23'b0);
            bn = (b[30:23] == 8'hFF) && (b[22:0] != 23'b0);
            // monotonic key: real-value order == unsigned key order, -0 below +0
            ka = a[ELEN-1] ? ~a : (a | MSB);
            kb = b[ELEN-1] ? ~b : (b | MSB);
            pick_a = op ? (ka >= kb) : (ka <= kb);   // max : min
            if (an && bn)      r = CANON_NAN;
            else if (an)       r = b;
            else if (bn)       r = a;
            else               r = pick_a ? a : b;
            vd[i*ELEN +: ELEN] = (i < vl) ? r : '0;
        end
    end
endmodule
