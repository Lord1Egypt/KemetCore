#!/usr/bin/env bash
# KemetCore — drive an ASAP7 harden (synth->floorplan->place->CTS->route->GDS)
# through the OpenROAD-flow-scripts container. Usage: flow/harden.sh bast_mac
set -euo pipefail
DESIGN="${1:-bast_mac}"
REPO="$(cd "$(dirname "$0")/.." && pwd)"
IMAGE="${ORFS_IMAGE:-openroad/orfs:latest}"
CFG="/work/flow/designs/asap7/${DESIGN}/config.mk"
MAKE_ARGS="${ORFS_MAKE_ARGS:-NUM_CORES=4}"       # cap workers -> bound peak RAM
echo "▶ Hardening '${DESIGN}' on ASAP7 via ${IMAGE} (repo ${REPO})"
docker run --rm -v "${REPO}:/work" -e KEMETCORE=/work \
    -w /OpenROAD-flow-scripts/flow "${IMAGE}" \
    bash -lc "source /OpenROAD-flow-scripts/env.sh 2>/dev/null || true;
              make DESIGN_CONFIG=${CFG} WORK_HOME=/work/flow ${MAKE_ARGS} &&
              echo 'HARDEN_OK — GDS under flow/results/'"
