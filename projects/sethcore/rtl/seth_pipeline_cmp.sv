// SethCore — pipeline comparison harness (KemetCore Phase 2 RTL, verification only)
//
// Instantiates the interlock pipeline (seth_pipeline) and the forwarding pipeline
// (seth_pipeline_fwd) side by side, sharing clock/reset and the program-load port.
// The testbench (tb/test_pipeline_fwd.py) loads the same program into both, runs
// until each halts, and checks:
//   (1) both reach the SAME architectural register state as the golden ISA model;
//   (2) the forwarding core halts in FEWER-OR-EQUAL cycles (strictly fewer on the
//       data-hazard-heavy programs) — proof that forwarding is a pure performance win.
// Not a synthesis target.

module seth_pipeline_cmp #(
    parameter int WORDS = 1024
) (
    input  logic        clk,
    input  logic        rst,
    input  logic        load_en,
    input  logic [31:0] load_addr,
    input  logic [31:0] load_data,
    output logic        il_halted,
    output logic        fw_halted
);
    seth_pipeline #(.WORDS(WORDS)) u_il (
        .clk(clk), .rst(rst), .load_en(load_en),
        .load_addr(load_addr), .load_data(load_data),
        .dbg_pc(), .halted(il_halted));

    seth_pipeline_fwd #(.WORDS(WORDS)) u_fw (
        .clk(clk), .rst(rst), .load_en(load_en),
        .load_addr(load_addr), .load_data(load_data),
        .dbg_pc(), .halted(fw_halted));
endmodule
