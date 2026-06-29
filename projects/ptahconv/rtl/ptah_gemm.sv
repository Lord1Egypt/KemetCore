// PtahConv — sequential fp32 GEMM engine (KemetCore Phase 2 RTL)
//
// Computes C[M][N] = A[M][K] @ B[K][N] in fp32 by driving a single ptah_mac PE
// over every (i,j) output, accumulating the K-long dot product SEQUENTIALLY. This
// is the conv-as-matmul datapath (im2col'd activations x filters); it reuses the
// cocotb-verified ptah_mac so each output equals the golden dot_seq in the exact
// hardware order -> the whole GEMM is bit-exact vs golden matmul_seq (the numpy
// references' pairwise sums are NOT bit-identical).
//
// Host protocol: preload A (load_sel=0) and B (load_sel=1) row-major via the
// load port while idle, pulse `start` with M/N/K, wait for `done`, then read C
// row-major (C[i][j] at rd_addr = i*N + j). Small fixed-capacity memories
// (MAX x MAX); M,N,K are runtime values up to MAX.
//
// Bit-exact vs golden matmul_seq — see tb/test_gemm.py.

module ptah_gemm #(
    parameter int MAX = 16
) (
    input  logic        clk,
    input  logic        rst_n,
    // preload port (A when load_sel=0, B when load_sel=1)
    input  logic        load_en,
    input  logic        load_sel,
    input  logic [15:0] load_addr,
    input  logic [31:0] load_data,
    // run
    input  logic        start,
    input  logic [7:0]  M,
    input  logic [7:0]  N,
    input  logic [7:0]  K,
    output logic        busy,
    output logic        done,
    // result read
    input  logic [15:0] rd_addr,
    output logic [31:0] c_data
);
    localparam int AD = MAX * MAX;

    logic [31:0] amem [0:AD-1];
    logic [31:0] bmem [0:AD-1];
    logic [31:0] cmem [0:AD-1];

    logic [7:0]  mr, nr, kr;          // latched dims
    logic [7:0]  i, j, k;             // loop indices
    logic [15:0] aidx, bidx;

    // operand fetch (combinational from the memories)
    assign aidx = i * kr + {8'b0, k};
    assign bidx = k * nr + {8'b0, j};
    wire [31:0] a_op = amem[aidx[$clog2(AD)-1:0]];
    wire [31:0] b_op = bmem[bidx[$clog2(AD)-1:0]];

    typedef enum logic [1:0] {IDLE, COMP, WB} state_t;
    state_t state;

    logic        mac_en, mac_clear;
    logic [31:0] mac_acc;
    ptah_mac u_mac (
        .clk(clk), .rst_n(rst_n), .en(mac_en), .clear(mac_clear),
        .a(a_op), .b(b_op), .acc(mac_acc)
    );

    always_comb begin
        mac_en    = (state == COMP);
        mac_clear = (state == COMP) && (k == 8'd0);
    end

    integer t;
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            state <= IDLE; busy <= 1'b0; done <= 1'b0;
            i <= 8'd0; j <= 8'd0; k <= 8'd0;
            mr <= 8'd0; nr <= 8'd0; kr <= 8'd0;
        end else begin
            done <= 1'b0;
            if (load_en) begin
                if (load_sel) bmem[load_addr[$clog2(AD)-1:0]] <= load_data;
                else          amem[load_addr[$clog2(AD)-1:0]] <= load_data;
            end
            case (state)
                IDLE: begin
                    busy <= 1'b0;
                    if (start) begin
                        mr <= M; nr <= N; kr <= K;
                        i <= 8'd0; j <= 8'd0; k <= 8'd0;
                        busy <= 1'b1; state <= COMP;
                    end
                end
                COMP: begin
                    // this cycle accumulates product k (mac_en high); advance k
                    if (k == kr - 8'd1) state <= WB;   // acc finalises at next edge
                    else                k <= k + 8'd1;
                end
                WB: begin
                    cmem[(i * nr + j)] <= mac_acc;      // store finished output
                    k <= 8'd0;
                    if (j == nr - 8'd1) begin
                        j <= 8'd0;
                        if (i == mr - 8'd1) begin
                            busy <= 1'b0; done <= 1'b1; state <= IDLE;
                        end else begin
                            i <= i + 8'd1; state <= COMP;
                        end
                    end else begin
                        j <= j + 8'd1; state <= COMP;
                    end
                end
                default: state <= IDLE;
            endcase
        end
    end

    assign c_data = cmem[rd_addr[$clog2(AD)-1:0]];
endmodule
