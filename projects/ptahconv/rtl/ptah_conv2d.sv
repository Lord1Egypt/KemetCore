// PtahConv — direct 2D convolution engine (KemetCore Phase 2 RTL)
//
// Single-batch fp32 conv: for each output (co,oh,ow) it streams the receptive
// field in (ic,ky,kx) order through one ptah_mac PE, accumulating SEQUENTIALLY so
// it is bit-exact vs the golden conv2d_seq (the numpy reference's np.sum is
// pairwise and NOT bit-identical). Implicit zero padding: a tap whose source falls
// outside the input feeds +0.0, and 0*w + acc == acc is an exact no-op.
//
// Host preloads the input (Cin*H*W, CHW) and weights (Cout*Cin*KH*KW) via the load
// ports, programs the runtime dims, pulses start, waits done, then reads the output
// (Cout*OH*OW, CHW). Fixed capacities MAX_* bound the buffers. Composes the
// verified ptah_mac. Verified bit-exact vs conv2d_seq — see tb/test_conv2d.py.

module ptah_conv2d #(
    parameter int MAX_IN  = 256,   // Cin*H*W
    parameter int MAX_W   = 256,   // Cout*Cin*KH*KW
    parameter int MAX_OUT = 256    // Cout*OH*OW
) (
    input  logic        clk,
    input  logic        rst,
    // preload ports
    input  logic        ld_in_en,
    input  logic [15:0] ld_in_addr,
    input  logic [31:0] ld_in_data,
    input  logic        ld_w_en,
    input  logic [15:0] ld_w_addr,
    input  logic [31:0] ld_w_data,
    // runtime dims
    input  logic [7:0]  Cin, H, W, Cout, KH, KW, stride, pad,
    input  logic        start,
    output logic        busy,
    output logic        done,
    // output read
    input  logic [15:0] rd_addr,
    output logic [31:0] rd_data
);
    logic [31:0] imem [0:MAX_IN-1];
    logic [31:0] wmem [0:MAX_W-1];
    logic [31:0] omem [0:MAX_OUT-1];

    // Address widths derived from the buffer capacities so the memory indices are
    // never silently truncated if MAX_* are raised above 256 (P0.3 hardening).
    localparam int AWI = (MAX_IN  > 1) ? $clog2(MAX_IN)  : 1;
    localparam int AWW = (MAX_W   > 1) ? $clog2(MAX_W)   : 1;
    localparam int AWO = (MAX_OUT > 1) ? $clog2(MAX_OUT) : 1;

    logic [7:0]  OH, OW;
    logic [7:0]  co, oh, ow, ic, ky, kx;
    // signed source coordinates (for padding compare)
    logic signed [15:0] ih, iw;
    wire in_range = (ih >= 0) && (ih < $signed({8'd0, H}))
                 && (iw >= 0) && (iw < $signed({8'd0, W}));

    // flat addresses (16-bit; products of <=8-bit dims, fit comfortably)
    wire [15:0] in_idx = (({8'd0,ic} * {8'd0,H}) + {8'd0,ih[7:0]}) * {8'd0,W} + {8'd0,iw[7:0]};
    wire [15:0] w_idx  = ((({8'd0,co} * {8'd0,Cin}) + {8'd0,ic}) * {8'd0,KH} + {8'd0,ky}) * {8'd0,KW} + {8'd0,kx};
    wire [15:0] o_idx  = (({8'd0,co} * {8'd0,OH}) + {8'd0,oh}) * {8'd0,OW} + {8'd0,ow};

    wire        last_tap = (ic == Cin - 8'd1) && (ky == KH - 8'd1) && (kx == KW - 8'd1);
    wire        first_tap = (ic == 8'd0) && (ky == 8'd0) && (kx == 8'd0);

    // ptah_mac PE
    wire [31:0] a_op = in_range ? imem[in_idx[AWI-1:0]] : 32'h0000_0000;   // pad -> +0.0
    wire [31:0] b_op = wmem[w_idx[AWW-1:0]];
    logic       mac_en, mac_clear;
    logic [31:0] mac_acc;
    ptah_mac u_mac (.clk(clk), .rst_n(~rst), .en(mac_en), .clear(mac_clear),
                    .a(a_op), .b(b_op), .acc(mac_acc));

    typedef enum logic [1:0] {IDLE, TAP, WB} state_t;
    state_t state;
    assign mac_en    = (state == TAP);
    assign mac_clear = (state == TAP) && first_tap;

    always_comb begin
        ih = $signed({8'd0, oh}) * $signed({8'd0, stride}) + $signed({8'd0, ky}) - $signed({8'd0, pad});
        iw = $signed({8'd0, ow}) * $signed({8'd0, stride}) + $signed({8'd0, kx}) - $signed({8'd0, pad});
    end

    always_ff @(posedge clk) begin
        if (rst) begin
            state <= IDLE; busy <= 1'b0; done <= 1'b0;
            co<=0; oh<=0; ow<=0; ic<=0; ky<=0; kx<=0; OH<=0; OW<=0;
        end else begin
            done <= 1'b0;
            // preload only while IDLE: gating with (state == IDLE) prevents a
            // stray load from corrupting imem/wmem during an in-flight convolution.
            if (ld_in_en && state == IDLE) imem[ld_in_addr[AWI-1:0]] <= ld_in_data;
            if (ld_w_en  && state == IDLE) wmem[ld_w_addr[AWW-1:0]]  <= ld_w_data;
            case (state)
                IDLE: begin
                    busy <= 1'b0;
                    if (start) begin
                        OH <= (H + 2*pad - KH) / stride + 8'd1;
                        OW <= (W + 2*pad - KW) / stride + 8'd1;
                        co<=0; oh<=0; ow<=0; ic<=0; ky<=0; kx<=0;
                        busy <= 1'b1; state <= TAP;
                    end
                end
                TAP: begin
                    // advance the inner (ic,ky,kx) iteration
                    if (last_tap) begin
                        state <= WB;        // acc finalises at this edge
                    end else if (kx == KW - 8'd1) begin
                        kx <= 0;
                        if (ky == KH - 8'd1) begin ky <= 0; ic <= ic + 8'd1; end
                        else ky <= ky + 8'd1;
                    end else kx <= kx + 8'd1;
                end
                WB: begin
                    omem[o_idx[AWO-1:0]] <= mac_acc;
                    ic<=0; ky<=0; kx<=0;
                    if (ow == OW - 8'd1) begin
                        ow <= 0;
                        if (oh == OH - 8'd1) begin
                            oh <= 0;
                            if (co == Cout - 8'd1) begin
                                busy <= 1'b0; done <= 1'b1; state <= IDLE;
                            end else co <= co + 8'd1;
                        end else oh <= oh + 8'd1;
                    end else ow <= ow + 8'd1;
                    state <= (co == Cout-8'd1 && oh == OH-8'd1 && ow == OW-8'd1) ? IDLE : TAP;
                end
                default: state <= IDLE;
            endcase
        end
    end

    assign rd_data = omem[rd_addr[AWO-1:0]];
endmodule
