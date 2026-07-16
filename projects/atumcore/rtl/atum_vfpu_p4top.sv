// AtumCore — vfpu unit (Phase 4 P&R wrapper)
//
// Wraps atum_vfpu in a registered boundary (flop in, flop out) to provide
// constrained I/O timing for OpenROAD ASAP7 flow. VLMAX is fixed to 8 for the baseline.

module atum_vfpu_p4top (
    input  logic        clk,
    input  logic [8*32-1:0] vs1,
    input  logic [8*32-1:0] vs2,
    input  logic [8*32-1:0] vd_old,
    input  logic            fop,
    input  logic [7:0]      mask,
    input  logic [3:0]      vl,
    output logic [8*32-1:0] vd_new
);

    // Flop in
    logic [255:0] vs1_q, vs2_q, vd_old_q;
    logic         fop_q;
    logic [7:0]   mask_q;
    logic [3:0]   vl_q;
    
    always_ff @(posedge clk) begin
        vs1_q    <= vs1;
        vs2_q    <= vs2;
        vd_old_q <= vd_old;
        fop_q    <= fop;
        mask_q   <= mask;
        vl_q     <= vl;
    end

    // The combinational vfpu
    logic [255:0] vd_new_d;
    atum_vfpu #(
        .VLMAX(8),
        .ELEN(32)
    ) core (
        .vs1   (vs1_q   ),
        .vs2   (vs2_q   ),
        .vd_old(vd_old_q),
        .fop   (fop_q   ),
        .mask  (mask_q  ),
        .vl    (vl_q    ),
        .vd_new(vd_new_d)
    );

    // Flop out
    always_ff @(posedge clk) begin
        vd_new <= vd_new_d;
    end

endmodule
