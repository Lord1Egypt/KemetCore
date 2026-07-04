// SethCore — RV32 machine-mode CSR file (Zicsr storage + RMW) — Phase 2 RTL
//
// The M-mode CSR subset a minimal RV32IM trap-capable core needs: mstatus, misa,
// mie, mtvec, mscratch, mepc, mcause, mtval, mip, and the read-only ID CSRs. It
// applies the Zicsr read/modify/write (csrrw/csrrs/csrrc + immediate forms) and
// WARL-legalises every write, exactly matching golden seth_mcsr_model.MCsr:
//   * mstatus : only MIE(3)/MPIE(7) writable; MPP(12:11) reads fixed 2'b11
//   * misa    : read-only 0x40001100 (MXL=32, ext I+M)
//   * mie     : only MSIE(3)/MTIE(7)/MEIE(11) writable
//   * mtvec   : BASE[31:2] writable, MODE = bit0 only (bit1 forced 0, WARL)
//   * mepc    : bit0 forced 0 (IALIGN=32); mscratch/mcause/mtval fully writable
//   * mip / ID CSRs : read-only (mip reads 0 here; no soft-writable interrupt bits)
// rd_val is the pre-write value (combinational); the write commits on a `valid`
// cycle. Trap side-effects (auto mepc/mcause) are a later core-integration step.
//
// Verified bit-exact vs golden MCsr over random CSR-op sequences — see tb/test_mcsr.py.

module seth_mcsr (
    input  logic        clk,
    input  logic        rst,
    input  logic        valid,       // a CSR instruction executes this cycle
    input  logic [2:0]  funct3,      // [1:0] RW/RS/RC, [2] immediate form
    input  logic [11:0] csr_addr,
    input  logic [31:0] rs1,
    input  logic [4:0]  zimm,
    output logic [31:0] rd_val,      // pre-write value of csr_addr (to rd)
    input  logic [11:0] rd_addr,     // independent read-back port (verification/debug)
    output logic [31:0] rd_data
);
    localparam logic [11:0] MSTATUS=12'h300, MISA=12'h301, MIE=12'h304, MTVEC=12'h305,
                            MSCRATCH=12'h340, MEPC=12'h341, MCAUSE=12'h342, MTVAL=12'h343;
    localparam logic [31:0] MISA_VAL      = 32'h4000_1100;              // MXL=32, I+M
    localparam logic [31:0] MSTATUS_WMASK = (32'h1 << 3) | (32'h1 << 7);
    localparam logic [31:0] MSTATUS_MPP   = 32'h3 << 11;
    localparam logic [31:0] MIE_WMASK     = (32'h1 << 3) | (32'h1 << 7) | (32'h1 << 11);

    // stored (writable) state
    logic [31:0] mstatus_s, mtvec_s, mie_s, mscratch_s, mepc_s, mcause_s, mtval_s;

    // combinational read of any CSR address -> its current legal value
    function automatic logic [31:0] csr_read(input logic [11:0] a);
        case (a)
            MSTATUS:  csr_read = (mstatus_s & MSTATUS_WMASK) | MSTATUS_MPP;
            MISA:     csr_read = MISA_VAL;
            MIE:      csr_read = mie_s & MIE_WMASK;
            MTVEC:    csr_read = mtvec_s;
            MSCRATCH: csr_read = mscratch_s;
            MEPC:     csr_read = mepc_s & 32'hFFFF_FFFE;
            MCAUSE:   csr_read = mcause_s;
            MTVAL:    csr_read = mtval_s;
            default:  csr_read = 32'h0;            // mip, ID CSRs, unimplemented -> 0
        endcase
    endfunction

    wire [31:0] old     = csr_read(csr_addr);
    wire [31:0] operand = funct3[2] ? {27'd0, zimm} : rs1;

    // read/modify/write raw value + write-enable per Zicsr
    logic [31:0] raw;
    logic        do_write;
    always_comb begin
        case (funct3[1:0])
            2'b01:   begin raw = operand;                   do_write = valid;              end // RW
            2'b10:   begin raw = old | operand;             do_write = valid && (operand != 0); end // RS
            2'b11:   begin raw = old & ~operand;            do_write = valid && (operand != 0); end // RC
            default: begin raw = old;                       do_write = 1'b0;               end
        endcase
    end

    assign rd_val  = old;
    assign rd_data = csr_read(rd_addr);

    always_ff @(posedge clk) begin
        if (rst) begin
            mstatus_s <= 32'h0; mtvec_s <= 32'h0; mie_s <= 32'h0; mscratch_s <= 32'h0;
            mepc_s <= 32'h0; mcause_s <= 32'h0; mtval_s <= 32'h0;
        end else if (do_write) begin
            case (csr_addr)                      // WARL legalisation on store
                MSTATUS:  mstatus_s  <= raw & MSTATUS_WMASK;
                MIE:      mie_s      <= raw & MIE_WMASK;
                MTVEC:    mtvec_s    <= (raw & 32'hFFFF_FFFC) | (raw & 32'h1);
                MSCRATCH: mscratch_s <= raw;
                MEPC:     mepc_s     <= raw & 32'hFFFF_FFFE;
                MCAUSE:   mcause_s   <= raw;
                MTVAL:    mtval_s    <= raw;
                default:  ;                       // read-only CSRs: ignore
            endcase
        end
    end
endmodule
