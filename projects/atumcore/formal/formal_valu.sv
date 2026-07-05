// AtumCore — FORMAL: atum_valu lane algebra with every lane active (mask all-1s,
// vl=VLMAX). Proves ADD lane-commutativity and XOR self-inverse for ALL vectors.
module formal_valu #(parameter int VLMAX=8, parameter int ELEN=32) (
    input logic [VLMAX*ELEN-1:0] x, y
);
    localparam [3:0] OP_ADD=4'd0, OP_XOR=4'd5;
    localparam [VLMAX-1:0] FULL = {VLMAX{1'b1}};
    localparam [$clog2(VLMAX+1)-1:0] VL = VLMAX[$clog2(VLMAX+1)-1:0];
    wire [VLMAX*ELEN-1:0] add_xy, add_yx, xor_xx;
    atum_valu u_axy (.vs1(x), .vs2(y), .vd_old('0), .op(OP_ADD), .mask(FULL), .vl(VL), .vd_new(add_xy));
    atum_valu u_ayx (.vs1(y), .vs2(x), .vd_old('0), .op(OP_ADD), .mask(FULL), .vl(VL), .vd_new(add_yx));
    atum_valu u_xxx (.vs1(x), .vs2(x), .vd_old('0), .op(OP_XOR), .mask(FULL), .vl(VL), .vd_new(xor_xx));
    always_comb begin
        assert (add_xy == add_yx);       // per-lane add commutes
        assert (xor_xx == '0);           // per-lane XOR self-inverse
    end
endmodule
