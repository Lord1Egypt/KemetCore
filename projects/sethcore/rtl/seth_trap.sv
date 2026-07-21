// SethCore — M-mode trap controller (Zicsr trap side-effects) — Phase 2 RTL
//
// Combinational vectoring + CSR-update logic for taking a trap and returning from
// one. Pairs with seth_mcsr, which stores the resulting mepc/mcause/mstatus. It
// exposes both the trap-enter and mret result sets at once; the core selects which
// to commit. mstatus layout matches seth_mcsr (MIE=3, MPIE=7, MPP=[12:11]=2'b11).
//
// Trap enter:
//   enter_target = mtvec BASE, or BASE + 4*cause for an interrupt when MODE(bit0)=1
//   enter_mepc   = pc (bit0 cleared);  enter_mcause = {is_interrupt, cause[30:0]}
//   enter_mstatus: MPIE <- MIE, MIE <- 0, MPP <- 2'b11
// mret:
//   ret_target   = mepc (bit0 cleared)
//   ret_mstatus  : MIE <- MPIE, MPIE <- 1
//
// Bit-exact vs golden seth_trap_model — see tb/test_trap.py. Combinational.

module seth_trap (
    input  logic [31:0] pc,            // interrupted instruction pc (for mepc)
    input  logic [30:0] cause,         // exception/interrupt cause code
    input  logic        is_interrupt,
    input  logic [31:0] mtvec,
    input  logic [31:0] mstatus,
    input  logic [31:0] mepc,          // for mret
    output logic [31:0] enter_target,
    output logic [31:0] enter_mepc,
    output logic [31:0] enter_mcause,
    output logic [31:0] enter_mstatus,
    output logic [31:0] ret_target,
    output logic [31:0] ret_mstatus
);
    wire [31:0] base     = mtvec & 32'hFFFF_FFFC;
    wire        vec_mode = mtvec[0];

    // 4*cause, kept 32-bit ( (4*c) mod 2^32 == 4*(c mod 2^30) == {cause[29:0],2'b00} )
    wire [31:0] cause_x4 = {cause[29:0], 2'b00};
    assign enter_target  = (is_interrupt && vec_mode) ? (base + cause_x4) : base;
    assign enter_mepc    = pc & 32'hFFFF_FFFC;
    assign enter_mcause  = {is_interrupt, cause};

    // MPIE <- old MIE, MIE <- 0, MPP <- 2'b11; other bits preserved
    wire mie_old = mstatus[3];
    assign enter_mstatus = (mstatus & ~((32'h1 << 3) | (32'h1 << 7) | (32'h3 << 11)))
                           | ({31'd0, mie_old} << 7) | (32'h3 << 11);

    assign ret_target    = mepc & 32'hFFFF_FFFC;
    // MIE <- old MPIE, MPIE <- 1
    wire mpie_old = mstatus[7];
    assign ret_mstatus   = (mstatus & ~((32'h1 << 3) | (32'h1 << 7)))
                           | ({31'd0, mpie_old} << 3) | (32'h1 << 7);
endmodule
