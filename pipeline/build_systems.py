"""Build systems.tsv from history/SOURCES.tsv, the curated metadata in systems_meta.py and the raw files on disk."""
import csv, pathlib, sys
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from systems_meta import SYSTEMS, DERIVED_PATTERN, DERIVED_FROM, NOTES, LABEL_SOURCES
LABEL_FILES = {name for files in LABEL_SOURCES.values() for name, _, _ in files}
from versions import version_of

ROOT = pathlib.Path(__file__).resolve().parent.parent
COLS = ["system_id","domain","name","authority","url","license","license_status",
        "code_pattern","pattern_status","case_sensitive","raw_file","derived_from",
        "version","retrieved_at","notes"]

def flat(v):
    """Collapse whitespace so that each record stays on one physical line.

    systems.tsv is read by Python, by awk and by eye. The csv module would quote a field
    containing a newline and still produce valid CSV, but `wc -l` and `awk -F'\t'` would
    then disagree with the parser about the number of rows. The prose fields are written
    across several source lines on purpose, so collapsing their whitespace is safe."""
    return " ".join(str(v).split()) if v is not None else ""

def check(rows):
    """Verify the written file: it must read back identically, with one physical line per
    row and every column on every line."""
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
    with open(ROOT/"history"/"SOURCES.tsv", encoding="utf-8") as fh:
        return {r["system_id"]: r for r in csv.DictReader(fh, delimiter="\t")}

def raw_dir(sid):
    """A derived system has no raw file of its own and reads its parent's."""
    return ROOT/"data"/DERIVED_FROM.get(sid, sid)/"raw"

def raw_target(sid, src):
    """The source file named in SOURCES.tsv; a label source next to it is never the raw file."""
    named = raw_dir(sid)/src[DERIVED_FROM.get(sid, sid)]["file"]
    if named.exists(): return str(named.relative_to(ROOT))
    entries = sorted(p for p in raw_dir(sid).iterdir() if p.name not in LABEL_FILES)
    if not entries: sys.exit(f"{sid}: raw/ is empty")
    return str(entries[0].relative_to(ROOT))

def retrieved(sid, src):
    """The fetch date recorded in SOURCES.tsv. File modification times are not used: copying a
    raw file resets them, and the date they gave was the copy, not the retrieval."""
    d = src[DERIVED_FROM.get(sid, sid)].get("retrieved_at", "")
    if not d: sys.exit(f"{sid}: no retrieved_at in SOURCES.tsv")
    return d

def notes(sid):
    """Curator notes, plus the URL of the file the labels come from when it is not the main source."""
    n = NOTES.get(sid, "")
    for name, url, date in LABEL_SOURCES.get(sid, []):
        n = (n + " " if n else "") + f"labels from {url}, retrieved {date}."
    return n

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
            "case_sensitive": str(cs).lower(), "raw_file": raw_target(sid, src),
            "derived_from": DERIVED_FROM.get(sid, ""),
            "version": version_of(sid, ROOT/raw_target(sid, src)),
            "retrieved_at": retrieved(sid, src), "notes": notes(sid),
        })
    rows = [{k: flat(v) for k, v in r.items()} for r in rows]

    with open(ROOT/"systems.tsv", "w", newline="", encoding="utf-8") as fh:
        # QUOTE_NONE without an escapechar makes the writer raise instead of silently quoting
        # a field that would break the one-record-per-line contract.
        w = csv.DictWriter(fh, fieldnames=COLS, delimiter="\t", lineterminator="\n",
                           quoting=csv.QUOTE_NONE, quotechar=None)
        w.writeheader(); w.writerows(rows)

    check(rows)
    print(f"wrote systems.tsv: {len(rows)} systems, {len(COLS)} columns, round-trip verified")


if __name__ == "__main__":
    main()
