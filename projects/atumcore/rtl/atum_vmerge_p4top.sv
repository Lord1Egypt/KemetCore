// AtumCore — vmerge unit (Phase 4 P&R wrapper)
//
// Wraps atum_vmerge in a registered boundary (flop in, flop out) to provide
// constrained I/O timing for OpenROAD ASAP7 flow.

module atum_vmerge_p4top (
    input  logic        clk,
    input  logic [255:0] vs1,
    input  logic [255:0] vs2,
    input  logic [7:0]   m,
    input  logic [3:0]   vl,
    output logic [255:0] vd
);

    // Flop in
    logic [255:0] vs1_q;
    logic [255:0] vs2_q;
    logic [7:0]   m_q;
    logic [3:0]   vl_q;

    always_ff @(posedge clk) begin
        vs1_q <= vs1;
        vs2_q <= vs2;
        m_q   <= m;
        vl_q  <= vl;
    end

    // The core
    logic [255:0] vd_d;
    
    atum_vmerge #(
        .VLMAX(8),
        .ELEN(32)
    ) core (
        .vs1(vs1_q),
        .vs2(vs2_q),
        .m  (m_q  ),
        .vl (vl_q ),
        .vd (vd_d )
    );

    // Flop out
    always_ff @(posedge clk) begin
        vd <= vd_d;
    end

endmodule
