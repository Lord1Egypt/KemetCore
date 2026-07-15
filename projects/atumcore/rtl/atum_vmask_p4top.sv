// AtumCore — atum_vmask registered wrapper for Phase 4 P&R
module atum_vmask_p4top #(
    parameter int VLMAX = 8,
    parameter int ELEN  = 32
) (
    input  logic                       clk,
    input  logic [VLMAX*ELEN-1:0]      vs1,
    input  logic [VLMAX*ELEN-1:0]      vs2,
    input  logic [2:0]                 op,
    input  logic [VLMAX-1:0]           mask,
    input  logic [$clog2(VLMAX+1)-1:0] vl,
    output logic [VLMAX-1:0]           vd_mask
);
    logic [VLMAX*ELEN-1:0]      vs1_r;
    logic [VLMAX*ELEN-1:0]      vs2_r;
    logic [2:0]                 op_r;
    logic [VLMAX-1:0]           mask_r;
    logic [$clog2(VLMAX+1)-1:0] vl_r;

    logic [VLMAX-1:0]           vd_mask_w;
    logic [VLMAX-1:0]           vd_mask_r;

    always_ff @(posedge clk) begin
        vs1_r  <= vs1;
        vs2_r  <= vs2;
        op_r   <= op;
        mask_r <= mask;
        vl_r   <= vl;
        vd_mask_r <= vd_mask_w;
    end

    atum_vmask #(
        .VLMAX(VLMAX),
        .ELEN(ELEN)
    ) u_core (
        .vs1(vs1_r),
        .vs2(vs2_r),
        .op(op_r),
        .mask(mask_r),
        .vl(vl_r),
        .vd_mask(vd_mask_w)
    );

    assign vd_mask = vd_mask_r;
endmodule
