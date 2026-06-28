// AtumCore — vector integer compare-to-mask unit (KemetCore Phase 2 RTL)
//
// The mask-producing datapath of the RVV unit: VLMAX parallel 32-bit comparators
// that evaluate one element-wise vector compare (vd_mask[i] = vs1[i] CMP vs2[i]) in
// a single combinational pass. The destination is a MASK register — one bit per
// lane, not a full element — which is what RVV vmseq/vmslt/... write and what the
// masked execution in the rest of the unit consumes.
//
// A lane bit is set only when the lane is BOTH body-active (i < vl) AND mask-active
// (mask[i]) AND the comparison holds; otherwise the bit reads 0. This mirrors the
// golden VectorUnit._cmp exactly (inactive/tail lanes read 0).
//
// Signedness: vmsltu/vmsleu treat operands as unsigned 32-bit; vmslt/vmsle treat
// them as signed; vmseq/vmsne are bit equality (sign-independent). Operands cross
// the boundary packed little-endian by lane: element i at bits [i*ELEN +: ELEN].
// Purely combinational — Yosys must report 0 latches. Verified vs the golden — see
// tb/test_vmask.py.

module atum_vmask #(
    parameter int VLMAX = 8,
    parameter int ELEN  = 32
) (
    input  logic [VLMAX*ELEN-1:0]      vs1,
    input  logic [VLMAX*ELEN-1:0]      vs2,
    input  logic [2:0]                 op,
    input  logic [VLMAX-1:0]           mask,
    input  logic [$clog2(VLMAX+1)-1:0] vl,
    output logic [VLMAX-1:0]           vd_mask
);
    // op encoding (matches golden compare method order)
    localparam logic [2:0] OP_SEQ  = 3'd0,   // ==
                           OP_SNE  = 3'd1,   // !=
                           OP_SLTU = 3'd2,   // unsigned <
                           OP_SLT  = 3'd3,   // signed   <
                           OP_SLEU = 3'd4,   // unsigned <=
                           OP_SLE  = 3'd5;   // signed   <=

    always_comb begin
        for (int i = 0; i < VLMAX; i++) begin
            logic [ELEN-1:0] a, b;
            logic            cmp, active;
            a = vs1[i*ELEN +: ELEN];
            b = vs2[i*ELEN +: ELEN];
            unique case (op)
                OP_SEQ:  cmp = (a == b);
                OP_SNE:  cmp = (a != b);
                OP_SLTU: cmp = (a < b);
                OP_SLT:  cmp = ($signed(a) <  $signed(b));
                OP_SLEU: cmp = (a <= b);
                OP_SLE:  cmp = ($signed(a) <= $signed(b));
                default: cmp = 1'b0;
            endcase
            active = (i < vl) && mask[i];
            vd_mask[i] = active && cmp;
        end
    end
endmodule
