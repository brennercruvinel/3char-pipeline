"""Deposit manifest: sha256, bytes and row count of every file in a 3char snapshot.

usage: python manifest.py <3char_root> <MANIFEST.tsv>
"""
import glob
import hashlib
import os
import sys

import pyarrow.parquet as pq


def main(root, out):
    files = sorted(glob.glob(f"{root}/data/*/*.parquet")) + [f"{root}/systems.parquet", f"{root}/README.md", f"{root}/CHANGELOG.md"]
    rows_total = 0
    with open(out, "w", encoding="utf-8") as fh:
        fh.write("path\tsha256\tbytes\trows\n")
        for p in files:
            rel = os.path.relpath(p, root); b = open(p, "rb").read()
            rows = pq.read_metadata(p).num_rows if p.endswith(".parquet") else ""
            if rel.startswith("data/"): rows_total += rows
            fh.write(f"{rel}\t{hashlib.sha256(b).hexdigest()}\t{len(b)}\t{rows}\n")
    print(len(files), "files;", rows_total, "data rows")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
