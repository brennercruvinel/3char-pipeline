"""csv, tab and headerless table sources. one spec per system, one generic reader."""
import re, sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
from core import parser, row, read_csv, label_file

def _first_token(s):
    return re.split(r"[\s,]", s.strip().strip('"'), 1)[0]

def expand_range(v):
    """'105-199' -> the individual codes. IANA writes unassigned blocks this way."""
    m = re.fullmatch(r"(\d+)\s*-\s*(\d+)", v.strip())
    if not m: return None
    lo, hi = int(m.group(1)), int(m.group(2))
    return [str(n) for n in range(lo, hi + 1)] if hi - lo < 2000 else None

# ---------------------------------------------------------------- simple tables

@parser("cls/elm")
def elements(path, sysrow):
    for r in read_csv(path):
        yield row("cls/elm", r["Symbol"], r["Name"],
                  extra={k: r.get(k) for k in ("AtomicNumber","AtomicMass","GroupBlock",
                                               "StandardState","YearDiscovered")})

@parser("cmp/htt")
def http_methods(path, sysrow):
    for r in read_csv(path):
        yield row("cmp/htt", r["Method Name"], r["Method Name"],
                  extra={"safe": r.get("Safe"), "idempotent": r.get("Idempotent"),
                         "reference": r.get("Reference")})

@parser("cmp/sts")
def http_status(path, sysrow):
    for r in read_csv(path):
        val, desc = r["Value"].strip(), (r.get("Description") or "").strip()
        codes = expand_range(val) or [val]
        st = "unassigned" if desc.lower() == "unassigned" else None
        for c in codes:
            yield row("cmp/sts", c, desc, status=st,
                      extra={"reference": r.get("Reference"), "range": val if len(codes) > 1 else None})

@parser("cmp/dns")
def dns_types(path, sysrow):
    skip = {"unassigned", "reserved", "private use"}
    # IANA leaves Meaning empty for nine types. The four ILNP types take the sentence of RFC 6742 that
    # defines each, SPF takes the title of RFC 7208, and the IANA-reserved four take that reference.
    ilnp = " ".join(label_file(path, "cmp/dns", 0).read_text(encoding="utf-8").split())
    rfc7208 = label_file(path, "cmp/dns", 1).read_text(encoding="utf-8").splitlines()
    at = next(i for i, l in enumerate(rfc7208) if l.strip().startswith("Sender Policy Framework"))
    spf_title = " ".join(l.strip() for l in rfc7208[at:at + 2])   # the title runs over two centred lines
    def meaning(t, ref):
        if ref == "[IANA-Reserved]": return "IANA-Reserved"
        if ref == "[RFC7208]": return spf_title
        m = re.search(r"(The [^.]{0,40}\b%s\b[^.]*? is used(?: to)? hold [^.]*\.)" % re.escape(t), ilnp)
        return re.sub(r"^The \S+ Resource Record ", "", m.group(1)) if m else ""   # drop the section heading
    for r in read_csv(path):
        t = (r.get("TYPE") or "").strip()
        if not t or t.lower() in skip: continue
        yield row("cmp/dns", t, r.get("Meaning") or meaning(t, (r.get("Reference") or "").strip()),
                  extra={"value": r.get("Value"), "reference": r.get("Reference"),
                         "registered": r.get("Registration Date")})

@parser("wrt/iau")
def constellations(path, sysrow):
    """Serpens appears twice, once per half (Caput and Cauda). one abbreviation, one row."""
    seen = set()
    for r in read_csv(path):
        c = r["desig"]
        if c in seen: continue
        seen.add(c)
        yield row("wrt/iau", c, r["la"], description=r.get("en"),
                  aliases=[r.get("id")] if r.get("id") != c else [],
                  extra={"genitive": r.get("gen"), "rank": r.get("rank")})

@parser("lng/i39")
def iso639_1(path, sysrow):
    for r in read_csv(path):
        yield row("lng/i39", r["alpha2"], r["English"])

@parser("lng/i31")
def iso3166(path, sysrow):
    for r in read_csv(path):
        yield row("lng/i31", r["alpha-3"], r["name"], aliases=[r.get("alpha-2")],
                  extra={"numeric": r.get("country-code"), "region": r.get("region"),
                         "sub_region": r.get("sub-region")})

@parser("lng/ioc")
def ioc_codes(path, sysrow):
    for r in read_csv(path):
        code = (r.get("IOC") or "").strip()
        if not code: continue
        iso3, fifa = (r.get("ISO3166-1-Alpha-3") or "").strip(), (r.get("FIFA") or "").strip()
        # the source writes a footnote marker where the UK has four FIFA members, and the
        # ioc code often equals the iso3: an alias must be a code and must not repeat the code
        aliases = sorted({a for a in (iso3, fifa) if a.isalpha() and a != code})
        yield row("lng/ioc", code, r.get("official_name_en") or r.get("CLDR display name") or "",
                  aliases=aliases,
                  extra={"iso3": iso3, "fifa": fifa if fifa.isalpha() else None,
                         "iso2": r.get("ISO3166-1-Alpha-2"), "capital": r.get("Capital"),
                         "continent": r.get("Continent"), "tld": r.get("TLD")})

@parser("lng/glt")
def glottolog(path, sysrow):
    for r in read_csv(path):
        yield row("lng/glt", r["Glottocode"] or r["ID"], r["Name"],
                  aliases=[r.get("ISO639P3code")],
                  extra={"level": r.get("Level"), "macroarea": r.get("Macroarea"),
                         "family_id": r.get("Family_ID"),
                         "isolate": r.get("Is_Isolate")})

@parser("trp/unl")
def unlocode(path, sysrow):
    for r in read_csv(path):
        loc = (r.get("Location") or "").strip()
        if not loc: continue
        yield row("trp/unl", loc, r.get("Name") or "", parent_code=r.get("Country"),
                  status="deprecated" if (r.get("Change") or "").strip() == "X" else None,
                  aliases=[r.get("IATA")],
                  extra={"country": r.get("Country"), "locode": f'{r.get("Country","")}{loc}',
                         "function": r.get("Function"), "coordinates": r.get("Coordinates")})

def _airports(path, sid, col):
    for r in read_csv(path):
        code = (r.get(col) or "").strip()
        if not code: continue
        yield row(sid, code, r.get("name") or "",
                  extra={"type": r.get("type"), "country": r.get("iso_country"),
                         "municipality": r.get("municipality"),
                         "scheduled": r.get("scheduled_service")})

@parser("trp/iata")
def iata(path, sysrow):  return _airports(path, "trp/iata", "iata_code")

@parser("trp/icao")
def icao(path, sysrow):  return _airports(path, "trp/icao", "icao_code")

@parser("cmp/asm")
def x86_mnemonics(path, sysrow):
    seen = {}
    for r in read_csv(path):
        mnem = _first_token(r.get("Instruction") or "")
        if not mnem: continue
        seen.setdefault(mnem, r.get("Description") or "")
    for mnem, desc in seen.items():
        yield row("cmp/asm", mnem, desc)

@parser("trp/olc")
def open_location_code(path, sysrow):
    """these are the reference encoder test vectors, not a registry. plus codes are
    generated from coordinates, so no complete enumeration exists to ship. the file
    repeats a code across wrapped longitudes (+/-360), which is one code, not three."""
    cols = ["lat","lng","latint","lngint","length","code"]
    seen = set()
    for r in read_csv(path, header=False, fieldnames=cols, comment="#"):
        c = (r.get("code") or "").strip()
        if not c or c in seen: continue
        seen.add(c)
        # the label is the coordinate the test vector encodes, as the file writes it
        yield row("trp/olc", c, f"{r.get('lat')}, {r.get('lng')}", extra={"lat": r.get("lat"), "lng": r.get("lng"),
                                           "length": r.get("length")})

# ---------------------------------------------------------------- hierarchical

@parser("cls/atc")
def atc(path, sysrow):
    """A > A01 > A01A > A01AA > A01AA01. parent is the previous level's prefix."""
    cut = {1: None, 3: 1, 4: 3, 5: 4, 7: 5}
    order, agg = [], {}
    for r in read_csv(path):
        c = (r.get("atc_code") or "").strip()
        if not c: continue
        na = lambda k: (r.get(k) or "").strip() or None
        na = lambda k, r=r: (None if (r.get(k) or "").strip() in ("", "NA") else r[k].strip())
        if c not in agg:
            order.append(c)
            agg[c] = {"label": r.get("atc_name") or "", "note": na("note"), "ddd": []}
        d = {"adm_r": na("adm_r"), "ddd": na("ddd"), "uom": na("uom")}
        if any(d.values()) and d not in agg[c]["ddd"]:
            agg[c]["ddd"].append(d)
    for c in order:
        a = agg[c]; n = cut.get(len(c))
        yield row("cls/atc", c, a["label"], parent_code=c[:n] if n else None,
                  extra={"note": a["note"], "ddd": a["ddd"] or None})

@parser("cls/bsc")
def bisac(path, sysrow):
    """headerless, two columns. the XXX000000 entry of each prefix is the parent."""
    rows = list(read_csv(path, header=False, fieldnames=["code","label"]))
    general = {r["code"][:3] for r in rows if r["code"].endswith("000000")}
    for r in rows:
        c = r["code"].strip()
        top = f"{c[:3]}000000"
        yield row("cls/bsc", c, r["label"].strip(),
                  parent_code=top if (c != top and c[:3] in general) else None)

@parser("fin/cus")
def cik_cusip(path, sysrow):
    """the mapping gives CUSIP issuer prefixes and the SEC CIK of the filer; the issuer's name is the
    one EDGAR registers for that CIK, from the SEC's CIK lookup file ("NAME:0000012345:")."""
    names = {}
    with open(label_file(path, "fin/cus"), encoding="latin-1") as fh:
        for line in fh:
            m = re.match(r"^(.*):(\d{10}):\s*$", line.rstrip("\n"))
            if m and m.group(1).strip(): names.setdefault(int(m.group(2)), m.group(1).strip())
    seen = set()
    for r in read_csv(path):
        c = (r.get("cusip6") or "").strip()
        if not c or c in seen: continue
        seen.add(c)
        cik = int(float(r["cik"])) if (r.get("cik") or "").strip() else None
        yield row("fin/cus", c, names.get(cik, ""), extra={"cik": str(cik) if cik else None, "cusip8": r.get("cusip8")})
