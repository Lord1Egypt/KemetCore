// AnubisCore — SHAKE128 XOF core (Keccak-f[1600]) — KemetCore Phase 2 RTL
//
// The extendable-output function built on the same Keccak-f[1600] permutation as
// the SHA-3 cores, with SHAKE128's 1344-bit rate (21 lanes; capacity 256) and a
// genuine two-phase sponge:
//   ABSORB  — the host streams padded 1344-bit rate blocks (domain pad 0x1F is the
//             host's job, as for the SHA-3 cores). `init` clears the state on the
//             first block; subsequent blocks chain. Each block runs one 24-round
//             permutation and pulses `absorb_done`.
//   SQUEEZE — after the final absorb, the first 1344 bits of state (out_block) are
//             the first output block. Pulsing `squeeze` runs ONE more permutation
//             and presents the next 1344 bits (`squeeze_done`); repeat for as many
//             output bytes as needed. This is the XOF squeeze across permutations.
//
// out_block always reflects {lane20..lane0} of the current state, so the host reads
// the rate after absorb_done (block 0) and after each squeeze_done (blocks 1..).
//
// Bit-exact vs hashlib.shake_128 — see tb/test_shake128.py.

module shake128_xof_core (
    input  logic          clk,
    input  logic          rst_n,
    input  logic          start,        // begin absorbing `block`
    input  logic          init,         // 1: clear state (first block), 0: chain
    input  logic [1343:0] block,        // 21 rate lanes, pre-packed little-endian
    input  logic          squeeze,      // pulse: run one permutation, emit next block
    output logic          busy,
    output logic          absorb_done,  // 1-cycle pulse when a block is absorbed
    output logic          squeeze_done, // 1-cycle pulse after a squeeze permutation
    output logic [1343:0] out_block     // {lane20..lane0} of the current state
);
    localparam int RATE_LANES = 21;     // 1344 bits / 64

    function automatic logic [63:0] rotl(input logic [63:0] x, input int n);
        rotl = (x << n) | (x >> (64 - n));
    endfunction

    function automatic int off(input int x, input int y);
        case (5*x + y)
            0: off=0;   1: off=36;  2: off=3;   3: off=41;  4: off=18;
            5: off=1;   6: off=44;  7: off=10;  8: off=45;  9: off=2;
            10: off=62; 11: off=6;  12: off=43; 13: off=15; 14: off=61;
            15: off=28; 16: off=55; 17: off=25; 18: off=21; 19: off=56;
            20: off=27; 21: off=20; 22: off=39; 23: off=8;  24: off=14;
            default: off=0;
        endcase
    endfunction

    function automatic logic [63:0] rc(input logic [4:0] r);
        case (r)
            0:  rc=64'h0000000000000001; 1:  rc=64'h0000000000008082;
            2:  rc=64'h800000000000808A; 3:  rc=64'h8000000080008000;
            4:  rc=64'h000000000000808B; 5:  rc=64'h0000000080000001;
            6:  rc=64'h8000000080008081; 7:  rc=64'h8000000000008009;
            8:  rc=64'h000000000000008A; 9:  rc=64'h0000000000000088;
            10: rc=64'h0000000080008009; 11: rc=64'h000000008000000A;
            12: rc=64'h000000008000808B; 13: rc=64'h800000000000008B;
            14: rc=64'h8000000000008089; 15: rc=64'h8000000000008003;
            16: rc=64'h8000000000008002; 17: rc=64'h8000000000000080;
            18: rc=64'h000000000000800A; 19: rc=64'h800000008000000A;
            20: rc=64'h8000000080008081; 21: rc=64'h8000000000008080;
            22: rc=64'h0000000080000001; 23: rc=64'h8000000080008008;
            default: rc=64'h0;
        endcase
    endfunction

    typedef enum logic [1:0] {IDLE, PERM, FIN} state_t;
    state_t state;
    logic   op_sq;                       // 0: absorb, 1: squeeze (latched)

    logic [63:0] s   [0:24];
    logic [63:0] nxt [0:24];
    logic [4:0]  round;
    integer i;

    logic [63:0] c  [0:4];
    logic [63:0] d  [0:4];
    logic [63:0] a1 [0:24];
    logic [63:0] bb [0:24];
    always_comb begin
        integer x, y;
        for (x = 0; x < 5; x++)
            c[x] = s[x] ^ s[x+5] ^ s[x+10] ^ s[x+15] ^ s[x+20];
        for (x = 0; x < 5; x++)
            d[x] = c[(x+4)%5] ^ rotl(c[(x+1)%5], 1);
        for (y = 0; y < 5; y++)
            for (x = 0; x < 5; x++)
                a1[5*y+x] = s[5*y+x] ^ d[x];
        for (y = 0; y < 5; y++)
            for (x = 0; x < 5; x++)
                bb[5*((2*x+3*y)%5) + y] = rotl(a1[5*y+x], off(x, y));
        for (y = 0; y < 5; y++)
            for (x = 0; x < 5; x++)
                nxt[5*y+x] = bb[5*y+x] ^ ((~bb[5*y+((x+1)%5)]) & bb[5*y+((x+2)%5)]);
        nxt[0] = nxt[0] ^ rc(round);
    end

    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            state        <= IDLE;
            busy         <= 1'b0;
            absorb_done  <= 1'b0;
            squeeze_done <= 1'b0;
            round        <= 5'd0;
            op_sq        <= 1'b0;
            for (i = 0; i < 25; i++) s[i] <= 64'd0;
        end else begin
            absorb_done  <= 1'b0;
            squeeze_done <= 1'b0;
            case (state)
                IDLE: begin
                    busy <= 1'b0;
                    if (start) begin
                        for (i = 0; i < 25; i++) begin
                            logic [63:0] base;
                            base = init ? 64'd0 : s[i];
                            if (i < RATE_LANES) s[i] <= base ^ block[64*i +: 64];
                            else                s[i] <= base;
                        end
                        round <= 5'd0; busy <= 1'b1; op_sq <= 1'b0; state <= PERM;
                    end else if (squeeze) begin
                        round <= 5'd0; busy <= 1'b1; op_sq <= 1'b1; state <= PERM;
                    end
                end
                PERM: begin
                    for (i = 0; i < 25; i++) s[i] <= nxt[i];
                    if (round == 5'd23) state <= FIN;
                    else round <= round + 5'd1;
                end
                FIN: begin
                    absorb_done  <= ~op_sq;
                    squeeze_done <=  op_sq;
                    busy <= 1'b0;
                    state <= IDLE;
                end
                default: state <= IDLE;
            endcase
        end
    end

    genvar gl;
    generate
        for (gl = 0; gl < RATE_LANES; gl = gl + 1) begin : out_lane
            assign out_block[64*gl +: 64] = s[gl];
        end
    endgenerate
endmodule
