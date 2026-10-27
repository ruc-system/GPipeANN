#!/usr/bin/env bash
# OpenAI1M four-SSD comparison. R128/L200/PQ64, navigation, recall-matched ef.
set -euo pipefail

DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
source "${DIR}/common.sh"
source "${DIR}/paper_knobs.sh"
apply_paper_knobs

require_bin quiver_search
require_bin flashanns_search
require_bin gustann_search
ae_lock
OUT="$(prepare_out openai1m)"
cd "${ROOT}"

use_dataset openai1m
SEARCH_INDEX_DIR="${OPENAI1M_NAV_INDEX_DIR}"
require_file "${SEARCH_INDEX_DIR}/${OPENAI1M_INDEX_PREFIX}_disk.index"
require_file "${QUERY}"
require_file "${GT}"
require_file "${SEARCH_INDEX_DIR}/${OPENAI1M_INDEX_PREFIX}_pq_pivots.bin"
require_file "${SEARCH_INDEX_DIR}/${OPENAI1M_INDEX_PREFIX}_pq_compressed.bin"
require_file "${SEARCH_INDEX_DIR}/nav/nav_index"
require_file "${SEARCH_INDEX_DIR}/nav/nav_index.data"
require_file "${SEARCH_INDEX_DIR}/nav/map.txt"

# The build and query knobs are defined once in common.sh.
EF="${OPENAI1M_EF}"
REPEAT_OPENAI="${OPENAI1M_REPEAT}"
OPENAI_NBS="${OPENAI1M_NUM_BLOCKS_LIST}"
OPENAI_MBS="${OPENAI1M_MINI_BATCH_LIST}"
{
  echo "R=${OPENAI1M_R} Lbuild=${OPENAI1M_LBUILD} PQ=${OPENAI1M_PQ_BYTES}"
  echo "ef=${EF} repeat=${REPEAT_OPENAI} index=${SEARCH_INDEX_DIR}"
  echo "navigation=enabled nav_sample=first10000 nav_R=32 nav_Lbuild=50"
  echo "SPDK_BASE_LBA=${SPDK_BASE_LBA} SPDK_IO_BYTES=${SPDK_IO_BYTES}"
} >> "${OUT}/env.txt"
export QUIVER_AE_TARGET_RECALL_OVERRIDE=0.90

run_search "${OUT}/flashanns_openai1m_ef${EF}_pw2.log" \
  "${BIN_DIR}/bin/flashanns_search" --index-dir "${SEARCH_INDEX_DIR}" \
  --query "${QUERY}" --ground-truth "${GT}" --data-type float \
  --topk "${TOPK}" --ef-search "${EF}" --repeat "${REPEAT_OPENAI}" \
  --pipe-width 2 --poll-threads "${POLL_THREADS}" \
  --ssd-list-file "${SSD_LIST}" --num-blocks-list "${OPENAI_NBS}"

run_search "${OUT}/gustann_openai1m_ef${EF}_pw1.log" \
  "${BIN_DIR}/bin/gustann_search" --index-dir "${SEARCH_INDEX_DIR}" \
  --query "${QUERY}" --ground-truth "${GT}" --data-type float \
  --topk "${TOPK}" --ef-search "${EF}" --repeat "${REPEAT_OPENAI}" \
  --pipe-width 1 --worker-threads "${WORKER_THREADS}" \
  --runner-contexts "${RUNNER_CONTEXTS}" --ssd-list-file "${SSD_LIST}" \
  --mini-batch-list "${OPENAI_MBS}"

for q in 1 2; do
  quiver_nbs="${OPENAI1M_QUIVER_Q1_NBS}"
  if [[ "$q" == 2 ]]; then quiver_nbs="${OPENAI1M_QUIVER_Q2_NBS}"; fi
  run_search "${OUT}/quiver_openai1m_ef${EF}_q${q}_pw2.log" \
    "${BIN_DIR}/bin/quiver_search" --index-dir "${SEARCH_INDEX_DIR}" \
    --query "${QUERY}" --ground-truth "${GT}" --data-type float \
    --topk "${TOPK}" --ef-search "${EF}" --repeat "${REPEAT_OPENAI}" \
    --pipe-width 2 --queries-per-block "${q}" --poll-threads "${POLL_THREADS}" \
    --early-exit-policy none --ssd-list-file "${SSD_LIST}" \
    --num-blocks-list "${quiver_nbs}"
done

echo "DONE ${OUT}"
