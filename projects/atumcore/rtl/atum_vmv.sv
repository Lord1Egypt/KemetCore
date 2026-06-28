// AtumCore — vector move unit (KemetCore Phase 2 RTL)
//
// The fundamental data moves:
//   op=0 vmv.v.x -> broadcast (splat) the scalar x to every active lane
//   op=1 vmv.v.v -> copy the source vector vs lane-for-lane
// Active lanes are i < vl; tail lanes read 0. Mirrors golden VectorUnit.vmv_vx /
// vmv_vv exactly. Vectors are lane-packed LE (element i at [i*ELEN +: ELEN]).
// Purely combinational — Yosys must report 0 latches. Verified vs the golden —
// see tb/test_vmv.py.

module atum_vmv #(
    parameter int VLMAX = 8,
    parameter int ELEN  = 32
) (
    input  logic [VLMAX*ELEN-1:0]      vs,      // source vector (vmv.v.v)
    input  logic [ELEN-1:0]            x,       // scalar (vmv.v.x)
    input  logic                       op,      // 0 = splat scalar, 1 = copy vector
    input  logic [$clog2(VLMAX+1)-1:0] vl,
    output logic [VLMAX*ELEN-1:0]      vd
);
    always_comb begin
        logic [ELEN-1:0] e;
        for (int i = 0; i < VLMAX; i++) begin
            e = op ? vs[i*ELEN +: ELEN] : x;
            vd[i*ELEN +: ELEN] = (i < vl) ? e : '0;
        end
    end
endmodule
