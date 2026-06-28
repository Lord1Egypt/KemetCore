// AtumCore — fp32 vector subtract lane array (KemetCore Phase 2 RTL)
//
// Completes the fp arithmetic lane set (add/mul already in atum_vfpu): VLMAX parallel
// fp32 lanes computing a difference per combinational pass via the bit-exact HapiCore
// adder (subtraction is exact addition of the negated operand: x - y === x + (-y) in
// IEEE-754, and negation just flips the sign bit). op selects the operand order:
//   0 = vfsub  : vd = vs1 - vs2
//   1 = vfrsub : vd = vs2 - vs1
// Active-element semantics match golden VectorUnit._wr_f32: a lane writes only when
// body-active (i < vl) AND mask-active; else the destination element is undisturbed.
// fp32 elements cross the port boundary as raw bit patterns, packed little-endian by
// lane (element i at [i*32 +: 32]). Purely combinational — Yosys must report 0
// latches. Verified vs the golden — see tb/test_vfsub.py.

module atum_vfsub #(
    parameter int VLMAX = 8,
    parameter int ELEN  = 32
) (
    input  logic [VLMAX*ELEN-1:0]      vs1,
    input  logic [VLMAX*ELEN-1:0]      vs2,
    input  logic [VLMAX*ELEN-1:0]      vd_old,
    input  logic                       op,    // 0 = vfsub (vs1-vs2), 1 = vfrsub (vs2-vs1)
    input  logic [VLMAX-1:0]           mask,
    input  logic [$clog2(VLMAX+1)-1:0] vl,
    output logic [VLMAX*ELEN-1:0]      vd_new
);
    localparam int VLW = $clog2(VLMAX+1);
    genvar gi;
    generate
        for (gi = 0; gi < VLMAX; gi++) begin : lane
            logic [ELEN-1:0] e1, e2, x, y, yneg, res;
            logic            active;
            assign e1 = vs1[gi*ELEN +: ELEN];
            assign e2 = vs2[gi*ELEN +: ELEN];
            // minuend x, subtrahend y; y is negated (flip sign) and added.
            assign x    = op ? e2 : e1;
            assign y    = op ? e1 : e2;
            assign yneg = {~y[ELEN-1], y[ELEN-2:0]};
            hapi_fp32_add u_add (.a(x), .b(yneg), .y(res));
            assign active = mask[gi] & (VLW'(gi) < vl);
            assign vd_new[gi*ELEN +: ELEN] = active ? res : vd_old[gi*ELEN +: ELEN];
        end
    endgenerate
endmodule
