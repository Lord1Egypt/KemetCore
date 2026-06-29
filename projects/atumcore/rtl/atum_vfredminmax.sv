// AtumCore — fp32 vector min/max reduction unit (KemetCore Phase 2 RTL)
//
// Horizontal fp32 minimum (op=0, vfredmin) / maximum (op=1, vfredmax) over the active
// elements of one vector. The accumulator is seeded with the reduction identity
// (+inf for min, -inf for max) and folded left-to-right; inactive lanes contribute the
// same identity, which is a no-op. Each fold step uses the SAME monotonic-key + NaN
// rule as atum_vfminmax:
//   * exactly one operand NaN  -> the other (number) operand (NaN propagation)
//   * both NaN                 -> canonical quiet NaN (cannot occur here: the
//                                 accumulator is always a number)
//   * otherwise                -> smaller (min) / larger (max) by unsigned key compare
// key(x) = x[31] ? ~x : (x|msb) reproduces real-value order and places -0 below +0.
// Since the accumulator is seeded with a number and NaN lanes are skipped, an all-NaN
// active set reduces to the identity (matches the golden, documented). Scalar result.
// Purely combinational — Yosys must report 0 latches. Verified — see test_vfredminmax.py.

module atum_vfredminmax #(
    parameter int VLMAX = 8,
    parameter int ELEN  = 32
) (
    input  logic [VLMAX*ELEN-1:0]      vs,
    input  logic                       op,      // 0 = vfredmin, 1 = vfredmax
    input  logic [VLMAX-1:0]           mask,
    input  logic [$clog2(VLMAX+1)-1:0] vl,
    output logic [ELEN-1:0]            result
);
    localparam int VLW = $clog2(VLMAX+1);
    localparam logic [ELEN-1:0] CANON_NAN = 32'h7FC00000;
    localparam logic [ELEN-1:0] POS_INF   = 32'h7F800000;
    localparam logic [ELEN-1:0] NEG_INF   = 32'hFF800000;
    localparam logic [ELEN-1:0] MSB       = {1'b1, {(ELEN-1){1'b0}}};

    always_comb begin
        logic [ELEN-1:0] ident, acc, lane, addend, nxt, ka, kb;
        logic            an, bn, active, pick_a;
        ident = op ? NEG_INF : POS_INF;          // max:-inf, min:+inf
        acc   = ident;
        for (int i = 0; i < VLMAX; i++) begin
            active = mask[i] & (VLW'(i) < vl);
            lane   = vs[i*ELEN +: ELEN];
            addend = active ? lane : ident;       // inactive -> identity (no-op)
            an = (acc[30:23]    == 8'hFF) && (acc[22:0]    != 23'b0);
            bn = (addend[30:23] == 8'hFF) && (addend[22:0] != 23'b0);
            ka = acc[ELEN-1]    ? ~acc    : (acc    | MSB);
            kb = addend[ELEN-1] ? ~addend : (addend | MSB);
            pick_a = op ? (ka >= kb) : (ka <= kb);
            if (an && bn)      nxt = CANON_NAN;
            else if (an)       nxt = addend;
            else if (bn)       nxt = acc;
            else               nxt = pick_a ? acc : addend;
            acc = nxt;
        end
        result = acc;
    end
endmodule
