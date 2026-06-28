// AtumCore — vector execute unit (KemetCore Phase 2 RTL)
//
// Integrates the three AtumCore datapaths behind one decoded operation, the way
// seth_core integrates the SethCore blocks:
//   vclass 0 (ALU) -> atum_valu  : integer element ops incl vmacc (subop = valu op)
//   vclass 1 (FP)  -> atum_vfpu  : fp32 vfadd/vfmul          (subop[0] = fop)
//   vclass 2 (RED) -> atum_vredu : vredsum/vredmax over vs1  (subop[0] = redop)
//
// The result is always a vector vd_new. For a reduction the scalar lands in element
// 0 and the remaining elements keep vd_old (the usual RVV "scalar into vd[0]"
// convention), so the unit has a single uniform vector output. Purely combinational
// — Yosys must report 0 latches. Verified vs the golden — see tb/test_vexec.py.

module atum_vexec #(
    parameter int VLMAX = 8,
    parameter int ELEN  = 32
) (
    input  logic [VLMAX*ELEN-1:0]      vs1,
    input  logic [VLMAX*ELEN-1:0]      vs2,
    input  logic [VLMAX*ELEN-1:0]      vd_old,
    input  logic [1:0]                 vclass,  // 0=ALU, 1=FP, 2=RED
    input  logic [3:0]                 subop,   // ALU op / {3'b0,fop} / {3'b0,redop}
    input  logic [VLMAX-1:0]           mask,
    input  logic [$clog2(VLMAX+1)-1:0] vl,
    output logic [VLMAX*ELEN-1:0]      vd_new
);
    logic [VLMAX*ELEN-1:0] alu_vd, fp_vd, red_vd;
    logic [ELEN-1:0]       red_scalar;

    atum_valu  #(.VLMAX(VLMAX), .ELEN(ELEN)) u_valu (
        .vs1(vs1), .vs2(vs2), .vd_old(vd_old), .op(subop),
        .mask(mask), .vl(vl), .vd_new(alu_vd));

    atum_vfpu  #(.VLMAX(VLMAX), .ELEN(ELEN)) u_vfpu (
        .vs1(vs1), .vs2(vs2), .vd_old(vd_old), .fop(subop[0]),
        .mask(mask), .vl(vl), .vd_new(fp_vd));

    atum_vredu #(.VLMAX(VLMAX), .ELEN(ELEN)) u_vredu (
        .vs(vs1), .mask(mask), .vl(vl), .redop(subop[0]), .result(red_scalar));

    // reduction scalar -> element 0; elements 1..VLMAX-1 keep vd_old
    assign red_vd = {vd_old[VLMAX*ELEN-1:ELEN], red_scalar};

    always_comb begin
        unique case (vclass)
            2'd0:    vd_new = alu_vd;
            2'd1:    vd_new = fp_vd;
            2'd2:    vd_new = red_vd;
            default: vd_new = vd_old;
        endcase
    end
endmodule
