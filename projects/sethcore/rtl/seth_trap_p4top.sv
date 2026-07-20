// SethCore — registered P&R boundary top for seth_trap (KemetCore Phase 4 depth)
//
// seth_trap is purely combinational. This wrapper latches the operands,
// drives the verified core, and latches the result — a real reg -> logic -> reg path for
// ASAP7 place/route + timing closure. seth_trap is instantiated UNCHANGED.
module seth_trap_p4top (
    input  logic        clk,
    input  logic        rst,
    input  logic [31:0] pc_in,
    input  logic [30:0] cause_in,
    input  logic        is_interrupt_in,
    input  logic [31:0] mtvec_in,
    input  logic [31:0] mstatus_in,
    input  logic [31:0] mepc_in,
    output logic [31:0] enter_target_out,
    output logic [31:0] enter_mepc_out,
    output logic [31:0] enter_mcause_out,
    output logic [31:0] enter_mstatus_out,
    output logic [31:0] ret_target_out,
    output logic [31:0] ret_mstatus_out
);
    logic [31:0] pc_q;
    logic [30:0] cause_q;
    logic        is_interrupt_q;
    logic [31:0] mtvec_q;
    logic [31:0] mstatus_q;
    logic [31:0] mepc_q;

    logic [31:0] enter_target_c;
    logic [31:0] enter_mepc_c;
    logic [31:0] enter_mcause_c;
    logic [31:0] enter_mstatus_c;
    logic [31:0] ret_target_c;
    logic [31:0] ret_mstatus_c;

    always_ff @(posedge clk) begin
        if (rst) begin
            pc_q <= 32'd0;
            cause_q <= 31'd0;
            is_interrupt_q <= 1'b0;
            mtvec_q <= 32'd0;
            mstatus_q <= 32'd0;
            mepc_q <= 32'd0;
        end else begin
            pc_q <= pc_in;
            cause_q <= cause_in;
            is_interrupt_q <= is_interrupt_in;
            mtvec_q <= mtvec_in;
            mstatus_q <= mstatus_in;
            mepc_q <= mepc_in;
        end
    end

    seth_trap u_core (
        .pc(pc_q),
        .cause(cause_q),
        .is_interrupt(is_interrupt_q),
        .mtvec(mtvec_q),
        .mstatus(mstatus_q),
        .mepc(mepc_q),
        .enter_target(enter_target_c),
        .enter_mepc(enter_mepc_c),
        .enter_mcause(enter_mcause_c),
        .enter_mstatus(enter_mstatus_c),
        .ret_target(ret_target_c),
        .ret_mstatus(ret_mstatus_c)
    );

    always_ff @(posedge clk) begin
        if (rst) begin
            enter_target_out  <= 32'd0;
            enter_mepc_out    <= 32'd0;
            enter_mcause_out  <= 32'd0;
            enter_mstatus_out <= 32'd0;
            ret_target_out    <= 32'd0;
            ret_mstatus_out   <= 32'd0;
        end else begin
            enter_target_out  <= enter_target_c;
            enter_mepc_out    <= enter_mepc_c;
            enter_mcause_out  <= enter_mcause_c;
            enter_mstatus_out <= enter_mstatus_c;
            ret_target_out    <= ret_target_c;
            ret_mstatus_out   <= ret_mstatus_c;
        end
    end
endmodule
