// ImentetCore — softmax stabilization: y = x - max(x) — KemetCore Phase 2 RTL
//
// The exp-free, bit-exact pre-step of a numerically-stable softmax: subtract the
// row maximum from a length-LS score vector so the largest logit becomes 0.
//   m   = max_i x_i     -- sequential fp32 max (RISC-V fmax ordering)
//   y_j = x_j - m       -- fp32 subtract, x + (-m) exact negation (hapi_fp32_add)
// The max is a self-contained non-NaN comparator using the monotonic ordering key
// key(a) = a[31] ? ~a : (a | 0x8000_0000) — for finite/inf fp32, a > b iff
// key(a) > key(b) as unsigned. A new element replaces the running max only when
// STRICTLY greater, matching the golden's tie handling (earlier index wins).
// Defined for finite/-inf scores (attention domain incl. causal -inf mask).
// Purely combinational. Bit-exact vs golden imentet_fp32.rowmax_sub — see tb.

module imentet_rowmax_sub #(
    parameter int LS = 8
) (
    input  logic [32*LS-1:0] x,   // LS fp32 scores, x_i = x[32*i +: 32]
    output logic [32*LS-1:0] y    // LS fp32 results, y_i = x_i - max
);
    function automatic logic [31:0] okey(input logic [31:0] a);
        okey = a[31] ? ~a : (a | 32'h8000_0000);
    endfunction

    // sequential max reduction in a scalar accumulator (avoids array self-feedback;
    // strictly-greater replace keeps the earlier index on a tie)
    logic [31:0] m;
    always_comb begin
        logic [31:0] xj;
        m = x[31:0];
        for (int j = 1; j < LS; j++) begin
            xj = x[32*j +: 32];
            if (okey(xj) > okey(m)) m = xj;
        end
    end

    // y_j = x_j - m = x_j + (-m)
    genvar i;
    generate
        for (i = 0; i < LS; i++) begin : g_sub
            hapi_fp32_add u_sub (.a(x[32*i +: 32]), .b({~m[31], m[30:0]}),
                                 .y(y[32*i +: 32]));
        end
    endgenerate
endmodule
