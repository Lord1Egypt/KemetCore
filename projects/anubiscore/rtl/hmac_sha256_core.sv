// AnubisCore — HMAC-SHA256 core (KemetCore Phase 2 RTL)
//
// HMAC(K, m) = SHA256((K' ^ opad) || SHA256((K' ^ ipad) || m)), where K' is the
// key padded with zeros to the 64-byte block size (host pre-hashes keys > 64 B,
// the standard reduction). This core composes the verified `sha256_core`, driving
// it through four block-compressions, and constructs the ipad/opad key blocks and
// the outer second block internally.
//
// Streaming contract for the inner message (mirrors sha256_core's "host pads"
// convention): the core absorbs the ipad block itself (block 0), then requests
// the *remaining* inner blocks — i.e. SHA-256-padding of (ipad||m) minus its first
// 64 bytes — one at a time. When `need_block` is high the host presents `blk`
// with `blk_valid` (and `blk_last` on the final block). The host's padding length
// field must account for the 64-byte ipad prefix: length = (64 + len(m)) * 8.
//
// The outer hash is fully internal: block 0 = (K' ^ opad), block 1 = the 256-bit
// inner digest followed by SHA-256 padding for a 96-byte message (0x80, zeros,
// and the 64-bit length 768).
//
// Bit-exact against the Python golden (anubis_hash.hmac_sha256) and the stdlib
// hmac/hashlib — see tb/test_hmac_sha256.py.

module hmac_sha256_core (
    input  logic         clk,
    input  logic         rst_n,
    input  logic         start,       // pulse: begin HMAC, latches key
    input  logic [511:0] key,         // 64-byte key, zero-padded by host (MSB-first)
    output logic         need_block,  // high when ready for the next inner block
    input  logic [511:0] blk,         // inner message block (host SHA-padded)
    input  logic         blk_valid,   // 1: blk is presented this cycle
    input  logic         blk_last,    // 1: this is the final inner block
    output logic         busy,
    output logic         done,        // 1-cycle pulse when mac is valid
    output logic [255:0] mac          // HMAC-SHA256 digest, valid after done
);
    // ---- sha256_core instance -------------------------------------------- //
    logic         sha_start, sha_init;
    logic [511:0] sha_block;
    logic         sha_busy, sha_done;
    logic [255:0] sha_hash;

    sha256_core u_sha (
        .clk   (clk),
        .rst_n (rst_n),
        .start (sha_start),
        .init  (sha_init),
        .alg   (1'b0),          // SHA-256
        .block (sha_block),
        .busy  (sha_busy),
        .done  (sha_done),
        .hash  (sha_hash)
    );

    // ---- derived key blocks & outer second block ------------------------- //
    logic [511:0] key_r;
    logic [255:0] dig_r;        // inner digest D
    logic         last_r;

    wire [511:0] ipad_blk = key_r ^ {64{8'h36}};
    wire [511:0] opad_blk = key_r ^ {64{8'h5c}};
    // outer message = opad(64B) || D(32B) = 96 B; second block = D || pad(96B).
    // 256(D) + 8(0x80) + 184(zeros) + 64(len=768) = 512 bits.
    wire [511:0] dblock = {dig_r, 8'h80, 184'd0, 64'd768};

    typedef enum logic [2:0] {
        IDLE, S_IPAD, S_INNER_REQ, S_INNER_RUN, S_OPAD, S_DBLOCK
    } state_t;
    state_t state;

    assign need_block = (state == S_INNER_REQ);

    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            state     <= IDLE;
            busy      <= 1'b0;
            done      <= 1'b0;
            sha_start <= 1'b0;
            sha_init  <= 1'b0;
            sha_block <= 512'd0;
            key_r     <= 512'd0;
            dig_r     <= 256'd0;
            last_r    <= 1'b0;
            mac       <= 256'd0;
        end else begin
            sha_start <= 1'b0;
            done      <= 1'b0;
            case (state)
                IDLE: begin
                    busy <= 1'b0;
                    if (start) begin
                        key_r     <= key;
                        sha_block <= key ^ {64{8'h36}};   // ipad block (key just latched)
                        sha_init  <= 1'b1;
                        sha_start <= 1'b1;
                        busy      <= 1'b1;
                        state     <= S_IPAD;
                    end
                end
                S_IPAD: begin
                    if (sha_done) state <= S_INNER_REQ;
                end
                S_INNER_REQ: begin
                    if (blk_valid) begin
                        sha_block <= blk;
                        sha_init  <= 1'b0;       // chain from ipad state
                        sha_start <= 1'b1;
                        last_r    <= blk_last;
                        state     <= S_INNER_RUN;
                    end
                end
                S_INNER_RUN: begin
                    if (sha_done) begin
                        if (last_r) begin
                            dig_r     <= sha_hash;          // capture inner digest D
                            sha_block <= opad_blk;
                            sha_init  <= 1'b1;              // fresh IV for outer
                            sha_start <= 1'b1;
                            state     <= S_OPAD;
                        end else begin
                            state <= S_INNER_REQ;
                        end
                    end
                end
                S_OPAD: begin
                    if (sha_done) begin
                        sha_block <= dblock;               // D || pad
                        sha_init  <= 1'b0;                 // chain from opad state
                        sha_start <= 1'b1;
                        state     <= S_DBLOCK;
                    end
                end
                S_DBLOCK: begin
                    if (sha_done) begin
                        mac   <= sha_hash;
                        done  <= 1'b1;
                        busy  <= 1'b0;
                        state <= IDLE;
                    end
                end
                default: state <= IDLE;
            endcase
        end
    end
endmodule
