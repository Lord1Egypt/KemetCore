// AnubisCore — SHA-512 / SHA-384 core (KemetCore Phase 2 RTL)
//
// Multicycle implementation mirroring sha256_core, widened to the SHA-512 parameters:
// 64-bit words, 80 rounds per 1024-bit block, output 512-bit digest. The message
// schedule uses a 16-word sliding window so only 16 words are stored. `init` selects
// the IV (first block) vs. continuing the running hash (chaining), so multi-block
// messages are driven by streaming padded 1024-bit blocks. `alg` selects SHA-512 (0)
// or SHA-384 (1): identical compression, different IV; the SHA-384 digest is the top
// 384 bits of `hash` (hash[511:128]).
//
// The 80 K and the two 8-word IV sets are the standard FIPS 180-4 values (cube/square
// roots of the first primes), generated exactly. Bit-exact against hashlib.sha512 /
// hashlib.sha384 — see tb/test_sha512.py.

module sha512_core (
    input  logic          clk,
    input  logic          rst_n,
    input  logic          start,     // pulse 1 cycle to begin a block
    input  logic          init,      // 1: start from IV, 0: continue chaining
    input  logic          alg,       // 0: SHA-512, 1: SHA-384 (digest = hash[511:128])
    input  logic [1023:0] block,     // padded 1024-bit message block (W0 = MSBs)
    output logic          busy,
    output logic          done,      // 1-cycle pulse when block is absorbed
    output logic [511:0]  hash       // {H0,H1,...,H7}, valid after done
);
    // ---- pure functions -------------------------------------------------- //
    function automatic logic [63:0] rotr(input logic [63:0] x, input int n);
        rotr = (x >> n) | (x << (64 - n));
    endfunction
    function automatic logic [63:0] ssig0(input logic [63:0] x);
        ssig0 = rotr(x, 1) ^ rotr(x, 8) ^ (x >> 7);
    endfunction
    function automatic logic [63:0] ssig1(input logic [63:0] x);
        ssig1 = rotr(x, 19) ^ rotr(x, 61) ^ (x >> 6);
    endfunction
    function automatic logic [63:0] bsig0(input logic [63:0] x);
        bsig0 = rotr(x, 28) ^ rotr(x, 34) ^ rotr(x, 39);
    endfunction
    function automatic logic [63:0] bsig1(input logic [63:0] x);
        bsig1 = rotr(x, 14) ^ rotr(x, 18) ^ rotr(x, 41);
    endfunction

    function automatic logic [63:0] kconst(input logic [6:0] t);
        case (t)
            7'd0: kconst=64'h428a2f98d728ae22; 7'd1: kconst=64'h7137449123ef65cd;
            7'd2: kconst=64'hb5c0fbcfec4d3b2f; 7'd3: kconst=64'he9b5dba58189dbbc;
            7'd4: kconst=64'h3956c25bf348b538; 7'd5: kconst=64'h59f111f1b605d019;
            7'd6: kconst=64'h923f82a4af194f9b; 7'd7: kconst=64'hab1c5ed5da6d8118;
            7'd8: kconst=64'hd807aa98a3030242; 7'd9: kconst=64'h12835b0145706fbe;
            7'd10: kconst=64'h243185be4ee4b28c; 7'd11: kconst=64'h550c7dc3d5ffb4e2;
            7'd12: kconst=64'h72be5d74f27b896f; 7'd13: kconst=64'h80deb1fe3b1696b1;
            7'd14: kconst=64'h9bdc06a725c71235; 7'd15: kconst=64'hc19bf174cf692694;
            7'd16: kconst=64'he49b69c19ef14ad2; 7'd17: kconst=64'hefbe4786384f25e3;
            7'd18: kconst=64'h0fc19dc68b8cd5b5; 7'd19: kconst=64'h240ca1cc77ac9c65;
            7'd20: kconst=64'h2de92c6f592b0275; 7'd21: kconst=64'h4a7484aa6ea6e483;
            7'd22: kconst=64'h5cb0a9dcbd41fbd4; 7'd23: kconst=64'h76f988da831153b5;
            7'd24: kconst=64'h983e5152ee66dfab; 7'd25: kconst=64'ha831c66d2db43210;
            7'd26: kconst=64'hb00327c898fb213f; 7'd27: kconst=64'hbf597fc7beef0ee4;
            7'd28: kconst=64'hc6e00bf33da88fc2; 7'd29: kconst=64'hd5a79147930aa725;
            7'd30: kconst=64'h06ca6351e003826f; 7'd31: kconst=64'h142929670a0e6e70;
            7'd32: kconst=64'h27b70a8546d22ffc; 7'd33: kconst=64'h2e1b21385c26c926;
            7'd34: kconst=64'h4d2c6dfc5ac42aed; 7'd35: kconst=64'h53380d139d95b3df;
            7'd36: kconst=64'h650a73548baf63de; 7'd37: kconst=64'h766a0abb3c77b2a8;
            7'd38: kconst=64'h81c2c92e47edaee6; 7'd39: kconst=64'h92722c851482353b;
            7'd40: kconst=64'ha2bfe8a14cf10364; 7'd41: kconst=64'ha81a664bbc423001;
            7'd42: kconst=64'hc24b8b70d0f89791; 7'd43: kconst=64'hc76c51a30654be30;
            7'd44: kconst=64'hd192e819d6ef5218; 7'd45: kconst=64'hd69906245565a910;
            7'd46: kconst=64'hf40e35855771202a; 7'd47: kconst=64'h106aa07032bbd1b8;
            7'd48: kconst=64'h19a4c116b8d2d0c8; 7'd49: kconst=64'h1e376c085141ab53;
            7'd50: kconst=64'h2748774cdf8eeb99; 7'd51: kconst=64'h34b0bcb5e19b48a8;
            7'd52: kconst=64'h391c0cb3c5c95a63; 7'd53: kconst=64'h4ed8aa4ae3418acb;
            7'd54: kconst=64'h5b9cca4f7763e373; 7'd55: kconst=64'h682e6ff3d6b2b8a3;
            7'd56: kconst=64'h748f82ee5defb2fc; 7'd57: kconst=64'h78a5636f43172f60;
            7'd58: kconst=64'h84c87814a1f0ab72; 7'd59: kconst=64'h8cc702081a6439ec;
            7'd60: kconst=64'h90befffa23631e28; 7'd61: kconst=64'ha4506cebde82bde9;
            7'd62: kconst=64'hbef9a3f7b2c67915; 7'd63: kconst=64'hc67178f2e372532b;
            7'd64: kconst=64'hca273eceea26619c; 7'd65: kconst=64'hd186b8c721c0c207;
            7'd66: kconst=64'heada7dd6cde0eb1e; 7'd67: kconst=64'hf57d4f7fee6ed178;
            7'd68: kconst=64'h06f067aa72176fba; 7'd69: kconst=64'h0a637dc5a2c898a6;
            7'd70: kconst=64'h113f9804bef90dae; 7'd71: kconst=64'h1b710b35131c471b;
            7'd72: kconst=64'h28db77f523047d84; 7'd73: kconst=64'h32caab7b40c72493;
            7'd74: kconst=64'h3c9ebe0a15c9bebc; 7'd75: kconst=64'h431d67c49c100d4c;
            7'd76: kconst=64'h4cc5d4becb3e42b6; 7'd77: kconst=64'h597f299cfc657e2a;
            7'd78: kconst=64'h5fcb6fab3ad6faec; 7'd79: kconst=64'h6c44198c4a475817;
            default: kconst = 64'h0;
        endcase
    endfunction

    // alg = 0 -> SHA-512 IV, alg = 1 -> SHA-384 IV (same compression, different IV +
    // truncated digest). Both are the standard FIPS 180-4 constants.
    function automatic logic [63:0] iv(input logic a, input logic [2:0] i);
        if (a) begin
            case (i)                         // SHA-384
                3'd0: iv=64'hcbbb9d5dc1059ed8;
                3'd1: iv=64'h629a292a367cd507;
                3'd2: iv=64'h9159015a3070dd17;
                3'd3: iv=64'h152fecd8f70e5939;
                3'd4: iv=64'h67332667ffc00b31;
                3'd5: iv=64'h8eb44a8768581511;
                3'd6: iv=64'hdb0c2e0d64f98fa7;
                3'd7: iv=64'h47b5481dbefa4fa4;
                default: iv = 64'h0;
            endcase
        end else begin
            case (i)                         // SHA-512
                3'd0: iv=64'h6a09e667f3bcc908;
                3'd1: iv=64'hbb67ae8584caa73b;
                3'd2: iv=64'h3c6ef372fe94f82b;
                3'd3: iv=64'ha54ff53a5f1d36f1;
                3'd4: iv=64'h510e527fade682d1;
                3'd5: iv=64'h9b05688c2b3e6c1f;
                3'd6: iv=64'h1f83d9abfb41bd6b;
                3'd7: iv=64'h5be0cd19137e2179;
                default: iv = 64'h0;
            endcase
        end
    endfunction

    typedef enum logic [1:0] {IDLE, RUN, FIN} state_t;
    state_t state;

    logic [63:0] H [0:7];                  // running/chaining hash (pre-block value)
    logic [63:0] a,b,c,d,e,f,g,h;          // working variables
    logic [63:0] w [0:15];                 // sliding message-schedule window
    logic [6:0]  rc;                       // round counter 0..79

    // combinational round terms
    logic [63:0] t1, t2, wnext;
    always_comb begin
        t1    = h + bsig1(e) + ((e & f) ^ (~e & g)) + kconst(rc) + w[0];
        t2    = bsig0(a) + ((a & b) ^ (a & c) ^ (b & c));
        wnext = ssig1(w[14]) + w[9] + ssig0(w[1]) + w[0];
    end

    integer i;
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            state <= IDLE;
            busy  <= 1'b0;
            done  <= 1'b0;
            rc    <= 7'd0;
            // reset value is a constant (async reset requires it); H is reloaded from
            // the alg-selected IV on the first `init` block before it is ever used.
            for (i = 0; i < 8; i = i + 1) H[i] <= iv(1'b0, i[2:0]);
        end else begin
            done <= 1'b0;
            case (state)
                IDLE: begin
                    busy <= 1'b0;
                    if (start) begin
                        for (i = 0; i < 16; i = i + 1)
                            w[i] <= block[(15 - i) * 64 +: 64];
                        if (init) for (i = 0; i < 8; i = i + 1) H[i] <= iv(alg, i[2:0]);
                        a <= init ? iv(alg, 3'd0) : H[0];
                        b <= init ? iv(alg, 3'd1) : H[1];
                        c <= init ? iv(alg, 3'd2) : H[2];
                        d <= init ? iv(alg, 3'd3) : H[3];
                        e <= init ? iv(alg, 3'd4) : H[4];
                        f <= init ? iv(alg, 3'd5) : H[5];
                        g <= init ? iv(alg, 3'd6) : H[6];
                        h <= init ? iv(alg, 3'd7) : H[7];
                        rc    <= 7'd0;
                        busy  <= 1'b1;
                        state <= RUN;
                    end
                end
                RUN: begin
                    h <= g; g <= f; f <= e; e <= d + t1;
                    d <= c; c <= b; b <= a; a <= t1 + t2;
                    for (i = 0; i < 15; i = i + 1) w[i] <= w[i + 1];
                    w[15] <= wnext;
                    if (rc == 7'd79) state <= FIN;
                    else rc <= rc + 7'd1;
                end
                FIN: begin
                    H[0] <= H[0] + a; H[1] <= H[1] + b;
                    H[2] <= H[2] + c; H[3] <= H[3] + d;
                    H[4] <= H[4] + e; H[5] <= H[5] + f;
                    H[6] <= H[6] + g; H[7] <= H[7] + h;
                    done  <= 1'b1;
                    busy  <= 1'b0;
                    state <= IDLE;
                end
                default: state <= IDLE;
            endcase
        end
    end

    assign hash = {H[0], H[1], H[2], H[3], H[4], H[5], H[6], H[7]};
endmodule
