// NeithCore — 256-point negacyclic NTT engine (KemetCore Phase 2 RTL)
//
// Multicycle in-place radix-2 Cooley-Tukey forward NTT over Z_q (q = 7681, root =
// OMEGA = 3844), matching golden.ntt_cyclic(a, OMEGA). One butterfly per cycle:
//   * LOAD  : stream 256 coefficients; each is stored at its bit-reversed index.
//   * RUN   : 8 stages x 128 butterflies = 1024 cycles. Per (stage, pair) it reads
//             two samples, applies neith_butterfly with the running twiddle w, and
//             writes both back in place. The twiddle advances w *= wlen each pair
//             and resets to 1 at every block boundary (wlen is a per-stage ROM).
//   * DONE  : results are read out combinationally by address (natural order).
//
// Composes the verified neith_butterfly (+ its neith_modmul) and a second
// neith_modmul for the twiddle update. Bit-exact against golden.ntt_cyclic —
// see tb/test_ntt.py. Yosys-portable: register-array memory, casez/case ROMs.

module neith_ntt (
    input  logic        clk,
    input  logic        rst_n,
    input  logic        start,        // pulse 1 cycle to begin (then stream inputs)
    input  logic        in_valid,     // qualifies in_data during LOAD (256 beats)
    input  logic [12:0] in_data,      // input coefficient (natural order), < Q
    input  logic [7:0]  rd_addr,      // result read address (valid in DONE)
    output logic [12:0] out_data,     // result[rd_addr] (combinational)
    output logic        busy,
    output logic        done          // high in DONE (results valid)
);
    localparam logic [13:0] Q = 14'd7681;

    // ---- in-place coefficient memory (register array) --------------------- //
    logic [12:0] mem [0:255];

    // ---- helpers ---------------------------------------------------------- //
    function automatic logic [7:0] bitrev8(input logic [7:0] x);
        bitrev8 = {x[0], x[1], x[2], x[3], x[4], x[5], x[6], x[7]};
    endfunction

    // per-stage wlen = OMEGA^(256/length) mod Q (length = 2<<stage)
    function automatic logic [12:0] wlen_rom(input logic [2:0] s);
        case (s)
            3'd0: wlen_rom = 13'd7680;
            3'd1: wlen_rom = 13'd4298;
            3'd2: wlen_rom = 13'd1213;
            3'd3: wlen_rom = 13'd7154;
            3'd4: wlen_rom = 13'd1366;
            3'd5: wlen_rom = 13'd7351;
            3'd6: wlen_rom = 13'd5773;
            default: wlen_rom = 13'd3844;   // stage 7
        endcase
    endfunction

    // ---- control state ---------------------------------------------------- //
    typedef enum logic [1:0] {S_IDLE, S_LOAD, S_RUN, S_DONE} state_t;
    state_t      state;
    logic [7:0]  lc;          // load counter 0..255
    logic [2:0]  stage;       // 0..7
    logic [6:0]  p;           // pair index within stage, 0..127
    logic [12:0] w_reg;       // current twiddle wlen^k

    // index arithmetic for the current (stage, p)
    logic [7:0]  half;        // 1 << stage
    logic [6:0]  kk;          // p & (half-1)
    logic [7:0]  blk;         // p >> stage
    logic [7:0]  base;        // blk << (stage+1)
    logic [7:0]  iu, iv;
    assign half = 8'd1 << stage;
    assign kk   = p & (half[6:0] - 7'd1);
    assign blk  = {1'b0, p} >> stage;
    assign base = blk << (stage + 4'd1);
    assign iu   = base + {1'b0, kk};
    assign iv   = iu + half;

    logic last_k, last_pair;
    assign last_k    = (kk == (half[6:0] - 7'd1));   // block boundary
    assign last_pair = (p == 7'd127);                // stage boundary

    // ---- butterfly + twiddle update (combinational) ----------------------- //
    logic [12:0] u_val, v_val, bf_lo, bf_hi, w_mul;
    assign u_val = mem[iu];
    assign v_val = mem[iv];
    neith_butterfly u_bf  (.u(u_val), .v(v_val), .w(w_reg), .lo(bf_lo), .hi(bf_hi));
    neith_modmul    u_wmul(.a(w_reg), .b(wlen_rom(stage)), .r(w_mul));

    // ---- sequential control ----------------------------------------------- //
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            state <= S_IDLE;
            lc <= 8'd0; stage <= 3'd0; p <= 7'd0; w_reg <= 13'd1;
        end else begin
            case (state)
                S_IDLE: begin
                    if (start) begin
                        state <= S_LOAD;
                        lc <= 8'd0;
                    end
                end
                S_LOAD: begin
                    if (in_valid) begin
                        mem[bitrev8(lc)] <= in_data;
                        if (lc == 8'd255) begin
                            state <= S_RUN;
                            stage <= 3'd0; p <= 7'd0; w_reg <= 13'd1;
                        end
                        lc <= lc + 8'd1;
                    end
                end
                S_RUN: begin
                    mem[iu] <= bf_lo;
                    mem[iv] <= bf_hi;
                    w_reg   <= last_k ? 13'd1 : w_mul;
                    if (last_pair) begin
                        p <= 7'd0;
                        if (stage == 3'd7) state <= S_DONE;
                        else               stage <= stage + 3'd1;
                    end else begin
                        p <= p + 7'd1;
                    end
                end
                S_DONE: begin
                    if (start) begin   // allow a fresh transform
                        state <= S_LOAD;
                        lc <= 8'd0;
                    end
                end
                default: state <= S_IDLE;
            endcase
        end
    end

    assign out_data = mem[rd_addr];
    assign busy     = (state == S_LOAD) || (state == S_RUN);
    assign done     = (state == S_DONE);
endmodule
