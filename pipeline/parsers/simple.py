"""json and plain text sources."""
import json, pathlib, re, sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
from core import parser, row, ROOT, label_file

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
    """the list gives each extension's categories. the name comes, in order, from the shared MIME-info
    database (the comment of the MIME type whose glob is *.ext), from GitHub Linguist for extensions the
    list files under code, and from mime-db as the bare media type; otherwise from the categories."""
    xml = label_file(path, "cmp/ext", 0).read_text(encoding="utf-8")
    shared = {}
    for mtype, body in re.findall(r'<mime-type type="([^"]+)">(.*?)</mime-type>', xml, re.S):
        c = re.search(r"<comment>([^<]+)</comment>", body)
        for g in re.findall(r'<glob pattern="\*\.([^"]+)"', body):
            if c: shared.setdefault(g.lower(), (c.group(1), mtype))
    linguist, lang, in_ext = {}, None, False
    for line in label_file(path, "cmp/ext", 1).read_text(encoding="utf-8").splitlines():
        if re.match(r"^[^\s#].*:\s*$", line): lang, in_ext = line.strip()[:-1].strip('"'), False; continue
        if line.startswith("  extensions:"): in_ext = True; continue
        if re.match(r"^  \w", line): in_ext = False
        m = re.match(r'^  - "\.([^"]+)"', line)
        if in_ext and m: linguist.setdefault(m.group(1).lower(), lang)
    media = {}
    for mtype, v in json.loads(label_file(path, "cmp/ext", 2).read_text(encoding="utf-8")).items():
        for e in v.get("extensions", []): media.setdefault(e.lower(), mtype)
    for ext, cats in _load(path).items():
        e = ext.lower()
        if e in shared:
            label, source = shared[e][0], "shared-mime-info"
        elif e in linguist and "code" in cats:
            label, source = f"{linguist[e]} source file", "linguist"
        elif media.get(e, "application/octet-stream") != "application/octet-stream":
            label, source = f"File of media type {media[e]}", "mime-db"
        else:
            label, source = " and ".join(cats).capitalize() + " file", "categories"
        yield row("cmp/ext", ext, label, extra={"categories": cats, "media_type": (shared.get(e) or (None, media.get(e)))[1],
                                                "label_source": source})

@parser("bio/pdb")
def pdb_ids(path, sysrow):
    """the RCSB holdings list gives the IDs; the wwPDB entries index gives each entry's title
    (COMPOUND), classification, deposition date, method and resolution."""
    meta = {}
    with open(label_file(path, "bio/pdb"), encoding="utf-8", errors="replace") as fh:
        for line in fh:
            f = line.rstrip("\n").split("\t")
            if len(f) < 8 or not re.fullmatch(r"[0-9][A-Z0-9]{3}", f[0]): continue
            m, d, y = (f[2].split("/") + ["", "", ""])[:3]
            meta[f[0]] = {"label": f[3], "classification": f[1] or None,
                          "deposited": f"{'19' if int(y or 0) > 70 else '20'}{y}-{m}-{d}" if y else None,
                          "method": f[7] or "X-RAY DIFFRACTION", "resolution": f[6] or None}
    # entries the index does not carry: current ones from the RCSB API, withdrawn ones from the
    # wwPDB list of removed entries, which keeps their title and the entry that superseded them
    import gzip
    for e in json.loads(label_file(path, "bio/pdb", 2).read_text(encoding="utf-8"))["data"]["entries"]:
        res = (e.get("rcsb_entry_info") or {}).get("resolution_combined") or []
        meta.setdefault(e["rcsb_id"], {
            "label": e["struct"]["title"], "classification": (e.get("struct_keywords") or {}).get("pdbx_keywords"),
            "deposited": ((e.get("rcsb_accession_info") or {}).get("deposit_date") or "")[:10] or None,
            "method": "; ".join(x["method"] for x in e.get("exptl") or []) or None,
            "resolution": str(res[0]) if res else None})
    removed = json.load(gzip.open(label_file(path, "bio/pdb", 1), "rt", encoding="utf-8"))
    for eid in _load(path):
        m = meta.get(eid)
        status, gone = None, removed.get(eid)
        if m is None and gone:
            status = "obsolete"
            m = {"label": gone["title"], "deposited": (gone.get("deposit_date") or "")[:10] or None,
                 "obsolete_date": (gone.get("obsolete_date") or "")[:10] or None,
                 "superseded_by": gone.get("superseded_by") or None}
        m = m or {}
        yield row("bio/pdb", eid, m.get("label", ""), status=status,
                  extra={k: v for k, v in m.items() if k != "label"} or None)

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
    """the IANA list gives the TLDs; the Root Zone Database gives each one's type and the
    organisation that manages it, which is the only name IANA attaches to a TLD."""
    db = {}
    html = label_file(path, "trp/tld").read_text(encoding="utf-8")
    for slug, kind, manager in re.findall(
            r'href="/domains/root/db/([^"]+)\.html">[^<]*</a></span></td>\s*<td>([^<]*)</td>\s*<td>([^<]*)</td>', html):
        db[slug.upper()] = (kind.strip(), " ".join(manager.split()))
    for line in _lines(path):
        tld = line.strip()
        kind, manager = db.get(tld, (None, ""))
        yield row("trp/tld", tld, manager,
                  extra={"punycode": True if tld.startswith("XN--") else None, "type": kind})

@parser("cmp/git")
def git_commands(path, sysrow):
    """command-list.txt gives the commands; the NAME line of each command's manual page, in the
    source tree of the same commit, gives its one-line description ("git-add - Add file contents...")."""
    import tarfile
    names = {}
    with tarfile.open(label_file(path, "cmp/git")) as tf:
        for m in tf.getmembers():
            hit = re.search(r"/Documentation/(git-[a-z0-9-]+)\.(?:adoc|txt)$", m.name)
            if not hit: continue
            text = tf.extractfile(m).read().decode("utf-8", "replace")
            line = re.search(r"^NAME\n-+\n(\S+)\s+-\s+(.+)$", text, re.M)
            if line: names[hit.group(1)] = line.group(2).strip()
    for line in _lines(path):
        parts = line.split()
        if len(parts) < 2 or not parts[0].startswith("git-"): continue
        yield row("cmp/git", parts[0].removeprefix("git-"), names.get(parts[0], ""),
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
