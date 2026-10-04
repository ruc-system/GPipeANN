# FlashANNS baseline reimplementation

## Provenance and license

This directory contains an independent reimplementation of
[FlashANNS](https://doi.org/10.1145/3786652) written by the Quiver authors from
the algorithm and system descriptions in the published paper. It is not source
code from the FlashANNS authors and is not an official FlashANNS release. We
were not aware of a public official implementation when preparing the Quiver
artifact.

The code in this directory is released with the Quiver artifact under the
repository's [Apache License 2.0](../../LICENSE).

## Implemented design

The implementation provides the search-side FlashANNS baseline used in the
Quiver evaluation:

- SSD-resident graph traversal with GPU PQ distance evaluation;
- one query statically assigned to each CUDA thread block for the duration of
  a kernel launch;
- a dependency-relaxed pipeline with multiple outstanding graph-page reads per
  query, controlled by `--pipe-width`; and
- CPU polling threads that submit and complete page reads through the SPDK or
  memory backend.

The implementation uses the same index layout, input formats, SSD striping,
and measurement harness as the other graph-based systems in this artifact.
The main CUDA search loop is in `kernel.cuh`, host-side I/O polling and kernel
launching are in `search.cu`, and the command-line entry point is
`../../bin/flashanns_search.cu`.

Because the original implementation is unavailable, this code should be
treated as a paper-based reproduction rather than a source-equivalent port.
To keep the comparison controlled, all graph-based systems use the same
supplied prebuilt graph indexes (degree 128 for the 1B experiments). The
artifact therefore evaluates FlashANNS's search pipeline on a fixed common
graph and does not separately reproduce its hardware-specific graph-degree
selection procedure.

## Build

From the repository root, build the baseline with:

```bash
cmake -S . -B build \
  -DCMAKE_BUILD_TYPE=Release \
  -DQUIVER_ENABLE_SPDK=ON \
  -DQUIVER_BUILD_STRAWMEN=OFF
cmake --build build -j"$(nproc)" --target flashanns_search
```

The artifact-wide build command `./ae/scripts/build.sh` also builds this
target. See [`README-AE.md`](../../README-AE.md) for CUDA, SPDK, dataset, index,
and SSD setup.

## Run and configure

A representative SPDK-backed invocation is:

```bash
SPDK_BASE_LBA=0 build/bin/flashanns_search \
  --index-dir /path/to/index \
  --query /path/to/query.u8bin \
  --ground-truth /path/to/groundtruth.ibin \
  --data-type uint8 \
  --topk 10 \
  --ef-search 45 \
  --repeat 20 \
  --pipe-width 2 \
  --poll-threads 6 \
  --num-blocks-list 108,216,324,432,540,648,756,864,972,1080 \
  --ssd-list-file /path/to/ssd_list.txt
```

The main tuning parameters are:

| Option | Meaning |
|---|---|
| `--ef-search` | Graph-search breadth; tune this to match recall. |
| `--num-blocks` / `--num-blocks-list` | Concurrent CUDA thread blocks (and statically assigned queries); sweep this to obtain the throughput-latency curve. |
| `--pipe-width` | Maximum number of outstanding graph-page reads per query. The paper comparison uses 2. |
| `--poll-threads` | Number of CPU threads polling I/O completion. The AE configuration uses 6. |
| `--repeat` | Number of passes over the query set. The paper reproduction uses 20. |
| `--ssd-list-file` | PCI addresses for the SPDK-backed SSDs. If omitted, select `--memory-backend heap` or `mmap`. |

Advanced SPDK queue sizing is exposed through `--spdk-submit-queue-cap`,
`--spdk-task-contexts`, and `--spdk-runner-io-contexts`. Defaults are printed
by `build/bin/flashanns_search --help`.
