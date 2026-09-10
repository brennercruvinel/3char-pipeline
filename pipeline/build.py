"""run every registered parser, write one parquet per system plus systems.parquet."""
import argparse, importlib, pathlib, sys, time
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent/"parsers"))
import pyarrow as pa, pyarrow.parquet as pq
from core import ROOT, CANON, PARSERS, systems

SCHEMA = pa.schema([
    ("system_id", pa.string()), ("code", pa.string()), ("label", pa.string()),
    ("description", pa.string()), ("parent_code", pa.string()), ("status", pa.string()),
    ("aliases", pa.list_(pa.string())), ("extra", pa.string()),
])

def load_parsers():
    d = pathlib.Path(__file__).resolve().parent/"parsers"
    for f in sorted(d.glob("*.py")):
        if f.stem != "__init__":
            importlib.import_module(f.stem)

def build_one(sid, sysrow):
    fn = PARSERS[sid]
    rows = list(fn(sysrow["raw_file"], sysrow))
    if not rows:
        raise RuntimeError(f"{sid}: parser emitted nothing")
    tbl = pa.Table.from_pylist([{k: r[k] for k in CANON} for r in rows], schema=SCHEMA)
    out = ROOT/"data"/f"{sid}.parquet"
    out.parent.mkdir(parents=True, exist_ok=True)
    pq.write_table(tbl, out, compression="zstd")
    return len(rows), out.stat().st_size

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("only", nargs="*", help="system ids to build, default all registered")
    a = ap.parse_args()
    load_parsers()
    sysmap = systems()
    todo = a.only or sorted(PARSERS)
    missing = [s for s in todo if s not in PARSERS]
    if missing: sys.exit(f"no parser registered for: {missing}")

    total_rows = 0; failed = []
    for sid in todo:
        t0 = time.time()
        try:
            n, nbytes = build_one(sid, sysmap[sid])
        except Exception as e:
            print(f"  FAIL {sid}: {type(e).__name__}: {e}", file=sys.stderr)
            failed.append(sid); continue
        total_rows += n
        print(f"  {sid:<10} {n:>8,} codes  {nbytes/1024:>8.1f} KB  {time.time()-t0:>5.1f}s")

    unbuilt = sorted(set(sysmap) - set(PARSERS))
    print(f"\n{len(todo)-len(failed)}/{len(todo)} systems, {total_rows:,} codes")
    if unbuilt: print(f"{len(unbuilt)} systems still without a parser: {' '.join(unbuilt)}")
    return 1 if failed else 0

if __name__ == "__main__":
    sys.exit(main())
