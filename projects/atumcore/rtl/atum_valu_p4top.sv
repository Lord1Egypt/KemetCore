// AtumCore — registered P&R boundary top for atum_valu (KemetCore Phase 4)
//
// atum_valu (the VLMAX-lane RVV integer vector ALU) is purely combinational.
// This wrapper latches the two source vectors, the destination-old vector, the
// op/mask/vl control, drives the verified combinational vector ALU, and latches
// the result vector — a real reg -> logic -> reg path for ASAP7 place/route and
// timing closure. atum_valu is instantiated UNCHANGED (bit-exact behaviour).
module atum_valu_p4top #(
    parameter int VLMAX = 8,
    parameter int ELEN  = 32
) (
    input  logic                       clk,
    input  logic                       rst,
    input  logic [VLMAX*ELEN-1:0]      vs1_in,
    input  logic [VLMAX*ELEN-1:0]      vs2_in,
    input  logic [VLMAX*ELEN-1:0]      vd_old_in,
    input  logic [3:0]                 op_in,
    input  logic [VLMAX-1:0]           mask_in,
    input  logic [$clog2(VLMAX+1)-1:0] vl_in,
    output logic [VLMAX*ELEN-1:0]      vd_new_out
);
    logic [VLMAX*ELEN-1:0]      vs1_q, vs2_q, vd_old_q, vd_new_c;
    logic [3:0]                 op_q;
    logic [VLMAX-1:0]           mask_q;
    logic [$clog2(VLMAX+1)-1:0] vl_q;

    always_ff @(posedge clk) begin
        if (rst) begin
            vs1_q    <= '0;
            vs2_q    <= '0;
            vd_old_q <= '0;
            op_q     <= '0;
            mask_q   <= '0;
            vl_q     <= '0;
        end else begin
            vs1_q    <= vs1_in;
            vs2_q    <= vs2_in;
            vd_old_q <= vd_old_in;
            op_q     <= op_in;
            mask_q   <= mask_in;
            vl_q     <= vl_in;
        end
    end

    atum_valu #(.VLMAX(VLMAX), .ELEN(ELEN)) u_core (
        .vs1(vs1_q), .vs2(vs2_q), .vd_old(vd_old_q),
        .op(op_q), .mask(mask_q), .vl(vl_q), .vd_new(vd_new_c)
    );

    always_ff @(posedge clk) begin
        if (rst) vd_new_out <= '0;
        else     vd_new_out <= vd_new_c;
    end
endmodule
