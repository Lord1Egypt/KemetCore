// AnubisCore — SHA3-256 core P4 Top Wrapper
// Registered boundaries for ASAP7 Phase 4 P&R

module sha3_256_core_p4top (
    input  logic          clk,
    input  logic          rst_n,
    input  logic          start,
    input  logic          init,
    input  logic [1087:0] block,
    output logic          busy,
    output logic          done,
    output logic [255:0]  hash
);
    // Registered inputs
    logic          start_q;
    logic          init_q;
    logic [1087:0] block_q;

    // Registered outputs
    logic          busy_d;
    logic          done_d;
    logic [255:0]  hash_d;

    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            start_q <= 1'b0;
            init_q  <= 1'b0;
            block_q <= 1088'd0;
            busy    <= 1'b0;
            done    <= 1'b0;
            hash    <= 256'd0;
        end else begin
            start_q <= start;
            init_q  <= init;
            block_q <= block;
            busy    <= busy_d;
            done    <= done_d;
            hash    <= hash_d;
        end
    end

    sha3_256_core u_core (
        .clk   (clk),
        .rst_n (rst_n),
        .start (start_q),
        .init  (init_q),
        .block (block_q),
        .busy  (busy_d),
        .done  (done_d),
        .hash  (hash_d)
    );

endmodule
