// NeithCore — neith_butterfly registered wrapper for Phase 4 P&R
module neith_butterfly_p4top (
    input  logic        clk,
    input  logic [12:0] u,
    input  logic [12:0] v,
    input  logic [12:0] w,
    output logic [12:0] lo,
    output logic [12:0] hi
);
    logic [12:0] u_r, v_r, w_r;
    logic [12:0] lo_w, hi_w;
    logic [12:0] lo_r, hi_r;

    always_ff @(posedge clk) begin
        u_r <= u;
        v_r <= v;
        w_r <= w;
        lo_r <= lo_w;
        hi_r <= hi_w;
    end

    neith_butterfly u_core (
        .u(u_r),
        .v(v_r),
        .w(w_r),
        .lo(lo_w),
        .hi(hi_w)
    );

    assign lo = lo_r;
    assign hi = hi_r;
endmodule
