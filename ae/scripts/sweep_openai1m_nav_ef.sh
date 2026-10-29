#!/usr/bin/env bash
# Find the minimum ef reaching Recall@10 >= 0.90 with the OpenAI1M nav index.
set -euo pipefail

DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
source "${DIR}/common.sh"
source "${DIR}/paper_knobs.sh"
apply_paper_knobs

require_bin gpipeann_search
ae_lock
OUT="$(prepare_out openai1m_nav_ef_sweep)"
cd "${ROOT}"
use_dataset openai1m

NAV_INDEX_DIR="${OPENAI1M_NAV_INDEX_DIR:-${INDEX_ROOT}/openai1m-R128-L200-QD64-nav10k}"
require_file "${NAV_INDEX_DIR}/${OPENAI1M_INDEX_PREFIX}_disk.index"
require_file "${NAV_INDEX_DIR}/${OPENAI1M_INDEX_PREFIX}_pq_pivots.bin"
require_file "${NAV_INDEX_DIR}/${OPENAI1M_INDEX_PREFIX}_pq_compressed.bin"
require_file "${NAV_INDEX_DIR}/nav/nav_index"
require_file "${NAV_INDEX_DIR}/nav/nav_index.data"
require_file "${NAV_INDEX_DIR}/nav/map.txt"

EF_LIST="${OPENAI1M_NAV_EF_LIST:-45 50 55 60 65 70 75 80 85}"
{
  echo "purpose=minimum ef for Recall@10 >= 0.90"
  echo "R=${OPENAI1M_R} Lbuild=${OPENAI1M_LBUILD} PQ=${OPENAI1M_PQ_BYTES}"
  echo "index=${NAV_INDEX_DIR} repeat=1 q=1 blocks=108"
  echo "ef_list=${EF_LIST}"
} >> "${OUT}/env.txt"

for ef in ${EF_LIST}; do
  run_search "${OUT}/gpipeann_openai1m_nav_ef${ef}_q1_pw2.log" \
    "${BIN_DIR}/bin/gpipeann_search" --index-dir "${NAV_INDEX_DIR}" \
    --query "${QUERY}" --ground-truth "${GT}" --data-type float \
    --topk "${TOPK}" --ef-search "${ef}" --repeat 1 \
    --pipe-width 2 --queries-per-block 1 --poll-threads "${POLL_THREADS}" \
    --early-exit-policy none --ssd-list-file "${SSD_LIST}" --num-blocks 108
done

python3 - "${OUT}" <<'PY'
import csv
import re
import sys
from pathlib import Path

out = Path(sys.argv[1])
rows = []
for log in sorted(out.glob("gpipeann_openai1m_nav_ef*_q1_pw2.log"),
                  key=lambda p: int(re.search(r"ef(\d+)", p.name)[1])):
    text = log.read_text()
    ef = int(re.search(r"ef(\d+)", log.name)[1])
    recall = float(re.search(r"Recall @ 10:\s*([\d.]+)", text)[1])
    qps = float(re.search(r"QPS:\s*([\d.]+)", text)[1])
    rows.append({"ef": ef, "recall_at_10": recall, "qps": qps})
with (out / "recall.csv").open("w", newline="") as stream:
    writer = csv.DictWriter(stream, fieldnames=rows[0].keys())
    writer.writeheader(); writer.writerows(rows)
minimum = next((row for row in rows if row["recall_at_10"] >= .90), None)
(out / "minimum_ef.txt").write_text("none\n" if minimum is None else f'{minimum["ef"]}\n')
for row in rows:
    print(row)
print("minimum_ef", "none" if minimum is None else minimum["ef"])
PY

echo "DONE ${OUT}"
