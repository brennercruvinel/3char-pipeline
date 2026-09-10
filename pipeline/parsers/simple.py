"""json and plain text sources."""
import json, pathlib, re, sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
from core import parser, row, ROOT

def _load(path):
    return json.loads((ROOT/path).read_text(encoding="utf-8"))

def _lines(path, comment="#"):
    for l in (ROOT/path).read_text(encoding="utf-8", errors="replace").splitlines():
        l = l.rstrip()
        if not l.strip() or (comment and l.lstrip().startswith(comment)): continue
        yield l

# ------------------------------------------------------------------------ json

@parser("cmp/css")
def css_functions(path, sysrow):
    for name, v in _load(path).items():
        yield row("cmp/css", name.removesuffix("()"), name,
                  extra={"syntax": v.get("syntax"), "status": v.get("status"),
                         "groups": v.get("groups"), "mdn_url": v.get("mdn_url")})

@parser("cmp/hex")
def css_colors(path, sysrow):
    for name, hexval in _load(path).items():
        yield row("cmp/hex", name, hexval, extra={"hex": hexval})

@parser("cmp/ext")
def file_extensions(path, sysrow):
    for ext, cats in _load(path).items():
        yield row("cmp/ext", ext, "", extra={"categories": cats})

@parser("bio/pdb")
def pdb_ids(path, sysrow):
    for eid in _load(path):
        yield row("bio/pdb", eid, "")

@parser("fin/tck")
def sec_tickers(path, sysrow):
    seen = set()
    for v in _load(path).values():
        t = (v.get("ticker") or "").strip()
        if not t or t in seen: continue
        seen.add(t)
        yield row("fin/tck", t, v.get("title") or "", extra={"cik": v.get("cik_str")})

@parser("wrt/abj")
def hebrew(path, sysrow):
    """the file is grouped by kind. the code is the character, the name is the label,
    and a letter with a final form carries it as an alias."""
    for group, entries in _load(path).items():
        for name, ch in entries.items():
            forms = ch if isinstance(ch, list) else [ch]
            yield row("wrt/abj", forms[0], name, aliases=forms[1:],
                      extra={"group": group,
                             "codepoints": [f"U+{ord(c):04X}" for c in "".join(forms)]})

@parser("lng/mdy")
def cldr_months(path, sysrow):
    cal = _load(path)["main"]["en"]["dates"]["calendars"]["gregorian"]["months"]["format"]
    wide, abbr, narrow = cal["wide"], cal["abbreviated"], cal["narrow"]
    for k in sorted(wide, key=int):
        yield row("lng/mdy", abbr[k], wide[k],
                  aliases=[narrow[k], k], extra={"month_number": int(k)})

# ------------------------------------------------------------------ plain text

@parser("trp/tld")
def tlds(path, sysrow):
    for line in _lines(path):
        yield row("trp/tld", line.strip(), "",
                  extra={"punycode": True} if line.startswith("XN--") else None)

@parser("cmp/git")
def git_commands(path, sysrow):
    for line in _lines(path):
        parts = line.split()
        if len(parts) < 2 or not parts[0].startswith("git-"): continue
        yield row("cmp/git", parts[0].removeprefix("git-"), "",
                  extra={"category": parts[1], "attributes": parts[2:] or None})

@parser("lng/i15")
def iso15924(path, sysrow):
    for line in _lines(path):
        f = line.split(";")
        if len(f) < 4 or not f[0].strip(): continue
        yield row("lng/i15", f[0], f[2], aliases=[f[4]] if len(f) > 4 and f[4] else [],
                  extra={"numeric": f[1], "name_fr": f[3],
                         "unicode_version": f[5] if len(f) > 5 else None,
                         "date": f[6] if len(f) > 6 else None})

# ------------------------------------------------------------------ record-jar

def record_jar(path):
    """the BCP 47 registry format: fields separated by %%, continuations indented."""
    recs, cur, last = [], {}, None
    for raw in (ROOT/path).read_text(encoding="utf-8").splitlines():
        if raw.strip() == "%%":
            if cur: recs.append(cur)
            cur, last = {}, None
        elif raw[:1] in (" ", "\t") and last:
            cur[last][-1] += " " + raw.strip()
        elif ":" in raw:
            k, v = raw.split(":", 1); last = k.strip()
            cur.setdefault(last, []).append(v.strip())
    if cur: recs.append(cur)
    return recs

def _subtag_row(sid, r):
    code = (r.get("Subtag") or r.get("Tag") or [""])[0]
    if not code: return None
    return row(sid, code, (r.get("Description") or [""])[0],
               status="deprecated" if "Deprecated" in r else None,
               aliases=(r.get("Description") or [])[1:],
               extra={"type": (r.get("Type") or [None])[0],
                      "added": (r.get("Added") or [None])[0],
                      "scope": (r.get("Scope") or [None])[0],
                      "macrolanguage": (r.get("Macrolanguage") or [None])[0],
                      "preferred_value": (r.get("Preferred-Value") or [None])[0],
                      "prefix": r.get("Prefix")})

@parser("lng/b47")
def bcp47(path, sysrow):
    for r in record_jar(path):
        if "File-Date" in r and len(r) == 1: continue
        out = _subtag_row("lng/b47", r)
        if out: yield out

@parser("lng/i63")
def bcp47_three_letter(path, sysrow):
    """derived from the same registry as lng/b47, narrowed to three-letter languages.
    see the note on this system in systems.tsv for why this is not ISO 639-3."""
    for r in record_jar(path):
        if (r.get("Type") or [None])[0] != "language": continue
        out = _subtag_row("lng/i63", r)
        if out and len(out["code"]) == 3: yield out
