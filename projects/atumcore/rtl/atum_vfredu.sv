// AtumCore — fp32 vector sum reduction unit (KemetCore Phase 2 RTL)
//
// Horizontal fp32 sum over the active elements of one vector (vfredosum / vfredusum):
// the result scalar = (+0.0) + vs[0] + vs[1] + ... accumulated LEFT-TO-RIGHT through a
// chain of VLMAX bit-exact HapiCore adders (hapi_fp32_add). A lane participates only
// when body-active (i < vl) AND mask-active; inactive lanes add +0.0, which is an exact
// IEEE no-op, so the ordered (vfredosum) and unordered (vfredusum) results are identical
// here and bit-exact with the golden's sequential np.float32 accumulation. The scalar is
// written to element 0 of the destination by the caller. Purely combinational — Yosys
// must report 0 latches. Verified vs the golden — see tb/test_vfredu.py.

module atum_vfredu #(
    parameter int VLMAX = 8,
    parameter int ELEN  = 32
) (
    input  logic [VLMAX*ELEN-1:0]      vs,
    input  logic [VLMAX-1:0]           mask,
    input  logic [$clog2(VLMAX+1)-1:0] vl,
    output logic [ELEN-1:0]            result
);
    localparam int VLW = $clog2(VLMAX+1);

    // acc[0] = +0.0 seed; acc[i+1] = acc[i] + (active ? lane[i] : +0.0)
    logic [ELEN-1:0] acc [VLMAX+1];
    assign acc[0] = '0;                                    // +0.0
    genvar gi;
    generate
        for (gi = 0; gi < VLMAX; gi++) begin : chain
            logic [ELEN-1:0] lane, addend;
            logic            active;
            assign lane   = vs[gi*ELEN +: ELEN];
            assign active = mask[gi] & (VLW'(gi) < vl);
            assign addend = active ? lane : '0;            // +0.0 = identity
            hapi_fp32_add u_add (.a(acc[gi]), .b(addend), .y(acc[gi+1]));
        end
    endgenerate
    assign result = acc[VLMAX];
endmodule
