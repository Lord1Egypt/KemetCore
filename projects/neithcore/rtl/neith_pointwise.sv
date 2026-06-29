// NeithCore — NTT-domain pointwise polynomial multiply (KemetCore Phase 2 RTL)
//
// The middle stage of the NTT poly-mul pipeline (ntt -> POINTWISE -> intt): given two
// length-N coefficient vectors A and B already in the NTT domain, compute the
// element-wise modular product C[i] = A[i]*B[i] mod Q (Q = 7681). Because the full NTT
// fully diagonalises negacyclic convolution, the product polynomial is just this
// coefficient-wise multiply (== golden.poly_mul_ntt's inner `A[i]*B[i] % Q`).
//
// Streaming protocol mirrors neith_ntt: pulse `start` (-> LOAD), then drive N beats of
// (a_in, b_in) with `in_valid` high. The verified combinational neith_modmul computes
// each product as it streams, so the result is registered directly into the coefficient
// memory with no separate compute phase. After N beats `done` rises and results are read
// combinationally by `rd_addr`. `start` in DONE restarts. Yosys must report 0 latches.
// Verified vs the golden — see tb/test_pointwise.py.

module neith_pointwise #(
    parameter int N = 256
) (
    input  logic        clk,
    input  logic        rst_n,
    input  logic        start,        // pulse 1 cycle to begin (then stream inputs)
    input  logic        in_valid,     // qualifies a_in/b_in during LOAD (N beats)
    input  logic [12:0] a_in,         // A[i] in NTT domain, < Q
    input  logic [12:0] b_in,         // B[i] in NTT domain, < Q
    input  logic [7:0]  rd_addr,      // result read address (valid in DONE)
    output logic [12:0] out_data,     // C[rd_addr] (combinational)
    output logic        busy,
    output logic        done
);
    localparam logic [1:0]  S_IDLE = 2'd0, S_LOAD = 2'd1, S_DONE = 2'd2;
    localparam logic [31:0] NW = N;               // 32-bit mirror of N (width-safe compare)

    logic [1:0]  state;
    logic [8:0]  cnt;                 // 0..N
    logic [12:0] mem [0:N-1];
    logic [12:0] prod;

    // combinational Barrett modular multiply of the current streamed pair
    neith_modmul u_mm (.a(a_in), .b(b_in), .r(prod));

    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            state <= S_IDLE;
            cnt   <= '0;
        end else begin
            case (state)
                S_IDLE: if (start) begin state <= S_LOAD; cnt <= '0; end
                S_LOAD: if (in_valid) begin
                    mem[cnt[7:0]] <= prod;
                    if ({23'b0, cnt} == NW - 32'd1) state <= S_DONE;
                    cnt <= cnt + 1'b1;
                end
                S_DONE: if (start) begin state <= S_LOAD; cnt <= '0; end
                default: state <= S_IDLE;
            endcase
        end
    end

    assign busy     = (state == S_LOAD);
    assign done     = (state == S_DONE);
    assign out_data = mem[rd_addr];
endmodule
