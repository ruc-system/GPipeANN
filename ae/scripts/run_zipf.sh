#!/usr/bin/env bash
# SIFT1B Zipf per-query-ef, four-SSD QPS/latency comparison at Recall@10 ~= 0.90.
set -euo pipefail

DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
source "${DIR}/common.sh"
source "${DIR}/paper_knobs.sh"
apply_paper_knobs

require_bin quiver_search
require_bin flashanns_search
require_bin gustann_search
ae_lock
OUT="$(prepare_out zipf)"
cd "${ROOT}"

use_dataset sift1b
WORKLOAD="${ZIPF_WORKLOAD_DIR:-${DATASET_ROOT}/sift1b/zipf-ef-r90-v2}"
ZIPF_QUERY="${WORKLOAD}/query.u8bin"
ZIPF_GT="${WORKLOAD}/gt.ibin"
QUERY_EF_CSV="${WORKLOAD}/mapping.csv"
require_file "${ZIPF_QUERY}"
require_file "${ZIPF_GT}"
require_file "${QUERY_EF_CSV}"

# All three systems consume this exact mapping. The five Zipf classes are
# 35,45,55,70,95; measured Recall@10 is 0.9031/0.9030/0.8997.
ZIPF_MAX_EF="${ZIPF_MAX_EF:-95}"
REPEAT_ZIPF="${ZIPF_REPEAT:-20}"
ZIPF_NBS="${ZIPF_NUM_BLOCKS_LIST:-108,216,324,432,540,648,756,864,972,1080}"
ZIPF_MBS="${ZIPF_MINI_BATCH_LIST:-16,24,32,48,64,96,128,192}"
export QUIVER_AE_TARGET_RECALL_OVERRIDE=0.90

run_search "${OUT}/flashanns_sift1b_zipf_pw2.log" \
  "${BIN_DIR}/bin/flashanns_search" --index-dir "${INDEX_DIR}" \
  --query "${ZIPF_QUERY}" --ground-truth "${ZIPF_GT}" --data-type uint8 \
  --topk "${TOPK}" --ef-search "${ZIPF_MAX_EF}" \
  --query-ef-csv "${QUERY_EF_CSV}" --repeat "${REPEAT_ZIPF}" \
  --pipe-width 2 --poll-threads "${POLL_THREADS}" \
  --ssd-list-file "${SSD_LIST}" --num-blocks-list "${ZIPF_NBS}"

run_search "${OUT}/gustann_sift1b_zipf_pw1.log" \
  "${BIN_DIR}/bin/gustann_search" --index-dir "${INDEX_DIR}" \
  --query "${ZIPF_QUERY}" --ground-truth "${ZIPF_GT}" --data-type uint8 \
  --topk "${TOPK}" --ef-search "${ZIPF_MAX_EF}" \
  --query-ef-csv "${QUERY_EF_CSV}" --repeat "${REPEAT_ZIPF}" \
  --pipe-width 1 --worker-threads "${WORKER_THREADS}" \
  --runner-contexts "${RUNNER_CONTEXTS}" --ssd-list-file "${SSD_LIST}" \
  --mini-batch-list "${ZIPF_MBS}"

run_search "${OUT}/quiver_sift1b_zipf_q1_pw2.log" \
  "${BIN_DIR}/bin/quiver_search" --index-dir "${INDEX_DIR}" \
  --query "${ZIPF_QUERY}" --ground-truth "${ZIPF_GT}" --data-type uint8 \
  --topk "${TOPK}" --ef-search "${ZIPF_MAX_EF}" \
  --query-ef-csv "${QUERY_EF_CSV}" --repeat "${REPEAT_ZIPF}" \
  --pipe-width 2 --queries-per-block 1 --poll-threads "${POLL_THREADS}" \
  --early-exit-policy none --ssd-list-file "${SSD_LIST}" \
  --num-blocks-list "${QUIVER_LOWLAT_NB}"

run_search "${OUT}/quiver_sift1b_zipf_q2_pw2.log" \
  "${BIN_DIR}/bin/quiver_search" --index-dir "${INDEX_DIR}" \
  --query "${ZIPF_QUERY}" --ground-truth "${ZIPF_GT}" --data-type uint8 \
  --topk "${TOPK}" --ef-search "${ZIPF_MAX_EF}" \
  --query-ef-csv "${QUERY_EF_CSV}" --repeat "${REPEAT_ZIPF}" \
  --pipe-width 2 --queries-per-block 2 --poll-threads "${POLL_THREADS}" \
  --early-exit-policy none --ssd-list-file "${SSD_LIST}" \
  --num-blocks-list "${QUIVER_MID_NB}"

echo "DONE ${OUT}"
