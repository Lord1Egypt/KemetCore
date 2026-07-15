// SethCore — FORMAL: bounded termination of the iterative seth_muldiv_seq.
// The restoring-divide loop must always finish: `busy` is never asserted for
// more cycles than the worst-case divide takes. This rules out a livelock /
// stuck iteration counter regardless of the operands or when `start` fires.
// A watchdog counter (wrapper-only, references the `busy` port) counts how long
// busy has stayed continuously high; the proof asserts it never exceeds the
// worst-case latency BOUND. BMC from reset over all free input sequences.
// BOUND=33 is the proven-tight worst case: the proof FAILS at 32 and PASSES at
// 33, so the iterative divide always finishes in <=33 busy cycles.
module formal_muldiv_liveness #(parameter int BOUND = 33) (input logic clk);
    logic rst; logic start; logic [2:0] op; logic [31:0] a, b;

    logic [7:0] t = 8'd0;
    always_ff @(posedge clk) if (t != 8'hFF) t <= t + 8'd1;
    always_comb rst = (t == 8'd0);

    logic busy, done; logic [31:0] y;
    seth_muldiv_seq u_dut (.clk(clk), .rst(rst), .start(start),
                           .op(op), .a(a), .b(b), .busy(busy), .done(done), .y(y));

    // watchdog: cycles busy has been continuously high
    logic [7:0] busy_dur = 8'd0;
    always_ff @(posedge clk)
        if (rst)      busy_dur <= 8'd0;
        else if (busy) busy_dur <= busy_dur + 8'd1;
        else          busy_dur <= 8'd0;

    always_ff @(posedge clk) if (!rst) assert (busy_dur <= 8'(BOUND));
endmodule
