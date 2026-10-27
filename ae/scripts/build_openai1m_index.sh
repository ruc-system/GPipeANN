#!/usr/bin/env bash
# Build the single R128/L200/PQ64 OpenAI1M index; SSD writes are explicit.
set -euo pipefail
DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
source "${DIR}/common.sh"
require_file "${OPENAI1M_BASE}"

if [[ ! -d "${OPENAI1M_INDEX_DIR}" ]]; then
  builder="${ROOT}/deps/DiskANN/build/apps/build_disk_index"
  [[ -x "${builder}" ]] || { echo "missing executable: ${builder}" >&2; exit 1; }
  mkdir -p "$(dirname "${OPENAI1M_INDEX_DIR}")"
  stage="$(mktemp -d "${OPENAI1M_INDEX_DIR}.build.XXXXXX")"
  trap 'rm -rf "${stage}"' EXIT
  OMP_NUM_THREADS=32 "${builder}" --data_type float --dist_fn l2 \
    --data_path "${OPENAI1M_BASE}" \
    --index_path_prefix "${stage}/${OPENAI1M_INDEX_PREFIX}" \
    -R "${OPENAI1M_R}" -L "${OPENAI1M_LBUILD}" --QD "${OPENAI1M_PQ_BYTES}" \
    -B 0.1 -M 64 -T 32 > "${stage}/build.log" 2>&1
  mv "${stage}" "${OPENAI1M_INDEX_DIR}"
  trap - EXIT
fi

# Reusing a prepared graph preserves the image already written to SSD.
python3 - "${OPENAI1M_BASE}" "${OPENAI1M_INDEX_DIR}/${OPENAI1M_INDEX_PREFIX}" \
  "${OPENAI1M_R}" "${OPENAI1M_PQ_BYTES}" "${OPENAI1M_LBUILD}" <<'PY'
import json
import struct
import sys
from pathlib import Path
base, prefix, degree, pq = sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4])
with open(base, "rb") as f:
    n, dim = struct.unpack("<II", f.read(8))
with open(prefix + "_pq_compressed.bin", "rb") as f:
    assert struct.unpack("<II", f.read(8)) == (n, pq), "PQ shape mismatch"
assert Path(prefix + "_pq_compressed.bin").stat().st_size == 8 + n * pq
assert Path(prefix + "_pq_pivots.bin").is_file()
with open(prefix + "_disk.index", "rb") as f:
    rows, cols = struct.unpack("<II", f.read(8))
    header = struct.unpack("<" + "Q" * rows * cols, f.read(rows * cols * 8))
assert header[:2] == (n, dim), "graph/base shape mismatch"
assert header[3] == dim * 4 + (degree + 1) * 4, "graph degree/layout mismatch"
Path(prefix + "_build_config.json").write_text(json.dumps({
    "R": degree, "Lbuild": int(sys.argv[5]), "PQ_bytes": pq, "opq": False,
}, indent=2) + "\n")
print(f"Ready: {prefix} (n={n}, dim={dim}, R={degree}, PQ={pq})")
PY
