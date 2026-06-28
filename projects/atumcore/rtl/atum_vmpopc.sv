// AtumCore — vector mask reduction unit (KemetCore Phase 2 RTL)
//
// The mask-consuming datapath of the RVV unit: reduces a mask to a SCALAR.
//   op=0 vcpop  -> population count (number of set bits among active lanes)
//   op=1 vfirst -> index of the first set bit among active lanes, or -1 if none
//
// A lane contributes only when it is body-active (i < vl) AND v0.t-active
// (vmask[i]); drive vmask all-ones for the unmasked form. This mirrors the golden
// VectorUnit.vcpop / vfirst exactly. Purely combinational — Yosys must report 0
// latches. Verified vs the golden — see tb/test_vmpopc.py.
//
// The scalar result is signed and wide enough to hold both a count (0..VLMAX) and
// the first-set index or the -1 "none" sentinel: RW = $clog2(VLMAX+1)+1 bits.

module atum_vmpopc #(
    parameter int VLMAX = 8
) (
    input  logic [VLMAX-1:0]           m,
    input  logic [VLMAX-1:0]           vmask,   // v0.t input mask (all-1 = unmasked)
    input  logic                       op,      // 0 = vcpop, 1 = vfirst
    input  logic [$clog2(VLMAX+1)-1:0] vl,
    output logic signed [$clog2(VLMAX+1):0] result
);
    localparam int RW = $clog2(VLMAX+1) + 1;

    always_comb begin
        logic signed [RW-1:0] cnt;
        logic signed [RW-1:0] firstidx;
        logic                 found;
        logic                 active;
        cnt      = '0;
        firstidx = -1;                       // "none" sentinel
        found    = 1'b0;
        for (int i = 0; i < VLMAX; i++) begin
            active = (i < vl) && vmask[i] && m[i];
            if (active) cnt = cnt + 1;
            if (active && !found) begin
                firstidx = RW'(i);
                found    = 1'b1;
            end
        end
        result = op ? firstidx : cnt;
    end
endmodule
