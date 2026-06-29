// AtumCore — scalar <-> vector element-0 move unit (KemetCore Phase 2 RTL)
//
// The two halves of RVV's scalar/vector bridge (also covers the fp aliases vfmv.f.s /
// vfmv.s.f, which are bit-identical moves):
//   * EXTRACT (vmv.x.s / vfmv.f.s): scalar_out = element 0 of the source vector. RVV
//     reads element 0 regardless of vl.
//   * INSERT  (vmv.s.x / vfmv.s.f): vec_out = vd_old with element 0 replaced by
//     scalar_in, but ONLY when vl > 0; otherwise the destination is left unchanged.
//     Elements 1..VLMAX-1 are always the (undisturbed) tail.
// These pair with the reductions (atum_vredu / vfredu / vredminmax / vfredminmax) to
// move a scalar reduction result into/out of element 0. Purely combinational — Yosys
// must report 0 latches. Verified vs the golden — see tb/test_vmvsx.py.

module atum_vmvsx #(
    parameter int VLMAX = 8,
    parameter int ELEN  = 32
) (
    input  logic [VLMAX*ELEN-1:0]      vs,        // source vector (for extract)
    input  logic [ELEN-1:0]            scalar_in, // scalar to insert
    input  logic [VLMAX*ELEN-1:0]      vd_old,    // prior destination (for insert tail)
    input  logic [$clog2(VLMAX+1)-1:0] vl,
    output logic [ELEN-1:0]            scalar_out,// element 0 of vs
    output logic [VLMAX*ELEN-1:0]      vec_out    // vd_old with elem0 <- scalar_in if vl>0
);
    assign scalar_out = vs[0 +: ELEN];

    genvar gi;
    generate
        for (gi = 0; gi < VLMAX; gi++) begin : lane
            if (gi == 0) begin : e0
                assign vec_out[0 +: ELEN] = (vl != 0) ? scalar_in : vd_old[0 +: ELEN];
            end else begin : tail
                assign vec_out[gi*ELEN +: ELEN] = vd_old[gi*ELEN +: ELEN];
            end
        end
    endgenerate
endmodule
