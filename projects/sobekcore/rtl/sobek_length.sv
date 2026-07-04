// SobekCore — fp32 vector length ||v|| = sqrt(v.v) — KemetCore Phase 2 RTL
//
// The ray-segment distance primitive (e.g. |P1 - P0|). Purely combinational,
// fixed datapath order:
//   d   = dot3(v, v)   -- sum of squares (sobek_dot3: 3 fp32 muls + 2 adds)
//   len = sqrt(d)      -- correctly-rounded fp32 sqrt (hapi_fp32_sqrt)
// Bit-exact vs the fp32 golden sobek_fp32.length — see tb/test_length.py.

module sobek_length (
    input  logic [31:0] v0, v1, v2,
    output logic [31:0] len
);
    logic [31:0] d;

    // d = dot3(v, v)
    sobek_dot3 u_dot (.a0(v0), .a1(v1), .a2(v2),
                      .b0(v0), .b1(v1), .b2(v2), .y(d));

    // len = sqrt(d)
    hapi_fp32_sqrt u_sqrt (.x(d), .y(len));
endmodule
