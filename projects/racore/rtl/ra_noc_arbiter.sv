// RaCore — NoC round-robin arbiter (KemetCore Phase 2 RTL)
//
// The arbitration heart of the on-chip network crossbar: N masters raise request
// lines, and each arbitration grants exactly one in round-robin order, resuming
// the scan just past the last grantee so no master starves. Mirrors the golden
// NocCrossbar.arbitrate (scan cand=(last+k)%N for k=1..N, first requester wins).
//
// `grant_valid`/`grant_idx` are combinational over the current requests and the
// stored pointer; pulse `advance` on a clock to commit a grant (update the pointer
// and bump that master's grant counter). After reset the pointer is N-1 so the
// first scan starts at master 0 (matching the golden's _last = -1).
//
// Verified bit-exact vs golden NocCrossbar — see tb/test_noc.py.

module ra_noc_arbiter #(
    parameter int N = 4
) (
    input  logic           clk,
    input  logic           rst,
    input  logic [N-1:0]   requests,
    input  logic           advance,            // commit the current grant this cycle
    output logic           grant_valid,
    output logic [$clog2(N)-1:0] grant_idx,
    output logic [32*N-1:0] grants_flat       // per-master grant counters, packed
);
    localparam int W = $clog2(N);
    logic [W-1:0] last;

    // round-robin: first requester at or after (last+1), wrapping. N must be a
    // power of two so the wrap is a W-bit truncation (the SoC instantiates N=4/8).
    // Scan k=1..N low->high and latch the FIRST match (the `!grant_valid` guard
    // freezes the winner), so the closest requester after `last` wins — exactly
    // the golden NocCrossbar.arbitrate order. (Equivalent to, but clearer than,
    // the old high->low guarded-overwrite form; re-verified bit-exact.)
    logic [W-1:0] cand;
    always_comb begin
        grant_valid = 1'b0;
        grant_idx   = '0;
        cand        = '0;
        for (int k = 1; k <= N; k++) begin
            cand = last + k[W-1:0];
            if (requests[cand] && !grant_valid) begin
                grant_valid = 1'b1;
                grant_idx   = cand;
            end
        end
    end

    logic [31:0] grants [0:N-1];
    integer m;
    always_ff @(posedge clk) begin
        if (rst) begin
            last <= W'(N - 1);
            for (m = 0; m < N; m++) grants[m] <= 32'd0;
        end else if (advance && grant_valid) begin
            last <= grant_idx;
            grants[grant_idx] <= grants[grant_idx] + 32'd1;
        end
    end

    genvar gi;
    generate
        for (gi = 0; gi < N; gi = gi + 1) begin : pack
            assign grants_flat[32*gi +: 32] = grants[gi];
        end
    endgenerate
endmodule
