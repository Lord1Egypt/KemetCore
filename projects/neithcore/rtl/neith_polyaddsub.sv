// NeithCore — polynomial modular add / subtract (KemetCore Phase 2 RTL)
//
// Element-wise modular add/sub of two length-N coefficient vectors mod Q (Q = 7681),
// the workhorse combine step used throughout ML-KEM (key gen, encrypt, decrypt):
//   op = 0 padd : C[i] = (A[i] + B[i]) mod Q
//   op = 1 psub : C[i] = (A[i] - B[i]) mod Q
// Operands are assumed already reduced (< Q). add: s = a+b < 2Q, conditionally subtract
// Q. sub: if a >= b, a-b; else a+Q-b (one conditional, always in [0,Q)). Streaming
// protocol mirrors neith_ntt / neith_pointwise: pulse `start` (latches `op`), drive N
// beats of (a_in, b_in) with `in_valid`, then read results by `rd_addr` once `done`.
// Each result is computed combinationally and registered as it streams. Yosys must
// report 0 latches. Verified vs the golden — see tb/test_polyaddsub.py.

module neith_polyaddsub #(
    parameter int N = 256
) (
    input  logic        clk,
    input  logic        rst_n,
    input  logic        start,        // pulse 1 cycle to begin (latches op)
    input  logic        op,           // 0 = padd, 1 = psub (latched at start)
    input  logic        in_valid,     // qualifies a_in/b_in during LOAD (N beats)
    input  logic [12:0] a_in,         // A[i], < Q
    input  logic [12:0] b_in,         // B[i], < Q
    input  logic [7:0]  rd_addr,      // result read address (valid in DONE)
    output logic [12:0] out_data,     // C[rd_addr] (combinational)
    output logic        busy,
    output logic        done
);
    localparam logic [1:0]  S_IDLE = 2'd0, S_LOAD = 2'd1, S_DONE = 2'd2;
    localparam logic [31:0] NW = N;               // 32-bit mirror of N (width-safe compare)
    localparam logic [13:0] Q  = 14'd7681;

    logic [1:0]  state;
    logic        op_reg;
    logic [8:0]  cnt;                 // 0..N
    logic [12:0] mem [0:N-1];

    // combinational modular add / subtract of the current streamed pair
    logic [13:0] sum, addres, subres;
    logic [12:0] res;
    assign sum    = {1'b0, a_in} + {1'b0, b_in};                 // < 2Q, fits 14 bits
    assign addres = (sum >= Q) ? (sum - Q) : sum;                // mod-add
    assign subres = (a_in >= b_in) ? ({1'b0, a_in} - {1'b0, b_in})
                                   : ({1'b0, a_in} + Q - {1'b0, b_in});  // mod-sub
    assign res    = op_reg ? subres[12:0] : addres[12:0];

    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            state  <= S_IDLE;
            cnt    <= '0;
            op_reg <= 1'b0;
        end else begin
            case (state)
                S_IDLE: if (start) begin state <= S_LOAD; cnt <= '0; op_reg <= op; end
                S_LOAD: if (in_valid) begin
                    mem[cnt[7:0]] <= res;
                    if ({23'b0, cnt} == NW - 32'd1) state <= S_DONE;
                    cnt <= cnt + 1'b1;
                end
                S_DONE: if (start) begin state <= S_LOAD; cnt <= '0; op_reg <= op; end
                default: state <= S_IDLE;
            endcase
        end
    end

    assign busy     = (state == S_LOAD);
    assign done     = (state == S_DONE);
    assign out_data = mem[rd_addr];
endmodule
