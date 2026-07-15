// SethCore — RV32M SEQUENTIAL multiply/divide unit (KemetCore Phase 2 RTL)
//
// Bit-exact functional twin of the combinational seth_muldiv, but the divide is
// ITERATIVE (restoring division, one bit per cycle) instead of a single-cycle
// combinational `/`. This is the P&R-friendly form: the combinational 32-bit
// divide in seth_muldiv is a pathological critical path that explodes the CTS
// resizer, whereas this unit's longest path is one 32-bit add/subtract.
// Multiplies stay single-cycle (a 32x32 product is a benign path).
//
// op: 0 MUL 1 MULH 2 MULHSU 3 MULHU 4 DIV 5 DIVU 6 REM 7 REMU
//
// Handshake: pulse `start` for one cycle with a/b/op valid. `busy` is high while
// iterating; `done` pulses for one cycle when `y` is valid (MUL: 1 cycle after
// start; DIV/REM: ~34 cycles). Result matches golden _muldiv exactly, including
// div-by-zero (all-ones quotient / dividend remainder) and the signed
// INT_MIN / -1 overflow (quotient INT_MIN, remainder 0).
module seth_muldiv_seq (
    input  logic        clk,
    input  logic        rst,
    input  logic        start,
    input  logic [2:0]  op,
    input  logic [31:0] a,
    input  logic [31:0] b,
    output logic        busy,
    output logic        done,
    output logic [31:0] y
);
    localparam logic [1:0] IDLE = 2'd0, RUN = 2'd1, FIN = 2'd2;
    logic [1:0] state;

    // latched request / iteration state
    logic        rem_op;      // final result is the remainder (REM/REMU)
    logic        neg_q;       // negate quotient at the end (signed, signs differ)
    logic        neg_r;       // negate remainder at the end (signed, dividend<0)
    logic [5:0]  cnt;         // iteration counter
    logic [31:0] divisor;     // unsigned |b|
    logic [63:0] rq;          // {remainder[63:32], quotient/dividend[31:0]}
    logic [31:0] result_q;    // immediate result (MUL / special cases)

    // ---- combinational helpers (continuous, so they track a/b every cycle) ----
    logic signed [63:0] mul_ss, mul_su;
    logic        [63:0] mul_uu;
    assign mul_ss = $signed(a) * $signed(b);
    assign mul_su = $signed(a) * $signed({1'b0, b});
    assign mul_uu = a * b;

    // decode for a divide request
    logic        sgnd, is_rem, sa, sb;
    logic [31:0] ua, ub;
    assign sgnd   = (op == 3'd4) || (op == 3'd6);
    assign is_rem = (op == 3'd6) || (op == 3'd7);
    assign sa     = sgnd && a[31];
    assign sb     = sgnd && b[31];
    assign ua     = sa ? (~a + 32'd1) : a;   // |a|
    assign ub     = sb ? (~b + 32'd1) : b;   // |b|

    // one restoring-division step
    logic [63:0] rq_sh;
    logic [31:0] rem_hi;
    assign rq_sh  = rq << 1;
    assign rem_hi = rq_sh[63:32];

    // end-of-iteration sign fix-up
    logic [31:0] q_u, r_u, q_s, r_s;
    assign q_u = rq[31:0];
    assign r_u = rq[63:32];
    assign q_s = neg_q ? (~q_u + 32'd1) : q_u;
    assign r_s = neg_r ? (~r_u + 32'd1) : r_u;

    always_ff @(posedge clk) begin
        if (rst) begin
            state <= IDLE; busy <= 1'b0; done <= 1'b0; y <= 32'd0;
        end else begin
            done <= 1'b1; // MUTANT
            case (state)
                IDLE: begin
                    busy <= 1'b0;
                    if (start) begin
                        if (op <= 3'd3) begin
                            // multiplies: result now, finish next cycle
                            unique case (op)
                                3'd0:    result_q <= mul_uu[31:0];   // MUL
                                3'd1:    result_q <= mul_ss[63:32];  // MULH
                                3'd2:    result_q <= mul_su[63:32];  // MULHSU
                                default: result_q <= mul_uu[63:32];  // MULHU
                            endcase
                            busy <= 1'b1; state <= FIN;
                        end else if (b == 32'd0) begin
                            // div-by-zero: DIV/DIVU -> all-ones ; REM/REMU -> a
                            result_q <= is_rem ? a : 32'hFFFFFFFF;
                            busy <= 1'b1; state <= FIN;
                        end else if (sgnd && a == 32'h80000000 && b == 32'hFFFFFFFF) begin
                            // signed overflow: DIV -> INT_MIN ; REM -> 0
                            result_q <= is_rem ? 32'd0 : 32'h80000000;
                            busy <= 1'b1; state <= FIN;
                        end else begin
                            // normal iterative divide
                            rem_op  <= is_rem;
                            divisor <= ub;
                            rq      <= {32'd0, ua};
                            neg_q   <= sa ^ sb;
                            neg_r   <= sa;
                            cnt     <= 6'd32;
                            busy <= 1'b1; state <= RUN;
                        end
                    end
                end

                RUN: begin
                    if (cnt != 6'd0) begin
                        if (rem_hi >= divisor)
                            rq <= {rem_hi - divisor, rq_sh[31:0] | 32'd1};
                        else
                            rq <= rq_sh;
                        cnt <= cnt - 6'd1;
                    end else begin
                        y     <= rem_op ? r_s : q_s;
                        done  <= 1'b1;
                        busy  <= 1'b0;
                        state <= IDLE;
                    end
                end

                FIN: begin      // one-cycle finish for MUL / special-case results
                    y     <= result_q;
                    done  <= 1'b1;
                    busy  <= 1'b0;
                    state <= IDLE;
                end

                default: state <= IDLE;
            endcase
        end
    end
endmodule
