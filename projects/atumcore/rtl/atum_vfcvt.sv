// AtumCore — vector int <-> fp32 convert unit (KemetCore Phase 2 RTL)
//
// RVV vfcvt: each lane converts between a 32-bit integer and fp32, selected by op:
//   0 vfcvt.f.x    int32  -> fp32   (RNE)
//   1 vfcvt.f.xu   uint32 -> fp32   (RNE)
//   2 vfcvt.x.f    fp32   -> int32  (round to nearest, ties to even)
//   3 vfcvt.xu.f   fp32   -> uint32 (RNE)
//   4 vfcvt.rtz.x.f  fp32 -> int32  (truncate toward zero)
//   5 vfcvt.rtz.xu.f fp32 -> uint32 (truncate)
//
// fp->int saturates per the RVV rules: NaN -> max representable; +Inf / overflow ->
// max; -Inf / underflow -> min (0 for unsigned); negative -> 0 for unsigned. int->fp
// rounds the magnitude RNE (a 32-bit integer always fits fp32's 8-bit exponent, so no
// overflow to Inf). Tail lanes (i >= vl) read 0. Mirrors golden VectorUnit.vfcvt /
// _i2f / _f2i exactly. Purely combinational — Yosys must report 0 latches.
// Verified vs the golden — see tb/test_vfcvt.py.

module atum_vfcvt #(
    parameter int VLMAX = 8,
    parameter int ELEN  = 32
) (
    input  logic [VLMAX*ELEN-1:0]      vs,
    input  logic [2:0]                 op,
    input  logic [$clog2(VLMAX+1)-1:0] vl,
    output logic [VLMAX*ELEN-1:0]      vd
);
    // ---- int -> fp32 (magnitude RNE) ------------------------------------ //
    function automatic logic [31:0] i2f(input logic [31:0] xin,
                                        input logic        is_signed);
        logic        sign;
        logic [31:0] mag;
        logic [5:0]  msb;
        logic [5:0]  sh;
        logic [4:0]  rpos;
        logic [31:0] fracv;
        logic [31:0] shr;
        logic [24:0] keep;            // 24-bit significand (+1 for round carry)
        logic        round_bit, sticky, roundup;
        logic [8:0]  biased;
        logic [22:0] frac;
        begin
            if (is_signed && xin[31]) begin
                sign = 1'b1;
                mag  = (~xin) + 32'd1;     // |x|; 0x80000000 -> itself = 2**31
            end else begin
                sign = 1'b0;
                mag  = xin;
            end
            if (mag == 32'd0) begin
                i2f = 32'd0;
            end else begin
                msb = 6'd0;
                for (int b = 0; b < 32; b++) if (mag[b]) msb = b[5:0];
                if (msb <= 6'd23) begin
                    fracv  = mag << (6'd23 - msb);
                    frac   = fracv[22:0];
                    biased = {3'b0, msb} + 9'd127;
                end else begin
                    sh        = msb - 6'd23;            // 1..8
                    shr       = mag >> sh;
                    keep      = {1'b0, shr[23:0]};
                    rpos      = sh[4:0] - 5'd1;
                    round_bit = mag[rpos];
                    sticky    = |(mag & ((32'd1 << rpos) - 32'd1));
                    roundup   = round_bit & (sticky | keep[0]);
                    keep      = keep + {24'd0, roundup};
                    if (keep[24]) begin                 // rounding carried out
                        frac   = 23'd0;
                        biased = {3'b0, msb} + 9'd1 + 9'd127;
                    end else begin
                        frac   = keep[22:0];
                        biased = {3'b0, msb} + 9'd127;
                    end
                end
                i2f = {sign, biased[7:0], frac};
            end
        end
    endfunction

    // ---- fp32 -> int (RNE or truncate, saturating) ---------------------- //
    function automatic logic [31:0] f2i(input logic [31:0] xin,
                                        input logic        is_signed,
                                        input logic        is_trunc);
        logic        fsign;
        logic [7:0]  fexp;
        logic [22:0] fmant;
        logic [23:0] full;
        logic signed [9:0] E, shamt, rs;
        logic [5:0]  rsx;
        logic [4:0]  rpos;
        logic [31:0] fext, posmax, negmax, fshr;
        logic [33:0] mag;
        logic [23:0] keepm;
        logic        round_bit, sticky, roundup;
        begin
            fsign = xin[31];
            fexp  = xin[30:23];
            fmant = xin[22:0];
            posmax = is_signed ? 32'h7FFFFFFF : 32'hFFFFFFFF;
            negmax = is_signed ? 32'h80000000 : 32'h00000000;
            if (fexp == 8'hFF) begin
                f2i = (fmant != 0) ? posmax : (fsign ? negmax : posmax);
            end else if (fexp == 8'd0 && fmant == 23'd0) begin
                f2i = 32'd0;
            end else begin
                if (fexp == 8'd0) begin
                    full = {1'b0, fmant};
                    E    = -10'sd126;
                end else begin
                    full = {1'b1, fmant};
                    E    = $signed({2'b00, fexp}) - 10'sd127;
                end
                // overflow region: |value| beyond the integer range -> saturate.
                if (is_signed ? (E >= 10'sd31) : (E >= 10'sd32)) begin
                    f2i = fsign ? negmax : posmax;
                end else begin
                    shamt = E - 10'sd23;       // value = full * 2**shamt
                    if (shamt >= 0) begin       // E in [23..31]: exact integer
                        mag = {10'd0, full} << shamt[5:0];
                    end else begin
                        rs        = 10'sd23 - E;             // > 0
                        rsx       = (rs > 10'sd32) ? 6'd32 : rs[5:0];
                        fext      = {8'b0, full};
                        fshr      = fext >> rsx;
                        keepm     = fshr[23:0];
                        rpos      = rsx[4:0] - 5'd1;
                        round_bit = fext[rpos];
                        sticky    = |(fext & ((32'd1 << rpos) - 32'd1));
                        roundup   = (~is_trunc) & round_bit & (sticky | keepm[0]);
                        mag       = {10'd0, keepm} + {33'd0, roundup};
                    end
                    if (is_signed) begin
                        if (!fsign)
                            f2i = (mag > 34'h7FFFFFFF) ? 32'h7FFFFFFF : mag[31:0];
                        else
                            f2i = (mag > 34'h80000000) ? 32'h80000000
                                                       : (~mag[31:0] + 32'd1);
                    end else begin
                        if (fsign)
                            f2i = 32'd0;
                        else
                            f2i = (mag > 34'hFFFFFFFF) ? 32'hFFFFFFFF : mag[31:0];
                    end
                end
            end
        end
    endfunction

    // Decode op once; each lane then needs just one i2f + one f2i datapath (the
    // two directions share the same signed/trunc controls), muxed by direction —
    // far lighter than instantiating all six conversions per lane.
    logic       sel_i2f;     // op 0/1 -> int->fp ; else fp->int
    logic       i2f_signed;  // op 0
    logic       f2i_signed;  // op 2/4
    logic       f2i_trunc;   // op 4/5
    always_comb begin
        sel_i2f    = (op == 3'd0) || (op == 3'd1);
        i2f_signed = (op == 3'd0);
        f2i_signed = (op == 3'd2) || (op == 3'd4);
        f2i_trunc  = (op == 3'd4) || (op == 3'd5);
    end

    always_comb begin
        logic [31:0] x, r;
        for (int i = 0; i < VLMAX; i++) begin
            x = vs[i*ELEN +: ELEN];
            r = sel_i2f ? i2f(x, i2f_signed) : f2i(x, f2i_signed, f2i_trunc);
            vd[i*ELEN +: ELEN] = (i < vl) ? r : 32'd0;
        end
    end
endmodule
