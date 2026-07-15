// GebCore — 2:4 structured-sparsity pruner (KemetCore Phase 2 RTL)
//
// The compression front-end for 2:4 sparsity: from a group of four fp32 weights
// it keeps the two with the largest magnitude and emits the keep-mask plus the two
// kept (value, lane-index) pairs in ascending lane order — exactly the metadata the
// verified geb_spmac consumes.
//
// Magnitude is compared on the sign-cleared IEEE bits as an unsigned integer
// (key = w[30:0]); for non-NaN operands this is the true |.| order, and because
// both the RTL and the golden use the identical integer compare + lower-lane
// tie-break, the selection is deterministic for ANY bit pattern. Each lane's rank
// = how many other lanes "beat" it (greater key, or equal key at a lower index);
// the two lanes with rank < 2 are kept, so exactly two survive.
//
// Verified against the Python reference prune_group — see tb/test_prune.py.
// Combinational only.

module geb_prune (
    input  logic [31:0] w0,
    input  logic [31:0] w1,
    input  logic [31:0] w2,
    input  logic [31:0] w3,
    output logic [3:0]  keep_mask,   // bit i set => lane i kept (exactly 2 set)
    output logic [31:0] val0,        // first kept value (lower lane index)
    output logic [1:0]  idx0,
    output logic [31:0] val1,        // second kept value
    output logic [1:0]  idx1
);
    logic [31:0] w   [0:3];
    logic [30:0] key [0:3];
    assign w[0] = w0; assign w[1] = w1; assign w[2] = w2; assign w[3] = w3;

    always_comb begin
        for (int i = 0; i < 4; i++) key[i] = w[i][30:0];
    end

    // beats(j,i): lane j outranks lane i (greater magnitude, or equal with j<i)
    function automatic logic beats(input int j, input int i);
        beats = (key[j] > key[i]) || (key[j] == key[i] && j < i);
    endfunction

    logic [2:0] rank [0:3];
    logic       keep [0:3];
    always_comb begin
        for (int i = 0; i < 4; i++) begin
            rank[i] = 3'd0;
            for (int j = 0; j < 4; j++)
                if (j != i && beats(j, i)) rank[i] = rank[i] + 3'd1;
            keep[i] = (rank[i] < 3'd2);
        end
    end

    always_comb begin
        keep_mask = {keep[3], keep[2], keep[1], keep[0]};
        // collect kept lanes in ascending index order
        val0 = 32'd0; idx0 = 2'd0;
        val1 = 32'd0; idx1 = 2'd0;
        begin
            logic got0;
            got0 = 1'b0;
            for (int i = 0; i < 4; i++) begin
                if (keep[i]) begin
                    if (!got0) begin
                        val0 = w[i]; idx0 = i[1:0]; got0 = 1'b1;
                    end else begin
                        val1 = w[i]; idx1 = i[1:0];
                    end
                end
            end
        end
    end

`ifdef FORMAL
    // Formal properties for 2:4 structured-sparsity invariant
    always_comb begin
        // 1. Exactly 2 kept
        assert ((keep_mask[0] + keep_mask[1] + keep_mask[2] + keep_mask[3]) == 3'd2);

        // 2. The kept values exactly match the selected weights and indices
        if (keep_mask[0] && keep_mask[1]) begin
            assert (val0 == w[0] && idx0 == 2'd0);
            assert (val1 == w[1] && idx1 == 2'd1);
        end else if (keep_mask[0] && keep_mask[2]) begin
            assert (val0 == w[0] && idx0 == 2'd0);
            assert (val1 == w[2] && idx1 == 2'd2);
        end else if (keep_mask[0] && keep_mask[3]) begin
            assert (val0 == w[0] && idx0 == 2'd0);
            assert (val1 == w[3] && idx1 == 2'd3);
        end else if (keep_mask[1] && keep_mask[2]) begin
            assert (val0 == w[1] && idx0 == 2'd1);
            assert (val1 == w[2] && idx1 == 2'd2);
        end else if (keep_mask[1] && keep_mask[3]) begin
            assert (val0 == w[1] && idx0 == 2'd1);
            assert (val1 == w[3] && idx1 == 2'd3);
        end else if (keep_mask[2] && keep_mask[3]) begin
            assert (val0 == w[2] && idx0 == 2'd2);
            assert (val1 == w[3] && idx1 == 2'd3);
        end

        // 3. A kept lane's magnitude must be >= a dropped lane's magnitude (or equal with lower index)
        for (int i = 0; i < 4; i++) begin
            for (int j = 0; j < 4; j++) begin
                if (keep_mask[i] && !keep_mask[j]) begin
                    assert(beats(i, j));
                end
            end
        end
    end
`endif
endmodule
