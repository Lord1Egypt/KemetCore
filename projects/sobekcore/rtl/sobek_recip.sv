// SobekCore — fp32 reciprocal 1/x — KemetCore Phase 2 RTL
//
// The Moller-Trumbore inv_det step: inv_det = 1/det, formed once and shared by
// the u, v and t barycentric weightings. Purely combinational — a single
// correctly-rounded HapiCore fp32 divide of the constant 1.0 by x:
//   y = 1.0 / x
// Bit-exact vs the fp32 golden sobek_fp32.recip — see tb/test_recip.py.

module sobek_recip (
    input  logic [31:0] x,
    output logic [31:0] y
);
    // 32'h3F800000 == fp32 1.0
    hapi_fp32_div u_div (.a(32'h3F80_0000), .b(x), .y(y));
endmodule
