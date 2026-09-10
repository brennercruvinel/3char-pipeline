"""migrate SOURCES.tsv + curated metadata + disk state into systems.tsv."""
import csv, datetime, pathlib, sys
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from systems_meta import SYSTEMS, DERIVED_PATTERN, DERIVED_FROM, NOTES

ROOT = pathlib.Path(__file__).resolve().parent.parent
COLS = ["system_id","domain","name","authority","url","license","license_status",
        "code_pattern","pattern_status","case_sensitive","raw_file","derived_from",
        "version","retrieved_at","notes"]

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

with open(ROOT/"systems.tsv", "w", newline="", encoding="utf-8") as fh:
    w = csv.DictWriter(fh, fieldnames=COLS, delimiter="\t", lineterminator="\n")
    w.writeheader(); w.writerows(rows)
print(f"wrote systems.tsv: {len(rows)} systems")
