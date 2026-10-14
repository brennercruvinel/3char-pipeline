"""Every number the card quotes, checked against the outputs of census.py, keys.py and crosscheck_wikidata.py.

usage: python card_check.py <README.md> <census.json> <keys.json> <crosscheck.json>
Exits non-zero on the first mismatch or missing figure.
"""
import json
import re
import sys


def fmt(n): return f"{n:,}"


def main(card, census, keys, cross):
    text = open(card, encoding="utf-8").read(); c = json.load(open(census)); k = json.load(open(keys)); x = json.load(open(cross))
    expect = {"systems": c["systems"], "rows": c["rows"], "distinct literals": c["distinct_literals"], "in one system": c["k_hist"]["1"],
              "in two or more": c["in_two_or_more"], "in three or more": c["in_three_or_more"], "collapsed": c["after_collapsing_derived_families"]}
    for L in c["length_curve"][:5]:
        expect[f"L{L['length']} claimed"] = L["claimed"]; expect[f"L{L['length']} two"] = L["in_two_or_more"]
    for sid, e in k.items():
        if not e["code_unique"]: expect[f"{sid} rows"] = e["rows"]; expect[f"{sid} distinct"] = e["distinct_codes"]
    for r in x:
        if r.get("rejected"): expect[f"{r['system']} rejected"] = r["rejected"]
    ok = True
    for name, n in expect.items():
        hit = fmt(n) in text or (n < 1000 and re.search(rf"\b{n}\b", text))
        print(f"{'ok ' if hit else 'MISSING'} {name:28s} {fmt(n)}"); ok &= bool(hit)
    contained = c["fully_contained_systems"]
    for sid in contained:
        if f"`{sid}`" not in text: print("MISSING contained", sid); ok = False
    for sid, v in c["per_system"].items():
        line = next((l for l in text.splitlines() if l.startswith(f"| `{sid}` |")), None)
        if line and f"| {fmt(v['rows'])} |" not in line: print("COUNT MISMATCH", sid, v["rows"]); ok = False
    for L in c["length_curve"][:5]:
        if f"| {L['length']} | {fmt(L['space'])} | {fmt(L['claimed'])} | {fmt(L['in_two_or_more'])} | {L['observed_rate']:.3f} |" not in text:
            print("CURVE ROW MISMATCH", L["length"]); ok = False
    print("ALL OK" if ok else "CHECK FAILED"); sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main(*sys.argv[1:])
