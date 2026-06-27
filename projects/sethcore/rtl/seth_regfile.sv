// SethCore — RV32 register file (KemetCore Phase 2 RTL)
//
// 32 x 32-bit architectural register file with two asynchronous read ports and
// one synchronous write port. x0 is hardwired to zero (writes to it are dropped,
// reads of it return 0). This is the datapath's state element: the ID stage reads
// rs1/rs2, the WB stage writes rd.
//
// Spec (deliberate, standard): write commits on the rising clock edge; reads are
// combinational over the *committed* state (no internal write-to-read bypass) —
// same-cycle WB->ID forwarding is the hazard unit's job, kept out of the regfile.
//
// Verified against a Python reference model — see tb/test_regfile.py.
// Yosys-portable; the only sequential state is the register array.

module seth_regfile (
    input  logic        clk,
    input  logic        we,
    input  logic [4:0]  waddr,
    input  logic [31:0] wdata,
    input  logic [4:0]  raddr1,
    input  logic [4:0]  raddr2,
    output logic [31:0] rdata1,
    output logic [31:0] rdata2
);
    logic [31:0] regs [0:31];

    always_ff @(posedge clk)
        if (we && waddr != 5'd0)
            regs[waddr] <= wdata;

    assign rdata1 = (raddr1 == 5'd0) ? 32'd0 : regs[raddr1];
    assign rdata2 = (raddr2 == 5'd0) ? 32'd0 : regs[raddr2];
endmodule
