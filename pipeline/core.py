"""shared plumbing: the canonical row, the parser registry, csv helpers."""
import csv, json, pathlib, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
CANON = ["system_id","code","label","description","parent_code","status","aliases","extra"]

PARSERS = {}

def parser(*system_ids):
    """register a callable as the parser for one or more systems."""
    def deco(fn):
        for sid in system_ids:
            if sid in PARSERS:
                raise RuntimeError(f"{sid} already has a parser ({PARSERS[sid].__name__})")
            PARSERS[sid] = fn
        return fn
    return deco

def row(system_id, code, label, description=None, parent_code=None,
        status=None, aliases=None, extra=None):
    """one canonical row. empty strings collapse to None so parquet stays honest
    about the difference between 'the source said nothing' and 'the source said ""'."""
    clean = lambda v: (v.strip() or None) if isinstance(v, str) else v
    return {
        "system_id": system_id,
        "code": str(code).strip(),
        "label": (clean(label) or ""),
        "description": clean(description),
        "parent_code": clean(parent_code),
        "status": clean(status),
        "aliases": [a for a in (aliases or []) if a and str(a).strip()],
        "extra": json.dumps(
            {k: v for k, v in (extra or {}).items() if v not in (None, "", [])},
            ensure_ascii=False, sort_keys=True) if extra else None,
    }

def systems():
    with open(ROOT/"systems.tsv", encoding="utf-8") as fh:
        return {r["system_id"]: r for r in csv.DictReader(fh, delimiter="\t")}

def read_csv(path, delimiter=",", header=True, comment=None, encoding="utf-8-sig",
             fieldnames=None):
    """yield dicts. handles the BOM, comment prefixes and headerless files."""
    with open(ROOT/path, encoding=encoding, newline="") as fh:
        lines = [l for l in fh if not (comment and l.lstrip().startswith(comment))]
    rd = csv.DictReader(lines, delimiter=delimiter, fieldnames=fieldnames) if (header or fieldnames) \
         else csv.reader(lines, delimiter=delimiter)
    if not header and fieldnames:
        pass
    for r in rd:
        yield r
