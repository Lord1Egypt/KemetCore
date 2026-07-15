// AtumCore — atum_vsadd registered wrapper for Phase 4 P&R
module atum_vsadd_p4top #(
    parameter int VLMAX = 8,
    parameter int ELEN  = 32
) (
    input  logic                             clk,
    input  logic [VLMAX*ELEN-1:0]            vs1,
    input  logic [VLMAX*ELEN-1:0]            vs2,
    input  logic [VLMAX*ELEN-1:0]            vd_old,
    input  logic [1:0]                       op,
    input  logic [VLMAX-1:0]                 mask,
    input  logic [$clog2(VLMAX+1)-1:0]       vl,
    output logic [VLMAX*ELEN-1:0]            vd_new
);
    logic [VLMAX*ELEN-1:0]            vs1_r;
    logic [VLMAX*ELEN-1:0]            vs2_r;
    logic [VLMAX*ELEN-1:0]            vd_old_r;
    logic [1:0]                       op_r;
    logic [VLMAX-1:0]                 mask_r;
    logic [$clog2(VLMAX+1)-1:0]       vl_r;
    
    logic [VLMAX*ELEN-1:0]            vd_new_w;
    logic [VLMAX*ELEN-1:0]            vd_new_r;

    always_ff @(posedge clk) begin
        vs1_r <= vs1;
        vs2_r <= vs2;
        vd_old_r <= vd_old;
        op_r <= op;
        mask_r <= mask;
        vl_r <= vl;
        vd_new_r <= vd_new_w;
    end

    atum_vsadd u_core (
        .vs1(vs1_r),
        .vs2(vs2_r),
        .vd_old(vd_old_r),
        .op(op_r),
        .mask(mask_r),
        .vl(vl_r),
        .vd_new(vd_new_w)
    );

    assign vd_new = vd_new_r;
endmodule
