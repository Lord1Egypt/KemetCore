// AtumCore — vector saturating integer add/sub (KemetCore Phase 2 RTL)
//
// RVV fixed-point saturating arithmetic: VLMAX parallel 32-bit lanes computing one
// element-wise add or subtract that CLAMPS (saturates) to the destination range
// instead of wrapping, selected by op:
//   0 vsaddu : unsigned a+b, clamp high to 2^32-1
//   1 vsadd  : signed   a+b, clamp to [-2^31, 2^31-1]
//   2 vssubu : unsigned a-b, clamp low to 0
//   3 vssub  : signed   a-b, clamp to [-2^31, 2^31-1]
// Each lane carries one extra bit so the true (pre-saturation) result is exact, then
// the out-of-range cases are detected and pinned to the nearest representable value.
// Active-element semantics match atum_valu / golden _wr_int: a lane writes only when
// body-active (i < vl) AND mask-active; else the destination element is undisturbed.
// Operands cross the boundary packed little-endian by lane (element i at [i*ELEN +:
// ELEN]). Purely combinational — Yosys must report 0 latches. Verified vs the golden
// — see tb/test_vsadd.py.

module atum_vsadd #(
    parameter int VLMAX = 8,
    parameter int ELEN  = 32
) (
    input  logic [VLMAX*ELEN-1:0]      vs1,
    input  logic [VLMAX*ELEN-1:0]      vs2,
    input  logic [VLMAX*ELEN-1:0]      vd_old,
    input  logic [1:0]                 op,    // 0 saddu, 1 sadd, 2 ssubu, 3 ssub
    input  logic [VLMAX-1:0]           mask,
    input  logic [$clog2(VLMAX+1)-1:0] vl,
    output logic [VLMAX*ELEN-1:0]      vd_new
);
    localparam logic [31:0] SMAX = 32'h7FFF_FFFF;   // INT32_MAX
    localparam logic [31:0] SMIN = 32'h8000_0000;   // INT32_MIN
    localparam logic [31:0] UMAX = 32'hFFFF_FFFF;

    always_comb begin
        for (int i = 0; i < VLMAX; i++) begin
            logic [ELEN-1:0]   a, b, res;
            logic [ELEN:0]     usum, udiff;          // 33-bit unsigned
            logic signed [ELEN:0] ssum, sdiff;       // 33-bit signed
            logic              active;
            a = vs1[i*ELEN +: ELEN];
            b = vs2[i*ELEN +: ELEN];
            usum  = {1'b0, a} + {1'b0, b};
            udiff = {1'b0, a} - {1'b0, b};
            ssum  = $signed({a[ELEN-1], a}) + $signed({b[ELEN-1], b});
            sdiff = $signed({a[ELEN-1], a}) - $signed({b[ELEN-1], b});
            unique case (op)
                2'd0:    res = usum[ELEN] ? UMAX : usum[ELEN-1:0];          // vsaddu
                2'd1:    res = (ssum > $signed({1'b0, SMAX})) ? SMAX :      // vsadd
                               (ssum < $signed({1'b1, SMIN})) ? SMIN
                                                              : ssum[ELEN-1:0];
                2'd2:    res = udiff[ELEN] ? 32'd0 : udiff[ELEN-1:0];       // vssubu (borrow -> 0)
                2'd3:    res = (sdiff > $signed({1'b0, SMAX})) ? SMAX :     // vssub
                               (sdiff < $signed({1'b1, SMIN})) ? SMIN
                                                               : sdiff[ELEN-1:0];
                default: res = '0;
            endcase
            active = (i < vl) && mask[i];
            vd_new[i*ELEN +: ELEN] = active ? res : vd_old[i*ELEN +: ELEN];
        end
    end
endmodule
