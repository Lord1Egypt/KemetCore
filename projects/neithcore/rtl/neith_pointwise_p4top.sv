// P&R wrapper for NeithCore pointwise multiplier (KemetCore Phase 4 P&R)
//
// Wraps the sequential neith_pointwise datapath in registers to ensure
// exact timing constraint boundaries during ASAP7 synthesis and P&R.

module neith_pointwise_p4top (
    input  logic        clk,
    input  logic        rst_n,
    input  logic        start,
    input  logic        in_valid,
    input  logic [12:0] a_in,
    input  logic [12:0] b_in,
    input  logic [7:0]  rd_addr,
    output logic [12:0] out_data,
    output logic        busy,
    output logic        done
);
    logic        start_reg;
    logic        in_valid_reg;
    logic [12:0] a_in_reg, b_in_reg;
    logic [7:0]  rd_addr_reg;
    
    logic [12:0] out_data_comb;
    logic        busy_comb, done_comb;

    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            start_reg    <= 1'b0;
            in_valid_reg <= 1'b0;
            a_in_reg     <= '0;
            b_in_reg     <= '0;
            rd_addr_reg  <= '0;
            
            out_data     <= '0;
            busy         <= 1'b0;
            done         <= 1'b0;
        end else begin
            start_reg    <= start;
            in_valid_reg <= in_valid;
            a_in_reg     <= a_in;
            b_in_reg     <= b_in;
            rd_addr_reg  <= rd_addr;
            
            out_data     <= out_data_comb;
            busy         <= busy_comb;
            done         <= done_comb;
        end
    end

    neith_pointwise u_core (
        .clk(clk),
        .rst_n(rst_n),
        .start(start_reg),
        .in_valid(in_valid_reg),
        .a_in(a_in_reg),
        .b_in(b_in_reg),
        .rd_addr(rd_addr_reg),
        .out_data(out_data_comb),
        .busy(busy_comb),
        .done(done_comb)
    );
endmodule
