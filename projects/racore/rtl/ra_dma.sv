// RaCore — descriptor DMA engine (KemetCore Phase 2 RTL)
//
// A byte-addressable scratchpad with a descriptor-driven copy engine: 1D (a
// contiguous run) and 2D/strided (rows of row_bytes at independent source/dest
// strides), mirroring the golden Dma.copy / copy_2d. Internally everything is the
// 2D form (1D = rows 1, row_bytes = len). One byte is moved per cycle:
//   mem[dst + r*dst_stride + c] <= mem[src + r*src_stride + c].
// For NON-overlapping regions this is identical to the golden's read-all-then-write
// (the SoC schedules non-overlapping descriptors).
//
// Host: preload the scratchpad via the load port, program the descriptor, pulse
// start, wait for done, then read bytes back. Verified bit-exact vs golden Dma —
// see tb/test_dma.py.

module ra_dma #(
    parameter int AW = 10                 // scratchpad address width (bytes)
) (
    input  logic          clk,
    input  logic          rst,
    // preload / readback port
    input  logic          load_en,
    input  logic [AW-1:0] load_addr,
    input  logic [7:0]    load_data,
    input  logic [AW-1:0] rd_addr,
    output logic [7:0]    rd_data,
    // descriptor
    input  logic [AW-1:0] src,
    input  logic [AW-1:0] dst,
    input  logic [15:0]   rows,           // 1 for a 1D copy
    input  logic [15:0]   row_bytes,      // = length for a 1D copy
    input  logic [15:0]   src_stride,
    input  logic [15:0]   dst_stride,
    input  logic          start,
    output logic          busy,
    output logic          done
);
    localparam int SIZE = (1 << AW);
    logic [7:0] mem [0:SIZE-1];

    logic [15:0] r, c;
    typedef enum logic [1:0] {IDLE, COPY} state_t;
    state_t state;

    // current source/dest byte addresses (truncated to the scratchpad size)
    wire [31:0] saddr = {{(32-AW){1'b0}}, src} + (r * src_stride) + {16'd0, c};
    wire [31:0] daddr = {{(32-AW){1'b0}}, dst} + (r * dst_stride) + {16'd0, c};

    always_ff @(posedge clk) begin
        if (rst) begin
            state <= IDLE; busy <= 1'b0; done <= 1'b0; r <= 16'd0; c <= 16'd0;
        end else begin
            done <= 1'b0;
            if (load_en) mem[load_addr] <= load_data;
            case (state)
                IDLE: begin
                    busy <= 1'b0;
                    if (start) begin
                        r <= 16'd0; c <= 16'd0; busy <= 1'b1; state <= COPY;
                    end
                end
                COPY: begin
                    // move one byte (skip if the descriptor is empty)
                    if (rows != 16'd0 && row_bytes != 16'd0)
                        mem[daddr[AW-1:0]] <= mem[saddr[AW-1:0]];
                    if (rows == 16'd0 || row_bytes == 16'd0) begin
                        busy <= 1'b0; done <= 1'b1; state <= IDLE;
                    end else if (c == row_bytes - 16'd1) begin
                        c <= 16'd0;
                        if (r == rows - 16'd1) begin
                            busy <= 1'b0; done <= 1'b1; state <= IDLE;
                        end else r <= r + 16'd1;
                    end else c <= c + 16'd1;
                end
                default: state <= IDLE;
            endcase
        end
    end

    assign rd_data = mem[rd_addr];
endmodule
