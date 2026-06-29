// AtumCore — fp32 vector square-root lane array (KemetCore Phase 2 RTL)
//
// Unary fp op (vd = sqrt(vs2)): VLMAX parallel fp32 lanes composing the bit-exact,
// correctly-rounded HapiCore square root (hapi_fp32_sqrt). Active-element semantics
// match golden VectorUnit._wr_f32: a lane writes only when body-active (i < vl) AND
// mask-active; else the destination element is undisturbed. fp32 elements cross the
// port boundary as raw bit patterns packed little-endian by lane (element i at
// [i*32 +: 32]). Purely combinational — Yosys must report 0 latches.
// Verified vs the golden — see tb/test_vfsqrt.py.

module atum_vfsqrt #(
    parameter int VLMAX = 8,
    parameter int ELEN  = 32
) (
    input  logic [VLMAX*ELEN-1:0]      vs2,   // source operand (RVV unary vd = f(vs2))
    input  logic [VLMAX*ELEN-1:0]      vd_old,
    input  logic [VLMAX-1:0]           mask,
    input  logic [$clog2(VLMAX+1)-1:0] vl,
    output logic [VLMAX*ELEN-1:0]      vd_new
);
    localparam int VLW = $clog2(VLMAX+1);
    genvar gi;
    generate
        for (gi = 0; gi < VLMAX; gi++) begin : lane
            logic [ELEN-1:0] e, res;
            logic            active;
            assign e = vs2[gi*ELEN +: ELEN];
            hapi_fp32_sqrt u_sqrt (.x(e), .y(res));
            assign active = mask[gi] & (VLW'(gi) < vl);
            assign vd_new[gi*ELEN +: ELEN] = active ? res : vd_old[gi*ELEN +: ELEN];
        end
    endgenerate
endmodule
