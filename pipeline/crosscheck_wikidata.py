"""Every published code against the Wikidata format constraint (P1793) of the matching property, full match.

usage: python crosscheck_wikidata.py <3char_root> <wikidata_p1793.tsv> [out.json]
The tsv has columns ?p ?pLabel ?regex from a SPARQL export. Forms compared: ICD-10-CM in dotted form (the authority
file is undotted); UN/LOCODE as the full locode in extra.locode (the bare code has no country); BCP 47 language
subtags only, because P305 describes full tags and the registry holds seven subtag types.
"""
import csv
import json
import re
import sys

import pyarrow.parquet as pq

PAIRS = [("cls/icd", "P4229"), ("lng/glt", "P1394"), ("lng/i39", "P218"), ("lng/i63", "P220"), ("lng/ioc", "P984"), ("bio/gen", "P353"),
         ("bio/pdb", "P638"), ("fin/i42", "P498"), ("lng/i15", "P506"), ("trp/unl", "P1937"), ("wrt/tz", "P6687"), ("cls/loc", "P1149"), ("lng/b47", "P305")]


def forms(sid, rows):
    if sid == "cls/icd": return [c if len(c) <= 3 else c[:3] + "." + c[3:] for c in (r["code"] for r in rows)]
    if sid == "trp/unl": return [json.loads(r["extra"])["locode"] for r in rows]
    if sid == "lng/b47": return [r["code"] for r in rows if json.loads(r["extra"]).get("type") == "language"]
    return [r["code"] for r in rows]


def main(root, tsv, out=None):
    wd = {}
    for r in csv.DictReader(open(tsv, encoding="utf-8"), delimiter="\t"):
        wd.setdefault(r["?p"].rsplit("/", 1)[-1].rstrip(">"), []).append(r["?regex"].strip().strip('"').replace("\\\\", "\\"))
    res = []
    for sid, prop in PAIRS:
        rows = pq.read_table(f"{root}/data/{sid}.parquet", columns=["code", "extra"]).to_pylist()
        vals = forms(sid, rows)
        for rx in wd.get(prop, []):
            try: c = re.compile(rx)
            except re.error as e: res.append({"system": sid, "property": prop, "regex": rx, "error": str(e)}); continue
            bad = [v for v in vals if not c.fullmatch(v)]
            res.append({"system": sid, "property": prop, "regex": rx, "tested": len(vals), "rejected": len(bad), "examples": bad[:8]})
    if out: json.dump(res, open(out, "w"), indent=1)
    for r in res: print(f"{r['system']:8s} {r['property']:6s} rejected {r.get('rejected')}/{r.get('tested')}  {r.get('examples', r.get('error'))[:6]}")


if __name__ == "__main__":
    main(*sys.argv[1:])
