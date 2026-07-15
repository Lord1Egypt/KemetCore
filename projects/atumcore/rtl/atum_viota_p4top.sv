// AtumCore — atum_viota registered wrapper for Phase 4 P&R
module atum_viota_p4top #(
    parameter int VLMAX = 8,
    parameter int ELEN  = 32
) (
    input  logic                       clk,
    input  logic [VLMAX-1:0]           m,
    input  logic [VLMAX-1:0]           vmask,
    input  logic                       op,
    input  logic [$clog2(VLMAX+1)-1:0] vl,
    output logic [VLMAX*ELEN-1:0]      vd
);
    logic [VLMAX-1:0]           m_r;
    logic [VLMAX-1:0]           vmask_r;
    logic                       op_r;
    logic [$clog2(VLMAX+1)-1:0] vl_r;
    
    logic [VLMAX*ELEN-1:0]      vd_w;
    logic [VLMAX*ELEN-1:0]      vd_r;

    always_ff @(posedge clk) begin
        m_r     <= m;
        vmask_r <= vmask;
        op_r    <= op;
        vl_r    <= vl;
        vd_r    <= vd_w;
    end

    atum_viota #(
        .VLMAX(VLMAX),
        .ELEN(ELEN)
    ) u_core (
        .m(m_r),
        .vmask(vmask_r),
        .op(op_r),
        .vl(vl_r),
        .vd(vd_w)
    );

    assign vd = vd_r;
endmodule
