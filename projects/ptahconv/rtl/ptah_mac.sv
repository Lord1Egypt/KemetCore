// PtahConv — fp32 multiply / fp32 accumulate MAC cell (KemetCore Phase 2 RTL)
//
// The convolution compute primitive: a 2D conv output is a dot product of an
// im2col input window with a filter, and this PE streams that dot product. Each
// cycle it multiplies an fp32 pair (correctly-rounded, hapi_fp32_mul), then adds
// it into a registered fp32 running sum (correctly-rounded, hapi_fp32_add) — a
// purely SEQUENTIAL accumulation. The golden dot_seq accumulates in the identical
// element order, so the PE is bit-exact (the numpy conv references use pairwise /
// blocked sums and are NOT bit-identical — sequential MAC hardware must match a
// sequential golden, the lesson from BastCore/GebCore).
//
// Drive a length-K dot product by pulsing `clear` with the first element and `en`
// for all K elements; `acc` holds the fp32 result one cycle after the last input.
// Composes the verified HapiCore fp32 primitives.
//
// Bit-exact against golden dot_seq — see tb/test_mac.py.

module ptah_mac (
    input  logic        clk,
    input  logic        rst_n,
    input  logic        en,      // accumulate the (a,b) product this cycle
    input  logic        clear,   // start a fresh dot product (ignore old acc)
    input  logic [31:0] a,       // fp32
    input  logic [31:0] b,       // fp32
    output logic [31:0] acc      // fp32 running accumulator (registered)
);
    logic [31:0] prod;
    hapi_fp32_mul u_mul (.a(a), .b(b), .y(prod));

    logic [31:0] addend, sum;
    assign addend = clear ? 32'h0000_0000 : acc;     // seed a fresh sum from +0
    hapi_fp32_add u_add (.a(addend), .b(prod), .y(sum));

    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n)       acc <= 32'h0000_0000;
        else if (en)      acc <= sum;
    end
endmodule
