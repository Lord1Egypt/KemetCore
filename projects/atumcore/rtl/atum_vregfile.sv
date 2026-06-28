// AtumCore — vector register file (KemetCore Phase 2 RTL)
//
// NREGS architectural vector registers, each VLEN bits (VLMAX lanes x ELEN). Two
// asynchronous read ports and one synchronous write port; a synchronous reset clears
// all registers to 0 for a deterministic boot. Unlike the scalar file there is no
// hardwired-zero register (RVV v0 is a mask register, not a constant), matching the
// golden VectorUnit which treats v0..v31 uniformly.
//
// This is the state element the vector core writes from its writeback stage and reads
// for vs1/vs2. Verified against a Python reference — see tb/test_vregfile.py.
// Yosys-portable; the only sequential state is the register array.

module atum_vregfile #(
    parameter int NREGS = 32,
    parameter int VLMAX = 8,
    parameter int ELEN  = 32
) (
    input  logic                 clk,
    input  logic                 rst,
    input  logic                 we,
    input  logic [$clog2(NREGS)-1:0] waddr,
    input  logic [VLMAX*ELEN-1:0]    wdata,
    input  logic [$clog2(NREGS)-1:0] raddr1,
    input  logic [$clog2(NREGS)-1:0] raddr2,
    output logic [VLMAX*ELEN-1:0]    rdata1,
    output logic [VLMAX*ELEN-1:0]    rdata2
);
    logic [VLMAX*ELEN-1:0] regs [0:NREGS-1];

    always_ff @(posedge clk)
        if (rst)
            for (int i = 0; i < NREGS; i++)
                regs[i] <= '0;
        else if (we)
            regs[waddr] <= wdata;

    assign rdata1 = regs[raddr1];
    assign rdata2 = regs[raddr2];
endmodule
