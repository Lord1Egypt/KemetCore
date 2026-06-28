// AtumCore — vector signed fractional multiply (KemetCore Phase 2 RTL)
//
// RVV vsmul: VLMAX parallel lanes computing the signed fixed-point (Q31) fractional
// product of two elements — the full signed 64-bit product is rounded off by SEW-1
// (=31) fractional bits (round-to-nearest, ties up = vxrm rnu) and then SATURATED to
// the signed 32-bit range. The classic DSP "multiply two Q31 fractions, get a Q31
// fraction" with the single overflow case (-1 * -1 = +1.0 in Q31) pinned to INT32_MAX.
//
// roundoff_signed(prod, 31) = (prod + 2^30) >>> 31 (arithmetic) — exact since the
// product is held at full 64-bit width. Active-element semantics match atum_valu /
// golden _wr_int: a lane writes only when body-active (i < vl) AND mask-active; else
// the destination element is undisturbed. Operands cross the boundary packed
// little-endian by lane (element i at [i*ELEN +: ELEN]). Purely combinational — Yosys
// must report 0 latches. Verified vs the golden — see tb/test_vsmul.py.

module atum_vsmul #(
    parameter int VLMAX = 8,
    parameter int ELEN  = 32
) (
    input  logic [VLMAX*ELEN-1:0]      vs1,
    input  logic [VLMAX*ELEN-1:0]      vs2,
    input  logic [VLMAX*ELEN-1:0]      vd_old,
    input  logic [VLMAX-1:0]           mask,
    input  logic [$clog2(VLMAX+1)-1:0] vl,
    output logic [VLMAX*ELEN-1:0]      vd_new
);
    localparam logic [31:0] SMAX = 32'h7FFF_FFFF;
    localparam logic [31:0] SMIN = 32'h8000_0000;

    always_comb begin
        for (int i = 0; i < VLMAX; i++) begin
            logic [ELEN-1:0]      a, b, res;
            logic signed [63:0]   prod, rnd;
            logic signed [32:0]   shifted;          // 33-bit: holds up to +2^31
            logic                 active;
            a = vs1[i*ELEN +: ELEN];
            b = vs2[i*ELEN +: ELEN];
            // full 64-bit signed product (operands sign-extended to 64 bits)
            prod    = $signed({{32{a[ELEN-1]}}, a}) * $signed({{32{b[ELEN-1]}}, b});
            rnd     = prod + 64'sd1073741824;        // + 2^30  (round-to-nearest, ties up)
            shifted = rnd[63:31];                    // arithmetic >>> 31 -> 33-bit signed
            // saturate to signed 32-bit (only -1*-1 in Q31 overflows -> +2^31 -> SMAX)
            if (shifted > $signed({1'b0, SMAX}))
                res = SMAX;
            else if (shifted < $signed({1'b1, SMIN}))
                res = SMIN;
            else
                res = shifted[ELEN-1:0];
            active = (i < vl) && mask[i];
            vd_new[i*ELEN +: ELEN] = active ? res : vd_old[i*ELEN +: ELEN];
        end
    end
endmodule
