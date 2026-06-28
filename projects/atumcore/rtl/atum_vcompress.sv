// AtumCore — vector compress unit (KemetCore Phase 2 RTL)
//
// Stream compaction / filter: packs the source elements whose compress-mask bit is
// set (among i < vl) contiguously into the low lanes of the result, preserving
// order; the remaining high lanes read 0. The kept element from source lane i lands
// at lane viota(m)[i] — so this is the data-motion consumer of the iota prefix-sum
// (atum_viota). Used to gather the "true" elements of a predicate into a dense
// vector (e.g. after a vms* compare).
//
// Implementation: a running destination counter walks the lanes; when a lane is
// active (i < vl) and its compress bit is set, the source element is routed to the
// current destination lane (a variable LHS index that synthesises to a mux tree)
// and the counter advances. Mirrors golden VectorUnit.vcompress exactly. Purely
// combinational — Yosys must report 0 latches. Verified vs the golden — see
// tb/test_vcompress.py.

module atum_vcompress #(
    parameter int VLMAX = 8,
    parameter int ELEN  = 32
) (
    input  logic [VLMAX*ELEN-1:0]      vs,      // source vector (lane-packed LE)
    input  logic [VLMAX-1:0]           m,       // compress mask (which lanes to keep)
    input  logic [$clog2(VLMAX+1)-1:0] vl,
    output logic [VLMAX*ELEN-1:0]      vd
);
    always_comb begin
        logic [ELEN-1:0] outarr [VLMAX];
        logic [$clog2(VLMAX+1)-1:0] dst;
        dst = '0;
        for (int j = 0; j < VLMAX; j++)
            outarr[j] = '0;                       // high (unfilled) lanes read 0
        for (int i = 0; i < VLMAX; i++) begin
            if ((i < vl) && m[i]) begin
                // dst < VLMAX at every write (at most VLMAX kept) -> low bits index
                outarr[dst[$clog2(VLMAX)-1:0]] = vs[i*ELEN +: ELEN];
                dst = dst + 1'b1;
            end
        end
        for (int j = 0; j < VLMAX; j++)
            vd[j*ELEN +: ELEN] = outarr[j];
    end
endmodule
