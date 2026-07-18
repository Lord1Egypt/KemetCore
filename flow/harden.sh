#!/usr/bin/env bash
# KemetCore — drive an ASAP7 harden (synth->floorplan->place->CTS->route->GDS)
# through the OpenROAD-flow-scripts container. Usage: flow/harden.sh bast_mac
set -euo pipefail
DESIGN="${1:-bast_mac}"
REPO="$(cd "$(dirname "$0")/.." && pwd)"
IMAGE="${ORFS_IMAGE:-openroad/orfs@sha256:86dfae2d567b8570d71fa49f24ea420a2e79d9645673ba41fd70c5a63510e4aa}"
CFG="/work/flow/designs/asap7/${DESIGN}/config.mk"
MAKE_ARGS="${ORFS_MAKE_ARGS:-NUM_CORES=4}"       # cap workers -> bound peak RAM
echo "▶ Hardening '${DESIGN}' on ASAP7 via ${IMAGE} (repo ${REPO})"
# LEC_CHECK=0: skip ORFS's post-resize logical-equivalence check — its bundled
# formal binary (KEPLER_FORMAL_EXE) uses AVX-512 and SIGILLs on non-AVX512 CPUs
# (e.g. Coffee Lake). The flow is otherwise fully local. See FLOW.md.
docker run --rm -v "${REPO}:/work" -e KEMETCORE=/work -e LEC_CHECK=0 \
    -w /OpenROAD-flow-scripts/flow "${IMAGE}" \
    bash -lc "source /OpenROAD-flow-scripts/env.sh 2>/dev/null || true;
              make DESIGN_CONFIG=${CFG} WORK_HOME=/work/flow ${MAKE_ARGS} &&
              echo 'HARDEN_OK — GDS under flow/results/'"
