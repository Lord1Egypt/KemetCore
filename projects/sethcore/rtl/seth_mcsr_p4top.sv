// SethCore — registered P&R boundary top for seth_mcsr (KemetCore Phase 4 depth)
//
// Wraps seth_mcsr to ensure all I/O are registered.
module seth_mcsr_p4top (
    input  logic        clk,
    input  logic        rst,
    input  logic        valid_in,
    input  logic [2:0]  funct3_in,
    input  logic [11:0] csr_addr_in,
    input  logic [31:0] rs1_in,
    input  logic [4:0]  zimm_in,
    input  logic [11:0] rd_addr_in,
    output logic [31:0] rd_val_out,
    output logic [31:0] rd_data_out
);
    logic        valid_q;
    logic [2:0]  funct3_q;
    logic [11:0] csr_addr_q;
    logic [31:0] rs1_q;
    logic [4:0]  zimm_q;
    logic [11:0] rd_addr_q;

    logic [31:0] rd_val_c;
    logic [31:0] rd_data_c;

    always_ff @(posedge clk) begin
        if (rst) begin
            valid_q <= 1'b0;
            funct3_q <= 3'd0;
            csr_addr_q <= 12'd0;
            rs1_q <= 32'd0;
            zimm_q <= 5'd0;
            rd_addr_q <= 12'd0;
        end else begin
            valid_q <= valid_in;
            funct3_q <= funct3_in;
            csr_addr_q <= csr_addr_in;
            rs1_q <= rs1_in;
            zimm_q <= zimm_in;
            rd_addr_q <= rd_addr_in;
        end
    end

    seth_mcsr u_core (
        .clk(clk),
        .rst(rst),
        .valid(valid_q),
        .funct3(funct3_q),
        .csr_addr(csr_addr_q),
        .rs1(rs1_q),
        .zimm(zimm_q),
        .rd_val(rd_val_c),
        .rd_addr(rd_addr_q),
        .rd_data(rd_data_c)
    );

    always_ff @(posedge clk) begin
        if (rst) begin
            rd_val_out <= 32'd0;
            rd_data_out <= 32'd0;
        end else begin
            rd_val_out <= rd_val_c;
            rd_data_out <= rd_data_c;
        end
    end
endmodule
