// NeithCore — full negacyclic polynomial multiply (KemetCore Phase 2 RTL)
//
// The capstone that ties the NTT primitives together: computes c = a * b in the
// negacyclic ring Z_Q[x]/(x^N + 1) (Q = 7681, N = 256) entirely in hardware, i.e.
// c = intt( pointwise( ntt(a), ntt(b) ) ) == golden.poly_mul_ntt(a, b). One shared
// neith_ntt engine (negacyclic, fwd & inv) and one neith_pointwise are sequenced by a
// master FSM through four compute phases:
//   FWDA : A = ntt(a)         INV  : c = intt(C)
//   FWDB : B = ntt(b)         PW   : C = A .* B  (mod Q)
//
// Streaming I/O mirrors the leaf units: pulse `start`, drive N beats of (a_in, b_in)
// with `in_valid` (LOAD), then read the product by `rd_addr` once `done`. Internally
// each phase pulses its sub-engine's start, streams N coefficients from a buffer,
// waits for the sub-engine `done`, then reads N results back into the next buffer.
// Yosys must report 0 latches. Verified vs the golden — see tb/test_polymul.py.

module neith_polymul #(
    parameter int N = 256
) (
    input  logic        clk,
    input  logic        rst_n,
    input  logic        start,        // pulse 1 cycle to begin (then stream a/b)
    input  logic        in_valid,     // qualifies a_in/b_in during external LOAD (N beats)
    input  logic [12:0] a_in,
    input  logic [12:0] b_in,
    input  logic [7:0]  rd_addr,      // product read address (valid in DONE)
    output logic [12:0] out_data,     // c[rd_addr] (combinational)
    output logic        busy,
    output logic        done
);
    localparam logic [31:0] NW = N;

    // master phases
    localparam logic [2:0] P_IDLE = 3'd0, P_LOAD = 3'd1, P_FWDA = 3'd2,
                           P_FWDB = 3'd3, P_PW = 3'd4, P_INV = 3'd5, P_DONE = 3'd6;
    // compute-phase sub-states
    localparam logic [2:0] SP_START = 3'd0, SP_STREAM = 3'd1, SP_WAIT = 3'd2,
                           SP_READ = 3'd3, SP_NEXT = 3'd4;

    logic [2:0]  phase, sub;
    logic [8:0]  cnt;                 // stream/read counter 0..N
    logic [12:0] bufA [0:N-1];
    logic [12:0] bufB [0:N-1];
    logic [12:0] bufC [0:N-1];        // pointwise result
    logic [12:0] bufR [0:N-1];        // final product

    // ---- sub-engines --------------------------------------------------------- //
    logic        ntt_start, ntt_mode, ntt_in_valid, ntt_done;
    logic [12:0] ntt_in_data, ntt_out;
    logic [7:0]  ntt_rd_addr;
    logic        pw_start, pw_in_valid, pw_done;
    logic [12:0] pw_a_in, pw_b_in, pw_out;
    logic [7:0]  pw_rd_addr;

    neith_ntt u_ntt (    // neith_ntt is fixed at 256 points (N must be 256)
        .clk(clk), .rst_n(rst_n), .start(ntt_start), .mode(ntt_mode), .nega(1'b1),
        .in_valid(ntt_in_valid), .in_data(ntt_in_data), .rd_addr(ntt_rd_addr),
        .out_data(ntt_out), .busy(), .done(ntt_done)
    );
    neith_pointwise #(.N(N)) u_pw (
        .clk(clk), .rst_n(rst_n), .start(pw_start), .in_valid(pw_in_valid),
        .a_in(pw_a_in), .b_in(pw_b_in), .rd_addr(pw_rd_addr),
        .out_data(pw_out), .busy(), .done(pw_done)
    );

    // which sub-engine the current phase uses (PW uses pointwise, others use ntt)
    wire use_pw  = (phase == P_PW);
    wire eng_done = use_pw ? pw_done : ntt_done;
    wire [12:0] eng_out = use_pw ? pw_out : ntt_out;

    // source coefficient streamed at index cnt (combinational read of the source buffer)
    logic [12:0] src_a, src_b;
    always_comb begin
        src_a = bufA[cnt[7:0]];
        src_b = bufB[cnt[7:0]];
        unique case (phase)
            P_FWDA:  src_a = bufA[cnt[7:0]];
            P_FWDB:  src_a = bufB[cnt[7:0]];
            P_INV:   src_a = bufC[cnt[7:0]];
            default: src_a = bufA[cnt[7:0]];
        endcase
    end

    // ---- sub-engine drive (combinational from phase/sub) --------------------- //
    always_comb begin
        ntt_start    = 1'b0;
        ntt_mode     = 1'b0;
        ntt_in_valid = 1'b0;
        ntt_in_data  = '0;
        ntt_rd_addr  = cnt[7:0];
        pw_start     = 1'b0;
        pw_in_valid  = 1'b0;
        pw_a_in      = src_a;
        pw_b_in      = src_b;
        pw_rd_addr   = cnt[7:0];
        if (phase == P_FWDA || phase == P_FWDB || phase == P_INV) begin
            ntt_mode     = (phase == P_INV);                 // 1 = inverse on INV
            ntt_start    = (sub == SP_START);
            ntt_in_valid = (sub == SP_STREAM);
            ntt_in_data  = src_a;
        end else if (phase == P_PW) begin
            pw_start    = (sub == SP_START);
            pw_in_valid = (sub == SP_STREAM);
        end
    end

    // ---- master FSM ---------------------------------------------------------- //
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            phase <= P_IDLE;
            sub   <= SP_START;
            cnt   <= '0;
        end else begin
            case (phase)
                P_IDLE: if (start) begin phase <= P_LOAD; cnt <= '0; end
                P_LOAD: if (in_valid) begin
                    bufA[cnt[7:0]] <= a_in;
                    bufB[cnt[7:0]] <= b_in;
                    if ({23'b0, cnt} == NW - 32'd1) begin phase <= P_FWDA; sub <= SP_START; cnt <= '0; end
                    else cnt <= cnt + 1'b1;
                end
                // the four compute phases share the same sub-FSM
                P_FWDA, P_FWDB, P_PW, P_INV: begin
                    case (sub)
                        SP_START: begin sub <= SP_STREAM; cnt <= '0; end
                        SP_STREAM: begin
                            if ({23'b0, cnt} == NW - 32'd1) begin sub <= SP_WAIT; end
                            cnt <= cnt + 1'b1;
                        end
                        SP_WAIT: if (eng_done) begin sub <= SP_READ; cnt <= '0; end
                        SP_READ: begin
                            // capture eng_out[cnt] into the destination buffer
                            case (phase)
                                P_FWDA: bufA[cnt[7:0]] <= eng_out;
                                P_FWDB: bufB[cnt[7:0]] <= eng_out;
                                P_PW:   bufC[cnt[7:0]] <= eng_out;
                                default:bufR[cnt[7:0]] <= eng_out;   // P_INV
                            endcase
                            if ({23'b0, cnt} == NW - 32'd1) sub <= SP_NEXT;
                            cnt <= cnt + 1'b1;
                        end
                        default: begin                                // SP_NEXT
                            sub <= SP_START;
                            cnt <= '0;
                            case (phase)
                                P_FWDA: phase <= P_FWDB;
                                P_FWDB: phase <= P_PW;
                                P_PW:   phase <= P_INV;
                                default:phase <= P_DONE;              // P_INV
                            endcase
                        end
                    endcase
                end
                P_DONE: if (start) begin phase <= P_LOAD; cnt <= '0; end
                default: phase <= P_IDLE;
            endcase
        end
    end

    assign busy     = (phase != P_IDLE) && (phase != P_DONE);
    assign done     = (phase == P_DONE);
    assign out_data = bufR[rd_addr];
endmodule
