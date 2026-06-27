// NeithCore — Cooley-Tukey NTT butterfly mod Q = 7681 (KemetCore Phase 2 RTL)
//
// The atom of the radix-2 NTT (see golden ntt_cyclic):
//     t  = v * w   mod Q          (modular multiply by the twiddle factor)
//     lo = (u + t) mod Q
//     hi = (u - t) mod Q
// All ports are residues in [0, Q). Combinational; instantiates neith_modmul.
//
// Bit-exact against the golden butterfly — see tb/test_butterfly.py.
// Yosys-portable: no int'() casts, width-matched operands.

module neith_butterfly (
    input  logic [12:0] u,    // upper sample, < Q
    input  logic [12:0] v,    // lower sample, < Q
    input  logic [12:0] w,    // twiddle factor, < Q
    output logic [12:0] lo,   // (u + v*w) mod Q
    output logic [12:0] hi    // (u - v*w) mod Q
);
    localparam logic [13:0] Q = 14'd7681;

    logic [12:0] t;           // v*w mod Q
    neith_modmul u_mm (.a(v), .b(w), .r(t));

    logic [13:0] sum;         // u + t       (< 2Q)
    logic [13:0] diff;        // u - t + Q   (in [1, 2Q))
    logic [13:0] sum_red, diff_red;
    assign sum  = {1'b0, u} + {1'b0, t};
    assign diff = ({1'b0, u} + Q) - {1'b0, t};
    assign sum_red  = (sum  >= Q) ? (sum  - Q) : sum;
    assign diff_red = (diff >= Q) ? (diff - Q) : diff;
    assign lo = sum_red[12:0];
    assign hi = diff_red[12:0];
endmodule
