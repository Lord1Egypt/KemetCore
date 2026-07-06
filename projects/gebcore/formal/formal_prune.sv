// GebCore — FORMAL: geb_prune enforces the 2:4 structured-sparsity invariant —
// EXACTLY two of the four lanes are kept, for ALL weight inputs.
module formal_prune (input logic [31:0] w0, w1, w2, w3);
    wire [3:0] keep;
    geb_prune u (.w0(w0), .w1(w1), .w2(w2), .w3(w3), .keep_mask(keep));
    always_comb
        assert ((keep[0] + keep[1] + keep[2] + keep[3]) == 3'd2);
endmodule
