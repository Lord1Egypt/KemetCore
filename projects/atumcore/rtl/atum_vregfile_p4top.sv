// AtumCore — vregfile unit (Phase 4 P&R wrapper)
//
// Wraps atum_vregfile in a registered boundary (flop in, flop out) to provide
// constrained I/O timing for OpenROAD ASAP7 flow.

module atum_vregfile_p4top (
    input  logic        clk,
    input  logic        rst,
    input  logic        we,
    input  logic [4:0]  waddr,
    input  logic [255:0] wdata,
    input  logic [4:0]  raddr1,
    input  logic [4:0]  raddr2,
    input  logic [4:0]  raddr3,
    output logic [255:0] rdata1,
    output logic [255:0] rdata2,
    output logic [255:0] rdata3
);

    // Flop in
    logic        rst_q;
    logic        we_q;
    logic [4:0]  waddr_q;
    logic [255:0] wdata_q;
    logic [4:0]  raddr1_q;
    logic [4:0]  raddr2_q;
    logic [4:0]  raddr3_q;

    always_ff @(posedge clk) begin
        rst_q    <= rst;
        we_q     <= we;
        waddr_q  <= waddr;
        wdata_q  <= wdata;
        raddr1_q <= raddr1;
        raddr2_q <= raddr2;
        raddr3_q <= raddr3;
    end

    // The core
    logic [255:0] rdata1_d, rdata2_d, rdata3_d;
    
    atum_vregfile #(
        .NREGS(32),
        .VLMAX(8),
        .ELEN(32)
    ) core (
        .clk   (clk     ),
        .rst   (rst_q   ),
        .we    (we_q    ),
        .waddr (waddr_q ),
        .wdata (wdata_q ),
        .raddr1(raddr1_q),
        .raddr2(raddr2_q),
        .raddr3(raddr3_q),
        .rdata1(rdata1_d),
        .rdata2(rdata2_d),
        .rdata3(rdata3_d)
    );

    // Flop out
    always_ff @(posedge clk) begin
        rdata1 <= rdata1_d;
        rdata2 <= rdata2_d;
        rdata3 <= rdata3_d;
    end

endmodule
