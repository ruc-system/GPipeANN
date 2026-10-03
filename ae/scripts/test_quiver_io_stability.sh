#!/usr/bin/env bash
# Repeated fresh-process runs, without retries or reuse of cached results.
# Defaults reproduce reviewer A9's DEEP-1B Figure 5 failure point.
# Example: STABILITY_ATTEMPTS=3 STABILITY_Q=4 STABILITY_BLOCKS=864,972 \
#            bash ae/scripts/test_quiver_io_stability.sh
set -euo pipefail
DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
source "${DIR}/common.sh"

attempts="${STABILITY_ATTEMPTS:-30}"
timeout_s="${STABILITY_TIMEOUT:-300}"
for value in "${attempts}" "${timeout_s}"; do
  [[ "${value}" =~ ^[1-9][0-9]*$ ]] || {
    echo "STABILITY_ATTEMPTS and STABILITY_TIMEOUT must be positive integers" >&2
    exit 2
  }
done
require_bin quiver_search
ae_lock
use_dataset "${STABILITY_DATASET:-deep1b}"
mkdir -p "${ROOT}/.cache"
out="$(mktemp -d "${ROOT}/.cache/io-stability.XXXXXX")"
echo "Validation logs: ${out}"
date -Is > "${out}/started.txt"
sha256sum "${BIN_DIR}/bin/quiver_search" > "${out}/binary.sha256"

numa_args=()
read -r -a numa_args <<< "${AE_NUMA_PREFIX}"
search_cmd=(sudo -n env
  "CUDA_VISIBLE_DEVICES=${GPU_ID}" SPDK_QPAIRS_PER_SSD=1 SPDK_NUM_QP=1
  QUIVER_SPDK_DIAG=0 "SPDK_BASE_LBA=${SPDK_BASE_LBA}"
  "QUIVER_SPDK_BLOCK_OFFSET=${QUIVER_SPDK_BLOCK_OFFSET}"
  timeout --kill-after=10 "${timeout_s}" "${numa_args[@]}"
  "${BIN_DIR}/bin/quiver_search"
  --index-dir "${INDEX_DIR}" --query "${QUERY}" --ground-truth "${GT}"
  --data-type "${DATA_TYPE}" --topk 10 --ef-search "${STABILITY_EF:-145}"
  --repeat "${REPEAT:-20}" --pipe-width 2
  --queries-per-block "${STABILITY_Q:-3}" --poll-threads "${POLL_THREADS:-6}"
  --early-exit-policy none --ssd-list-file "${SSD_LIST}"
  --num-blocks-list "${STABILITY_BLOCKS:-972}")
printf '%q ' "${search_cmd[@]}" > "${out}/command.txt"
printf '\n' >> "${out}/command.txt"
IFS=, read -r -a blocks <<< "${STABILITY_BLOCKS:-972}"
for ((attempt=1; attempt<=attempts; ++attempt)); do
  log="${out}/attempt_${attempt}.log"
  rc=0
  "${search_cmd[@]}" > "${log}" 2>&1 || rc=$?
  ae_strip_ansi_log "${log}"
  results="$(awk '/^Recall @ 10:/ {n++} END {print n+0}' "${log}")"
  if [[ "${rc}" == 0 && "${results:-0}" != "${#blocks[@]}" ]]; then
    echo "Incomplete results in ${log}" >&2
    rc=1
  fi
  printf 'attempt=%s rc=%s results=%s\n' "${attempt}" "${rc}" "${results:-0}" |
    tee -a "${out}/status.txt"
  awk '/QPS:|Recall @|Cuda Error/' "${log}"
  # Fail on the first error; retries must not hide a regression.
  if [[ "${rc}" != 0 ]]; then exit "${rc}"; fi
done
sha256sum --check "${out}/binary.sha256"
date -Is > "${out}/finished.txt"
