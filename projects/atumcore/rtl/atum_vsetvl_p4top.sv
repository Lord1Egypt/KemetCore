// AtumCore — vsetvl unit (Phase 4 P&R wrapper)
//
// Wraps atum_vsetvl in a registered boundary (flop in, flop out) to provide
// constrained I/O timing for OpenROAD ASAP7 flow. VLMAX is fixed to 8 for the baseline.

module atum_vsetvl_p4top (
    input  logic        clk,
    input  logic [31:0] avl,
    output logic [3:0]  vl
);

    // Flop in
    logic [31:0] avl_q;
    always_ff @(posedge clk) begin
        avl_q <= avl;
    end

    // The combinational vsetvl
    logic [3:0] vl_d;
    atum_vsetvl #(
        .VLMAX(8)
    ) core (
        .avl(avl_q),
        .vl (vl_d )
    );

    // Flop out
    always_ff @(posedge clk) begin
        vl <= vl_d;
    end

endmodule
