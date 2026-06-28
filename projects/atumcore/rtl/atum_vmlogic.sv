// AtumCore — vector mask logical unit (KemetCore Phase 2 RTL)
//
// The mask-combining datapath of the RVV unit: bitwise logic on two mask operands
// (one bit per lane), producing a mask. These are the vmand.mm / vmor.mm / ... ops
// that combine the masks the compare unit (atum_vmask) produces — e.g. selecting
// elements that satisfy two predicates at once.
//
// Result bit i = (m1[i] OP m2[i]) for body-active lanes (i < vl), else 0. Mask
// logical ops are themselves unmasked; only the body is written here, mirroring the
// golden VectorUnit._vmlogic exactly. Purely combinational — Yosys must report 0
// latches. Verified vs the golden — see tb/test_vmlogic.py.

module atum_vmlogic #(
    parameter int VLMAX = 8
) (
    input  logic [VLMAX-1:0]           m1,
    input  logic [VLMAX-1:0]           m2,
    input  logic [2:0]                 op,
    input  logic [$clog2(VLMAX+1)-1:0] vl,
    output logic [VLMAX-1:0]           vd_mask
);
    // op encoding (matches golden mask-logic method order)
    localparam logic [2:0] OP_AND  = 3'd0,   // m1 & m2
                           OP_OR   = 3'd1,   // m1 | m2
                           OP_XOR  = 3'd2,   // m1 ^ m2
                           OP_NAND = 3'd3,   // ~(m1 & m2)
                           OP_NOR  = 3'd4,   // ~(m1 | m2)
                           OP_XNOR = 3'd5,   // ~(m1 ^ m2)
                           OP_ANDN = 3'd6,   // m1 & ~m2
                           OP_ORN  = 3'd7;   // m1 | ~m2

    always_comb begin
        for (int i = 0; i < VLMAX; i++) begin
            logic a, b, r;
            a = m1[i];
            b = m2[i];
            unique case (op)
                OP_AND:  r = a & b;
                OP_OR:   r = a | b;
                OP_XOR:  r = a ^ b;
                OP_NAND: r = ~(a & b);
                OP_NOR:  r = ~(a | b);
                OP_XNOR: r = ~(a ^ b);
                OP_ANDN: r = a & ~b;
                OP_ORN:  r = a | ~b;
                default: r = 1'b0;
            endcase
            vd_mask[i] = (i < vl) ? r : 1'b0;
        end
    end
endmodule
