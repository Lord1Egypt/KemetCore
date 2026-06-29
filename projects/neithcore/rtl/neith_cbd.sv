// NeithCore — centered binomial distribution (CBD) noise sampler (KemetCore Phase 2 RTL)
//
// The secret/error generator of ML-KEM (golden _cbd): each coefficient draws 2*ETA
// random bits and computes out = (popcount(a_bits) - popcount(b_bits)) mod Q, giving a
// small centered value in [-ETA, ETA] reduced mod Q (Q = 7681). The 2*ETA random bits of
// element i are presented on in_data: bits [ETA-1:0] = a_bits, bits [2*ETA-1:ETA] =
// b_bits (matching the golden's draw order a-then-b). Streaming protocol mirrors the
// other NeithCore poly units: pulse `start`, drive N beats of `in_data` with `in_valid`,
// read results by `rd_addr` once `done`. Each coefficient is element-independent,
// computed combinationally and registered as it streams. Yosys must report 0 latches.
// Verified vs the golden — see tb/test_cbd.py.

module neith_cbd #(
    parameter int N   = 256,
    parameter int ETA = 2
) (
    input  logic        clk,
    input  logic        rst_n,
    input  logic        start,        // pulse 1 cycle to begin
    input  logic        in_valid,     // qualifies in_data during LOAD (N beats)
    input  logic [12:0] in_data,      // 2*ETA random bits: [ETA-1:0]=a, [2*ETA-1:ETA]=b
    input  logic [7:0]  rd_addr,      // result read address (valid in DONE)
    output logic [12:0] out_data,     // noise coefficient (mod Q), combinational
    output logic        busy,
    output logic        done
);
    localparam logic [1:0]  S_IDLE = 2'd0, S_LOAD = 2'd1, S_DONE = 2'd2;
    localparam logic [31:0] NW = N;               // 32-bit mirror of N (width-safe compare)
    localparam logic [13:0] Q  = 14'd7681;
    localparam int          PW = $clog2(ETA + 1); // popcount width

    logic [1:0]  state;
    logic [8:0]  cnt;                 // 0..N
    logic [12:0] mem [0:N-1];

    // combinational CBD of the current streamed bits: (popcount(a) - popcount(b)) mod Q
    logic [PW-1:0]      pa, pb;
    logic signed [13:0] diff;
    logic [13:0]        modval;
    logic [12:0]        res;
    always_comb begin
        pa = '0;
        pb = '0;
        for (int k = 0; k < ETA; k++) begin
            pa = pa + {{(PW-1){1'b0}}, in_data[k]};
            pb = pb + {{(PW-1){1'b0}}, in_data[ETA + k]};
        end
        diff   = $signed({{(14-PW){1'b0}}, pa}) - $signed({{(14-PW){1'b0}}, pb});
        // mod Q: diff in [-ETA, ETA], so a single +Q fixes any negative value
        modval = (diff < 0) ? (Q + diff) : {1'b0, diff[12:0]};
        res    = modval[12:0];
    end

    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            state <= S_IDLE;
            cnt   <= '0;
        end else begin
            case (state)
                S_IDLE: if (start) begin state <= S_LOAD; cnt <= '0; end
                S_LOAD: if (in_valid) begin
                    mem[cnt[7:0]] <= res;
                    if ({23'b0, cnt} == NW - 32'd1) state <= S_DONE;
                    cnt <= cnt + 1'b1;
                end
                S_DONE: if (start) begin state <= S_LOAD; cnt <= '0; end
                default: state <= S_IDLE;
            endcase
        end
    end

    assign busy     = (state == S_LOAD);
    assign done     = (state == S_DONE);
    assign out_data = mem[rd_addr];
endmodule
