// ImentetCore — imentet_mask_add registered wrapper for Phase 4 P&R
module imentet_mask_add_p4top #(
    parameter int LS = 8
) (
    input  logic             clk,
    input  logic [32*LS-1:0] x,
    input  logic [32*LS-1:0] m,
    output logic [32*LS-1:0] y
);
    logic [32*LS-1:0] x_r, m_r, y_w, y_r;

    always_ff @(posedge clk) begin
        x_r <= x;
        m_r <= m;
        y_r <= y_w;
    end

    imentet_mask_add #(.LS(LS)) u_core (
        .x(x_r),
        .m(m_r),
        .y(y_w)
    );

    assign y = y_r;
endmodule
