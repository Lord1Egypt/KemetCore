// RaCore — KAI (Kemet Accelerator Interface) register block — KemetCore Phase 2 RTL
//
// The memory-mapped register contract every accelerator implements, so the SoC
// host drives any block the same way. Word offsets:
//   0x000 ID     (RO) = {BLOCK_ID, 24'h4B4D54 'KMT'}
//   0x004 CAPS   (RW)
//   0x008 CTRL   (RW)  bit0 GO, bit1 ABORT, bit2 IRQ_EN, bit3 SOFT_RST
//   0x00C STATUS (RO from host's view; updated by hardware) bit0 BUSY,1 DONE,2 ERR
//   0x020 SRC / 0x028 DST / 0x030 LEN (RW descriptor)
//   0xF00 PERF   (RO) cycle count, latched from `perf` when the engine finishes
//
// Writing CTRL with the GO bit set emits a one-cycle `go` pulse and sets BUSY; the
// wrapped engine runs and asserts `done` (with its `perf` count), which clears BUSY,
// sets DONE and latches PERF. ABORT/SOFT_RST clear the run state. SRC/DST/LEN/CTRL
// are exposed to the engine. Synchronous reset.
//
// Verified bit-exact vs the Python reference kai_regs_step — see tb/test_kai_regs.py.

module ra_kai_regs #(
    parameter logic [7:0] BLOCK_ID = 8'h00
) (
    input  logic        clk,
    input  logic        rst,
    input  logic [11:0] addr,
    input  logic        wen,
    input  logic        ren,
    input  logic [31:0] wdata,
    output logic [31:0] rdata,
    // engine handshake
    output logic        go,            // 1-cycle pulse on CTRL.GO write
    input  logic        done,          // engine finished
    input  logic        err_in,        // engine error
    input  logic [31:0] perf,          // cycle count, latched on done
    output logic [31:0] src,
    output logic [31:0] dst,
    output logic [31:0] len,
    output logic [31:0] ctrl
);
    localparam [11:0] OFF_ID=12'h000, OFF_CAPS=12'h004, OFF_CTRL=12'h008,
                      OFF_STAT=12'h00C, OFF_SRC=12'h020, OFF_DST=12'h028,
                      OFF_LEN=12'h030, OFF_PERF=12'hF00;
    localparam [31:0] ID_VAL = {BLOCK_ID, 24'h4B_4D54};

    logic [31:0] caps, status, perf_r;

    always_ff @(posedge clk) begin
        if (rst) begin
            caps <= 32'd0; ctrl <= 32'd0; status <= 32'd0;
            src <= 32'd0; dst <= 32'd0; len <= 32'd0; perf_r <= 32'd0;
            go <= 1'b0;
        end else begin
            go <= 1'b0;
            if (wen) begin
                case (addr)
                    OFF_CAPS: caps <= wdata;
                    OFF_SRC:  src  <= wdata;
                    OFF_DST:  dst  <= wdata;
                    OFF_LEN:  len  <= wdata;
                    OFF_CTRL: begin
                        ctrl <= wdata;
                        if (wdata[0]) begin           // GO
                            go     <= 1'b1;
                            status <= 32'h0000_0001;  // BUSY
                        end
                        if (wdata[1] || wdata[3]) begin  // ABORT or SOFT_RST
                            status <= 32'd0;
                        end
                    end
                    default: ;                        // ID/STATUS/PERF not host-writable
                endcase
            end
            if (done) begin
                status <= err_in ? 32'h0000_0006 : 32'h0000_0002;  // ERR|DONE : DONE
                perf_r <= perf;
            end
        end
    end

    always_comb begin
        case (addr)
            OFF_ID:   rdata = ID_VAL;
            OFF_CAPS: rdata = caps;
            OFF_CTRL: rdata = ctrl;
            OFF_STAT: rdata = status;
            OFF_SRC:  rdata = src;
            OFF_DST:  rdata = dst;
            OFF_LEN:  rdata = len;
            OFF_PERF: rdata = perf_r;
            default:  rdata = 32'd0;
        endcase
    end
endmodule
