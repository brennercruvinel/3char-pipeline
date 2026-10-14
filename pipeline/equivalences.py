"""Lists in a published 3char snapshot that describe the same entities, with the same codes or with different ones.

usage: python equivalences.py <3char_root> <out.json> [figure.svg]

Each link has an explicit test, recorded in the output. Labels are compared after removing accents, case and
punctuation, which undercounts entities whose names are spelled differently in the two lists. The optional SVG is
the figure shown in the dataset card.
"""
import collections
import json
import pathlib
import re
import sys
import unicodedata

import pyarrow.parquet as pq


def norm(s):
    s = unicodedata.normalize("NFKD", s or "").encode("ascii", "ignore").decode().casefold()
    return re.sub(r"[^a-z0-9]+", " ", s).strip()


def load(root):
    systems = {}
    for p in sorted(pathlib.Path(root, "data").glob("*/*.parquet")):
        rows = pq.read_table(p, columns=["system_id", "code", "label", "aliases", "extra"]).to_pylist()
        systems[rows[0]["system_id"]] = rows
    return systems


def ex(r):
    return json.loads(r["extra"]) if r["extra"] else {}


def same_label(a, b):
    return norm(a["label"]) != "" and norm(a["label"]) == norm(b["label"])


def first_by_code(rows):
    d = {}
    for r in rows:
        d.setdefault(r["code"], r)
    return d


def links(sy):
    out = []

    def add(kind, a, b, test, linked, same, note=""):
        out.append({"kind": kind, "a": a, "b": b, "test": test, "a_entries": len(sy[a]), "linked": linked,
                    "same_entity": same, "note": note})

    # Same entities under the same codes.
    for a, b in (("lng/i63", "lng/b47"), ("lng/i39", "lng/b47"), ("lng/i15", "lng/b47"), ("lng/ioc", "lng/i31")):
        target = collections.defaultdict(list)
        for r in sy[b]:
            target[r["code"]].append(r)
        shared = [r for r in sy[a] if r["code"] in target]
        add("same_code", a, b, "same code and same normalized label", len(shared),
            sum(any(same_label(r, t) for t in target[r["code"]]) for r in shared))
    region = {r["code"]: r for r in sy["lng/b47"] if ex(r).get("type") == "region"}
    hits = [(r, region[al]) for r in sy["lng/i31"] for al in r["aliases"] if al in region]
    add("same_code", "lng/i31", "lng/b47", "ISO 3166-1 alpha-2 code (alias) is a BCP 47 region subtag with the same normalized label",
        len(hits), sum(same_label(a, b) for a, b in hits))
    unl = collections.defaultdict(list)
    for r in sy["trp/unl"]:
        unl[r["code"]].append(ex(r))
    shared = [r for r in sy["trp/iata"] if r["code"] in unl]
    add("same_code", "trp/iata", "trp/unl",
        "IATA code is a UN/LOCODE code in the same country at a location with the airport function", len(shared),
        sum(any(u["country"] == ex(r)["country"] and "4" in (u.get("function") or "") for u in unl[r["code"]]) for r in shared),
        "labels differ by construction: airport name against place name")
    tld = {r["code"].casefold() for r in sy["trp/tld"]}
    add("same_code_unchecked", "lng/i31", "trp/tld", "ISO 3166-1 alpha-2 code (alias) is also a top-level domain; entity not checked",
        sum(al.casefold() in tld for r in sy["lng/i31"] for al in r["aliases"]), None,
        "the TLD list carries no country names to compare")

    # Same entities under different codes.
    aa3 = first_by_code(sy["bio/aa3"])
    pairs = [(r, aa3[ex(r)["three_letter"]]) for r in sy["bio/aa1"] if ex(r).get("three_letter") in aa3]
    add("different_code", "bio/aa1", "bio/aa3", "one-letter code linked to a three-letter code by the source table",
        len(pairs), sum(same_label(a, b) for a, b in pairs))
    i31 = first_by_code(sy["lng/i31"])
    pairs = [(r, i31[ex(r)["iso3"]]) for r in sy["lng/ioc"] if ex(r).get("iso3") in i31 and ex(r)["iso3"] != r["code"]]
    add("different_code", "lng/ioc", "lng/i31", "IOC code linked to a different ISO 3166-1 alpha-3 code by extra.iso3",
        len(pairs), sum(same_label(a, b) for a, b in pairs))
    i63 = first_by_code(sy["lng/i63"])
    pairs = [(r, i63[al]) for r in sy["lng/glt"] for al in r["aliases"] if al in i63]
    add("different_code", "lng/glt", "lng/i63", "glottocode linked to a three-letter language subtag by its aliases",
        len(pairs), sum(same_label(a, b) for a, b in pairs))
    key = lambda r: (norm(r["label"]), ex(r).get("municipality"), ex(r).get("country"))
    icao = collections.Counter(key(r) for r in sy["trp/icao"])
    matched = sum(1 for r in sy["trp/iata"] if icao[key(r)] == 1)
    add("different_code", "trp/iata", "trp/icao", "exactly one ICAO airport with the same name, municipality and country",
        matched, matched, "both systems are read from the same OurAirports file")
    mor = {r["code"] for r in sy["com/mor"]}
    chars = sum(1 for r in sy["com/bau"] for al in r["aliases"] if al in mor)
    add("different_code", "com/bau", "com/mor", "ITA2 combination and Morse signal for the same character",
        chars, chars, "the character is the shared entity")
    return out


def shared_with_same_label(sy, derived):
    """Case-folded codes in two or more systems, and how many carry the same name in at least two of them.

    Systems derived from another (systems.derived_from) are left out, so a derived pair counts once, as in the
    census. A label equal to its own code carries no name and is ignored. Name matching misses equivalences whose
    names differ, such as an airport and the place it serves, so the count is a lower bound on shared meaning.
    """
    labels = collections.defaultdict(lambda: collections.defaultdict(set))
    for sid, rows in sy.items():
        if sid in derived:
            continue
        for r in rows:
            name = norm(r["label"])
            labels[r["code"].casefold()][sid].add("" if name == norm(r["code"]) else name)
    shared = same = 0
    for per_system in labels.values():
        if len(per_system) < 2:
            continue
        shared += 1
        seen = collections.Counter(n for names in per_system.values() for n in names if n)
        same += any(k > 1 for k in seen.values())
    return {"shared_codes": shared, "with_same_name_in_two_systems": same, "derived_systems_left_out": sorted(derived)}


# Figure layout: positions are fixed so that the figure stays stable between releases.
W, H = 1000, 640
NODES = {
    "lng/glt": (330, 70, "Glottolog"), "lng/i63": (120, 150, "3-letter subtags"),
    "lng/b47": (270, 270, "BCP 47 subtags"), "lng/i39": (90, 380, "ISO 639-1"), "lng/i15": (200, 480, "ISO 15924"),
    "lng/ioc": (540, 110, "IOC countries"), "lng/i31": (540, 290, "ISO 3166-1"), "trp/tld": (540, 450, "Top-level domains"),
    "trp/iata": (790, 290, "IATA airports"), "trp/unl": (900, 130, "UN/LOCODE"), "trp/icao": (900, 450, "ICAO airports"),
    "bio/aa1": (150, 580, "Amino acids, 1-letter"), "bio/aa3": (390, 580, "Amino acids, 3-letter"),
    "com/bau": (640, 580, "ITA2 teleprinter"), "com/mor": (870, 580, "Morse code"),
}
STYLE = {"same_code": ("same", ""), "different_code": ("diff", "7 5"), "same_code_unchecked": ("unk", "2 4")}
LEGEND = (("same", "", "Same code, same entity"), ("diff", "7 5", "Different codes, same entity"),
          ("unk", "2 4", "Same code, entity not checked"))
BEND = {("lng/ioc", "lng/i31", "same_code"): -40, ("lng/ioc", "lng/i31", "different_code"): 40}


def figure(links_):
    s = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" '
         'font-family="system-ui, -apple-system, Segoe UI, sans-serif" role="img" aria-labelledby="t d">',
         '<title id="t">Lists in 3char that describe the same entities</title>',
         '<desc id="d">Solid lines join lists that use the same code for the same entity; dashed lines join lists that '
         'link the same entity under different codes; the dotted line marks codes that coincide without a checked '
         'entity. Each label gives the entries of the first list that pass the test, out of all its entries.</desc>',
         '<style>',
         ' .same{stroke:#2a78d6}.diff{stroke:#eb6834}.unk{stroke:#8a8984}',
         ' .node{fill:#fcfcfb;stroke:#c9c8c3}.id{fill:#0b0b0b;font-size:13px;font-weight:600}.nm{fill:#52514e;font-size:11px}',
         ' .lab{fill:#0b0b0b;font-size:12px;paint-order:stroke;stroke:#fcfcfb;stroke-width:3px;stroke-linejoin:round}',
         ' .key{fill:#52514e;font-size:12px}',
         '</style>',
         # An opaque surface keeps the figure legible on light and dark pages, which an image cannot detect.
         f'<rect width="{W}" height="{H}" rx="12" fill="#fcfcfb"/>']
    for l in links_:
        (x1, y1, _), (x2, y2, _) = NODES[l["a"]], NODES[l["b"]]
        cls, dash = STYLE[l["kind"]]
        bend = BEND.get((l["a"], l["b"], l["kind"]), 0)
        mx, my = (x1 + x2) / 2 + bend, (y1 + y2) / 2
        dash = f' stroke-dasharray="{dash}"' if dash else ""
        n = l["linked"] if l["same_entity"] is None else l["same_entity"]
        s.append(f'<path class="{cls}" d="M{x1},{y1} Q{mx + bend},{my} {x2},{y2}" fill="none" stroke-width="2.5" '
                 f'stroke-linecap="round"{dash}/>')
        s.append(f'<text class="lab" x="{mx}" y="{my - 6}" text-anchor="middle">{n:,} of {l["a_entries"]:,}</text>')
    for sid, (x, y, name) in NODES.items():
        s.append(f'<rect class="node" x="{x - 70}" y="{y - 22}" width="140" height="44" rx="8" stroke-width="1"/>')
        s.append(f'<text class="id" x="{x}" y="{y - 3}" text-anchor="middle">{sid}</text>')
        s.append(f'<text class="nm" x="{x}" y="{y + 13}" text-anchor="middle">{name}</text>')
    for i, (cls, dash, text) in enumerate(LEGEND):
        y = 24 + i * 20
        dash = f' stroke-dasharray="{dash}"' if dash else ""
        s.append(f'<line class="{cls}" x1="700" y1="{y}" x2="740" y2="{y}" stroke-width="2.5" stroke-linecap="round"{dash}/>')
        s.append(f'<text class="key" x="748" y="{y + 4}">{text}</text>')
    s.append("</svg>")
    return "\n".join(s) + "\n"


def main(root, out, svg=None):
    sy = load(root)
    result = links(sy)
    derived = {r["system_id"] for r in pq.read_table(f"{root}/systems.parquet").to_pylist() if r["derived_from"]}
    summary = shared_with_same_label(sy, derived)
    pathlib.Path(out).write_text(json.dumps({**summary, "links": result}, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    print(summary)
    if svg:
        pathlib.Path(svg).parent.mkdir(parents=True, exist_ok=True)
        pathlib.Path(svg).write_text(figure(result), encoding="utf-8")
    for l in result:
        print(f"{l['kind']:20} {l['a']:9} {l['b']:9} linked={l['linked']:6} same_entity={l['same_entity']}")


if __name__ == "__main__":
    main(*sys.argv[1:])
