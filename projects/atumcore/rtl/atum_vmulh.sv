// AtumCore — vector multiply-high (KemetCore Phase 2 RTL)
//
// RVV vmulh / vmulhu / vmulhsu: VLMAX parallel lanes returning the HIGH 32 bits of the
// 64-bit product of two 32-bit elements — the extended-precision multiply used for
// fixed-point scaling and 64-bit-from-32-bit arithmetic. op selects the signedness:
//   0 vmulh   : signed   * signed
//   1 vmulhu  : unsigned * unsigned
//   2 vmulhsu : signed(vs1) * unsigned(vs2)
// Each lane forms the full signed/unsigned 64-bit product (operands extended to 64 bits
// with the appropriate sign/zero extension) and keeps bits [63:32]. Active-element
// semantics match atum_valu / golden _wr_int: a lane writes only when body-active
// (i < vl) AND mask-active; else the destination element is undisturbed. Operands cross
// the boundary packed little-endian by lane (element i at [i*ELEN +: ELEN]). Purely
// combinational — Yosys must report 0 latches. Verified vs the golden — see
// tb/test_vmulh.py.

module atum_vmulh #(
    parameter int VLMAX = 8,
    parameter int ELEN  = 32
) (
    input  logic [VLMAX*ELEN-1:0]      vs1,
    input  logic [VLMAX*ELEN-1:0]      vs2,
    input  logic [VLMAX*ELEN-1:0]      vd_old,
    input  logic [1:0]                 op,    // 0 vmulh, 1 vmulhu, 2 vmulhsu
    input  logic [VLMAX-1:0]           mask,
    input  logic [$clog2(VLMAX+1)-1:0] vl,
    output logic [VLMAX*ELEN-1:0]      vd_new
);
    always_comb begin
        for (int i = 0; i < VLMAX; i++) begin
            logic [ELEN-1:0]      a, b, res;
            logic        [2*ELEN-1:0] pu;             // unsigned product
            logic signed [2*ELEN-1:0] ps, pm;         // signed / signed*unsigned products
            logic                 active;
            a = vs1[i*ELEN +: ELEN];
            b = vs2[i*ELEN +: ELEN];
            pu = {{ELEN{1'b0}}, a} * {{ELEN{1'b0}}, b};                          // u*u
            ps = $signed({{ELEN{a[ELEN-1]}}, a}) * $signed({{ELEN{b[ELEN-1]}}, b});  // s*s
            pm = $signed({{ELEN{a[ELEN-1]}}, a}) * $signed({{ELEN{1'b0}}, b});   // s(a)*u(b)
            unique case (op)
                2'd0:    res = ps[2*ELEN-1:ELEN];      // vmulh
                2'd1:    res = pu[2*ELEN-1:ELEN];      // vmulhu
                2'd2:    res = pm[2*ELEN-1:ELEN];      // vmulhsu
                default: res = '0;
            endcase
            active = (i < vl) && mask[i];
            vd_new[i*ELEN +: ELEN] = active ? res : vd_old[i*ELEN +: ELEN];
        end
    end
endmodule
