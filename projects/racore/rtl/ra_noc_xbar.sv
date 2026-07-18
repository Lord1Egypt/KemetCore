// RaCore — KAI NoC Crossbar (KemetCore Phase 2 RTL)
//
// A simple crossbar integrating the ra_noc_arbiter to mux N masters to 1 slave
// (the shared scratchpad). This implements the NoC fabric for RaCore-Lite.

module ra_noc_xbar #(
    parameter int N = 4
) (
    input  logic clk,
    input  logic rst,

    // Master interfaces (N masters)
    input  logic [N-1:0]        m_req,
    input  logic [N-1:0][31:0]  m_addr,
    input  logic [N-1:0]        m_we,
    input  logic [N-1:0][3:0]   m_be,
    input  logic [N-1:0][31:0]  m_wdata,
    output logic [N-1:0]        m_grant,

    // Slave interface (1 slave)
    output logic        s_req,
    output logic [31:0] s_addr,
    output logic        s_we,
    output logic [3:0]  s_be,
    output logic [31:0] s_wdata
);

    logic           grant_valid;
    logic [$clog2(N)-1:0] grant_idx;
    
    ra_noc_arbiter #(
        .N(N)
    ) arbiter (
        .clk(clk),
        .rst(rst),
        .requests(m_req),
        .advance(grant_valid), // advance on any grant
        .grant_valid(grant_valid),
        .grant_idx(grant_idx),
        .grants_flat()
    );

    always_comb begin
        s_req   = 1'b0;
        s_addr  = 32'd0;
        s_we    = 1'b0;
        s_be    = 4'd0;
        s_wdata = 32'd0;
        m_grant = '0;

        if (grant_valid) begin
            m_grant[grant_idx] = 1'b1;
            s_req   = 1'b1;
            s_addr  = m_addr[grant_idx];
            s_we    = m_we[grant_idx];
            s_be    = m_be[grant_idx];
            s_wdata = m_wdata[grant_idx];
        end
    end

endmodule
