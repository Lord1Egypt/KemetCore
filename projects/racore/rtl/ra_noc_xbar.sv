// RaCore — KAI NoC Crossbar (KemetCore Phase 2 RTL)
//
// A true N x M bus interconnect crossbar integrating the ra_noc_arbiter.
// Routes N masters to M slaves based on address decoding.

module ra_noc_xbar #(
    parameter int M_COUNT = 4, // Masters
    parameter int S_COUNT = 2, // Slaves
    parameter logic [S_COUNT*32-1:0] S_BASE = {32'h10000000, 32'h00000000},
    parameter logic [S_COUNT*32-1:0] S_MASK = {32'hFFFF0000, 32'hFFF00000}
) (
    input  logic clk,
    input  logic rst,

    // Master interfaces
    input  logic [M_COUNT-1:0]        m_req,
    input  logic [M_COUNT*32-1:0]     m_addr_flat,
    input  logic [M_COUNT-1:0]        m_we,
    input  logic [M_COUNT*4-1:0]      m_be_flat,
    input  logic [M_COUNT*32-1:0]     m_wdata_flat,
    output logic [M_COUNT-1:0]        m_grant,
    output logic [M_COUNT*32-1:0]     m_rdata_flat,

    // Slave interfaces
    output logic [S_COUNT-1:0]        s_req,
    output logic [S_COUNT*32-1:0]     s_addr_flat,
    output logic [S_COUNT-1:0]        s_we,
    output logic [S_COUNT*4-1:0]      s_be_flat,
    output logic [S_COUNT*32-1:0]     s_wdata_flat,
    input  logic [S_COUNT*32-1:0]     s_rdata_flat
);

    // Internal unpacked arrays for structured access
    logic [31:0] m_addr  [0:M_COUNT-1];
    logic [3:0]  m_be    [0:M_COUNT-1];
    logic [31:0] m_wdata [0:M_COUNT-1];
    logic [31:0] m_rdata [0:M_COUNT-1];

    logic [31:0] s_addr  [0:S_COUNT-1];
    logic [3:0]  s_be    [0:S_COUNT-1];
    logic [31:0] s_wdata [0:S_COUNT-1];
    logic [31:0] s_rdata [0:S_COUNT-1];

    // Unflatten inputs
    generate
        for (genvar i = 0; i < M_COUNT; i++) begin : unflat_m
            assign m_addr[i]  = m_addr_flat[i*32 +: 32];
            assign m_be[i]    = m_be_flat[i*4 +: 4];
            assign m_wdata[i] = m_wdata_flat[i*32 +: 32];
        end
        for (genvar i = 0; i < S_COUNT; i++) begin : unflat_s
            assign s_rdata[i] = s_rdata_flat[i*32 +: 32];
        end
    endgenerate

    // Flatten outputs
    generate
        for (genvar i = 0; i < M_COUNT; i++) begin : flat_m
            assign m_rdata_flat[i*32 +: 32] = m_rdata[i];
        end
        for (genvar i = 0; i < S_COUNT; i++) begin : flat_s
            assign s_addr_flat[i*32 +: 32]  = s_addr[i];
            assign s_be_flat[i*4 +: 4]      = s_be[i];
            assign s_wdata_flat[i*32 +: 32] = s_wdata[i];
        end
    endgenerate

    // Decode master addresses
    logic [S_COUNT-1:0] m_to_s_req [0:M_COUNT-1];
    
    always_comb begin
        for (int m = 0; m < M_COUNT; m++) begin
            m_to_s_req[m] = '0;
            for (int s = 0; s < S_COUNT; s++) begin
                m_to_s_req[m][s] = m_req[m] && ((m_addr[m] & S_MASK[s*32 +: 32]) == S_BASE[s*32 +: 32]);
            end
        end
    end

    logic [S_COUNT-1:0]                   s_grant_valid;
    logic [$clog2(M_COUNT)-1:0] s_grant_idx [0:S_COUNT-1];
    
    // For each slave, collect requests from all masters
    logic [M_COUNT-1:0] s_requests [0:S_COUNT-1];
    always_comb begin
        for (int s = 0; s < S_COUNT; s++) begin
            for (int m = 0; m < M_COUNT; m++) begin
                s_requests[s][m] = m_to_s_req[m][s];
            end
        end
    end

    generate
        for (genvar s = 0; s < S_COUNT; s++) begin : gen_arb
            ra_noc_arbiter #(
                .N(M_COUNT)
            ) arbiter (
                .clk(clk),
                .rst(rst),
                .requests(s_requests[s]),
                .advance(s_grant_valid[s]), // advance on any grant
                .grant_valid(s_grant_valid[s]),
                .grant_idx(s_grant_idx[s]),
                .grants_flat()
            );
            
            always_comb begin
                s_req[s]   = s_grant_valid[s];
                s_addr[s]  = m_addr[ s_grant_idx[s] ];
                s_we[s]    = m_we[ s_grant_idx[s] ];
                s_be[s]    = m_be[ s_grant_idx[s] ];
                s_wdata[s] = m_wdata[ s_grant_idx[s] ];
            end
        end
    endgenerate

    // Route grants back to masters
    always_comb begin
        m_grant = '0;
        for (int s = 0; s < S_COUNT; s++) begin
            if (s_grant_valid[s]) begin
                m_grant[ s_grant_idx[s] ] = 1'b1;
            end
        end
    end

    // Track which slave each master successfully accessed for 1-cycle read latency
    localparam int S_IDX_W = (S_COUNT > 1) ? $clog2(S_COUNT) : 1;
    logic [M_COUNT*S_IDX_W-1:0] m_active_slave_q;
    logic [M_COUNT-1:0] m_active_q;

    always_ff @(posedge clk) begin
        if (rst) begin
            m_active_q <= '0;
            m_active_slave_q <= '0;
        end else begin
            m_active_q <= m_grant;
            for (int m = 0; m < M_COUNT; m++) begin
                if (m_grant[m]) begin
                    for (int s = 0; s < S_COUNT; s++) begin
                        if (s_grant_valid[s] && s_grant_idx[s] == m[$clog2(M_COUNT)-1:0]) begin
                            m_active_slave_q[m*S_IDX_W +: S_IDX_W] <= s[S_IDX_W-1:0];
                        end
                    end
                end
            end
        end
    end

    // Route read data back
    always_comb begin
        for (int m = 0; m < M_COUNT; m++) begin
            if (m_active_q[m]) begin
                m_rdata[m] = s_rdata[ m_active_slave_q[m*S_IDX_W +: S_IDX_W] ];
            end else begin
                m_rdata[m] = 32'd0;
            end
        end
    end

endmodule
