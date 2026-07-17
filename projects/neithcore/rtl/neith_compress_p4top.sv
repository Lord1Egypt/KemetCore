// P&R wrapper for NeithCore compress module (KemetCore Phase 4 P&R)
//
// Wraps the combinational neith_compress datapath in registers to ensure
// exact timing constraint boundaries during ASAP7 synthesis and P&R.

module neith_compress_p4top #(
    parameter int D = 10
) (
    input  logic         clk,
    input  logic         rst_n,
    input  logic [12:0]  x,
    output logic [D-1:0] c
);
    logic [12:0]  x_reg;
    logic [D-1:0] c_comb;

    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            x_reg <= '0;
            c     <= '0;
        end else begin
            x_reg <= x;
            c     <= c_comb;
        end
    end

    neith_compress #(
        .D(D)
    ) u_core (
        .x(x_reg),
        .c(c_comb)
    );
endmodule
