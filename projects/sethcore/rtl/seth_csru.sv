// SethCore — Zicsr CSR register bank (KemetCore Phase 2 RTL)
//
// Adds storage to the combinational seth_csr datapath: a 16-entry CSR register
// bank with the full read-modify-write Zicsr semantics. On a valid CSR
// instruction it reads the addressed CSR, computes the rd value (old contents)
// and the next value via the verified seth_csr unit, and commits the write on the
// clock edge when csr_we is asserted (CSRRW always; CSRRS/CSRRC only on a non-zero
// operand). A synchronous reset clears the bank.
//
// This is a generic Zicsr storage block — real machine-mode CSRs with side
// effects (counters, trap registers, WARL fields) layer on top of it. CSRs are
// indexed by the low 4 address bits.
//
// Verified against the Python reference csr_bank_step — see tb/test_csru.py.

module seth_csru (
    input  logic        clk,
    input  logic        rst,
    input  logic        valid,       // a CSR instruction executes this cycle
    input  logic [2:0]  funct3,
    input  logic [11:0] csr_addr,
    input  logic [31:0] rs1,
    input  logic [4:0]  zimm,
    output logic [31:0] rd_val,      // value written to rd (old CSR), combinational
    input  logic [11:0] rd_addr,     // debug/read-back address
    output logic [31:0] rd_data      // current contents of rd_addr (combinational)
);
    logic [31:0] csr [0:15];
    wire [3:0]   a   = csr_addr[3:0];
    wire [31:0]  cur = csr[a];

    logic [31:0] csr_out;
    logic        csr_we;
    seth_csr u_op (
        .funct3 (funct3),
        .csr_in (cur),
        .rs1    (rs1),
        .zimm   (zimm),
        .rd_val (rd_val),
        .csr_out(csr_out),
        .csr_we (csr_we)
    );

    integer i;
    always_ff @(posedge clk) begin
        if (rst)
            for (i = 0; i < 16; i++) csr[i] <= 32'd0;
        else if (valid && csr_we)
            csr[a] <= csr_out;
    end

    assign rd_data = csr[rd_addr[3:0]];
endmodule
