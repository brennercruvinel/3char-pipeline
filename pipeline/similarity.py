"""Similarity between the systems of a published 3char snapshot, and the figures that show it.

usage: python similarity.py <3char_root> <out.json> [figures_dir]

Three measures, each with its own denominator:

1. Shared codes. For every pair of systems that share at least MIN_SHARED case-folded codes: how many they share,
   the share of each system's codes found in the other (containment), and how many shared codes carry the same
   normalized label in both. Labels are compared after removing accents, case and punctuation, so a pair whose
   lists spell names differently, or label different things (an airport and its city), scores low even when the
   codes denote the same entity. The same-label share separates lists that reuse each other's codes for the same
   entities from lists whose codes coincide by chance.
2. Cross-references. For every field of every system (aliases and each string field in extra), the share of its
   distinct values that are codes of another system, matched case-sensitively. A field that covers another system
   is an explicit link between the two lists; its cardinality says whether the link is one-to-one.
3. Readings. The literals claimed by the most systems, with the label each system gives them, and for the pairs
   that share the most codes, the first shared codes with both labels.

The figures are a containment matrix and a scatter of shared codes against the same-label share. Both are plain
SVG with a <title> on every mark, so a browser shows the value on hover.
"""
import collections
import itertools
import json
import math
import pathlib
import re
import sys
import unicodedata
from html import escape

import pyarrow.parquet as pq

MIN_SHARED = 10
MIN_VALUES = 10
MIN_COVERAGE = 0.9
TOP_LITERALS = 20
PAIR_EXAMPLES = 4
DOMAINS = ["bio", "cls", "cmp", "com", "fin", "grf", "lng", "nte", "trp", "wrt"]


def norm(s):
    s = unicodedata.normalize("NFKD", s or "").encode("ascii", "ignore").decode().casefold()
    return re.sub(r"[^a-z0-9]+", " ", s).strip()


def load(root):
    systems = {}
    for p in sorted(pathlib.Path(root, "data").glob("*/*.parquet")):
        rows = pq.read_table(p, columns=["system_id", "code", "label", "aliases", "extra"]).to_pylist()
        systems[rows[0]["system_id"]] = rows
    derived = {r["system_id"]: r["derived_from"]
               for r in pq.read_table(pathlib.Path(root, "systems.parquet")).to_pylist() if r["derived_from"]}
    return systems, derived


def folded(systems):
    """system -> case-folded code -> (first code as written, first label, set of normalized labels)."""
    out = {}
    for s, rows in systems.items():
        d = {}
        for r in rows:
            k = r["code"].casefold()
            if k not in d: d[k] = [r["code"], r["label"], set()]
            if norm(r["label"]): d[k][2].add(norm(r["label"]))
        out[s] = d
    return out


def shared_codes(fold, derived):
    pairs = []
    for a, b in itertools.combinations(sorted(fold), 2):
        common = fold[a].keys() & fold[b].keys()
        if len(common) < MIN_SHARED: continue
        same = sorted(c for c in common if fold[a][c][2] & fold[b][c][2])
        examples = [{"code": c, "a": fold[a][c][1], "b": fold[b][c][1]} for c in sorted(common)[:PAIR_EXAMPLES]]
        pairs.append({"a": a, "b": b, "shared": len(common), "same_label": len(same),
                      "same_label_share": round(len(same) / len(common), 4),
                      "share_of_a": round(len(common) / len(fold[a]), 4), "share_of_b": round(len(common) / len(fold[b]), 4),
                      "jaccard": round(len(common) / len(fold[a].keys() | fold[b].keys()), 4),
                      "derived_pair": derived.get(a) == b or derived.get(b) == a, "examples": examples})
    return sorted(pairs, key=lambda x: (-x["shared"], x["a"], x["b"]))


def fields(rows):
    vals = collections.defaultdict(list)  # field -> [(code, value)]
    for r in rows:
        for v in r["aliases"] or []:
            vals["aliases"].append((r["code"], v))
        for k, v in (json.loads(r["extra"]) if r["extra"] else {}).items():
            for x in (v if isinstance(v, list) else [v]):
                if isinstance(x, str) and x: vals[f"extra.{k}"].append((r["code"], x))
    return vals


def cross_references(systems):
    codes = {s: {r["code"] for r in rows} for s, rows in systems.items()}
    out = []
    for a, rows in systems.items():
        for field, pairs in fields(rows).items():
            distinct = {v for _, v in pairs}
            if len(distinct) < MIN_VALUES: continue
            for b in systems:
                if b == a: continue
                hit = distinct & codes[b]
                if len(hit) / len(distinct) < MIN_COVERAGE: continue
                src_per_val = collections.Counter(v for _, v in pairs if v in hit)
                val_per_src = collections.Counter(c for c, v in pairs if v in hit)
                card = ("1" if max(val_per_src.values()) == 1 else "n") + ":" + ("1" if max(src_per_val.values()) == 1 else "n")
                out.append({"system": a, "field": field, "target": b, "values": len(distinct),
                            "coverage": round(len(hit) / len(distinct), 4),
                            "target_covered": round(len(hit) / len(codes[b]), 4), "cardinality": card})
    return sorted(out, key=lambda x: (-x["coverage"], -x["values"], x["system"], x["field"], x["target"]))


def readings(fold):
    owners = collections.defaultdict(list)
    for s, d in fold.items():
        for k in d: owners[k].append(s)
    top = sorted(owners.items(), key=lambda kv: (-len(kv[1]), kv[0]))[:TOP_LITERALS]
    return [{"literal": k, "systems": len(ss),
             "readings": [{"system": s, "code": fold[s][k][0], "label": fold[s][k][1]} for s in sorted(ss)]}
            for k, ss in top]


# ------------------------------------------------------------------------------------------------ figures

STYLE = """<style>
.viz{--surface:#fcfcfb;--ink:#0b0b0b;--ink2:#52514e;--grid:#e4e3df;--mark:#2a78d6;--ring:#fcfcfb;
--s0:#f0efec;--s1:#cde2fb;--s2:#9ec5f4;--s3:#6da7ec;--s4:#3987e5;--s5:#256abf;--s6:#184f95;--s7:#0d366b}
@media (prefers-color-scheme:dark){.viz{--surface:#1a1a19;--ink:#f0efec;--ink2:#c3c2b7;--grid:#383835;--mark:#3987e5;
--ring:#1a1a19;--s0:#262624;--s1:#0d366b;--s2:#104281;--s3:#184f95;--s4:#1c5cab;--s5:#256abf;--s6:#3987e5;--s7:#86b6ef}}
text{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Helvetica,Arial,sans-serif;fill:var(--ink)}
.t2{fill:var(--ink2)}.bg{fill:var(--surface)}.grid{stroke:var(--grid);stroke-width:1}
</style>"""
BINS = [0, 0.05, 0.15, 0.3, 0.5, 0.7, 0.9, 1.0001]  # containment steps for the eight sequential fills


def step(v):
    return next(i for i, hi in enumerate(BINS[1:]) if v < hi) if v > 0 else 0


def matrix_svg(fold, pairs):
    """cell (row, column) = share of the row system's codes that the column system also has."""
    involved = sorted({p["a"] for p in pairs} | {p["b"] for p in pairs},
                      key=lambda s: (DOMAINS.index(s.split("/")[0]), s))
    share = {}
    for p in pairs:
        share[(p["a"], p["b"])] = (p["share_of_a"], p["shared"])
        share[(p["b"], p["a"])] = (p["share_of_b"], p["shared"])
    n, cell, left, top = len(involved), 14, 78, 78
    w, h = left + n * cell + 250, top + n * cell + 40
    s = [f'<svg xmlns="http://www.w3.org/2000/svg" class="viz" viewBox="0 0 {w} {h}" width="{w}" height="{h}" '
         f'role="img" aria-label="Share of each system\'s codes that another system also has">', STYLE,
         f'<rect class="bg" width="{w}" height="{h}"/>']
    for i, sid in enumerate(involved):
        y = top + i * cell
        s.append(f'<text x="{left - 6}" y="{y + 10.5}" font-size="10" text-anchor="end" class="t2">{sid}</text>')
        x = left + i * cell
        s.append(f'<text transform="translate({x + 10},{top - 6}) rotate(-60)" font-size="10" class="t2">{sid}</text>')
    for i, a in enumerate(involved):
        for j, b in enumerate(involved):
            x, y = left + j * cell, top + i * cell
            if a == b:
                s.append(f'<rect x="{x + 1}" y="{y + 1}" width="{cell - 2}" height="{cell - 2}" rx="2" fill="var(--grid)"/>')
                continue
            v, k = share.get((a, b), (0, 0))
            tip = f"{a} in {b}: {k:,} shared codes, {v:.1%} of {a}" if k else f"{a} and {b}: fewer than {MIN_SHARED} shared codes"
            s.append(f'<rect x="{x + 1}" y="{y + 1}" width="{cell - 2}" height="{cell - 2}" rx="2" '
                     f'fill="var(--s{step(v)})"><title>{escape(tip)}</title></rect>')
    # domain separators
    prev = None
    for i, sid in enumerate(involved):
        d = sid.split("/")[0]
        if prev and d != prev:
            p = i * cell
            s.append(f'<line class="grid" x1="{left}" x2="{left + n * cell}" y1="{top + p}" y2="{top + p}" stroke-width="2"/>')
            s.append(f'<line class="grid" y1="{top}" y2="{top + n * cell}" x1="{left + p}" x2="{left + p}" stroke-width="2"/>')
        prev = d
    lx, ly = left + n * cell + 24, top
    s.append(f'<text x="{lx}" y="{ly}" font-size="11" font-weight="600">Share of the row system\'s</text>')
    s.append(f'<text x="{lx}" y="{ly + 14}" font-size="11" font-weight="600">codes in the column system</text>')
    labels = ["none, or under 10 codes", "under 5%", "5 to 15%", "15 to 30%", "30 to 50%", "50 to 70%", "70 to 90%", "90% or more"]
    for i, lab in enumerate(labels):
        y = ly + 30 + i * 18
        s.append(f'<rect x="{lx}" y="{y}" width="12" height="12" rx="2" fill="var(--s{i})"/>')
        s.append(f'<text x="{lx + 18}" y="{y + 10}" font-size="10" class="t2">{lab}</text>')
    s.append("</svg>")
    return "\n".join(s)


def pairs_svg(pairs):
    """x: shared codes (log scale); y: share of shared codes with the same name in both systems."""
    pts = [p for p in pairs if not p["derived_pair"]]
    w, h, l, r, t, b = 900, 540, 64, 210, 56, 56
    pw, ph = w - l - r, h - t - b
    xmax = 10 ** math.ceil(math.log10(max(p["shared"] for p in pts)))
    X = lambda v: l + (math.log10(v) - 1) / (math.log10(xmax) - 1) * pw
    Y = lambda v: t + (1 - v) * ph
    s = [f'<svg xmlns="http://www.w3.org/2000/svg" class="viz" viewBox="0 0 {w} {h}" width="{w}" height="{h}" '
         f'role="img" aria-label="Pairs of systems by shared codes and by the share of those codes with the same name">',
         STYLE, f'<rect class="bg" width="{w}" height="{h}"/>']
    for v in [10 ** e for e in range(1, int(math.log10(xmax)) + 1)]:
        s.append(f'<line class="grid" x1="{X(v):.1f}" x2="{X(v):.1f}" y1="{t}" y2="{t + ph}"/>')
        s.append(f'<text x="{X(v):.1f}" y="{t + ph + 16}" font-size="10" text-anchor="middle" class="t2">{v:,}</text>')
    for v in (0, 0.25, 0.5, 0.75, 1):
        s.append(f'<line class="grid" x1="{l}" x2="{l + pw}" y1="{Y(v):.1f}" y2="{Y(v):.1f}"/>')
        s.append(f'<text x="{l - 8}" y="{Y(v) + 3.5:.1f}" font-size="10" text-anchor="end" class="t2">{v:.0%}</text>')
    s.append(f'<text x="{l + pw / 2}" y="{h - 14}" font-size="11" text-anchor="middle" class="t2">Codes the two systems share (log scale)</text>')
    s.append(f'<text transform="translate(16,{t + ph / 2}) rotate(-90)" font-size="11" text-anchor="middle" class="t2">'
             f'Shared codes with the same name in both</text>')
    for p in sorted(pts, key=lambda p: p["shared"]):
        tip = (f"{p['a']} and {p['b']}: {p['shared']:,} shared codes, {p['same_label']:,} with the same name "
               f"({p['same_label_share']:.1%})")
        s.append(f'<circle cx="{X(p["shared"]):.1f}" cy="{Y(p["same_label_share"]):.1f}" r="4.5" fill="var(--mark)" '
                 f'stroke="var(--ring)" stroke-width="2"><title>{escape(tip)}</title></circle>')
    # direct labels: the pairs with the most shared codes and the pairs whose names agree most, without overlaps
    chosen = sorted(pts, key=lambda p: -p["shared"])[:2] + [p for p in pts if p["same_label_share"] > 0.5]
    placed = []
    for p in chosen:
        x, y = X(p["shared"]), Y(p["same_label_share"])
        text = f'{p["a"]} · {p["b"]}'
        for dy in (4, -10, 16, -22, 28, -34):
            box = (x + 8, y + dy - 10, x + 8 + 6.2 * len(text), y + dy + 2)
            if box[2] < w - 6 and not any(not (box[2] < q[0] or box[0] > q[2] or box[3] < q[1] or box[1] > q[3]) for q in placed):
                placed.append(box)
                s.append(f'<text x="{box[0]:.1f}" y="{y + dy:.1f}" font-size="10" class="t2">{text}</text>')
                break
    s.append(f'<text x="{l}" y="{t - 30}" font-size="11" class="t2">Each dot is a pair of systems sharing {MIN_SHARED} or more codes; '
             f'the derived pair lng/b47 and lng/i63 is left out</text>')
    low = sum(p["same_label_share"] < 0.01 for p in pts)
    s.append(f'<text x="{X(10) + 4:.1f}" y="{Y(0.2):.1f}" font-size="10" class="t2">{low} of {len(pts)} pairs: '
             f'under 1% of shared codes with the same name</text>')
    s.append("</svg>")
    return "\n".join(s)


def main(root, out, figdir=None):
    systems, derived = load(root)
    fold = folded(systems)
    pairs = shared_codes(fold, derived)
    result = {"systems": len(systems), "min_shared": MIN_SHARED, "min_values": MIN_VALUES, "min_coverage": MIN_COVERAGE,
              "pairs": len(pairs),
              "pairs_same_label_over_half": sum(p["same_label_share"] > 0.5 for p in pairs if not p["derived_pair"]),
              "pairs_same_label_under_1pct": sum(p["same_label_share"] < 0.01 for p in pairs if not p["derived_pair"]),
              "shared_codes": pairs, "cross_references": cross_references(systems), "readings": readings(fold)}
    pathlib.Path(out).write_text(json.dumps(result, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    if figdir:
        d = pathlib.Path(figdir); d.mkdir(parents=True, exist_ok=True)
        (d/"similarity_matrix.svg").write_text(matrix_svg(fold, pairs), encoding="utf-8")
        (d/"similarity_pairs.svg").write_text(pairs_svg(pairs), encoding="utf-8")
    print(f"{len(pairs)} pairs share >= {MIN_SHARED} codes; {result['pairs_same_label_over_half']} of them name more than "
          f"half of those codes the same way; {len(result['cross_references'])} cross-reference fields")


if __name__ == "__main__":
    main(*sys.argv[1:])
