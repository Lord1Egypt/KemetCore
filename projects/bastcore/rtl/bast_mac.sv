// BastCore — bf16 multiply / fp32 accumulate MAC cell (KemetCore Phase 2 RTL)
//
// The processing element of the BF16 tensor core. Each cycle it multiplies a bf16
// pair, widens the bf16 product to fp32 (exact — bf16 and fp32 share the 8-bit,
// bias-127 exponent, so it is a zero-extend of the mantissa), and accumulates it
// into a registered fp32 running sum. This is exactly the golden datapath:
//     out = sum_k round_bf16(a_k * b_k)   accumulated in fp32
// (golden/bast_matmul.py). Composes the verified HapiCore primitives
// hapi_bf16_mul + hapi_fp32_add.
//
// Drive a length-K dot product by pulsing `clear` with the first element and `en`
// for all K elements; `acc` holds the fp32 result one cycle after the last input.
//
// Bit-exact against golden.matmul on (1xK)*(Kx1) dot products — see tb/test_mac.py.

module bast_mac (
    input  logic        clk,
    input  logic        rst_n,
    input  logic        en,      // accumulate the (a,b) product this cycle
    input  logic        clear,   // start a fresh dot product (ignore old acc)
    input  logic [15:0] a,       // bf16
    input  logic [15:0] b,       // bf16
    output logic [31:0] acc      // fp32 running accumulator (registered)
);
    // bf16 product (combinational)
    logic [15:0] prod_bf16;
    hapi_bf16_mul u_mul (.a(a), .b(b), .y(prod_bf16));

    // bf16 -> fp32 is an exact zero-extend (shared exponent field & bias)
    logic [31:0] prod_fp32;
    assign prod_fp32 = {prod_bf16, 16'b0};

    // fp32 accumulate: clear starts from +0 (golden seeds out = 0.0)
    logic [31:0] addend, sum;
    assign addend = clear ? 32'h0000_0000 : acc;
    hapi_fp32_add u_add (.a(addend), .b(prod_fp32), .y(sum));

    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n)
            acc <= 32'h0000_0000;
        else if (en)
            acc <= sum;
    end
endmodule
