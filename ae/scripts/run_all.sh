#!/usr/bin/env bash
# Test only (no compile). Compile first: ./ae/scripts/build.sh
# ./ae/scripts/run_all.sh [all|e2e|...]
# Production binaries use build/; instrumentation figures use build-ae/.
set -euo pipefail

DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd -- "${DIR}/../.." && pwd)"
source "${DIR}/paper_knobs.sh"
apply_paper_knobs
want="${1:-all}"

# Set AE_RUN_ID to keep a reviewer's results separate. Reusing an explicit ID
# across selected-figure invocations collects those figures into one run.
AE_RUN_ID="${AE_RUN_ID:-}"
export AE_RUN_ID
result_root="${ROOT}/ae/results"
if [[ -n "${AE_RUN_ID}" ]]; then
  if [[ ! "${AE_RUN_ID}" =~ ^[A-Za-z0-9][A-Za-z0-9._-]*$ || ${#AE_RUN_ID} -gt 64 ]]; then
    echo "ERROR: invalid AE_RUN_ID: ${AE_RUN_ID}" >&2
    echo "Use 1-64 characters (letters, digits, '.', '_' or '-'); start with a letter or digit." >&2
    echo "Example: AE_RUN_ID=reviewer1-20260930 ./ae/scripts/run_all.sh ${want}" >&2
    exit 1
  fi
  result_root="${ROOT}/ae/results/runs/${AE_RUN_ID}"
  if [[ -L "${result_root}" ]]; then
    echo "ERROR: the run directory is a symbolic link and cannot be used safely:" >&2
    echo "  ${result_root}" >&2
    echo "Choose a different AE_RUN_ID or contact the authors." >&2
    exit 1
  fi
fi

ALL_FIGS=(latency_qps io_latency e2e fusion ablation q_sensitivity)
declare -A PAPER_FIGURE=(
  [latency_qps]=1 [io_latency]=3 [e2e]=5
  [fusion]=6 [ablation]=7 [q_sensitivity]=8
)

selected=()
for name in "${ALL_FIGS[@]}"; do
  if [[ "${want}" == "all" || "${want}" == "${name}" || "${want}" == "fig_${name}.sh" ]]; then
    selected+=("${name}")
  fi
done
if [[ "${#selected[@]}" -eq 0 ]]; then
  echo "unknown experiment: ${want}" >&2
  echo "accepted: all ${ALL_FIGS[*]}" >&2
  exit 1
fi

# Explicit run IDs are immutable per figure. This permits assembling a run by
# invoking different selected figures with the same ID, but prevents an
# accidental rerun from destroying that ID's existing result.
if [[ -n "${AE_RUN_ID}" && -z "${AE_DEBUG_ROOT:-}" ]]; then
  for name in "${selected[@]}"; do
    if [[ -e "${result_root}/${name}" ]]; then
      echo "ERROR: run '${AE_RUN_ID}' already contains results for '${name}'." >&2
      echo "Existing results were not changed: ${result_root}/${name}" >&2
      echo "Choose a new ID to rerun it, for example:" >&2
      echo "  AE_RUN_ID=${AE_RUN_ID}-rerun ./ae/scripts/run_all.sh ${want}" >&2
      exit 1
    fi
  done
fi

total="${#selected[@]}"
started="$(date +%s)"
stage_root=""
if [[ -n "${AE_DEBUG_ROOT:-}" ]]; then
  AE_DEBUG_ROOT="$(realpath -m "${AE_DEBUG_ROOT}")"
  AE_DEBUG_RUN_ID="${AE_DEBUG_RUN_ID:-$(date +%Y%m%d_%H%M%S)_$$}"
  export AE_DEBUG_ROOT AE_DEBUG_RUN_ID
  mkdir -p "${AE_DEBUG_ROOT}"
  echo "debug history: ${AE_DEBUG_ROOT} (run ${AE_DEBUG_RUN_ID})"
else
  stage_root="${ROOT}/.cache/ae-staging/run.$$"
  mkdir -p "${stage_root}"
  # Never delete unpublished results, including on publication/plot failures.
  trap 'if [[ -d "${stage_root}" ]]; then rmdir "${stage_root}" 2>/dev/null || echo "Unpublished results retained: ${stage_root}" >&2; fi' EXIT
  mkdir -p "${result_root}"
  if [[ -n "${AE_RUN_ID}" ]]; then
    echo "run id: ${AE_RUN_ID}"
    echo "results: ${result_root}"
  fi
fi

publish_result() {
  local name="$1"
  local status="${2:-complete}"
  local incoming="${stage_root}/${name}"
  local final="${result_root}/${name}"
  local backup="${result_root}/.${name}.previous.$$"

  [[ -f "${incoming}/env.txt" ]] || {
    echo "incomplete staged result: ${incoming}" >&2
    return 1
  }
  printf 'status=%s\n' "${status}" > "${incoming}/status.env" || return 1
  mkdir -p "${result_root}" || return 1
  # Recheck at publication time in case another invocation using the same ID
  # passed the preflight check concurrently while this experiment was running.
  if [[ -n "${AE_RUN_ID}" && -e "${final}" ]]; then
    echo "ERROR: another run published '${name}' under AE_RUN_ID=${AE_RUN_ID}." >&2
    echo "Existing results were not changed: ${final}" >&2
    echo "Rerun with a new AE_RUN_ID." >&2
    return 1
  fi
  if [[ -e "${backup}" ]]; then
    echo "existing result backup retained: ${backup}" >&2
    return 1
  fi
  if [[ -e "${final}" ]]; then
    mv "${final}" "${backup}" || return 1
  fi
  if mv "${incoming}" "${final}"; then
    rm -rf "${backup}"
    echo "published ${final}"
    return 0
  fi
  [[ ! -e "${final}" && -e "${backup}" ]] && mv "${backup}" "${final}"
  return 1
}

failures=()
i=0
for name in "${selected[@]}"; do
  i=$((i + 1))
  echo
  echo "===== [${i}/${total}] ${name} -> paper Figure ${PAPER_FIGURE[${name}]} (AE_SCALE=${AE_SCALE:-1b}) ====="
  step_started="$(date +%s)"
  if [[ -n "${AE_DEBUG_ROOT:-}" ]]; then
    if "${DIR}/fig_${name}.sh"; then
      echo "kept debug attempt under ${AE_DEBUG_ROOT}/${name}/runs/${AE_DEBUG_RUN_ID}"
      if find "${AE_DEBUG_ROOT}/${name}/runs/${AE_DEBUG_RUN_ID}" -name failed_points.tsv -type f -size +0c -print -quit | grep -q .; then
        failures+=("${name}:skipped-points")
      fi
    else
      rc=$?
      failures+=("${name}:rc=${rc}")
      echo "WARNING: ${name} failed rc=${rc}; debug history was kept; continuing." >&2
    fi
  else
    if AE_OUTPUT_ROOT="${stage_root}" "${DIR}/fig_${name}.sh"; then
      status=complete
      if find "${stage_root}/${name}" -name failed_points.tsv -type f -size +0c -print -quit | grep -q .; then
        status=partial
        failures+=("${name}:skipped-points")
      fi
      if ! publish_result "${name}" "${status}"; then
        failures+=("${name}:publish-failed")
        echo "WARNING: could not publish ${name}; retained ${stage_root}/${name}; continuing." >&2
      fi
    else
      rc=$?
      failures+=("${name}:rc=${rc}")
      if [[ -d "${stage_root}/${name}" ]]; then
        {
          echo "figure=${name}"
          echo "exit_code=${rc}"
          echo "failed_at=$(date -Iseconds)"
        } > "${stage_root}/${name}/failure.env" || echo "WARNING: could not write failure metadata for ${name}; retaining data." >&2
        if publish_result "${name}" failed; then
          echo "WARNING: published partial ${name} results and continuing." >&2
        else
          echo "WARNING: could not publish partial ${name} results; continuing." >&2
        fi
      else
        echo "WARNING: ${name} failed before creating a result directory; continuing." >&2
      fi
    fi
  fi
  echo "----- ${name} done in $(( ($(date +%s) - step_started) / 60 )) min -----"
done

echo
echo "All ${total} experiment(s) finished in $(( ($(date +%s) - started) / 60 )) min."
if [[ -n "${AE_RUN_ID}" ]]; then
  echo "Results: ${result_root}"
fi
echo "Generating plots from successful results..."

# Plot only the selected figures from this invocation. A plotting error must
# not prevent the other figures from being rendered, or delete their results.
for name in "${selected[@]}"; do
  source_dir="${result_root}/${name}"
  plot_root="${ROOT}/ae/figures"
  [[ -z "${AE_RUN_ID}" ]] || plot_root+="/runs/${AE_RUN_ID}"
  if [[ -n "${AE_DEBUG_ROOT:-}" ]]; then
    source_dir="${AE_DEBUG_ROOT}/${name}/runs/${AE_DEBUG_RUN_ID}"
    plot_root="${AE_DEBUG_ROOT}/figures/${AE_DEBUG_RUN_ID}"
  elif [[ -d "${stage_root}/${name}" ]]; then
    source_dir="${stage_root}/${name}"
    # Keep plots next to unpublished data instead of overwriting another run.
    plot_root="${stage_root}/plots"
  fi
  if [[ -d "${source_dir}" ]]; then
    if ! python3 "${DIR}/plot_all.py" "${source_dir}" -o "${plot_root}"; then
      failures+=("${name}:plot-failed-or-empty")
      echo "WARNING: no complete plot for ${name}; data retained; continuing." >&2
    fi
  fi
done

if [[ "${#failures[@]}" -gt 0 ]]; then
  echo "WARNING: run finished with omissions/errors: ${failures[*]}" >&2
  exit 1
fi
