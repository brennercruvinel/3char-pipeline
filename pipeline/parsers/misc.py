"""tzdb zone files, the what3words api surface, and the IUPAC amino acid table."""
import html, pathlib, re, sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
from core import parser, row, ROOT

ZONE_FILES = ["africa","antarctica","asia","australasia","europe","northamerica",
              "southamerica","etcetera","backward","backzone","factory"]

@parser("wrt/tz")
def tzdata(path, sysrow):
    """two kinds of code live in tzdb and both matter. the zone name is the canonical
    identifier an application stores, Europe/Lisbon. the abbreviation is the three or
    four letters a timestamp actually prints, WET or WEST, and it comes from a Zone's
    FORMAT field, where %s is filled by the LETTER column of whichever Rule applies."""
    base = ROOT/path
    root = base if base.is_dir() else base.parent
    letters = {}       # rule name -> set of LETTER values
    zones = {}         # zone name -> {"formats": set, "rules": set}
    order = []

    for fname in ZONE_FILES:
        f = root/fname
        if not f.exists(): continue
        current = None
        for raw in f.read_text(encoding="utf-8", errors="replace").splitlines():
            line = raw.split("#", 1)[0].rstrip()
            if not line.strip(): continue
            parts = line.split()
            if parts[0] == "Rule" and len(parts) >= 10:
                letters.setdefault(parts[1], set()).add(parts[9])
            elif parts[0] == "Zone" and len(parts) >= 5:
                current = parts[1]
                if current not in zones:
                    order.append(current); zones[current] = {"formats": set(), "rules": set(),
                                                             "file": fname}
                zones[current]["formats"].add(parts[4]); zones[current]["rules"].add(parts[3])
            elif raw[:1] in (" ", "\t") and current and len(parts) >= 3:
                zones[current]["formats"].add(parts[2]); zones[current]["rules"].add(parts[1])
            elif parts[0] == "Link" and len(parts) >= 3:
                tgt = parts[2]
                if tgt not in zones:
                    order.append(tgt)
                    zones[tgt] = {"formats": set(), "rules": set(), "file": fname,
                                  "link_to": parts[1]}

    countries = {}
    tab = root/"zone1970.tab"
    if tab.exists():
        for line in tab.read_text(encoding="utf-8").splitlines():
            if line.startswith("#") or not line.strip(): continue
            f = line.split("\t")
            if len(f) >= 3: countries[f[2]] = f[0]

    version = (root/"version").read_text().strip() if (root/"version").exists() else None

    for z in order:
        v = zones[z]
        yield row("wrt/tz", z, z.split("/")[-1].replace("_", " "),
                  extra={"kind": "zone", "countries": countries.get(z),
                         "link_to": v.get("link_to"), "file": v["file"],
                         "version": version})

    abbr = {}
    for z in order:
        for fmt in zones[z]["formats"]:
            for rule in zones[z]["rules"]:
                for a in _expand(fmt, letters.get(rule, {""})):
                    abbr.setdefault(a, set()).add(z)
    for a in sorted(abbr):
        zs = sorted(abbr[a])
        yield row("wrt/tz", a, "", extra={"kind": "abbreviation", "zone_count": len(zs),
                                          "zones": zs[:10], "version": version})

def _expand(fmt, letter_set):
    """FORMAT is either a literal (WET), a %s template filled from Rule LETTERs,
    a %z placeholder the runtime turns into a numeric offset, or an A/B pair."""
    if "%z" in fmt: return []
    if "/" in fmt: return [p for p in fmt.split("/") if p]
    if "%s" in fmt:
        out = []
        for L in letter_set:
            L = "" if L == "-" else L
            cand = fmt.replace("%s", L)
            if cand and not cand.startswith("%"): out.append(cand)
        return out
    return [fmt] if fmt else []

@parser("trp/w3w")
def what3words(path, sysrow):
    """the openapi document is the api surface, so the operations are the codes."""
    import re as _re
    t = (ROOT/path).read_text(encoding="utf-8")
    seen = []
    for m in _re.finditer(r"^\s+operationId:\s*(\S+)", t, _re.M):
        if m.group(1) not in seen: seen.append(m.group(1))
    for op in seen:
        yield row("trp/w3w", op, "", extra={"kind": "operation"})

@parser("bio/aa1", "bio/aa3")
def iupac_amino_acids(path, sysrow):
    """JCBN Recommendations 1983, Table 1. columns are trivial name, three letter symbol,
    one letter symbol, systematic name, formula. the published table carries footnote
    letters glued onto the symbols, so Asparagine arrives as 'Asnd' and 'N d', and the
    footnote has to come off before the symbol is read."""
    from lxml import html as LH
    sid = sysrow["system_id"]
    doc = LH.parse(str(ROOT/path))
    seen = set()
    for tr in doc.xpath("//table//tr"):
        cells = [" ".join(c.text_content().split()) for c in tr.xpath("./td|./th")]
        if len(cells) < 4: continue
        trivial, three_raw, one_raw, systematic = cells[0], cells[1], cells[2], cells[3]
        m3 = re.match(r"([A-Z][a-z]{2})", three_raw)
        m1 = re.match(r"([A-Z])(?![A-Z])", one_raw)
        if not (m3 and m1) or not trivial or trivial.startswith("Trivial"): continue
        three, one = m3.group(1), m1.group(1)
        code = one if sid == "bio/aa1" else three
        if code in seen: continue
        seen.add(code)
        yield row(sid, code, trivial, description=systematic,
                  aliases=[three if sid == "bio/aa1" else one],
                  extra={"three_letter": three, "one_letter": one,
                         "systematic_name": systematic,
                         "formula": cells[4] if len(cells) > 4 else None})
