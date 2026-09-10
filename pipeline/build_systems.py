"""migrate SOURCES.tsv + curated metadata + disk state into systems.tsv."""
import csv, datetime, pathlib, sys
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from systems_meta import SYSTEMS, DERIVED_PATTERN, DERIVED_FROM, NOTES

ROOT = pathlib.Path(__file__).resolve().parent.parent
COLS = ["system_id","domain","name","authority","url","license","license_status",
        "code_pattern","pattern_status","case_sensitive","raw_file","derived_from",
        "version","retrieved_at","notes"]

def flat(v):
    """systems.tsv is read by python, by awk and by eye, so it has to be strictly one
    record per physical line. the csv module would happily quote a field containing a
    newline and stay valid CSV, but `wc -l` and `awk -F'\t'` would then disagree with
    the parser about how many rows exist. collapsing whitespace is the right call for
    the prose fields, which are written across several source lines on purpose."""
    return " ".join(str(v).split()) if v is not None else ""

def check(rows):
    """prove the invariant instead of trusting it: the file must read back identical,
    on the same number of physical lines, with every line carrying every column."""
    text = (ROOT/"systems.tsv").read_text(encoding="utf-8")
    lines = text.splitlines()
    if len(lines) != len(rows) + 1:
        sys.exit(f"systems.tsv: {len(lines)} lines for {len(rows)} rows plus a header")
    for n, line in enumerate(lines, 1):
        got = line.split("\t")
        if len(got) != len(COLS):
            sys.exit(f"systems.tsv line {n}: {len(got)} columns, expected {len(COLS)}")
    with open(ROOT/"systems.tsv", encoding="utf-8") as fh:
        back = list(csv.DictReader(fh, delimiter="\t"))
    if back != rows:
        bad = next((r["system_id"] for r, b in zip(rows, back) if r != b), "?")
        sys.exit(f"systems.tsv does not round-trip, first mismatch at {bad}")

def sources():
    with open(ROOT/"SOURCES.tsv", encoding="utf-8") as fh:
        return {r["dom/id"]: r for r in csv.DictReader(fh, delimiter="\t")}

def raw_dir(sid):
    """a derived system has no raw of its own, it reads the parent's."""
    return ROOT/"data"/DERIVED_FROM.get(sid, sid)/"raw"

def raw_target(sid):
    entries = sorted(raw_dir(sid).iterdir())
    if not entries: sys.exit(f"{sid}: raw/ vazio")
    return str(entries[0].relative_to(ROOT))

def retrieved(sid):
    m = max(p.stat().st_mtime for p in raw_dir(sid).rglob("*") if p.is_file())
    return datetime.date.fromtimestamp(m).isoformat()

def main():
    src = sources()
    disagree = set(SYSTEMS) ^ set(src)
    if disagree: sys.exit(f"systems_meta and SOURCES.tsv disagree on: {sorted(disagree)}")
    unknown = (set(DERIVED_PATTERN) | set(DERIVED_FROM) | set(NOTES)) - set(SYSTEMS)
    if unknown: sys.exit(f"metadata references unknown systems: {sorted(unknown)}")

    rows = []
    for sid, (name, authority, pattern, cs, lic, status) in sorted(SYSTEMS.items()):
        rows.append({
            "system_id": sid, "domain": sid.split("/")[0], "name": name, "authority": authority,
            "url": src[sid]["url"], "license": lic, "license_status": status,
            "code_pattern": pattern,
            "pattern_status": "derived" if sid in DERIVED_PATTERN else "provisional",
            "case_sensitive": str(cs).lower(), "raw_file": raw_target(sid),
            "derived_from": DERIVED_FROM.get(sid, ""), "version": "",
            "retrieved_at": retrieved(sid), "notes": NOTES.get(sid, ""),
        })
    rows = [{k: flat(v) for k, v in r.items()} for r in rows]

    with open(ROOT/"systems.tsv", "w", newline="", encoding="utf-8") as fh:
        # QUOTE_NONE with no escapechar: the writer raises rather than quietly quoting a
        # field that would break the one-record-per-line contract.
        w = csv.DictWriter(fh, fieldnames=COLS, delimiter="\t", lineterminator="\n",
                           quoting=csv.QUOTE_NONE, quotechar=None)
        w.writeheader(); w.writerows(rows)

    check(rows)
    print(f"wrote systems.tsv: {len(rows)} systems, {len(COLS)} columns, round-trip verified")


if __name__ == "__main__":
    main()
