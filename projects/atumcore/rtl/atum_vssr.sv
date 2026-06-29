// AtumCore — vector scaling shift-right with rounding (KemetCore Phase 2 RTL)
//
// RVV vssrl / vssra: VLMAX parallel lanes computing a rounding right shift — the
// classic fixed-point "scale down by 2^shamt with rounding" — selected by op:
//   0 vssrl : logical    right shift (value treated as unsigned)
//   1 vssra : arithmetic right shift (value treated as signed)
// The shift amount is the low 5 bits of vs2; the value is vs1. Rounding is
// round-to-nearest, ties up (vxrm rnu): roundoff(v, d) = (v >> d) + bit(v, d-1), i.e.
// the bit shifted past the LSB is added back. (For d = 0 the result is just v.)
// Active-element semantics match atum_valu / golden _wr_int: a lane writes only when
// body-active (i < vl) AND mask-active; else the destination element is undisturbed.
// Operands cross the boundary packed little-endian by lane (element i at [i*ELEN +:
// ELEN]). Purely combinational — Yosys must report 0 latches. Verified vs the golden
// — see tb/test_vssr.py.

module atum_vssr #(
    parameter int VLMAX = 8,
    parameter int ELEN  = 32
) (
    input  logic [VLMAX*ELEN-1:0]      vs1,
    input  logic [VLMAX*ELEN-1:0]      vs2,
    input  logic [VLMAX*ELEN-1:0]      vd_old,
    input  logic                       op,    // 0 = vssrl (logical), 1 = vssra (signed)
    input  logic [VLMAX-1:0]           mask,
    input  logic [$clog2(VLMAX+1)-1:0] vl,
    output logic [VLMAX*ELEN-1:0]      vd_new
);
    always_comb begin
        for (int i = 0; i < VLMAX; i++) begin
            logic [ELEN-1:0]      a, res, shifted, sh_log, sh_ari;
            logic signed [ELEN-1:0] as;
            logic [4:0]           sh, rpos;
            logic                 round_bit, active;
            a   = vs1[i*ELEN +: ELEN];
            as  = $signed(a);
            sh  = vs2[i*ELEN +: 5];                  // shamt = low 5 bits of vs2 element
            rpos = sh - 5'd1;
            // compute both shifts in dedicated nets so the op-mux can't coerce the
            // arithmetic (signed) shift back to logical (the classic ?: signedness trap)
            sh_log  = a  >>  sh;                       // logical
            sh_ari  = as >>> sh;                       // arithmetic
            shifted = op ? sh_ari : sh_log;
            // rnu rounding: add the bit that was shifted past the LSB (only if sh != 0)
            round_bit = (sh == 5'd0) ? 1'b0 : a[rpos];
            res = shifted + {31'd0, round_bit};
            active = (i < vl) && mask[i];
            vd_new[i*ELEN +: ELEN] = active ? res : vd_old[i*ELEN +: ELEN];
        end
    end
endmodule
