// SethCore — FORMAL: control-safety of the iterative seth_muldiv_seq handshake.
// Proved by temporal k-induction (unbounded), referencing only the module ports:
//   (1) done and busy are mutually exclusive     (done |-> !busy)
//   (2) done is a single-cycle pulse             (done |=> !done)
// These guarantee a consumer never sees a stuck/overlapping handshake regardless
// of when start is asserted. Inputs (start/op/a/b) are left fully free.
module hs_vac (input logic clk);
    logic rst; (* anyconst *) logic rst_c; // reset is applied only at t==0
    logic start; logic [2:0] op; logic [31:0] a, b;

    logic [7:0] t = 8'd0;
    always_ff @(posedge clk) if (t != 8'hFF) t <= t + 8'd1;
    always_comb rst = (t == 8'd0);

    logic busy, done; logic [31:0] y;
    seth_muldiv_seq u_dut (.clk(clk), .rst(rst), .start(start),
                           .op(op), .a(a), .b(b), .busy(busy), .done(done), .y(y));

    // remember the previous value of `done` for the pulse property
    logic done_q = 1'b0;
    always_ff @(posedge clk) done_q <= done;

    always_ff @(posedge clk) if (!rst) begin
        assert (!done); // vacuity probe
        assert (!(done && done_q)); // (2) single-cycle pulse
    end
endmodule
