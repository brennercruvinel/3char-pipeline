"""Collision census and per-system counts on a published 3char snapshot.

usage: python census.py <3char_root> [out.json]
Definitions. literal: a code string after casefold. record: one row. system: one parquet. a literal collides when it
occurs in two or more systems. a derived family is a system built from another (systems.derived_from); families are
collapsed by counting the family once. the length curve counts ASCII alphabetic literals only, against a null that
draws each system's literals uniformly from the 26^L strings of that length.
"""
import collections
import glob
import json
import math
import sys

import pyarrow.parquet as pq


def main(root, out=None):
    systems = {r["system_id"]: r for r in pq.read_table(f"{root}/systems.parquet").to_pylist()}
    per, lits = {}, collections.defaultdict(set)
    for p in sorted(glob.glob(f"{root}/data/*/*.parquet")):
        t = pq.read_table(p, columns=["system_id", "code"]); sid = t["system_id"][0].as_py()
        codes = t["code"].to_pylist(); per[sid] = {"rows": len(codes), "distinct_codes": len(set(codes))}
        for c in codes: lits[c.casefold()].add(sid)
    k_hist = collections.Counter(len(s) for s in lits.values())
    fam = {}
    for sid, r in systems.items():
        s = sid
        while systems.get(s, {}).get("derived_from"): s = systems[s]["derived_from"].split(",")[0].strip()
        fam[sid] = s
    collapsed = sum(len({fam[s] for s in ss}) > 1 for ss in lits.values())
    contained = sorted(sid for sid in per if all(len(lits[c]) > 1 for c in lits if sid in lits[c]))
    share = {sid: sum(1 for c, ss in lits.items() if sid in ss and len(ss) > 1) / sum(1 for ss in lits.values() if sid in ss) for sid in per}
    curve = []
    for L in range(1, 8):
        al = [c for c in lits if c.isascii() and c.isalpha() and len(c) == L]
        if not al: continue
        space = 26 ** L; sizes = [sum(1 for c in al if s in lits[c]) for s in per]
        p_unclaimed = [1 - n / space for n in sizes]
        exp_claimed = space * (1 - math.prod(p_unclaimed))
        exp_two = space * (1 - math.prod(p_unclaimed) - sum((sizes[i] / space) * math.prod(p for j, p in enumerate(p_unclaimed) if j != i) for i in range(len(sizes))))
        obs_two = sum(len(lits[c]) > 1 for c in al)
        curve.append({"length": L, "space": space, "claimed": len(al), "in_two_or_more": obs_two, "observed_rate": obs_two / len(al),
                      "null_rate": exp_two / exp_claimed if exp_claimed else None, "null_expected_claimed": exp_claimed})
    top = sorted(((c, sorted(ss)) for c, ss in lits.items()), key=lambda x: -len(x[1]))[:10]
    res = {"systems": len(per), "rows": sum(v["rows"] for v in per.values()), "distinct_literals": len(lits),
           "in_two_or_more": sum(len(s) > 1 for s in lits.values()), "in_three_or_more": sum(len(s) > 2 for s in lits.values()),
           "k_hist": dict(sorted(k_hist.items())), "after_collapsing_derived_families": collapsed, "derived_families": {k: v for k, v in fam.items() if k != v},
           "fully_contained_systems": contained, "share_claimed_elsewhere": share, "top_literals": [{"literal": c, "systems": s} for c, s in top],
           "length_curve": curve, "per_system": per}
    if out: json.dump(res, open(out, "w"), indent=1)
    print(json.dumps({k: v for k, v in res.items() if k not in ("per_system", "share_claimed_elsewhere", "length_curve")}, indent=1))
    for c in curve: print(c)


if __name__ == "__main__":
    main(*sys.argv[1:])
