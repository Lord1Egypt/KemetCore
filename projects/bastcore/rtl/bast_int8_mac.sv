// BastCore — INT8 multiply / INT32 accumulate MAC cell (KemetCore Phase 2 RTL)
//
// The quantized-inference processing element: each cycle it multiplies a signed
// INT8 pair into a 16-bit product, sign-extends it to 32 bits, and accumulates
// into a registered INT32 running sum (two's-complement, wrapping — no saturation
// during accumulation, the standard int8/int32 GEMM behaviour):
//     acc = sum_k (a_k * b_k)
// Drive a length-K dot product by pulsing `clear` with the first element and `en`
// for all K elements; `acc` holds the result one cycle after the last input.
//
// Bit-exact against the golden int8_dot — see tb/test_int8_mac.py. Pure integer.

module bast_int8_mac (
    input  logic                clk,
    input  logic                rst_n,
    input  logic                en,      // accumulate the (a,b) product this cycle
    input  logic                clear,   // start a fresh dot product (ignore old acc)
    input  logic signed [7:0]   a,       // signed INT8
    input  logic signed [7:0]   b,       // signed INT8
    output logic signed [31:0]  acc      // INT32 running accumulator (registered)
);
    wire signed [15:0] prod   = a * b;                       // signed 8x8 -> 16-bit
    wire signed [31:0] addend = clear ? 32'sd0 : acc;
    wire signed [31:0] sum    = addend + {{16{prod[15]}}, prod};

    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) acc <= 32'sd0;
        else if (en) acc <= sum;
    end
endmodule
