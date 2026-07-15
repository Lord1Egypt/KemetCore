// AtumCore — atum_vcompress registered wrapper for Phase 4 P&R
module atum_vcompress_p4top #(
    parameter int VLMAX = 8,
    parameter int ELEN  = 32
) (
    input  logic                             clk,
    input  logic [VLMAX*ELEN-1:0]            vs,
    input  logic [VLMAX-1:0]                 m,
    input  logic [$clog2(VLMAX+1)-1:0]       vl,
    output logic [VLMAX*ELEN-1:0]            vd
);
    logic [VLMAX*ELEN-1:0]            vs_r;
    logic [VLMAX-1:0]                 m_r;
    logic [$clog2(VLMAX+1)-1:0]       vl_r;
    
    logic [VLMAX*ELEN-1:0]            vd_w;
    logic [VLMAX*ELEN-1:0]            vd_r;

    always_ff @(posedge clk) begin
        vs_r <= vs;
        m_r <= m;
        vl_r <= vl;
        vd_r <= vd_w;
    end

    atum_vcompress u_core (
        .vs(vs_r),
        .m(m_r),
        .vl(vl_r),
        .vd(vd_w)
    );

    assign vd = vd_r;
endmodule
