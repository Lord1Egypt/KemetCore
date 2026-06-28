// AtumCore — vector reduction unit (KemetCore Phase 2 RTL)
//
// Horizontal reductions over the active elements of one vector: vredsum (32-bit
// wrapping sum) and vredmax. A lane participates only when body-active (i < vl) AND
// mask-active; inactive lanes contribute the reduction identity (0). The result is a
// scalar written to element 0 of the destination.
//
// NOTE (matches the golden, not the RVV ISA): the golden VectorUnit widens uint32
// lanes to int64 before max(), so every value is non-negative — i.e. vredmax is an
// UNSIGNED maximum with identity 0, and 0 from inactive lanes never beats a real
// active lane. vredsum widens the same way then keeps the low 32 bits. We mirror the
// golden bit-for-bit. Purely combinational — Yosys must report 0 latches.
// Verified vs the golden — see tb/test_vredu.py.

module atum_vredu #(
    parameter int VLMAX = 8,
    parameter int ELEN  = 32
) (
    input  logic [VLMAX*ELEN-1:0]      vs,
    input  logic [VLMAX-1:0]           mask,
    input  logic [$clog2(VLMAX+1)-1:0] vl,
    input  logic                       redop,   // 0 = vredsum, 1 = vredmax
    output logic [ELEN-1:0]            result
);
    localparam int VLW = $clog2(VLMAX+1);
    localparam int SW  = ELEN + $clog2(VLMAX);   // sum width: VLMAX lanes, no overflow

    always_comb begin
        logic [SW-1:0]   sum;
        logic [ELEN-1:0] mx, v;
        logic            active;
        sum = '0;
        mx  = '0;                                 // identity for an unsigned max
        for (int i = 0; i < VLMAX; i++) begin
            active = mask[i] & (VLW'(i) < vl);
            v = active ? vs[i*ELEN +: ELEN] : '0;
            sum = sum + {{(SW-ELEN){1'b0}}, v};
            if (v > mx) mx = v;                   // unsigned compare
        end
        result = redop ? mx : sum[ELEN-1:0];
    end
endmodule
