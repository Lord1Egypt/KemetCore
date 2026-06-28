// AtumCore — vector floating-point classify unit (KemetCore Phase 2 RTL)
//
// RVV vfclass: each fp32 lane is classified into a 10-bit one-hot class written
// (zero-extended) to the destination element:
//   bit0 -inf  bit1 -normal  bit2 -subnormal  bit3 -0  bit4 +0
//   bit5 +subnormal  bit6 +normal  bit7 +inf  bit8 sNaN  bit9 qNaN
//
// Pure bit inspection (no arithmetic). Tail lanes (i >= vl) read 0. Mirrors golden
// VectorUnit.vfclass exactly. Vectors are lane-packed LE (element i at [i*ELEN +:
// ELEN]); fp32 = {sign[31], exp[30:23], mant[22:0]}. Purely combinational — Yosys
// must report 0 latches. Verified vs the golden — see tb/test_vfclass.py.

module atum_vfclass #(
    parameter int VLMAX = 8,
    parameter int ELEN  = 32          // fp32 lanes
) (
    input  logic [VLMAX*ELEN-1:0]      vs,
    input  logic [$clog2(VLMAX+1)-1:0] vl,
    output logic [VLMAX*ELEN-1:0]      vd
);
    always_comb begin
        logic [ELEN-1:0] x;
        logic            sign;
        logic [7:0]      exp;
        logic [22:0]     mant;
        logic [9:0]      cls;
        for (int i = 0; i < VLMAX; i++) begin
            x    = vs[i*ELEN +: ELEN];
            sign = x[31];
            exp  = x[30:23];
            mant = x[22:0];
            cls  = '0;
            if (exp == 8'hFF) begin
                if (mant == 23'b0) cls[sign ? 0 : 7] = 1'b1;          // -inf / +inf
                else               cls[mant[22] ? 9 : 8] = 1'b1;      // qNaN / sNaN
            end else if (exp == 8'b0) begin
                if (mant == 23'b0) cls[sign ? 3 : 4] = 1'b1;          // -0 / +0
                else               cls[sign ? 2 : 5] = 1'b1;          // -sub / +sub
            end else begin
                cls[sign ? 1 : 6] = 1'b1;                             // -normal / +normal
            end
            vd[i*ELEN +: ELEN] = (i < vl) ? {{(ELEN-10){1'b0}}, cls} : '0;
        end
    end
endmodule
