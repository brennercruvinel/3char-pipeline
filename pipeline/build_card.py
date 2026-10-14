"""Generate hub/README.md. The YAML front matter and the per-domain systems tables come from systems.parquet and
hub_manifest.json; the prose comes from pipeline/card_body.md, where {{SYSTEMS_TABLES}} marks where the tables go.
CH3_HUB_DIR overrides the hub folder."""
import json, os, pathlib, sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import pyarrow.parquet as pq
from core import ROOT

HUB = pathlib.Path(os.environ.get("CH3_HUB_DIR", ROOT/"hub"))
CFG = lambda sid: sid.replace("/", "-")
# Names and authorities in systems.parquet are stored as written in the metadata, often in lowercase. The card shows
# them with an initial capital, except where the first word is a name that is lowercase by convention.
KEEP_CASE = {"x86", "x86-64", "openCypher", "vCard", "schema.org", "tz", "wwPDB", "arXiv"}
display = lambda v: v if not v or v.split()[0] in KEEP_CASE else v[0].upper() + v[1:]

# The kind of list each system is. The card explains the five kinds; regular expressions and the remaining
# metadata stay in systems.parquet, which the card points to instead of repeating.
KINDS = {
 "Assigned code": ["bio/ec", "bio/gen", "bio/pdb", "cls/icd", "cls/loc", "cmp/dns", "cmp/ern", "cmp/htt", "cmp/mim",
                   "cmp/sts", "fin/cfi", "fin/i42", "fin/tck", "lng/b47", "lng/glt", "lng/i15", "lng/i31", "lng/i39",
                   "lng/i63", "lng/ioc", "nte/wnt", "trp/iata", "trp/ica2", "trp/icao", "trp/tld", "trp/unl",
                   "wrt/iau", "wrt/tz"],
 "Symbol": ["bio/aa1", "bio/aa3", "bio/cdn", "cls/elm", "com/bau", "com/mor", "com/tlg", "wrt/abj", "wrt/uni"],
 "Vocabulary term": ["cmp/asm", "cmp/css", "cmp/git", "cmp/hex", "cmp/reg", "cmp/vim", "grf/act", "grf/foa",
                     "grf/gql", "grf/lpg", "grf/oid", "grf/org", "grf/rdf", "grf/sch", "grf/shc", "grf/sio",
                     "grf/vcd", "lng/mdy"],
 "Community convention": ["cmp/ext", "cmp/frc"],
 "Test vector": ["trp/olc"],
}
KIND = {sid: kind for kind, sids in KINDS.items() for sid in sids}

DOMAIN_NAME = {
 "bio":"biology","cls":"classification","cmp":"computing","com":"communication",
 "fin":"finance","grf":"graph and vocabulary","lng":"language","nte":"lexical",
 "trp":"transport and place","wrt":"writing and time",
}


def yaml_front_matter(publish):
    y = ["---", "pretty_name: 3char", "license: other", "license_name: mixed-per-system",
         "license_link: https://huggingface.co/datasets/brennercruvinel/3char#licensing",
         "language:", "- en",
         "tags:", "- code-systems", "- controlled-vocabulary",
         "- taxonomy", "- identifiers", "- three-letter-codes", "- knowledge-base",
         "size_categories:", "- 100K<n<1M", "configs:",
         "- config_name: all", "  data_files:", "  - split: train", "    path: data/*/*.parquet",
         "- config_name: systems", "  data_files:", "  - split: train", "    path: systems.parquet"]
    for sid in publish:
        y += [f"- config_name: {CFG(sid)}", "  data_files:", "  - split: train", f"    path: data/{sid}.parquet"]
    return "\n".join(y + ["---", ""])


def systems_tables(publish, counts, sysrows):
    doms = {}
    for sid in publish: doms.setdefault(sid.split("/")[0], []).append(sid)
    b = []
    for dom in sorted(doms):
        b.append(f"### {DOMAIN_NAME[dom].capitalize()} (`{dom}`)\n")
        b.append("| ID | System | Kind | Authority | Codes |\n| --- | --- | --- | --- | ---: |")
        for sid in sorted(doms[dom]):
            r = sysrows[sid]
            b.append(f"| `{sid}` | {display(r['name'])} | {KIND[sid]} | {display(r['authority'])} | {counts[sid]:,} |")
        b.append("")
    return "\n".join(b).strip("\n")


def main():
    man = json.loads((ROOT/"pipeline"/"hub_manifest.json").read_text())
    publish, counts = man["publish"], man["counts"]
    sysrows = {r["system_id"]: r for r in pq.read_table(HUB/"systems.parquet").to_pylist()}
    assert set(KIND) == set(publish), f"KINDS does not cover the published systems: {sorted(set(KIND) ^ set(publish))}"
    body = (ROOT/"pipeline"/"card_body.md").read_text(encoding="utf-8")
    assert "{{SYSTEMS_TABLES}}" in body, "card_body.md must contain {{SYSTEMS_TABLES}}"
    out = yaml_front_matter(publish) + body.replace("{{SYSTEMS_TABLES}}", systems_tables(publish, counts, sysrows))
    (HUB/"README.md").write_text(out, encoding="utf-8")
    print(f"README.md: {len(publish)+2} configs, {out.count(chr(10))} lines")


if __name__ == "__main__":
    main()
