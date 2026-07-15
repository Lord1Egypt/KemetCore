// GebCore — FORMAL: geb_prune enforces the 2:4 structured-sparsity invariant —
// EXACTLY two of the four lanes are kept, for ALL weight inputs, and the kept
// weights and indices match exactly the magnitudes.
//
// The actual assertions live inside projects/gebcore/rtl/geb_prune.sv under
// `ifdef FORMAL.
module formal_prune (input logic [31:0] w0, w1, w2, w3);
    wire [3:0] keep;
    wire [31:0] val0, val1;
    wire [1:0] idx0, idx1;
    geb_prune u (.w0(w0), .w1(w1), .w2(w2), .w3(w3), .keep_mask(keep),
                 .val0(val0), .idx0(idx0), .val1(val1), .idx1(idx1));
endmodule
