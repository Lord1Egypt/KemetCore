module atum_vredu_p4top (
    input  logic         clk,
    input  logic [255:0] vs,      // 8 * 32 = 256
    input  logic [7:0]   mask,
    input  logic [3:0]   vl,
    input  logic [2:0]   redop,
    output logic [31:0]  result
);

    logic [255:0] vs_q;
    logic [7:0]   mask_q;
    logic [3:0]   vl_q;
    logic [2:0]   redop_q;

    logic [31:0]  result_d;
    logic [31:0]  result_q;

    always_ff @(posedge clk) begin
        vs_q    <= vs;
        mask_q  <= mask;
        vl_q    <= vl;
        redop_q <= redop;
        result_q <= result_d;
    end

    atum_vredu u_core (
        .vs(vs_q),
        .mask(mask_q),
        .vl(vl_q),
        .redop(redop_q),
        .result(result_d)
    );

    assign result = result_q;

endmodule
