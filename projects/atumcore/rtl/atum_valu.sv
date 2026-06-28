// AtumCore — vector integer ALU lane array (KemetCore Phase 2 RTL)
//
// The integer datapath of the RVV unit: VLMAX parallel 32-bit ALU lanes that
// evaluate one element-wise vector op (vd = vs1 OP vs2) in a single combinational
// pass, with RVV active-element semantics. A lane i commits its result only when it
// is BOTH body-active (i < vl) AND mask-active (mask[i]); otherwise the destination
// element keeps its old value (undisturbed tail/mask policy), mirroring the golden
// VectorUnit._wr_int exactly.
//
// Operands are read as unsigned 32-bit values (the golden widens uint32 lanes), so:
//   add/sub/mul keep the low 32 bits (wraparound); mul is the 32-bit low product;
//   shifts use shamt = b[4:0]; srl is logical. vmacc fuses into the destination:
//   r = vd_old + vs1*vs2 (low ELEN). This matches golden vadd/vsub/vmul/vand/vor/
//   vxor/vsll/vsrl/vmacc bit-for-bit. fp lanes (vfadd/vfmul over HapiCore fp32)
//   are a separate block.
//
// Vectors cross the port boundary packed little-endian by lane: element i occupies
// bits [i*ELEN +: ELEN]. Purely combinational — Yosys must report 0 latches.
// Verified vs the golden — see tb/test_valu.py.

module atum_valu #(
    parameter int VLMAX = 8,
    parameter int ELEN  = 32
) (
    input  logic [VLMAX*ELEN-1:0]      vs1,
    input  logic [VLMAX*ELEN-1:0]      vs2,
    input  logic [VLMAX*ELEN-1:0]      vd_old,
    input  logic [3:0]                 op,
    input  logic [VLMAX-1:0]           mask,
    input  logic [$clog2(VLMAX+1)-1:0] vl,
    output logic [VLMAX*ELEN-1:0]      vd_new
);
    // op encoding
    localparam logic [3:0] OP_ADD = 4'd0, OP_SUB = 4'd1, OP_MUL = 4'd2,
                           OP_AND = 4'd3, OP_OR  = 4'd4, OP_XOR = 4'd5,
                           OP_SLL = 4'd6, OP_SRL = 4'd7, OP_MACC = 4'd8;

    always_comb begin
        for (int i = 0; i < VLMAX; i++) begin
            logic [ELEN-1:0]   a, b, r;
            logic              active;
            a = vs1[i*ELEN +: ELEN];
            b = vs2[i*ELEN +: ELEN];
            unique case (op)
                OP_ADD:  r = a + b;
                OP_SUB:  r = a - b;
                OP_MUL:  r = a * b;            // low ELEN bits of the product
                OP_AND:  r = a & b;
                OP_OR:   r = a | b;
                OP_XOR:  r = a ^ b;
                OP_SLL:  r = a << b[4:0];
                OP_SRL:  r = a >> b[4:0];      // logical (a is unsigned)
                OP_MACC: r = vd_old[i*ELEN +: ELEN] + (a * b);  // vd += vs1*vs2 (low ELEN)
                default: r = '0;
            endcase
            // body-active (i < vl) AND mask-active -> write; else keep old element
            active = mask[i] & (32'(i) < {{(28){1'b0}}, vl});
            vd_new[i*ELEN +: ELEN] = active ? r : vd_old[i*ELEN +: ELEN];
        end
    end
endmodule
