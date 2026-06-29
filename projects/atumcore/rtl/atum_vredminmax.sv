// AtumCore — integer vector min/max reduction unit (KemetCore Phase 2 RTL)
//
// Horizontal integer minimum/maximum over the active elements of one vector, in both
// unsigned and signed flavours (the existing atum_vredu only covers an unsigned max):
//   op = 0 vredminu  (unsigned min, identity 0xFFFFFFFF)
//   op = 1 vredmaxu  (unsigned max, identity 0x00000000)
//   op = 2 vredmin   (signed   min, identity 0x7FFFFFFF = INT_MAX)
//   op = 3 vredmax   (signed   max, identity 0x80000000 = INT_MIN)
// A lane participates only when body-active (i < vl) AND mask-active; inactive lanes
// contribute the identity (a no-op). Signed compares use dedicated $signed nets so the
// unsigned identity constants never coerce the comparison to unsigned (the SystemVerilog
// ternary/relational signedness trap). Scalar result. Purely combinational — Yosys must
// report 0 latches. Verified vs the golden — see tb/test_vredminmax.py.

module atum_vredminmax #(
    parameter int VLMAX = 8,
    parameter int ELEN  = 32
) (
    input  logic [VLMAX*ELEN-1:0]      vs,
    input  logic [1:0]                 op,      // 0 minu, 1 maxu, 2 min(s), 3 max(s)
    input  logic [VLMAX-1:0]           mask,
    input  logic [$clog2(VLMAX+1)-1:0] vl,
    output logic [ELEN-1:0]            result
);
    localparam int VLW = $clog2(VLMAX+1);
    localparam logic [ELEN-1:0] U_MAX  = {ELEN{1'b1}};        // 0xFFFFFFFF
    localparam logic [ELEN-1:0] S_MAX  = {1'b0, {(ELEN-1){1'b1}}}; // 0x7FFFFFFF
    localparam logic [ELEN-1:0] S_MIN  = {1'b1, {(ELEN-1){1'b0}}}; // 0x80000000

    always_comb begin
        logic [ELEN-1:0] ident, acc, lane, addend, nxt;
        logic            active, keep;
        unique case (op)
            2'd0:    ident = U_MAX;     // unsigned min
            2'd1:    ident = '0;        // unsigned max
            2'd2:    ident = S_MAX;     // signed min
            default: ident = S_MIN;     // signed max
        endcase
        acc = ident;
        for (int i = 0; i < VLMAX; i++) begin
            active = mask[i] & (VLW'(i) < vl);
            lane   = vs[i*ELEN +: ELEN];
            addend = active ? lane : ident;          // inactive -> identity (no-op)
            unique case (op)
                2'd0:    keep = (acc <= addend);                       // unsigned
                2'd1:    keep = (acc >= addend);                       // unsigned
                2'd2:    keep = ($signed(acc) <= $signed(addend));     // signed
                default: keep = ($signed(acc) >= $signed(addend));     // signed
            endcase
            nxt = keep ? acc : addend;
            acc = nxt;
        end
        result = acc;
    end
endmodule
