// SethCore — FORMAL: iterative seth_muldiv_seq == combinational seth_muldiv for
// every MULTIPLY op (MUL/MULH/MULHSU/MULHU) and every special-case divide
// (divide-by-zero and the signed INT_MIN/-1 overflow) — the paths that finish in
// <=3 cycles. Proved by BMC from reset with anyconst operands (exhaustive over
// all such op/a/b). The normal iterative restoring-divide loop is EXCLUDED: its
// full 32-cycle symbolic BMC does not converge under z3; that path is covered
// bit-exact by the cocotb testbench (both units vs golden _muldiv).
module vac_probe (input logic clk);
    (* anyconst *) logic [2:0]  op_c;
    (* anyconst *) logic [31:0] a_c, b_c;

    logic [7:0] t = 8'd0;
    always_ff @(posedge clk) if (t != 8'hFF) t <= t + 8'd1;
    logic rst, start; always_comb begin rst = (t==8'd0); start = (t==8'd1); end

    logic [31:0] y_ref;
    seth_muldiv u_ref (.a(a_c), .b(b_c), .op(op_c), .y(y_ref));
    logic busy, done; logic [31:0] y_seq;
    seth_muldiv_seq u_dut (.clk(clk), .rst(rst), .start(start),
                           .op(op_c), .a(a_c), .b(b_c), .busy(busy), .done(done), .y(y_seq));

    // restrict to the short-latency paths (multiplies + special-case divides)
    wire is_mul  = (op_c <= 3'd3);
    wire is_divz = (op_c >= 3'd4) && (b_c == 32'd0);
    wire is_ovf  = ((op_c == 3'd4) || (op_c == 3'd6)) &&
                   (a_c == 32'h8000_0000) && (b_c == 32'hFFFF_FFFF);
    always_comb assume (is_mul || is_divz || is_ovf);

    always_comb if (t >= 8'd2 && done) assert (1'b0); // vacuity probe: fires iff done reachable
endmodule
