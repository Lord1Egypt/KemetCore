// SobekCore — fp32 Euclidean distance ||a - b|| — KemetCore Phase 2 RTL
//
// Distance between two points (e.g. ray origin to hit point). Purely
// combinational, fixed datapath order:
//   e_i = a_i - b_i    -- fp32 subtract, a + (-b) exact negation (hapi_fp32_add)
//   len = ||e||        -- sqrt(e.e) via sobek_length (dot3 + hapi_fp32_sqrt)
// Bit-exact vs the fp32 golden sobek_fp32.distance — see tb/test_distance.py.

module sobek_distance (
    input  logic [31:0] a0, a1, a2,
    input  logic [31:0] b0, b1, b2,
    output logic [31:0] len
);
    logic [31:0] e0, e1, e2;

    // e_i = a_i - b_i = a_i + (-b_i)
    hapi_fp32_add u_e0 (.a(a0), .b({~b0[31], b0[30:0]}), .y(e0));
    hapi_fp32_add u_e1 (.a(a1), .b({~b1[31], b1[30:0]}), .y(e1));
    hapi_fp32_add u_e2 (.a(a2), .b({~b2[31], b2[30:0]}), .y(e2));

    // len = ||e||
    sobek_length u_len (.v0(e0), .v1(e1), .v2(e2), .len(len));
endmodule
