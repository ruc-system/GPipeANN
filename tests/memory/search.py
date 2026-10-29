#!/usr/bin/env python3
"""Check real GPU search against brute force using a tiny synthetic index.

Only Python's standard library is required. No datasets, index builder, SPDK,
hugepages, or SSD device access are used. GPU timings are not benchmarks.
"""

import argparse
import math
import os
from pathlib import Path
import re
import shlex
import struct
import subprocess
import tempfile


def matrix(rows, cols, values, code):
    return struct.pack("<ii", rows, cols) + struct.pack(f"<{rows * cols}{code}", *values)


def fixture(root, dtype, dims, entry_query=False, navigation=False, count=32):
    chunks = 32
    code = {"uint8": "B", "int8": "b", "float": "f"}[dtype]
    decode = lambda value: value / 8 if dtype == "float" else value - 32 if dtype == "int8" else value
    codes = [[(i * 7 + d * 11) % 64 for d in range(dims)] for i in range(count)]
    vectors = [[decode(value) for value in row] for row in codes]
    query_ids = [13 if navigation else 0] if entry_query else [3, 7, 13, 21, 25, 31]
    queries = [[value + (d + 1) / 1024 for d, value in enumerate(vectors[i])]
               for i in query_ids]
    (root / "query.fbin").write_bytes(matrix(len(queries), dims,
                                           [v for row in queries for v in row], "f"))
    # Exact codewords keep this a search/I/O test rather than an ANN quality test.
    sections = [matrix(256, dims,
                       [decode((i + d * 11) % 64) for i in range(256) for d in range(dims)], "f"),
                matrix(dims, 1, [0] * dims, "f"),
                matrix(chunks + 1, 1, [i * dims // chunks for i in range(chunks + 1)], "i")]
    offsets, cursor = [], 8 + 4 * 8
    for section in sections:
        offsets.append(cursor)
        cursor += len(section)
    offsets.append(cursor)
    (root / "tiny_pq_pivots.bin").write_bytes(
        matrix(4, 1, offsets, "Q") + b"".join(sections))
    (root / "tiny_pq_compressed.bin").write_bytes(
        matrix(count, chunks, [(i * 7) % 64 for i in range(count) for _ in range(chunks)], "B"))
    node_size = dims * struct.calcsize(code) + count * 4
    nodes_per_page = 4096 // node_size
    sectors = math.ceil(node_size / 4096)
    header = matrix(8, 1, [count, dims, 0, node_size, nodes_per_page, 0, 0, 0], "Q")
    pages = bytearray((math.ceil(count / nodes_per_page) if nodes_per_page else count * sectors) * 4096)
    for i, vector in enumerate(vectors):
        neighbors = [j for j in range(count) if j != i]
        node = (struct.pack(f"<{dims}{code}", *vector)
                + struct.pack("<I", len(neighbors))
                + struct.pack(f"<{len(neighbors)}I", *neighbors))
        offset = ((i // nodes_per_page) * 4096 + (i % nodes_per_page) * node_size
                  if nodes_per_page else i * sectors * 4096)
        pages[offset:offset + node_size] = node
    (root / "tiny_disk.index").write_bytes(header.ljust(4096, b"\0") + pages)
    if navigation:
        nav = root / "nav"
        nav.mkdir()
        (nav / "nav_index.data").write_bytes(matrix(
            count, dims, [value for vector in vectors for value in vector], code))
        (nav / "map.txt").write_text("".join(f"{i}\n" for i in range(count)))
        # Match the navigation kernel's 28-neighbor graph contract.
        graph = struct.pack("<QIIQ", 24 + count * 29 * 4, 28, 0, 0)
        graph += b"".join(struct.pack("<29I", 28, *[(i + j) % count for j in range(1, 29)])
                          for i in range(count))
        (nav / "nav_index").write_bytes(graph)
    return vectors, queries


def read_results(path, code, rows, cols):
    data = path.read_bytes()
    if len(data) < 8 or struct.unpack_from("<ii", data) != (rows, cols):
        raise AssertionError(f"Invalid result dimensions: {path}")
    if len(data) != 8 + rows * cols * 4:
        raise AssertionError(f"Invalid result size: {path}")
    return struct.unpack_from(f"<{rows * cols}{code}", data, 8)


def check_results(prefix, vectors, queries, repeat, topk):
    rows = len(queries) * repeat
    ids = read_results(Path(str(prefix) + "_ids.bin"), "i", rows, topk)
    distances = read_results(Path(str(prefix) + "_distances.bin"), "f", rows, topk)
    all_distances = []
    for row in range(rows):
        query = queries[row % len(queries)]
        exact = [sum((a - b) ** 2 for a, b in zip(query, vector)) for vector in vectors]
        expected = sorted(exact)[:topk]
        found_ids = ids[row * topk:(row + 1) * topk]
        found_distances = distances[row * topk:(row + 1) * topk]
        if len(set(found_ids)) != topk or any(i < 0 or i >= len(vectors) for i in found_ids):
            raise AssertionError(f"Invalid/duplicate neighbors in row {row}: {found_ids}")
        for rank, (index, distance) in enumerate(zip(found_ids, found_distances)):
            if not (math.isfinite(distance)
                    and math.isclose(distance, exact[index], rel_tol=2e-5, abs_tol=1e-4)
                    and math.isclose(distance, expected[rank], rel_tol=2e-5, abs_tol=1e-4)):
                raise AssertionError(f"Wrong result row={row} rank={rank}: "
                                     f"id={index}, distance={distance}, expected={expected[rank]}")
        all_distances.extend(found_distances)
    return all_distances


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--binary", type=Path, required=True)
    parser.add_argument("--engine", choices=["gpipeann", "flashanns", "gustann"], default="gpipeann")
    parser.add_argument("--data-type", choices=["uint8", "int8", "float"], required=True)
    parser.add_argument("--dimensions", type=int, choices=[32, 1536], default=32)
    parser.add_argument("--node-count", type=int, choices=[32, 64], default=32)
    parser.add_argument("--topk", type=int, default=5)
    parser.add_argument("--navigation", action="store_true")
    parser.add_argument("--override-index", action="store_true")
    parser.add_argument("--entry-query", action="store_true",
                        help="Exercise the bootstrap-entry duplicate-neighbor regression")
    parser.add_argument("--per-query-ef", action="store_true",
                        help="Require the optional per-query ef feature; never silently skip it")
    parser.add_argument("--output-dir", type=Path,
                        help="Keep fixtures, logs and binary results in a unique run directory")
    args = parser.parse_args()
    if not 1 <= args.topk <= args.node_count:
        parser.error("topk must be within the fixture's node count")
    binary = args.binary.resolve(strict=True)
    # Host affinity is fixed by the production search launcher.
    required_cpus = {21}
    if hasattr(os, "sched_getaffinity") and not required_cpus <= os.sched_getaffinity(0):
        parser.error("The search launcher requires CPU 21 in this process's affinity mask")
    if args.output_dir:
        args.output_dir.mkdir(parents=True, exist_ok=True)
        temporary = tempfile.mkdtemp(prefix="run-", dir=args.output_dir.resolve())
        from contextlib import nullcontext
        context = nullcontext(temporary)
    else:
        context = tempfile.TemporaryDirectory(prefix="gpipeann-memory-search-")
    with context as temporary:
        root = Path(temporary)
        vectors, queries = fixture(root, args.data_type, args.dimensions, args.entry_query,
                                   args.navigation, args.node_count)
        override = root / "blocks.index"
        if args.override_index:
            disk_index = root / "tiny_disk.index"
            data = disk_index.read_bytes()
            override.write_bytes(data)
            disk_index.write_bytes(data[:4096] + bytes(len(data) - 4096))
        ground_truth = [index for query in queries for index in sorted(
            range(len(vectors)), key=lambda i: sum(
                (a - b) ** 2 for a, b in zip(query, vectors[i])))[:args.topk]]
        (root / "gt.bin").write_bytes(matrix(len(queries), args.topk, ground_truth, "i"))
        mapping = root / "mapping.csv"
        mapping.write_text("query_id,ef_search\n" + "".join(
            f"{i},{args.node_count + i * 4}\n" for i in range(len(queries))))
        reference = None
        failures = []
        variants = [(q, 2) for q in [1, 2, 4]] if args.engine == "gpipeann" else [(1, w) for w in [1, 2]]
        for q, width in variants:
            label = f"{args.engine} Q={q} W={width}"
            prefix = root / f"q{q}-w{width}"
            command = [str(binary), "--index-dir", str(root),
                       "--query", str(root / "query.fbin"), "--data-type", args.data_type,
                       "--ground-truth", str(root / "gt.bin"),
                       "--topk", str(args.topk), "--ef-search", str(args.node_count + 32),
                       "--repeat", "3", "--pipe-width", str(width)]
            if args.engine == "gustann":
                command += ["--mini-batch", "2", "--worker-threads", "1", "--runner-contexts", "2"]
            else:
                command += ["--num-blocks", "2", "--poll-threads", "1"]
            if args.engine == "gpipeann":
                command += ["--queries-per-block", str(q), "--early-exit-policy", "none",
                            "--result-prefix", str(prefix)]
            if args.per_query_ef:
                command += ["--query-ef-csv", str(mapping)]
            if args.override_index:
                command += ["--memory-index-file", str(override)]
            # Ignore machine-local tuning so every invocation uses the same setup.
            env = {key: value for key, value in os.environ.items()
                   if not key.startswith(("GPIPEANN_", "SPDK_", "CPU_POLL_"))}
            log = prefix.with_suffix(".log")
            try:
                result = subprocess.run(command, env=env, capture_output=True,
                                        text=True, timeout=30)
                log.write_text(shlex.join(command) + "\n" + result.stdout + result.stderr)
                if result.returncode:
                    raise AssertionError(f"Search exited with status {result.returncode}")
                if args.engine == "gpipeann":
                    distances = check_results(prefix, vectors, queries, 3, args.topk)
                else:
                    recall = re.search(rf"Recall @ {args.topk}:\s*([0-9.]+)", result.stdout)
                    if not recall or float(recall.group(1)) != 1.0:
                        raise AssertionError(f"Baseline search must return exact Recall@{args.topk}=1")
                    distances = []
            except subprocess.TimeoutExpired as error:
                log.write_text(shlex.join(command) + "\nTimed out after 30 seconds\n"
                               + str(error.stdout or "") + str(error.stderr or ""))
                failures.append(f"{label}: timeout; log: {log}")
                continue
            except (AssertionError, FileNotFoundError) as error:
                failures.append(f"{label}: {error}; log: {log}")
                continue
            if reference is not None and any(
                    not math.isclose(a, b, rel_tol=2e-5, abs_tol=1e-4)
                    for a, b in zip(reference, distances)):
                failures.append(f"{label}: Q variants disagree; log: {log}")
                continue
            reference = distances
            print(f"PASS {args.data_type} {label}: {len(queries) * 3} queries, exact top-{args.topk}")
        if failures:
            raise AssertionError("\n" + "\n".join(failures))


if __name__ == "__main__":
    main()
