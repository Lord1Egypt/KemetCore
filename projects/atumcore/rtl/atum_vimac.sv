// AtumCore — vector integer multiply-add family (KemetCore Phase 2 RTL)
//
// The integer fused multiply-add variants of RVV, completing the family begun by
// atum_valu's vmacc. VLMAX parallel lanes, each a 32-bit multiply + add/sub (low 32
// bits kept — modular 2^32, no saturation), selected by op:
//   0 vmacc  : vd = vd_old + vs1*vs2
//   1 vnmsac : vd = vd_old - vs1*vs2
//   2 vmadd  : vd = vs1*vd_old + vs2     (vd is the multiplicand)
//   3 vnmsub : vd = vs2 - vs1*vd_old
// vmacc/vnmsac multiply the two sources and accumulate into vd; vmadd/vnmsub multiply
// a source by the destination and add the other source. Active-element semantics match
// atum_valu / golden _wr_int: a lane writes only when body-active (i < vl) AND
// mask-active; else the destination element is undisturbed. Operands cross the boundary
// packed little-endian by lane (element i at [i*ELEN +: ELEN]). Purely combinational —
// Yosys must report 0 latches. Verified vs the golden — see tb/test_vimac.py.

module atum_vimac #(
    parameter int VLMAX = 8,
    parameter int ELEN  = 32
) (
    input  logic [VLMAX*ELEN-1:0]      vs1,
    input  logic [VLMAX*ELEN-1:0]      vs2,
    input  logic [VLMAX*ELEN-1:0]      vd_old,
    input  logic [1:0]                 op,    // 0 macc, 1 nmsac, 2 madd, 3 nmsub
    input  logic [VLMAX-1:0]           mask,
    input  logic [$clog2(VLMAX+1)-1:0] vl,
    output logic [VLMAX*ELEN-1:0]      vd_new
);
    always_comb begin
        for (int i = 0; i < VLMAX; i++) begin
            logic [ELEN-1:0] s1, s2, d, prod, addend, res;
            logic            active;
            s1 = vs1[i*ELEN +: ELEN];
            s2 = vs2[i*ELEN +: ELEN];
            d  = vd_old[i*ELEN +: ELEN];
            // vmacc/vnmsac multiply the two sources; vmadd/vnmsub multiply source by vd.
            prod   = op[1] ? (s1 * d) : (s1 * s2);     // low 32 bits (modular)
            // the non-product addend: vd for macc/nmsac, vs2 for madd/nmsub
            addend = op[1] ? s2 : d;
            // op[0] selects subtract-of-product (nmsac/nmsub) vs add (macc/madd)
            res    = op[0] ? (addend - prod) : (addend + prod);
            active = (i < vl) && mask[i];
            vd_new[i*ELEN +: ELEN] = active ? res : d;
        end
    end
endmodule
