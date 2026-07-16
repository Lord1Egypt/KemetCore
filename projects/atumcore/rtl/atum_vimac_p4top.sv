// AtumCore — vimac unit (Phase 4 P&R wrapper)
//
// Wraps atum_vimac in a registered boundary (flop in, flop out) to provide
// constrained I/O timing for OpenROAD ASAP7 flow.

module atum_vimac_p4top (
    input  logic        clk,
    input  logic [255:0] vs1,
    input  logic [255:0] vs2,
    input  logic [255:0] vd_old,
    input  logic [1:0]   op,
    input  logic [7:0]   mask,
    input  logic [3:0]   vl,
    output logic [255:0] vd_new
);

    // Flop in
    logic [255:0] vs1_q;
    logic [255:0] vs2_q;
    logic [255:0] vd_old_q;
    logic [1:0]   op_q;
    logic [7:0]   mask_q;
    logic [3:0]   vl_q;

    always_ff @(posedge clk) begin
        vs1_q    <= vs1;
        vs2_q    <= vs2;
        vd_old_q <= vd_old;
        op_q     <= op;
        mask_q   <= mask;
        vl_q     <= vl;
    end

    // The core
    logic [255:0] vd_new_d;
    
    atum_vimac #(
        .VLMAX(8),
        .ELEN(32)
    ) core (
        .vs1   (vs1_q   ),
        .vs2   (vs2_q   ),
        .vd_old(vd_old_q),
        .op    (op_q    ),
        .mask  (mask_q  ),
        .vl    (vl_q    ),
        .vd_new(vd_new_d)
    );

    // Flop out
    always_ff @(posedge clk) begin
        vd_new <= vd_new_d;
    end

endmodule
