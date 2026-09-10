"""test every emitted code against its system's code_pattern. fail the build on mismatch."""
import pathlib, re, sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import pyarrow.parquet as pq
from core import ROOT, systems
from known_exceptions import KNOWN

CONFIRMED = pathlib.Path(__file__).resolve().parent/"pattern_confirmed.txt"

def main():
    sysmap = systems()
    bad_total = 0; clean = []
    for sid, s in sorted(sysmap.items()):
        f = ROOT/"data"/f"{sid}.parquet"
        if not f.exists(): continue
        codes = pq.read_table(f, columns=["code"])["code"].to_pylist()
        rx = re.compile(s["code_pattern"])
        allowed = KNOWN.get(sid, {})
        bad = [c for c in codes if not rx.fullmatch(c or "") and c not in allowed]
        excused = sorted({c for c in codes if c in allowed})
        dupes = len(codes) - len(set(codes))
        if bad:
            bad_total += len(bad)
            print(f"FAIL {sid:<10} {len(bad):>6,}/{len(codes):,} codes fail {s['code_pattern']}",
                  file=sys.stderr)
            print(f"     sample: {bad[:8]}", file=sys.stderr)
        else:
            clean.append(sid)
            note = f"  ({dupes:,} duplicate codes)" if dupes else ""
            for c in excused:
                print(f"     known exception {c}: {allowed[c]}")
            print(f"ok   {sid:<10} {len(codes):>8,} codes match {s['code_pattern']}{note}")
    CONFIRMED.write_text("\n".join(clean) + "\n")
    print(f"\n{len(clean)} systems clean, {bad_total:,} failing codes")
    return 1 if bad_total else 0

if __name__ == "__main__":
    sys.exit(main())
