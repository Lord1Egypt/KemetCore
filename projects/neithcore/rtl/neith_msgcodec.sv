// NeithCore — ML-KEM message codec (KemetCore Phase 2 RTL)
//
// The message <-> polynomial boundary of the KEM (golden _encode / _decode):
//   mode = 0 ENCODE : out = in[0] ? floor(Q/2) : 0           (1 message bit -> coeff)
//   mode = 1 DECODE : out = (Q/4 < in < 3Q/4) ? 1 : 0        (coeff -> 1 message bit)
// With Q = 7681: floor(Q/2)=3840, Q/4=1920, 3Q/4=5760; decode keeps the bit in out[0]
// (out[12:1]=0). Coefficients are assumed already reduced (< Q) so c % Q == c. Streaming
// protocol mirrors neith_pointwise / neith_polyaddsub: pulse `start` (latches mode),
// drive N beats of `in_data` with `in_valid`, read results by `rd_addr` once `done`.
// Each element is independent and computed combinationally, then registered as it
// streams. Yosys must report 0 latches. Verified vs the golden — see tb/test_msgcodec.py.

module neith_msgcodec #(
    parameter int N = 256
) (
    input  logic        clk,
    input  logic        rst_n,
    input  logic        start,        // pulse 1 cycle to begin (latches mode)
    input  logic        mode,         // 0 = encode (bit->coeff), 1 = decode (coeff->bit)
    input  logic        in_valid,     // qualifies in_data during LOAD (N beats)
    input  logic [12:0] in_data,      // encode: message bit in [0]; decode: coeff < Q
    input  logic [7:0]  rd_addr,      // result read address (valid in DONE)
    output logic [12:0] out_data,     // result[rd_addr] (combinational)
    output logic        busy,
    output logic        done
);
    localparam logic [1:0]  S_IDLE = 2'd0, S_LOAD = 2'd1, S_DONE = 2'd2;
    localparam logic [31:0] NW  = N;              // 32-bit mirror of N (width-safe compare)
    localparam logic [12:0] Q2  = 13'd3840;       // floor(Q/2)
    localparam logic [12:0] Q4  = 13'd1920;       // floor(Q/4)
    localparam logic [12:0] Q34 = 13'd5760;       // floor(3Q/4)

    logic [1:0]  state;
    logic        mode_reg;
    logic [8:0]  cnt;                 // 0..N
    logic [12:0] mem [0:N-1];

    // combinational element codec for the current streamed beat
    logic        dec_bit;
    logic [12:0] res;
    assign dec_bit = (in_data > Q4) && (in_data < Q34);     // strict both sides
    assign res     = mode_reg ? {12'b0, dec_bit}            // decode -> bit in out[0]
                              : (in_data[0] ? Q2 : 13'd0);   // encode -> coeff

    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            state    <= S_IDLE;
            cnt      <= '0;
            mode_reg <= 1'b0;
        end else begin
            case (state)
                S_IDLE: if (start) begin state <= S_LOAD; cnt <= '0; mode_reg <= mode; end
                S_LOAD: if (in_valid) begin
                    mem[cnt[7:0]] <= res;
                    if ({23'b0, cnt} == NW - 32'd1) state <= S_DONE;
                    cnt <= cnt + 1'b1;
                end
                S_DONE: if (start) begin state <= S_LOAD; cnt <= '0; mode_reg <= mode; end
                default: state <= S_IDLE;
            endcase
        end
    end

    assign busy     = (state == S_LOAD);
    assign done     = (state == S_DONE);
    assign out_data = mem[rd_addr];
endmodule
