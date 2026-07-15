module seth_muldiv_p4top (
    input  logic        clk,
    input  logic [31:0] a,
    input  logic [31:0] b,
    input  logic [2:0]  op,
    output logic [31:0] y
);
    logic [31:0] a_q;
    logic [31:0] b_q;
    logic [2:0]  op_q;
    logic [31:0] y_d;
    logic [31:0] y_q;

    always_ff @(posedge clk) begin
        a_q  <= a;
        b_q  <= b;
        op_q <= op;
        y_q  <= y_d;
    end

    seth_muldiv u_core (
        .a(a_q),
        .b(b_q),
        .op(op_q),
        .y(y_d)
    );

    assign y = y_q;
endmodule
