// AtumCore — vector floating-point sign-injection unit (KemetCore Phase 2 RTL)
//
// Builds each result lane from the magnitude (exponent+mantissa) of vs1 and a sign
// chosen by op — pure bit manipulation, no arithmetic:
//   op=0 vfsgnj   -> sign = sign(vs2)             (copysign)
//   op=1 vfsgnjn  -> sign = ~sign(vs2)            (negate when vs2==vs1)
//   op=2 vfsgnjx  -> sign = sign(vs1) ^ sign(vs2) (abs when vs2==vs1)
//
// Tail lanes (i >= vl) read 0. Mirrors golden VectorUnit.vfsgnj exactly. Vectors
// cross the boundary packed little-endian by lane (element i at bits [i*ELEN +:
// ELEN]); fp32 layout = {sign[31], exp[30:23], mant[22:0]}. Purely combinational —
// Yosys must report 0 latches. Verified vs the golden — see tb/test_vfsgnj.py.

module atum_vfsgnj #(
    parameter int VLMAX = 8,
    parameter int ELEN  = 32          // fp32 lanes
) (
    input  logic [VLMAX*ELEN-1:0]      vs1,     // magnitude source
    input  logic [VLMAX*ELEN-1:0]      vs2,     // sign source
    input  logic [1:0]                 op,      // 0 sgnj, 1 sgnjn, 2 sgnjx
    input  logic [$clog2(VLMAX+1)-1:0] vl,
    output logic [VLMAX*ELEN-1:0]      vd
);
    always_comb begin
        logic [ELEN-1:0] a, b;
        logic            s;
        for (int i = 0; i < VLMAX; i++) begin
            a = vs1[i*ELEN +: ELEN];
            b = vs2[i*ELEN +: ELEN];
            unique case (op)
                2'd0:    s = b[ELEN-1];                 // copysign
                2'd1:    s = ~b[ELEN-1];                // negated sign
                2'd2:    s = a[ELEN-1] ^ b[ELEN-1];     // xor sign
                default: s = a[ELEN-1];
            endcase
            vd[i*ELEN +: ELEN] = (i < vl) ? {s, a[ELEN-2:0]} : '0;
        end
    end
endmodule
