// AtumCore — vsetvl unit (KemetCore Phase 2 RTL)
//
// The length-agnostic RVV configuration primitive: VL = min(AVL, VLMAX). Combinational.
// Matches the golden VectorUnit.vsetvl bit-for-bit. Yosys 0-latch.
// Verified vs the golden — see tb/test_vsetvl.py.

module atum_vsetvl #(
    parameter int VLMAX = 8
) (
    input  logic [31:0]                avl,
    output logic [$clog2(VLMAX+1)-1:0] vl
);
    localparam int VLW = $clog2(VLMAX+1);
    assign vl = (avl >= 32'(VLMAX)) ? VLW'(VLMAX) : avl[VLW-1:0];
endmodule
