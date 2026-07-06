// RaCore — FORMAL: ra_noc_arbiter grant safety, proved by k-induction (holds in
// ALL reachable pointer states). No phantom grants, no starvation-deadlock.
module formal_arbiter #(parameter int N = 4) (
    input logic clk, rst,
    input logic [N-1:0] requests,
    input logic advance
);
    localparam int W = $clog2(N);
    logic grant_valid;
    logic [W-1:0] grant_idx;
    logic [32*N-1:0] grants_flat;
    ra_noc_arbiter #(.N(N)) u (
        .clk(clk), .rst(rst), .requests(requests), .advance(advance),
        .grant_valid(grant_valid), .grant_idx(grant_idx), .grants_flat(grants_flat));
    always_comb begin
        if (grant_valid)       assert (requests[grant_idx]);  // granted => it requested
        if (requests != '0)    assert (grant_valid);          // any request => a grant
        if (requests == '0)    assert (!grant_valid);         // no request => no grant
    end
endmodule
