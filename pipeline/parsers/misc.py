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
                    order.append(current); zones[current] = {"lines": set(), "file": fname}
                zones[current]["lines"].add((parts[3], parts[4]))
            elif raw[:1] in (" ", "\t") and current and len(parts) >= 3:
                zones[current]["lines"].add((parts[1], parts[2]))
            elif parts[0] == "Link" and len(parts) >= 3:
                tgt = parts[2]
                if tgt not in zones:
                    order.append(tgt)
                    zones[tgt] = {"lines": set(), "file": fname, "link_to": parts[1]}

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

    # abbreviations are what the reference compiler prints: zic builds the default data set and the
    # strings come from each compiled TZif file. expanding FORMAT with LETTERs by hand cannot see which
    # rule applies in which years, and produced strings tzdb never prints (CEAMTT, EE+05T)
    import subprocess, tempfile
    with tempfile.TemporaryDirectory() as out:
        subprocess.run(["zic", "-d", out] + [f for f in ZONE_FILES if f != "backzone"],
                       cwd=root, check=True, capture_output=True)
        abbr = {}
        for f in pathlib.Path(out).rglob("*"):
            if f.is_file():
                for a in _tzif_abbreviations(f.read_bytes()):
                    abbr.setdefault(a, set()).add(str(f.relative_to(out)))
    names = _abbreviation_names((root/"theory.html").read_text(encoding="utf-8"))
    for a in sorted(abbr):
        zs = sorted(abbr[a])
        yield row("wrt/tz", a, names.get(a) or _offset_name(a), extra={"kind": "abbreviation", "zone_count": len(zs),
                                                                       "zones": zs[:10], "version": version})

def _tzif_abbreviations(b):
    """the abbreviation strings a TZif file declares (RFC 8536): the v2+ block when present, else v1."""
    import struct
    if b[:4] != b"TZif": return set()
    def block(off, size):
        isut, isstd, leap, timecnt, typecnt, charcnt = struct.unpack(">6l", b[off + 20:off + 44])
        o = off + 44 + timecnt * size + timecnt + typecnt * 6
        return o + charcnt + leap * (size + 4) + isstd + isut, b[o:o + charcnt]
    end, chars = block(0, 4)
    if b[4:5] in (b"2", b"3", b"4"): chars = block(end, 8)[1]
    return {c.decode("ascii") for c in chars.split(b"\0") if c}

def _offset_name(a):
    """numeric abbreviations are UTC offsets; -00 is the factory setting, a zone that is not known."""
    if a == "-00": return "Unknown time zone (tzdb factory setting)"
    m = re.fullmatch(r"([+-])(\d{2})(\d{2})?", a)
    return f"UTC{m.group(1)}{m.group(2)}:{m.group(3) or '00'}" if m else ""

def _abbreviation_names(theory):
    """theory.html lists the English abbreviations by region ("AEST/AEDT Australian Eastern"), the
    local mean times by place ("BMT Baghdad, Bangkok, ...") and the GMT/BST-style pairs."""
    text = " ".join(html.unescape(re.sub(r"<[^>]+>", " ", theory)).split())
    names = {}
    def add(a, n): names[a] = n if a not in names else f"{names[a]}; {n}"
    m = re.search(r"These abbreviations \(for standard/daylight/etc\. time\) are: (.*?)\.\s", text)
    for group, region in re.findall(r"([A-Za-z]+(?:/[A-Za-z]+)*) ([^,]+?(?:\([^)]*\))?)(?:,|$)", m.group(1)):
        region = region.strip()
        if not region.startswith("Waktu"):          # "Waktu Indonesia Barat" already says "time"
            r = re.match(r"^(.*?)((?: through| \d{4}).*)?$", region)
            region = f"{r.group(1)} time" + (f" ({r.group(2).strip()})" if r.group(2) else "")
        for a in group.split("/"): add(a, region)
    m = re.search(r"These abbreviations are: (.*?)\.\s", text)
    for a, places in re.findall(r"([A-Z]+MT) ([^;]+)", m.group(1)):
        add(a, f"Local mean time of {places.strip()}")
    m = re.search(r"They are: (.*?)\.\s", text)
    # "CMT/BST for Calamarca Mean Time and Bolivian Summer Time 1890–1932": the later abbreviations
    # take the summer-time half and the years
    for entry in re.split(r",\s*(?:and\s+)?(?=[A-Z]+/)", m.group(1)):
        group, what = entry.split(" for ", 1)
        years = re.search(r"\s(\d{4}–\d{4})$", what)
        halves = what[:years.start()].split(" and ") if years else [what]
        for a in group.split("/")[1:]:
            add(a, (halves[-1] if len(halves) > 1 else halves[0]) + (f" {years.group(1)}" if years else ""))
    return names

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
    seen = {}
    # an operation's summary sits a few lines above its operationId, at the same indentation
    for m in _re.finditer(r"^(\s+)summary:\s*(.+)\n(?:(?!\1summary:).*\n){0,12}?\1operationId:\s*(\S+)", t, _re.M):
        seen.setdefault(m.group(3), m.group(2).strip())
    for m in _re.finditer(r"^\s+operationId:\s*(\S+)", t, _re.M):
        seen.setdefault(m.group(1), "")
    for op, summary in seen.items():
        yield row("trp/w3w", op, summary, extra={"kind": "operation"})

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
