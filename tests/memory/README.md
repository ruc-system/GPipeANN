# File-backed debug tests

The memory backend is a single ordinary-file block reader. Without `--ssd-list-file`, the engine issues its normal loader requests against the index file using `pread`; it does not load a separate heap copy or expose heap/mmap modes. Quiver, FlashANNS, and GustANN share one host-side implementation in `src/shared/io/file_loader_base.hpp`. Their small adapters preserve the existing request types and tracing interfaces. Search kernels, scheduling, polling and result handling follow the normal engine paths.

The `main` branch preserves the paper GPU search kernels and SPDK I/O implementation while maintaining the file-backed debug backend. The `feature` branch additionally carries per-query ef, multi-sector node I/O, and OpenAI1M/Zipf evaluation support.

These tests require no SPDK setup, hugepages, SSD binding, or external datasets. Host tests need CMake and a C++17 compiler, without CUDA or third-party submodules. GPU search tests additionally require Python 3, CUDA, and a GPU. Debug timings can help investigate compute-side changes, but cannot establish GPU–SSD performance or absence of SSD performance regressions.

## Host block-reader tests

Run from the repository root:

```bash
cmake -S tests/memory -B build/memory-host -DCMAKE_BUILD_TYPE=Release
cmake --build build/memory-host --parallel 4
ctest --test-dir build/memory-host -L host --output-on-failure
```

The same test implementation is compiled against all three production loader adapters, plus FlashANNS tracing. It covers the 4 KiB metadata-page offset, out-of-order batches, concurrent reads, 4/8 KiB requests, buffer ownership, completion status, available timestamps, I/O counters, file updates after opening, missing/truncated files, and invalid request bounds. A failed read must not publish successful completion.

## GPU search tests

Set `CUDACXX` if nvcc is not on PATH. The paper CMake CUDA architecture list (`70;80;90`) is preserved:

```bash
git submodule update --init deps/spdlog deps/argparse
cmake -S . -B build/memory-gpu \
  -DQUIVER_ENABLE_SPDK=OFF \
  -DQUIVER_BUILD_DISKANN_TOOLS=OFF \
  -DQUIVER_BUILD_STRAWMEN=OFF
cmake --build build/memory-gpu \
  --target quiver_search flashanns_search gustann_search search_setup_test --parallel 4
cmake -S tests/memory -B build/memory-host \
  -DQUIVER_MEMORY_SEARCH_BINARY="$PWD/build/memory-gpu/bin/quiver_search" \
  -DQUIVER_MEMORY_BASELINE_BIN_DIR="$PWD/build/memory-gpu/bin" \
  -DQUIVER_MEMORY_ENTRY_TESTS=OFF -DQUIVER_MEMORY_EXTENDED_TESTS=OFF
cmake --build build/memory-host --parallel 4
ctest --test-dir build/memory-host --output-on-failure
build/memory-gpu/bin/search_setup_test
```

Tests generate complete graphs and exact PQ codebooks using Python's standard library. Quiver tests cover uint8, int8, and float; Q=1, 2, and 4; repeated queries; disk-medoid and navigation-selected entry nodes; a top-k above 32; and the `--memory-index-file` override. Returned IDs must be valid and unique, returned distances must match the corresponding vectors, and top-k distances must match an independent brute-force calculation. Ties may return different IDs with equal exact distances. Baseline tests use their production CLIs with pipe widths 1 and 2, checking Recall@5=1 against independently generated ground truth. Baseline CLIs do not export binary result arrays, so those checks are weaker than the Quiver result oracle.

`memory_search_entry_query` reproduces duplicate entry-node results on the synthetic graph using the paper kernels. Both branches retain the original bootstrap entry handling without an extra entry PQ calculation or visited seed. Entry, navigation-entry and large-top-k diagnostic cases are controlled by `QUIVER_MEMORY_ENTRY_TESTS`, OFF by default on both branches. Enable it explicitly to investigate the synthetic entry case; failures are reported normally. The source-level GPU search and SPDK I/O implementations on `main` match the paper baseline.

Each search has a 30-second timeout; failures retain logs and return a failing test status. Generated fixtures, full commands, logs, and available binary results are retained in unique `build/memory-host/search-*/run-*` directories. The production launchers require CPU 21 in the process's affinity mask. Set `CUDA_VISIBLE_DEVICES` to select a GPU. For a host-only configuration, set both `-DQUIVER_MEMORY_SEARCH_BINARY=` and `-DQUIVER_MEMORY_BASELINE_BIN_DIR=`.

The obsolete `--memory-backend` CLI flag and `memory_backend` Python argument are removed. Omit the SSD list to select the file-backed debug path; use `--memory-index-file` only when the data file differs from the discovered metadata index.

## Optional feature-branch tests

When testing a binary that includes per-query ef and multi-sector support, enable these cases explicitly:

```bash
cmake -S tests/memory -B build/memory-host \
  -DQUIVER_MEMORY_SEARCH_BINARY=/absolute/path/to/feature/quiver_search \
  -DQUIVER_MEMORY_EXTENDED_TESTS=ON -DQUIVER_MEMORY_ENTRY_TESTS=OFF
ctest --test-dir build/memory-host -L extended --output-on-failure
```

These cases supply varying per-query ef budgets with repeated queries, and a 1536-dimensional float index requiring 8 KiB reads per node. They use the same Quiver result oracle and Q matrix. Missing support causes failure, never a silent skip. These capabilities live on `feature`, so extended tests are off by default on `main`. These cases check functional behavior and do not establish performance. The host block-reader tests independently validate 8 KiB reads. Set both `-DQUIVER_MEMORY_EXTENDED_TESTS=OFF` and `-DQUIVER_MEMORY_ENTRY_TESTS=OFF` when returning to `main`.
