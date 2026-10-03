#!/usr/bin/env python3
"""Remove uncompleted points without deleting completed sweep results."""
import argparse
import csv
import json
import os
from pathlib import Path
import tempfile

FILES = ("metrics.csv", "breakdown.csv", "cta_samples.csv", "hop_samples.csv")


def snapshot(directory, state):
    state.write_text(json.dumps({name: (directory / name).stat().st_size
                                if (directory / name).exists() else 0
                                for name in FILES}))


def recover(directory, state, stem, axis, completed, all_done):
    offsets = json.loads(state.read_text())
    for name in FILES:
        path = directory / name
        if not path.exists():
            continue
        with path.open(newline="") as source:
            reader = csv.DictReader(source)
            fields = reader.fieldnames
            if not fields:
                continue
            if axis not in fields:
                # Older sample tables lack the occupancy key. Never publish
                # samples from an incomplete attempt as if they were valid.
                if not all_done:
                    if path.stat().st_size > offsets.get(name, 0):
                        # Preserve ambiguous raw samples for inspection; the
                        # .raw suffix keeps plotters from treating them as
                        # successfully attributed measurements.
                        archive = Path(tempfile.mkdtemp(dir=directory, prefix=".unassigned-samples-"))
                        os.link(path, archive / (name + ".raw"))
                    fd, temporary = tempfile.mkstemp(dir=directory, prefix=".recovery-")
                    os.fchmod(fd, path.stat().st_mode & 0o777)
                    try:
                        with path.open("rb") as raw, os.fdopen(fd, "wb") as output:
                            remaining = offsets.get(name, 0)
                            while remaining:
                                chunk = raw.read(min(remaining, 1024 * 1024))
                                if not chunk:
                                    break
                                output.write(chunk)
                                remaining -= len(chunk)
                        os.replace(temporary, path)
                    finally:
                        if os.path.exists(temporary):
                            os.unlink(temporary)
                continue
            fd, temporary = tempfile.mkstemp(dir=directory, prefix=".recovery-")
            os.fchmod(fd, path.stat().st_mode & 0o777)
            try:
                with os.fdopen(fd, "w", newline="") as output:
                    writer = csv.DictWriter(output, fieldnames=fields)
                    writer.writeheader()
                    for row in reader:
                        if row.get("stem") != stem or row.get(axis) in completed:
                            writer.writerow(row)
                os.replace(temporary, path)
            finally:
                if os.path.exists(temporary):
                    os.unlink(temporary)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("snapshot", "recover"))
    parser.add_argument("directory", type=Path)
    parser.add_argument("state", type=Path)
    parser.add_argument("--stem", default="")
    parser.add_argument("--axis", default="")
    parser.add_argument("--completed", default="")
    parser.add_argument("--all-done", action="store_true")
    args = parser.parse_args()
    if args.mode == "snapshot":
        snapshot(args.directory, args.state)
    else:
        recover(args.directory, args.state, args.stem, args.axis,
                set(args.completed.split(",")), args.all_done)


if __name__ == "__main__":
    main()
