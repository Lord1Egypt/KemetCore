// NeithCore — neith_polyaddsub registered wrapper for Phase 4 P&R
module neith_polyaddsub_p4top #(
    parameter int N = 256
) (
    input  logic        clk,
    input  logic        rst_n,
    input  logic        start,
    input  logic        op,
    input  logic        in_valid,
    input  logic [12:0] a_in,
    input  logic [12:0] b_in,
    input  logic [7:0]  rd_addr,
    output logic [12:0] out_data,
    output logic        busy,
    output logic        done
);
    logic        start_r;
    logic        op_r;
    logic        in_valid_r;
    logic [12:0] a_in_r;
    logic [12:0] b_in_r;
    logic [7:0]  rd_addr_r;

    logic [12:0] out_data_w;
    logic        busy_w;
    logic        done_w;

    logic [12:0] out_data_r;
    logic        busy_r;
    logic        done_r;

    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            start_r    <= '0;
            op_r       <= '0;
            in_valid_r <= '0;
            a_in_r     <= '0;
            b_in_r     <= '0;
            rd_addr_r  <= '0;
            out_data_r <= '0;
            busy_r     <= '0;
            done_r     <= '0;
        end else begin
            start_r    <= start;
            op_r       <= op;
            in_valid_r <= in_valid;
            a_in_r     <= a_in;
            b_in_r     <= b_in;
            rd_addr_r  <= rd_addr;
            out_data_r <= out_data_w;
            busy_r     <= busy_w;
            done_r     <= done_w;
        end
    end

    neith_polyaddsub #(
        .N(N)
    ) u_core (
        .clk(clk),
        .rst_n(rst_n),
        .start(start_r),
        .op(op_r),
        .in_valid(in_valid_r),
        .a_in(a_in_r),
        .b_in(b_in_r),
        .rd_addr(rd_addr_r),
        .out_data(out_data_w),
        .busy(busy_w),
        .done(done_w)
    );

    assign out_data = out_data_r;
    assign busy     = busy_r;
    assign done     = done_r;
endmodule
