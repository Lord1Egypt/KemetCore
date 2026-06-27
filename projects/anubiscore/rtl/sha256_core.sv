// AnubisCore — SHA-256 core (KemetCore Phase 2 RTL)
//
// Multicycle implementation: one round per cycle, 64 rounds per 512-bit block.
// The message schedule uses a 16-word sliding window so only 16 words are stored.
// `init` selects the IV (first block) vs. continuing the running hash (chaining),
// so multi-block messages are driven by streaming padded 512-bit blocks.
//
// Bit-exact against the Python golden (projects/anubiscore/golden/anubis_hash.py)
// and hashlib — see tb/test_sha256.py.

module sha256_core (
    input  logic         clk,
    input  logic         rst_n,
    input  logic         start,     // pulse 1 cycle to begin a block
    input  logic         init,      // 1: start from IV, 0: continue chaining
    input  logic [511:0] block,     // padded 512-bit message block (W0 = MSBs)
    output logic         busy,
    output logic         done,      // 1-cycle pulse when block is absorbed
    output logic [255:0] hash       // {H0,H1,...,H7}, valid after done
);
    // ---- pure functions -------------------------------------------------- //
    function automatic logic [31:0] rotr(input logic [31:0] x, input int n);
        rotr = (x >> n) | (x << (32 - n));
    endfunction
    function automatic logic [31:0] ssig0(input logic [31:0] x);
        ssig0 = rotr(x, 7) ^ rotr(x, 18) ^ (x >> 3);
    endfunction
    function automatic logic [31:0] ssig1(input logic [31:0] x);
        ssig1 = rotr(x, 17) ^ rotr(x, 19) ^ (x >> 10);
    endfunction
    function automatic logic [31:0] bsig0(input logic [31:0] x);
        bsig0 = rotr(x, 2) ^ rotr(x, 13) ^ rotr(x, 22);
    endfunction
    function automatic logic [31:0] bsig1(input logic [31:0] x);
        bsig1 = rotr(x, 6) ^ rotr(x, 11) ^ rotr(x, 25);
    endfunction

    function automatic logic [31:0] kconst(input logic [5:0] t);
        case (t)
            6'd0:  kconst=32'h428a2f98; 6'd1:  kconst=32'h71374491;
            6'd2:  kconst=32'hb5c0fbcf; 6'd3:  kconst=32'he9b5dba5;
            6'd4:  kconst=32'h3956c25b; 6'd5:  kconst=32'h59f111f1;
            6'd6:  kconst=32'h923f82a4; 6'd7:  kconst=32'hab1c5ed5;
            6'd8:  kconst=32'hd807aa98; 6'd9:  kconst=32'h12835b01;
            6'd10: kconst=32'h243185be; 6'd11: kconst=32'h550c7dc3;
            6'd12: kconst=32'h72be5d74; 6'd13: kconst=32'h80deb1fe;
            6'd14: kconst=32'h9bdc06a7; 6'd15: kconst=32'hc19bf174;
            6'd16: kconst=32'he49b69c1; 6'd17: kconst=32'hefbe4786;
            6'd18: kconst=32'h0fc19dc6; 6'd19: kconst=32'h240ca1cc;
            6'd20: kconst=32'h2de92c6f; 6'd21: kconst=32'h4a7484aa;
            6'd22: kconst=32'h5cb0a9dc; 6'd23: kconst=32'h76f988da;
            6'd24: kconst=32'h983e5152; 6'd25: kconst=32'ha831c66d;
            6'd26: kconst=32'hb00327c8; 6'd27: kconst=32'hbf597fc7;
            6'd28: kconst=32'hc6e00bf3; 6'd29: kconst=32'hd5a79147;
            6'd30: kconst=32'h06ca6351; 6'd31: kconst=32'h14292967;
            6'd32: kconst=32'h27b70a85; 6'd33: kconst=32'h2e1b2138;
            6'd34: kconst=32'h4d2c6dfc; 6'd35: kconst=32'h53380d13;
            6'd36: kconst=32'h650a7354; 6'd37: kconst=32'h766a0abb;
            6'd38: kconst=32'h81c2c92e; 6'd39: kconst=32'h92722c85;
            6'd40: kconst=32'ha2bfe8a1; 6'd41: kconst=32'ha81a664b;
            6'd42: kconst=32'hc24b8b70; 6'd43: kconst=32'hc76c51a3;
            6'd44: kconst=32'hd192e819; 6'd45: kconst=32'hd6990624;
            6'd46: kconst=32'hf40e3585; 6'd47: kconst=32'h106aa070;
            6'd48: kconst=32'h19a4c116; 6'd49: kconst=32'h1e376c08;
            6'd50: kconst=32'h2748774c; 6'd51: kconst=32'h34b0bcb5;
            6'd52: kconst=32'h391c0cb3; 6'd53: kconst=32'h4ed8aa4a;
            6'd54: kconst=32'h5b9cca4f; 6'd55: kconst=32'h682e6ff3;
            6'd56: kconst=32'h748f82ee; 6'd57: kconst=32'h78a5636f;
            6'd58: kconst=32'h84c87814; 6'd59: kconst=32'h8cc70208;
            6'd60: kconst=32'h90befffa; 6'd61: kconst=32'ha4506ceb;
            6'd62: kconst=32'hbef9a3f7; 6'd63: kconst=32'hc67178f2;
        endcase
    endfunction

    // initial hash value (IV)
    function automatic logic [31:0] iv(input logic [2:0] i);
        case (i)
            3'd0: iv=32'h6a09e667; 3'd1: iv=32'hbb67ae85;
            3'd2: iv=32'h3c6ef372; 3'd3: iv=32'ha54ff53a;
            3'd4: iv=32'h510e527f; 3'd5: iv=32'h9b05688c;
            3'd6: iv=32'h1f83d9ab; 3'd7: iv=32'h5be0cd19;
        endcase
    endfunction

    // ---- state ----------------------------------------------------------- //
    typedef enum logic [1:0] {IDLE, RUN, FIN} state_t;
    state_t state;

    logic [31:0] H [0:7];                 // running/chaining hash (pre-block value)
    logic [31:0] a,b,c,d,e,f,g,h;         // working variables
    logic [31:0] w [0:15];                // sliding message-schedule window
    logic [5:0]  rc;                       // round counter 0..63

    // combinational round terms
    logic [31:0] t1, t2, wnext;
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
            rc    <= 6'd0;
            for (i = 0; i < 8; i = i + 1) H[i] <= iv(i[2:0]);
        end else begin
            done <= 1'b0;
            case (state)
                IDLE: begin
                    busy <= 1'b0;
                    if (start) begin
                        // load message schedule (W0 = most-significant 32 bits)
                        for (i = 0; i < 16; i = i + 1)
                            w[i] <= block[(15 - i) * 32 +: 32];
                        // base hash for this block
                        if (init) for (i = 0; i < 8; i = i + 1) H[i] <= iv(i[2:0]);
                        a <= init ? iv(3'd0) : H[0];
                        b <= init ? iv(3'd1) : H[1];
                        c <= init ? iv(3'd2) : H[2];
                        d <= init ? iv(3'd3) : H[3];
                        e <= init ? iv(3'd4) : H[4];
                        f <= init ? iv(3'd5) : H[5];
                        g <= init ? iv(3'd6) : H[6];
                        h <= init ? iv(3'd7) : H[7];
                        rc    <= 6'd0;
                        busy  <= 1'b1;
                        state <= RUN;
                    end
                end
                RUN: begin
                    // one compression round
                    h <= g; g <= f; f <= e; e <= d + t1;
                    d <= c; c <= b; b <= a; a <= t1 + t2;
                    // advance the sliding window
                    for (i = 0; i < 15; i = i + 1) w[i] <= w[i + 1];
                    w[15] <= wnext;
                    if (rc == 6'd63) state <= FIN;
                    else rc <= rc + 6'd1;
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
