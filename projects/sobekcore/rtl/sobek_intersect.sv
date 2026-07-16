// SobekCore — fp32 Moller-Trumbore ray-triangle intersector — KemetCore Phase 2 RTL
//
// 6-stage pipelined datapath:
//   Stage 0: edge       (e1 = v1-v0, e2 = v2-v0, tvec = o-v0)
//   Stage 1: pvec/det   (pvec = d x e2, det = e1 . pvec)
//   Stage 2: u-test     (inv_det = 1/det, dot_u = tvec . pvec, u = dot_u * inv_det)
//   Stage 3: qvec/v-test(qvec = tvec x e1, dot_v = d . qvec, v = dot_v * inv_det)
//   Stage 4: t-compute  (dot_t = e2 . qvec, t = dot_t * inv_det, w = 1.0 - (u+v))
//   Stage 5: range-test (Checks bounds, hit=1 if valid)
//
// Latency: 6 cycles. Througput: 1 hit test / cycle.

module sobek_intersect (
    input  logic        clk,
    input  logic        rst_n,

    // Inputs
    input  logic        valid_in,
    input  logic [31:0] o0, o1, o2,    // origin
    input  logic [31:0] d0, d1, d2,    // direction
    input  logic [31:0] v0_0, v0_1, v0_2,  // vertex 0
    input  logic [31:0] v1_0, v1_1, v1_2,  // vertex 1
    input  logic [31:0] v2_0, v2_1, v2_2,  // vertex 2

    // Outputs
    output logic        valid_out,
    output logic        hit,
    output logic [31:0] t,
    output logic [31:0] u,
    output logic [31:0] v,
    output logic [31:0] w
);

    // =========================================================================
    // Stage 0: edge (e1 = v1 - v0, e2 = v2 - v0, tvec = o - v0)
    // =========================================================================
    logic [31:0] nv0_0, nv0_1, nv0_2;
    assign nv0_0 = {~v0_0[31], v0_0[30:0]};
    assign nv0_1 = {~v0_1[31], v0_1[30:0]};
    assign nv0_2 = {~v0_2[31], v0_2[30:0]};

    logic [31:0] e1_0, e1_1, e1_2;
    hapi_fp32_add u_e1_0 (.a(v1_0), .b(nv0_0), .y(e1_0));
    hapi_fp32_add u_e1_1 (.a(v1_1), .b(nv0_1), .y(e1_1));
    hapi_fp32_add u_e1_2 (.a(v1_2), .b(nv0_2), .y(e1_2));

    logic [31:0] e2_0, e2_1, e2_2;
    hapi_fp32_add u_e2_0 (.a(v2_0), .b(nv0_0), .y(e2_0));
    hapi_fp32_add u_e2_1 (.a(v2_1), .b(nv0_1), .y(e2_1));
    hapi_fp32_add u_e2_2 (.a(v2_2), .b(nv0_2), .y(e2_2));

    logic [31:0] tvec_0, tvec_1, tvec_2;
    hapi_fp32_add u_tvec_0 (.a(o0), .b(nv0_0), .y(tvec_0));
    hapi_fp32_add u_tvec_1 (.a(o1), .b(nv0_1), .y(tvec_1));
    hapi_fp32_add u_tvec_2 (.a(o2), .b(nv0_2), .y(tvec_2));

    // Registers
    logic valid_q1;
    logic [31:0] d0_q1, d1_q1, d2_q1;
    logic [31:0] e1_0_q1, e1_1_q1, e1_2_q1;
    logic [31:0] e2_0_q1, e2_1_q1, e2_2_q1;
    logic [31:0] tvec_0_q1, tvec_1_q1, tvec_2_q1;

    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            valid_q1 <= 1'b0;
        end else begin
            valid_q1 <= valid_in;
            if (valid_in) begin
                d0_q1 <= d0; d1_q1 <= d1; d2_q1 <= d2;
                e1_0_q1 <= e1_0; e1_1_q1 <= e1_1; e1_2_q1 <= e1_2;
                e2_0_q1 <= e2_0; e2_1_q1 <= e2_1; e2_2_q1 <= e2_2;
                tvec_0_q1 <= tvec_0; tvec_1_q1 <= tvec_1; tvec_2_q1 <= tvec_2;
            end
        end
    end

    // =========================================================================
    // Stage 1: pvec/det (pvec = d x e2, det = e1 . pvec)
    // =========================================================================
    logic [31:0] pvec_0, pvec_1, pvec_2;
    sobek_cross u_pvec (
        .a0(d0_q1), .a1(d1_q1), .a2(d2_q1),
        .b0(e2_0_q1), .b1(e2_1_q1), .b2(e2_2_q1),
        .c0(pvec_0), .c1(pvec_1), .c2(pvec_2)
    );

    logic [31:0] det;
    sobek_dot3 u_det (
        .a0(e1_0_q1), .a1(e1_1_q1), .a2(e1_2_q1),
        .b0(pvec_0), .b1(pvec_1), .b2(pvec_2),
        .y(det)
    );

    // Registers
    logic valid_q2;
    logic [31:0] d0_q2, d1_q2, d2_q2;
    logic [31:0] e1_0_q2, e1_1_q2, e1_2_q2;
    logic [31:0] e2_0_q2, e2_1_q2, e2_2_q2;
    logic [31:0] tvec_0_q2, tvec_1_q2, tvec_2_q2;
    logic [31:0] pvec_0_q2, pvec_1_q2, pvec_2_q2;
    logic [31:0] det_q2;

    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            valid_q2 <= 1'b0;
        end else begin
            valid_q2 <= valid_q1;
            if (valid_q1) begin
                d0_q2 <= d0_q1; d1_q2 <= d1_q1; d2_q2 <= d2_q1;
                e1_0_q2 <= e1_0_q1; e1_1_q2 <= e1_1_q1; e1_2_q2 <= e1_2_q1;
                e2_0_q2 <= e2_0_q1; e2_1_q2 <= e2_1_q1; e2_2_q2 <= e2_2_q1;
                tvec_0_q2 <= tvec_0_q1; tvec_1_q2 <= tvec_1_q1; tvec_2_q2 <= tvec_2_q1;
                pvec_0_q2 <= pvec_0; pvec_1_q2 <= pvec_1; pvec_2_q2 <= pvec_2;
                det_q2 <= det;
            end
        end
    end

    // =========================================================================
    // Stage 2: u-test (inv_det = 1/det, dot_u = tvec . pvec, u = dot_u * inv_det)
    // =========================================================================
    logic [31:0] inv_det;
    sobek_recip u_recip (.x(det_q2), .y(inv_det));

    logic [31:0] dot_u;
    sobek_dot3 u_dot_u (
        .a0(tvec_0_q2), .a1(tvec_1_q2), .a2(tvec_2_q2),
        .b0(pvec_0_q2), .b1(pvec_1_q2), .b2(pvec_2_q2),
        .y(dot_u)
    );

    logic [31:0] u_val;
    hapi_fp32_mul u_u_val (.a(dot_u), .b(inv_det), .y(u_val));

    // Registers
    logic valid_q3;
    logic [31:0] d0_q3, d1_q3, d2_q3;
    logic [31:0] e1_0_q3, e1_1_q3, e1_2_q3;
    logic [31:0] e2_0_q3, e2_1_q3, e2_2_q3;
    logic [31:0] tvec_0_q3, tvec_1_q3, tvec_2_q3;
    logic [31:0] inv_det_q3;
    logic [31:0] det_q3;
    logic [31:0] u_q3;

    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            valid_q3 <= 1'b0;
        end else begin
            valid_q3 <= valid_q2;
            if (valid_q2) begin
                d0_q3 <= d0_q2; d1_q3 <= d1_q2; d2_q3 <= d2_q2;
                e1_0_q3 <= e1_0_q2; e1_1_q3 <= e1_1_q2; e1_2_q3 <= e1_2_q2;
                e2_0_q3 <= e2_0_q2; e2_1_q3 <= e2_1_q2; e2_2_q3 <= e2_2_q2;
                tvec_0_q3 <= tvec_0_q2; tvec_1_q3 <= tvec_1_q2; tvec_2_q3 <= tvec_2_q2;
                inv_det_q3 <= inv_det;
                det_q3 <= det_q2;
                u_q3 <= u_val;
            end
        end
    end

    // =========================================================================
    // Stage 3: qvec/v-test (qvec = tvec x e1, dot_v = d . qvec, v = dot_v * inv_det)
    // =========================================================================
    logic [31:0] qvec_0, qvec_1, qvec_2;
    sobek_cross u_qvec (
        .a0(tvec_0_q3), .a1(tvec_1_q3), .a2(tvec_2_q3),
        .b0(e1_0_q3), .b1(e1_1_q3), .b2(e1_2_q3),
        .c0(qvec_0), .c1(qvec_1), .c2(qvec_2)
    );

    logic [31:0] dot_v;
    sobek_dot3 u_dot_v (
        .a0(d0_q3), .a1(d1_q3), .a2(d2_q3),
        .b0(qvec_0), .b1(qvec_1), .b2(qvec_2),
        .y(dot_v)
    );

    logic [31:0] v_val;
    hapi_fp32_mul u_v_val (.a(dot_v), .b(inv_det_q3), .y(v_val));

    // We also need u+v for Stage 4 w computation and range check
    logic [31:0] u_plus_v;
    hapi_fp32_add u_add_uv (.a(u_q3), .b(v_val), .y(u_plus_v));

    // Registers
    logic valid_q4;
    logic [31:0] e2_0_q4, e2_1_q4, e2_2_q4;
    logic [31:0] qvec_0_q4, qvec_1_q4, qvec_2_q4;
    logic [31:0] inv_det_q4;
    logic [31:0] det_q4;
    logic [31:0] u_q4;
    logic [31:0] v_q4;
    logic [31:0] uv_q4;

    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            valid_q4 <= 1'b0;
        end else begin
            valid_q4 <= valid_q3;
            if (valid_q3) begin
                e2_0_q4 <= e2_0_q3; e2_1_q4 <= e2_1_q3; e2_2_q4 <= e2_2_q3;
                qvec_0_q4 <= qvec_0; qvec_1_q4 <= qvec_1; qvec_2_q4 <= qvec_2;
                inv_det_q4 <= inv_det_q3;
                det_q4 <= det_q3;
                u_q4 <= u_q3;
                v_q4 <= v_val;
                uv_q4 <= u_plus_v;
            end
        end
    end

    // =========================================================================
    // Stage 4: t-compute (dot_t = e2 . qvec, t = dot_t * inv_det, w = 1.0 - uv)
    // =========================================================================
    logic [31:0] dot_t;
    sobek_dot3 u_dot_t (
        .a0(e2_0_q4), .a1(e2_1_q4), .a2(e2_2_q4),
        .b0(qvec_0_q4), .b1(qvec_1_q4), .b2(qvec_2_q4),
        .y(dot_t)
    );

    logic [31:0] t_val;
    hapi_fp32_mul u_t_val (.a(dot_t), .b(inv_det_q4), .y(t_val));

    logic [31:0] w_val;
    logic [31:0] neg_uv;
    assign neg_uv = {~uv_q4[31], uv_q4[30:0]};
    hapi_fp32_add u_w_val (.a(32'h3F80_0000), .b(neg_uv), .y(w_val));

    // Registers
    logic valid_q5;
    logic [31:0] det_q5;
    logic [31:0] u_q5, v_q5, uv_q5;
    logic [31:0] t_q5, w_q5;

    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            valid_q5 <= 1'b0;
        end else begin
            valid_q5 <= valid_q4;
            if (valid_q4) begin
                det_q5 <= det_q4;
                u_q5 <= u_q4;
                v_q5 <= v_q4;
                uv_q5 <= uv_q4;
                t_q5 <= t_val;
                w_q5 <= w_val;
            end
        end
    end

    // =========================================================================
    // Stage 5: range-test
    // =========================================================================
    // Check 1: abs(det) < EPS
    // EPS = 1e-7 (0x33d6bf95)
    logic abs_det_lt_eps;
    hapi_fp32_cmp u_cmp_eps (
        .a({1'b0, det_q5[30:0]}), .b(32'h33d6_bf95),
        .op(2'b01), .y(abs_det_lt_eps)
    );

    // Check 2: u < 0.0 or u > 1.0
    logic u_lt_0;
    hapi_fp32_cmp u_cmp_u_lt0 (
        .a(u_q5), .b(32'h0000_0000),
        .op(2'b01), .y(u_lt_0)
    );
    logic u_gt_1;
    hapi_fp32_cmp u_cmp_u_gt1 (
        .a(32'h3F80_0000), .b(u_q5),
        .op(2'b01), .y(u_gt_1)
    );

    // Check 3: v < 0.0 or (u+v) > 1.0
    logic v_lt_0;
    hapi_fp32_cmp u_cmp_v_lt0 (
        .a(v_q5), .b(32'h0000_0000),
        .op(2'b01), .y(v_lt_0)
    );
    logic uv_gt_1;
    hapi_fp32_cmp u_cmp_uv_gt1 (
        .a(32'h3F80_0000), .b(uv_q5),
        .op(2'b01), .y(uv_gt_1)
    );

    // Check 4: t < EPS (where EPS = 1e-7)
    logic t_lt_eps;
    hapi_fp32_cmp u_cmp_t_lt_eps (
        .a(t_q5), .b(32'h33d6_bf95),
        .op(2'b01), .y(t_lt_eps)
    );

    // Any check failing means miss (None).
    // if u_lt_0 or u_gt_1 or v_lt_0 or uv_gt_1 or t_lt_eps or abs_det_lt_eps -> hit=0
    logic miss;
    assign miss = abs_det_lt_eps | u_lt_0 | u_gt_1 | v_lt_0 | uv_gt_1 | t_lt_eps;

    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            valid_out <= 1'b0;
            hit <= 1'b0;
            t <= 32'd0;
            u <= 32'd0;
            v <= 32'd0;
            w <= 32'd0;
        end else begin
            valid_out <= valid_q5;
            if (valid_q5) begin
                hit <= !miss;
                t <= t_q5;
                u <= u_q5;
                v <= v_q5;
                w <= w_q5;
            end
        end
    end

endmodule
