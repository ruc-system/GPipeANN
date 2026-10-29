#!/usr/bin/env bash
# Paper Figure 7 (ablation) — 4 SSD, build-ae (STRAWMEN + LIGHT_BREAKDOWN).
# Panel (a) sweeps Recall@10 0.88..0.98 for FlashANNS / +S / +S+C.
# Panel (b) is the latency breakdown at Recall@10 = 0.90.
# +S strawman uses Q=2 (Q>=3 overflows smem); that limit is what +C removes.
set -euo pipefail
DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
source "${DIR}/common.sh"
source "${DIR}/paper_knobs.sh"
apply_paper_knobs

BIN_DIR="${INSTRUMENTED_BIN_DIR}"
# Instrumentation can add tens of seconds before the first result and can make
# adjacent occupancy points differ sharply. Do not classify that as a hang.
export HANG_FLOOR_FIRST="${HANG_FLOOR_FIRST:-300}"
export HANG_FLOOR="${HANG_FLOOR:-300}"

require_bin flashanns_search
require_bin gustann_search
require_bin gpipeann_search
require_bin strawmen_pq_in_smem
ae_lock
use_dataset sift
OUT="$(prepare_out ablation)"
cd "${ROOT}"

PLUS_S_Q="${PLUS_S_Q:-2}"
EF="${EF:-${EF_RECALL_90}}"
# Paper x axis: Recall@10 = 0.88 / 0.90 / 0.92 / 0.94 / 0.96 / 0.98.
ABLATION_EF_LIST="${ABLATION_EF_LIST:-${EF_RECALL_88} ${EF_RECALL_90} ${EF_RECALL_92} ${EF_RECALL_94} ${EF_RECALL_96} ${EF_RECALL_98}}"
ABLATION_A_SYSTEMS="${ABLATION_A_SYSTEMS:-flashanns plusS gpipeann}"
ABLATION_RUN_B="${ABLATION_RUN_B:-1}"
# Official AE path: the paper-selected occupancy for each submitted bar.
# Set ABLATION_SELECTED_ONLY=0 only if you want the full occupancy grid.
ABLATION_SELECTED_ONLY="${ABLATION_SELECTED_ONLY:-1}"

has_word() {
  local wanted="$1" word
  for word in $2; do
    [[ "${word}" == "${wanted}" ]] && return 0
  done
  return 1
}

# ---- panel (a): throughput at the paper-selected occupancy, per recall ----
# Each bar is the measured QPS of that selected point. +S stays at Q=2
# because Q>=3 overflows shared memory; removing that limit is what +C buys.
for ef in ${ABLATION_EF_LIST}; do
  echo "----- ablation (a) ef=${ef} -----"
  flash_nbs="${NUM_BLOCKS_LIST}"
  plus_s_nbs="${GPIPEANN_MID_NB:-216,324,432,540,648,756,864,972}"
  gpipeann_q_list="${GPIPEANN_Q_LIST}"
  if [[ "${ABLATION_SELECTED_ONLY}" == 1 ]]; then
    case "${ef}" in
      "${EF_RECALL_88}") flash_nbs=540; plus_s_nbs=324; gpipeann_q_list=2; selected_gpipeann_nbs=324 ;;
      "${EF_RECALL_90}") flash_nbs=432; plus_s_nbs=216; gpipeann_q_list=2; selected_gpipeann_nbs=432 ;;
      "${EF_RECALL_92}") flash_nbs=432; plus_s_nbs=216; gpipeann_q_list=2; selected_gpipeann_nbs=324 ;;
      "${EF_RECALL_94}") flash_nbs=324; plus_s_nbs=216; gpipeann_q_list=2; selected_gpipeann_nbs=216 ;;
      "${EF_RECALL_96}") flash_nbs=216; plus_s_nbs=108; gpipeann_q_list=1; selected_gpipeann_nbs=324 ;;
      "${EF_RECALL_98}") flash_nbs=108; plus_s_nbs=108; gpipeann_q_list=1; selected_gpipeann_nbs=216 ;;
      *) echo "no submitted Figure 7(a) point for ef=${ef}" >&2; exit 1 ;;
    esac
  fi

  if has_word flashanns "${ABLATION_A_SYSTEMS}"; then
    for pw in ${FLASH_PW_LIST}; do
      run_search "${OUT}/a_flashanns_${DATASET}_ef${ef}_pw${pw}.log" \
        "${BIN_DIR}/bin/flashanns_search" \
        --index-dir "${INDEX_DIR}" \
        --query "${QUERY}" \
        --ground-truth "${GT}" \
        --data-type "${DATA_TYPE}" \
        --topk "${TOPK}" \
        --ef-search "${ef}" \
        --repeat "${REPEAT}" \
        --pipe-width "${pw}" \
        --poll-threads "${POLL_THREADS}" \
        --ssd-list-file "${SSD_LIST}" \
        --num-blocks-list "${flash_nbs}"
    done
  fi

  if has_word plusS "${ABLATION_A_SYSTEMS}"; then
    for pw in ${GPIPEANN_PW_LIST}; do
      run_search "${OUT}/a_plusS_pq_in_smem_${DATASET}_q${PLUS_S_Q}_ef${ef}_pw${pw}.log" \
        "${BIN_DIR}/bin/strawmen_pq_in_smem" \
        --index-dir "${INDEX_DIR}" \
        --query "${QUERY}" \
        --ground-truth "${GT}" \
        --data-type "${DATA_TYPE}" \
        --topk "${TOPK}" \
        --ef-search "${ef}" \
        --repeat "${REPEAT}" \
        --pipe-width "${pw}" \
        --queries-per-block "${PLUS_S_Q}" \
        --poll-threads "${POLL_THREADS}" \
        --ssd-list-file "${SSD_LIST}" \
        --num-blocks-list "${plus_s_nbs}"
    done
  fi

  if has_word gpipeann "${ABLATION_A_SYSTEMS}"; then
    for pw in ${GPIPEANN_PW_LIST}; do
      for q in ${gpipeann_q_list}; do
        if [[ "${ABLATION_SELECTED_ONLY}" == 1 ]]; then
          gpipeann_nbs="${selected_gpipeann_nbs}"
        else
          case "${q}" in
            1) gpipeann_nbs="${GPIPEANN_LOWLAT_NB:-108,216,324}" ;;
            2) gpipeann_nbs="${GPIPEANN_MID_NB:-216,324,432,540,648,756,864,972}" ;;
            *) continue ;;
          esac
        fi
        run_search "${OUT}/a_gpipeann_${DATASET}_q${q}_ef${ef}_pw${pw}.log" \
          "${BIN_DIR}/bin/gpipeann_search" \
          --index-dir "${INDEX_DIR}" \
          --query "${QUERY}" \
          --ground-truth "${GT}" \
          --data-type "${DATA_TYPE}" \
          --topk "${TOPK}" \
          --ef-search "${ef}" \
          --repeat "${REPEAT}" \
          --pipe-width "${pw}" \
          --queries-per-block "${q}" \
          --poll-threads "${POLL_THREADS}" \
          --early-exit-policy none \
          --ssd-list-file "${SSD_LIST}" \
          --num-blocks-list "${gpipeann_nbs}"
      done
    done
  fi
done

# ---- panel (b): query latency breakdown at Recall@10 = 0.90 ----
# Comparing stall shares only means something at matched throughput, so each
# system runs at its own occupancy: POINT_* in common.sh holds the paper's set.
if [[ "${ABLATION_RUN_B}" == 1 ]]; then
run_search "${OUT}/b_gustann_${DATASET}_mb${POINT_GUST_MINI_BATCH}.log" \
  "${BIN_DIR}/bin/gustann_search" \
  --index-dir "${INDEX_DIR}" \
  --query "${QUERY}" \
  --ground-truth "${GT}" \
  --data-type "${DATA_TYPE}" \
  --topk "${TOPK}" \
  --ef-search "${EF}" \
  --repeat "${REPEAT}" \
  --pipe-width "${PIPE_WIDTH_GUST}" \
  --worker-threads "${WORKER_THREADS}" \
  --runner-contexts "${RUNNER_CONTEXTS}" \
  --ssd-list-file "${SSD_LIST}" \
  --mini-batch "${POINT_GUST_MINI_BATCH}"

run_search "${OUT}/b_flashanns_${DATASET}_nb${POINT_FLASH_BLOCKS}.log" \
  "${BIN_DIR}/bin/flashanns_search" \
  --index-dir "${INDEX_DIR}" \
  --query "${QUERY}" \
  --ground-truth "${GT}" \
  --data-type "${DATA_TYPE}" \
  --topk "${TOPK}" \
  --ef-search "${EF}" \
  --repeat "${REPEAT}" \
  --pipe-width "${PIPE_WIDTH_FLASH}" \
  --poll-threads "${POLL_THREADS}" \
  --ssd-list-file "${SSD_LIST}" \
  --num-blocks "${POINT_FLASH_BLOCKS}"

run_search "${OUT}/b_plusS_pq_in_smem_${DATASET}_q${PLUS_S_Q}_nb${POINT_PLUS_S_BLOCKS}.log" \
  "${BIN_DIR}/bin/strawmen_pq_in_smem" \
  --index-dir "${INDEX_DIR}" \
  --query "${QUERY}" \
  --ground-truth "${GT}" \
  --data-type "${DATA_TYPE}" \
  --topk "${TOPK}" \
  --ef-search "${EF}" \
  --repeat "${REPEAT}" \
  --pipe-width "${PIPE_WIDTH_GPIPEANN}" \
  --queries-per-block "${PLUS_S_Q}" \
  --poll-threads "${POLL_THREADS}" \
  --ssd-list-file "${SSD_LIST}" \
  --num-blocks "${POINT_PLUS_S_BLOCKS}"

run_search "${OUT}/b_gpipeann_${DATASET}_q${QUERIES_PER_BLOCK}_nb${POINT_GPIPEANN_BLOCKS}.log" \
  "${BIN_DIR}/bin/gpipeann_search" \
  --index-dir "${INDEX_DIR}" \
  --query "${QUERY}" \
  --ground-truth "${GT}" \
  --data-type "${DATA_TYPE}" \
  --topk "${TOPK}" \
  --ef-search "${EF}" \
  --repeat "${REPEAT}" \
  --pipe-width "${PIPE_WIDTH_GPIPEANN}" \
  --queries-per-block "${QUERIES_PER_BLOCK}" \
  --poll-threads "${POLL_THREADS}" \
  --early-exit-policy none \
  --ssd-list-file "${SSD_LIST}" \
  --num-blocks "${POINT_GPIPEANN_BLOCKS}"
fi

echo "DONE ${OUT}"
