// AtumCore — fp32 vector fused multiply-add lane array (KemetCore Phase 2 RTL)
//
// The fp FMA datapath of the RVV unit: VLMAX parallel fp32 lanes each computing a
// single-rounded fused multiply-add of the two sources and the destination
// accumulator, composing the bit-exact HapiCore fused core (hapi_fp32_fma — one
// rounding over the exact a*b+c). op[1:0] selects the full RVV FMA family:
//   0 = vfmacc  : vd =  vs1*vs2 + vd_old
//   1 = vfmsac  : vd =  vs1*vs2 - vd_old
//   2 = vfnmacc : vd = -vs1*vs2 - vd_old
//   3 = vfnmsac : vd = -vs1*vs2 + vd_old
// The product is negated (ops 2/3) by flipping a's sign before the fused multiply;
// the accumulator is negated (ops 1/2) by flipping acc's sign — both exact in IEEE
// since negation is a sign-bit flip and the single rounding still happens once inside
// the fused core. vd_old is BOTH the third FMA operand (the running accumulator) and
// the undisturbed value for inactive lanes. Active-element semantics match golden
// VectorUnit._wr_int: a lane writes only when body-active (i < vl) AND mask-active;
// else the destination element is undisturbed. fp32 elements cross the boundary as
// raw bit patterns, packed little-endian by lane (element i at [i*32 +: 32]).
// Purely combinational — Yosys must report 0 latches. Verified vs the golden — see
// tb/test_vfmacc.py.

module atum_vfmacc #(
    parameter int VLMAX = 8,
    parameter int ELEN  = 32
) (
    input  logic [VLMAX*ELEN-1:0]      vs1,
    input  logic [VLMAX*ELEN-1:0]      vs2,
    input  logic [VLMAX*ELEN-1:0]      vd_old,
    input  logic [1:0]                 op,    // 0 macc, 1 msac, 2 nmacc, 3 nmsac
    input  logic [VLMAX-1:0]           mask,
    input  logic [$clog2(VLMAX+1)-1:0] vl,
    output logic [VLMAX*ELEN-1:0]      vd_new
);
    localparam int VLW = $clog2(VLMAX+1);
    // product negated for ops 2/3 (the "n" variants); accumulator negated for 1/2.
    logic neg_prod, neg_acc;
    assign neg_prod = op[1];
    assign neg_acc  = op[0] ^ op[1];
    genvar gi;
    generate
        for (gi = 0; gi < VLMAX; gi++) begin : lane
            logic [ELEN-1:0] a0, b, acc, a, c, res;
            logic            active;
            assign a0  = vs1[gi*ELEN +: ELEN];
            assign b   = vs2[gi*ELEN +: ELEN];
            assign acc = vd_old[gi*ELEN +: ELEN];
            assign a   = neg_prod ? {~a0[ELEN-1],  a0[ELEN-2:0]}  : a0;
            assign c   = neg_acc  ? {~acc[ELEN-1], acc[ELEN-2:0]} : acc;
            hapi_fp32_fma u_fma (.a(a), .b(b), .c(c), .y(res));
            assign active = mask[gi] & (VLW'(gi) < vl);
            assign vd_new[gi*ELEN +: ELEN] = active ? res : acc;
        end
    endgenerate
endmodule
