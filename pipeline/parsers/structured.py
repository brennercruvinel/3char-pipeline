"""structured text: flat files, headers, grammars, help docs, ASN.1."""
import html, pathlib, re, sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
from core import parser, row, ROOT

def _text(path, enc="utf-8"):
    return (ROOT/path).read_text(encoding=enc, errors="replace")

# ------------------------------------------------------------ swissprot flat

@parser("bio/ec")
def enzyme(path, sysrow):
    """ExPASy flat file. records end at //, fields are two letter codes in column 0."""
    rec = {}
    for line in _text(path).splitlines():
        if line.startswith("//"):
            if rec.get("ID"):
                yield _ec_row(rec)
            rec = {}; continue
        if len(line) < 5 or line[:2] == "CC" and not rec.get("ID"): continue
        tag, val = line[:2], line[5:].strip()
        if tag in ("ID","DE","AN","CA","CC","DR","PR"):
            rec.setdefault(tag, []).append(val)
    if rec.get("ID"): yield _ec_row(rec)

def _ec_row(rec):
    code = rec["ID"][0]
    de = " ".join(rec.get("DE", [])).rstrip(".")
    status = None
    if de.lower().startswith("deleted entry"): status = "deprecated"
    elif de.lower().startswith("transferred entry"): status = "deprecated"
    parts = code.split(".")
    parent = ".".join(parts[:-1] + ["-"]) if parts[-1] != "-" else None
    return row("bio/ec", code, de, status=status,
               parent_code=parent if parent != code else None,
               aliases=[a.rstrip(".") for a in rec.get("AN", [])],
               extra={"catalytic_activity": rec.get("CA"), "comments": rec.get("CC"),
                      "prosite": rec.get("PR"),
                      "uniprot_count": sum(len(d.split(";")) for d in rec.get("DR", []))})

# ------------------------------------------------------------------- unicode

@parser("wrt/uni")
def emoji(path, sysrow):
    group = sub = None
    for line in _text(path).splitlines():
        if line.startswith("# group:"):   group = line.split(":", 1)[1].strip(); continue
        if line.startswith("# subgroup:"): sub = line.split(":", 1)[1].strip(); continue
        if not line.strip() or line.startswith("#"): continue
        left, _, right = line.partition("#")
        cps, _, status = left.partition(";")
        cps, status = cps.strip(), status.strip()
        if not cps: continue
        m = re.match(r"\s*(\S+)\s+(E\d+\.\d+)\s+(.*)", right)
        glyph, ver, name = (m.group(1), m.group(2), m.group(3).strip()) if m else (None, None, "")
        yield row("wrt/uni", cps, name, status=status or None,
                  extra={"glyph": glyph, "emoji_version": ver,
                         "group": group, "subgroup": sub,
                         "codepoint_count": len(cps.split())})

# ------------------------------------------------------------------ airlines

@parser("trp/ica2")
def airlines(path, sysrow):
    """openflights dump, headerless: id, name, alias, IATA, ICAO, callsign, country, active.
    the three letter ICAO designator is the code, the two letter IATA one rides as an alias."""
    import csv as _csv
    seen = set()
    for f in _csv.reader(_text(path).splitlines()):
        if len(f) < 8: continue
        _id, name, alias, iata, icao, callsign, country, active = f[:8]
        na = lambda v: None if v in ("", "\\N", "-", "N/A") else v
        code = na(icao)
        # openflights carries junk in this column: ???, ***, ---, :::, quotes
        if not code or not re.fullmatch(r"[A-Z0-9]{2,3}", code) or code in seen: continue
        seen.add(code)
        yield row("trp/ica2", code, na(name) or "",
                  status="current" if active == "Y" else "deprecated",
                  aliases=[x for x in (na(iata), na(alias)) if x],
                  extra={"callsign": na(callsign), "country": na(country),
                         "iata": na(iata)})

# ---------------------------------------------------------- LC classification

@parser("cls/loc")
def lc_classification(path, sysrow):
    """the outline names a CLASS letter, then its subclasses. the ranges under each
    subclass are captions, not codes, so they ride along in extra."""
    cls = None; buf = {}
    order = []
    for line in _text(path).splitlines():
        m = re.match(r"^CLASS ([A-Z])\s*[-–]\s*(.+)$", line.strip())
        if m:
            cls = m.group(1)
            if cls not in buf:
                order.append(cls); buf[cls] = {"label": m.group(2).strip().title(),
                                               "parent": None, "captions": []}
            continue
        m = re.match(r"^Subclass ([A-Z]{1,3})$", line.strip())
        if m:
            sc = m.group(1)
            if sc not in buf:
                order.append(sc); buf[sc] = {"label": "", "parent": cls, "captions": []}
            cur = sc; continue
        m = re.match(r"^([A-Z]{1,3})[\d(].*?\t+(.+)$", line)
        if m and m.group(1) in buf:
            buf[m.group(1)]["captions"].append(m.group(2).strip())
            if not buf[m.group(1)]["label"]:
                buf[m.group(1)]["label"] = m.group(2).strip()
    for code in order:
        v = buf[code]
        yield row("cls/loc", code, v["label"], parent_code=v["parent"],
                  extra={"captions": v["captions"][:12] or None,
                         "caption_count": len(v["captions"]) or None})

# --------------------------------------------------------------- C and grammar

@parser("cmp/frc")
def fourcc(path, sysrow):
    """VLC's list: B(codec, "description") opens a group, A("abcd") adds a fourcc to it."""
    desc = None; seen = set()
    for line in _text(path).splitlines():
        m = re.search(r'B\(\s*\w+\s*,\s*"([^"]*)"', line)
        if m: desc = m.group(1); continue
        for cc in re.findall(r'A\(\s*"([^"]{1,4})"\s*\)', line):
            if cc in seen: continue
            seen.add(cc)
            yield row("cmp/frc", cc, desc or "")

@parser("cmp/reg")
def x86_registers(path, sysrow):
    """LLVM tablegen. `def RAX : X86Reg<"rax", 0>` carries both the tablegen name and
    the assembler spelling, and the assembler spelling is the register you actually type."""
    seen = {}
    for m in re.finditer(r'def\s+([A-Z][A-Z0-9_]*)\s*:\s*X86Reg<\s*"([^"]*)"\s*,\s*(\d+)',
                         _text(path)):
        tag, asm, num = m.groups()
        if not asm or asm in seen: continue
        seen[asm] = (tag, num)
    for asm, (tag, num) in seen.items():
        yield row("cmp/reg", asm, "", aliases=[tag],
                  extra={"tablegen_name": tag, "encoding": int(num)})

@parser("grf/gql")
def cypher_keywords(path, sysrow):
    """ANTLR lexer rules in all caps are the reserved words of the grammar."""
    seen = set()
    for m in re.finditer(r"^([A-Z][A-Z_]*)\s*:", _text(path), re.M):
        k = m.group(1)
        if k in seen: continue
        seen.add(k)
        yield row("grf/gql", k, "")

# ------------------------------------------------------------------ html spec

@parser("cmp/ern")
def errno_names(path, sysrow):
    """POSIX.1 <errno.h>. the spec lists each macro as [ENAME] followed by its meaning."""
    t = html.unescape(re.sub(r"<[^>]+>", " ", _text(path)))
    t = " ".join(t.split())
    seen = set()
    for m in re.finditer(r"\[(E[A-Z0-9]+)\]\s+([^\[]{0,160}?)(?=\s*\[E[A-Z0-9]+\]|$)", t):
        name, meaning = m.group(1), m.group(2).strip().rstrip(".")
        if name in seen: continue
        seen.add(name)
        yield row("cmp/ern", name, meaning)

# ------------------------------------------------------------------- vim help

@parser("cmp/vim")
def vim_motions(path, sysrow):
    """vim's own identifier for anything is its help tag, the *name* form, so that is the
    code. the command spelling in column 0 rides as an alias, and the indented lines that
    follow a tagged entry are its description. section headings are not tags and are skipped."""
    lines = _text(path).splitlines()
    out, order = {}, []
    pending = []
    for line in lines:
        tags = re.findall(r"\*([^*\s]+)\*", line)
        if tags:
            head = re.split(r"\s{2,}|\t", line, 1)[0].strip().removesuffix(" or").strip()
            if re.match(r"^\d+\.\s", head) or head.startswith("="):
                continue                      # numbered section heading, not a command
            for t in tags:
                if t not in out:
                    order.append(t)
                    out[t] = {"desc": "", "alias": set()}
                if head and head != t and not head.startswith("*"):
                    out[t]["alias"].add(head)
                pending.append(t)
            continue
        if pending and re.match(r"^\s{2,}\S", line):
            desc = line.strip()
            for t in pending:
                if not out[t]["desc"]: out[t]["desc"] = desc[:200]
            pending = []
        elif not line.strip():
            pending = []
    for t in order:
        v = out[t]
        yield row("cmp/vim", t, v["desc"], aliases=sorted(v["alias"]),
                  extra={"kind": "command" if re.fullmatch(r"[^a-z]*[a-z]?[^-]{0,3}", t)
                                 and "-" not in t else "topic"})


# ---------------------------------------------------------------------- ASN.1

BASE1 = "TTTTTTTTTTTTTTTTCCCCCCCCCCCCCCCCAAAAAAAAAAAAAAAAGGGGGGGGGGGGGGGG"
BASE2 = "TTTTCCCCAAAAGGGGTTTTCCCCAAAAGGGGTTTTCCCCAAAAGGGGTTTTCCCCAAAAGGGG"
BASE3 = "TCAGTCAGTCAGTCAGTCAGTCAGTCAGTCAGTCAGTCAGTCAGTCAGTCAGTCAGTCAGTCAG"

@parser("bio/cdn")
def genetic_codes(path, sysrow):
    """NCBI ships one translation string per genetic code, 64 characters in a fixed codon
    order. the codon is the code, the standard table gives the label, and every other
    table's reading of that codon rides in extra. that is where the interesting part is:
    the same three letters mean different amino acids depending on the organism."""
    t = _text(path)
    tables = []
    for blk in re.split(r"Genetic-code-table\s*::=|,\s*\{\s*(?=name)", t):
        ids = re.search(r"\bid\s+(\d+)", blk)
        aa = re.search(r'ncbieaa\s+"([^"]{64})"', blk)
        st = re.search(r'sncbieaa\s+"([^"]{64})"', blk)
        nm = re.findall(r'name\s+"([^"]+)"', blk)
        if ids and aa:
            tables.append({"id": int(ids.group(1)), "name": nm[0] if nm else "",
                           "aa": aa.group(1), "starts": st.group(1) if st else "-"*64})
    if not tables:
        raise RuntimeError("no genetic code tables parsed")
    std = next((x for x in tables if x["id"] == 1), tables[0])
    for i in range(64):
        codon = BASE1[i] + BASE2[i] + BASE3[i]
        variants = {str(x["id"]): x["aa"][i] for x in tables if x["aa"][i] != std["aa"][i]}
        starts = sorted(str(x["id"]) for x in tables if x["starts"][i] == "M")
        yield row("bio/cdn", codon,
                  "stop" if std["aa"][i] == "*" else std["aa"][i],
                  description=f'standard genetic code translation of {codon}',
                  extra={"standard_aa": std["aa"][i], "differs_in_tables": variants or None,
                         "start_codon_in_tables": starts or None,
                         "table_count": len(tables)})
