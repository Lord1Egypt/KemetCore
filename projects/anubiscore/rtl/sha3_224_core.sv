// AnubisCore — SHA3-224 core (Keccak-f[1600]) — KemetCore Phase 2 RTL
//
// Identical Keccak-f[1600] permutation to sha3_256_core, but a 1152-bit rate
// block (18 lanes; capacity 448) and a 224-bit digest. The 224-bit output spans
// the first 3 full state lanes plus the low 32 bits of lane 3 (all < the 18-lane
// rate), so a single squeeze suffices — hash = {lane3[31:0],lane2,lane1,lane0}.
//
// Multicycle: absorb one 1152-bit rate block, run the 24-round permutation
// (1 round/cycle), repeat per padded block. `init` clears the 1600-bit state for
// the first block; subsequent blocks chain.
//
// State layout: s[5*y + x] holds Keccak lane (x,y). Each rate-block lane i is
// presented pre-packed little-endian by the host at block[64*i +: 64].
//
// Bit-exact against the Python golden + hashlib.sha3_224 — see tb/test_sha3_224.py.

module sha3_224_core (
    input  logic         clk,
    input  logic         rst_n,
    input  logic         start,
    input  logic         init,        // 1: clear state (first block), 0: chain
    input  logic [1151:0] block,      // 18 rate lanes, each pre-packed little-endian
    output logic         busy,
    output logic         done,
    output logic [223:0] hash         // {lane3[31:0],lane2,lane1,lane0}, valid after done
);
    localparam int RATE_LANES = 18;     // 1152 bits / 64

    function automatic logic [63:0] rotl(input logic [63:0] x, input int n);
        rotl = (x << n) | (x >> (64 - n));
    endfunction

    // rho rotation offsets, indexed by (5*x + y); case form is Yosys-friendly
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

    logic [63:0] s   [0:24];
    logic [63:0] nxt [0:24];
    logic [4:0]  round;
    integer i;

    // one Keccak-f round, combinational (module-level arrays keep it Yosys-safe)
    logic [63:0] c  [0:4];
    logic [63:0] d  [0:4];
    logic [63:0] a1 [0:24];
    logic [63:0] bb [0:24];
    always_comb begin
        integer x, y;
        // theta
        for (x = 0; x < 5; x++)
            c[x] = s[x] ^ s[x+5] ^ s[x+10] ^ s[x+15] ^ s[x+20];
        for (x = 0; x < 5; x++)
            d[x] = c[(x+4)%5] ^ rotl(c[(x+1)%5], 1);
        for (y = 0; y < 5; y++)
            for (x = 0; x < 5; x++)
                a1[5*y+x] = s[5*y+x] ^ d[x];
        // rho + pi
        for (y = 0; y < 5; y++)
            for (x = 0; x < 5; x++)
                bb[5*((2*x+3*y)%5) + y] = rotl(a1[5*y+x], off(x, y));
        // chi
        for (y = 0; y < 5; y++)
            for (x = 0; x < 5; x++)
                nxt[5*y+x] = bb[5*y+x] ^ ((~bb[5*y+((x+1)%5)]) & bb[5*y+((x+2)%5)]);
        // iota (rc() takes an int arg; pass round directly for older-Yosys portability)
        nxt[0] = nxt[0] ^ rc(round);
    end

    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            state <= IDLE;
            busy  <= 1'b0;
            done  <= 1'b0;
            round <= 5'd0;
            for (i = 0; i < 25; i++) s[i] <= 64'd0;
        end else begin
            done <= 1'b0;
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
                        round <= 5'd0;
                        busy  <= 1'b1;
                        state <= PERM;
                    end
                end
                PERM: begin
                    for (i = 0; i < 25; i++) s[i] <= nxt[i];
                    if (round == 5'd23) state <= FIN;
                    else round <= round + 5'd1;
                end
                FIN: begin
                    done  <= 1'b1;
                    busy  <= 1'b0;
                    state <= IDLE;
                end
                default: state <= IDLE;
            endcase
        end
    end

    assign hash = {s[3][31:0], s[2], s[1], s[0]};
endmodule
