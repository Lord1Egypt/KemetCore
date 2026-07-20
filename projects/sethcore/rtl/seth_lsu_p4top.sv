// SethCore — registered P&R boundary top for seth_lsu (KemetCore Phase 4 depth)
//
// seth_lsu is purely combinational. This wrapper latches the operands,
// drives the verified core, and latches the result — a real reg -> logic -> reg path for
// ASAP7 place/route + timing closure. seth_lsu is instantiated UNCHANGED.
module seth_lsu_p4top (
    input  logic        clk,
    input  logic        rst,
    input  logic [2:0]  funct3_in,
    input  logic [1:0]  addr_lo_in,
    input  logic [31:0] mem_word_in,
    input  logic [31:0] store_data_in,
    output logic [31:0] load_data_out,
    output logic [31:0] store_word_out,
    output logic [3:0]  wstrb_out
);
    logic [2:0]  funct3_q;
    logic [1:0]  addr_lo_q;
    logic [31:0] mem_word_q;
    logic [31:0] store_data_q;

    logic [31:0] load_data_c;
    logic [31:0] store_word_c;
    logic [3:0]  wstrb_c;

    always_ff @(posedge clk) begin
        if (rst) begin
            funct3_q <= 3'd0;
            addr_lo_q <= 2'd0;
            mem_word_q <= 32'd0;
            store_data_q <= 32'd0;
        end else begin
            funct3_q <= funct3_in;
            addr_lo_q <= addr_lo_in;
            mem_word_q <= mem_word_in;
            store_data_q <= store_data_in;
        end
    end

    seth_lsu u_core (
        .funct3(funct3_q),
        .addr_lo(addr_lo_q),
        .mem_word(mem_word_q),
        .store_data(store_data_q),
        .load_data(load_data_c),
        .store_word(store_word_c),
        .wstrb(wstrb_c)
    );

    always_ff @(posedge clk) begin
        if (rst) begin
            load_data_out <= 32'd0;
            store_word_out <= 32'd0;
            wstrb_out <= 4'd0;
        end else begin
            load_data_out <= load_data_c;
            store_word_out <= store_word_c;
            wstrb_out <= wstrb_c;
        end
    end
endmodule
