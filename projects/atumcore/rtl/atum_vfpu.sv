// AtumCore — fp32 vector lane array (KemetCore Phase 2 RTL)
//
// The floating-point datapath of the RVV unit: VLMAX parallel fp32 lanes evaluating
// one element-wise op (vd = vs1 OP vs2, OP in {vfadd, vfmul}) per combinational
// pass, composing the bit-exact HapiCore fp32 cores (hapi_fp32_add / hapi_fp32_mul).
// Active-element semantics match atum_valu / golden VectorUnit._wr_f32: a lane writes
// only when body-active (i < vl) AND mask-active; otherwise the destination element
// is undisturbed. fp32 elements cross the port boundary as raw bit patterns, packed
// little-endian by lane: element i at bits [i*32 +: 32].
//
// fop: 0 = vfadd, 1 = vfmul. Purely combinational — Yosys must report 0 latches.
// Verified vs the golden — see tb/test_vfpu.py.

module atum_vfpu #(
    parameter int VLMAX = 8,
    parameter int ELEN  = 32
) (
    input  logic [VLMAX*ELEN-1:0]      vs1,
    input  logic [VLMAX*ELEN-1:0]      vs2,
    input  logic [VLMAX*ELEN-1:0]      vd_old,
    input  logic                       fop,    // 0 = vfadd, 1 = vfmul
    input  logic [VLMAX-1:0]           mask,
    input  logic [$clog2(VLMAX+1)-1:0] vl,
    output logic [VLMAX*ELEN-1:0]      vd_new
);
    localparam int VLW = $clog2(VLMAX+1);
    genvar gi;
    generate
        for (gi = 0; gi < VLMAX; gi++) begin : lane
            logic [ELEN-1:0] mul_y, add_y, res;
            logic            active;
            hapi_fp32_mul u_mul (.a(vs1[gi*ELEN +: ELEN]), .b(vs2[gi*ELEN +: ELEN]), .y(mul_y));
            hapi_fp32_add u_add (.a(vs1[gi*ELEN +: ELEN]), .b(vs2[gi*ELEN +: ELEN]), .y(add_y));
            assign res    = fop ? mul_y : add_y;
            assign active = mask[gi] & (VLW'(gi) < vl);
            assign vd_new[gi*ELEN +: ELEN] = active ? res : vd_old[gi*ELEN +: ELEN];
        end
    endgenerate
endmodule
