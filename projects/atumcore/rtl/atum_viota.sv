// AtumCore — vector iota / index unit (KemetCore Phase 2 RTL)
//
// Produces an index vector from a mask — the bridge between masks and data motion:
//   op=0 viota -> exclusive prefix-sum of the source mask (element i = number of
//                 set source-mask bits strictly before i; a masked-off source bit
//                 contributes 0). This is exactly the destination index each kept
//                 element gets in a vector-compress.
//   op=1 vid   -> element index (vd[i] = i).
//
// Both write only active lanes (i < vl AND v0.t-active vmask[i]); inactive/tail
// lanes read 0, mirroring the golden VectorUnit.viota / vid exactly. Vectors cross
// the boundary packed little-endian by lane (element i at bits [i*ELEN +: ELEN]).
// Purely combinational — Yosys must report 0 latches. Verified vs the golden — see
// tb/test_viota.py.

module atum_viota #(
    parameter int VLMAX = 8,
    parameter int ELEN  = 32
) (
    input  logic [VLMAX-1:0]           m,       // source mask (viota only)
    input  logic [VLMAX-1:0]           vmask,   // v0.t input mask (all-1 = unmasked)
    input  logic                       op,      // 0 = viota, 1 = vid
    input  logic [$clog2(VLMAX+1)-1:0] vl,
    output logic [VLMAX*ELEN-1:0]      vd
);
    always_comb begin
        logic [ELEN-1:0] cnt;
        logic            active;
        cnt = '0;
        for (int i = 0; i < VLMAX; i++) begin
            active = (i < vl) && vmask[i];
            // viota writes the running prefix count; vid writes the lane index
            vd[i*ELEN +: ELEN] = active ? (op ? ELEN'(i) : cnt) : '0;
            // only viota advances the prefix sum, and only on an active set bit
            if (!op && active && m[i])
                cnt = cnt + 1'b1;
        end
    end
endmodule
