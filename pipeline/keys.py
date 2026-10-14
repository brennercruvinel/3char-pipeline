"""Identification keys per system: whether `code` is unique within a system and, when not, which field resolves a record.

usage: python keys.py <3char_root> [out.json]
"""
import collections
import glob
import json
import sys

import pyarrow.parquet as pq


def main(root, out=None):
    res = {}
    for p in sorted(glob.glob(f"{root}/data/*/*.parquet")):
        t = pq.read_table(p, columns=["system_id", "code", "label", "extra"]).to_pylist(); sid = t[0]["system_id"]
        n = len(t); codes = [r["code"] for r in t]; nd = len(set(codes))
        entry = {"rows": n, "distinct_codes": nd, "code_unique": n == nd, "repeated_codes": sum(v > 1 for v in collections.Counter(codes).values()), "key": ["code"]}
        if n != nd:
            ex = [json.loads(r["extra"]) if r["extra"] else {} for r in t]
            PREFER = ["type", "kind", "locode", "country", "group"]
            fields = sorted({k for e in ex for k in e}, key=lambda k: (PREFER.index(k) if k in PREFER else len(PREFER), k))
            for k in fields:
                if len({(r["code"], json.dumps(e.get(k), sort_keys=True)) for r, e in zip(t, ex)}) == n: entry["key"] = ["code", f"extra.{k}"]; break
            else:
                best = max(({k: len({(r["code"], json.dumps(e.get(k), sort_keys=True)) for r, e in zip(t, ex)}) for k in fields}).items(), key=lambda x: x[1])
                entry["key"] = ["code", f"extra.{best[0]}"]; entry["rows_still_repeated_under_key"] = n - best[1]
                entry["code_label_unique"] = len({(r["code"], r["label"]) for r in t}) == n
        res[sid] = entry
    if out: json.dump(res, open(out, "w"), indent=1)
    for sid, e in res.items():
        if not e["code_unique"]: print(sid, e)
    print("code unique in", sum(e["code_unique"] for e in res.values()), "of", len(res))


if __name__ == "__main__":
    main(*sys.argv[1:])
