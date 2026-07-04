// GebCore — 2:4 structured-sparse metadata compression — KemetCore Phase 2 RTL
//
// Compress one pruned group of 4 fp32 weights into the 2 kept lanes that feed the
// sparse MAC (geb_spmac). Matches golden compress_2of4 / compress_group: order the
// four lanes as [nonzero ascending] then [zero ascending] and emit the first two
// as (value, index) pairs. A lane is "nonzero" iff its magnitude bits are set, so
// +/-0 count as zero (like np.nonzero). Purely combinational.
//
// Bit-exact vs golden geb_sparse.compress_group — see tb/test_compress.py.

module geb_compress (
    input  logic [127:0] group,      // 4 fp32 weights, lane i = group[32*i +: 32]
    output logic [31:0]  val0,
    output logic [1:0]   idx0,
    output logic [31:0]  val1,
    output logic [1:0]   idx1
);
    // lane nonzero flags (magnitude bits set -> not +/-0)
    logic [3:0] nz;
    always_comb begin
        for (int i = 0; i < 4; i++)
            nz[i] = (group[32*i +: 31] != 31'd0);   // low 31 magnitude bits of lane i
    end

    // ordered lane list: nonzero lanes ascending, then zero lanes ascending.
    logic [1:0] ord [0:3];
    always_comb begin
        int p;
        for (int i = 0; i < 4; i++) ord[i] = 2'd0;   // default so every path assigns
        p = 0;
        for (int i = 0; i < 4; i++) if (nz[i])  begin ord[p] = i[1:0]; p++; end
        for (int i = 0; i < 4; i++) if (!nz[i]) begin ord[p] = i[1:0]; p++; end
    end

    assign idx0 = ord[0];
    assign idx1 = ord[1];
    assign val0 = group[32*ord[0] +: 32];
    assign val1 = group[32*ord[1] +: 32];
endmodule
