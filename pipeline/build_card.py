"""generate hub/README.md: yaml configs plus the card, systems table built from parquet."""
import json, pathlib, sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import pyarrow.parquet as pq
from core import ROOT

HUB = ROOT/"hub"
CFG = lambda sid: sid.replace("/", "-")
# a regex goes inside a table cell, and a bare | ends the cell even inside backticks.
# GFM resolves \| before inline parsing, so it survives into the code span. an html
# entity would not: entities are left alone inside code spans and would render literally.
md_cell = lambda v: v.replace("|", r"\|")

DOMAIN_NAME = {
 "bio":"biology","cls":"classification","cmp":"computing","com":"communication",
 "fin":"finance","grf":"graph and vocabulary","lng":"language","nte":"lexical",
 "trp":"transport and place","wrt":"writing and time",
}

def main():
    man = json.loads((ROOT/"pipeline"/"hub_manifest.json").read_text())
    publish, counts = man["publish"], man["counts"]
    sysrows = {r["system_id"]: r for r in pq.read_table(HUB/"systems.parquet").to_pylist()}
    total = sum(counts.values())

    y = ["---", "pretty_name: 3char", "license: other", "license_name: mixed-per-system",
         "license_link: https://huggingface.co/datasets/brennercruvinel/3char#provenance-and-licensing",
         "language:", "- en",
         "tags:", "- code-systems", "- controlled-vocabulary",
         "- taxonomy", "- identifiers", "- three-letter-codes", "- knowledge-base",
         f"size_categories:", "- 100K<n<1M", "configs:"]
    y += ["- config_name: all", "  data_files:", '  - split: train', '    path: data/*/*.parquet',
          "- config_name: systems", "  data_files:", "  - split: train",
          "    path: systems.parquet"]
    for sid in publish:
        y += [f"- config_name: {CFG(sid)}", "  data_files:", "  - split: train",
              f"    path: data/{sid}.parquet"]
    y += ["---", ""]

    doms = {}
    for sid in publish: doms.setdefault(sid.split("/")[0], []).append(sid)

    b = []
    b.append("# 3char\n")
    b.append(f"{len(publish)} code systems in one schema, {total:,} codes. the codes people "
             "actually type: `SFO`, `EUR`, `Ala`, `mov`, `TXT`, `Sgr`, `application/json`. "
             "three characters is the thesis, not a filter, so the systems that run two or "
             "four or seven characters are here too, each carrying the regex that says what "
             "it really is.\n")
    b.append("i built this because a three character token stopped being a category label for "
             "me and became a fixed memory address. what started as a personal addressing "
             "scheme turned into a question about how many independent authorities landed on "
             "the same shape, and the answer is most of them.\n")

    b.append("### how it loads\n")
    b.append("```python\nfrom datasets import load_dataset\n\n"
             '# every system, one table\nds = load_dataset("brennercruvinel/3char", "all")\n\n'
             '# one system\niata = load_dataset("brennercruvinel/3char", "trp-iata")\n\n'
             '# the registry of systems: authority, license, regex, provenance\n'
             'sysinfo = load_dataset("brennercruvinel/3char", "systems")\n```\n')

    b.append("### schema\n")
    b.append("one row per code, identical arrow schema across every config, which is what "
             "makes `all` concatenate at all.\n")
    b.append("| column | type | what it holds |\n| --- | --- | --- |")
    for c, t, d in [
        ("system_id","string","`<domain>/<id>`, joins to the `systems` config"),
        ("code","string","the code as the authority writes it, verbatim, no case folding"),
        ("label","string","short human name"),
        ("description","string","longer gloss when the source carries one"),
        ("parent_code","string","parent in the same system, for the hierarchical ones"),
        ("status","string","`current`, `deprecated`, `reserved`, `unassigned`, or null"),
        ("aliases","list<string>","other strings that resolve to the same referent"),
        ("extra","string","JSON object, source specific fields that fit nowhere above")]:
        b.append(f"| `{c}` | {t} | {d} |")
    b.append("")
    b.append("`extra` is a JSON string and not a struct on purpose. these sources agree on "
             "almost nothing past code and label, and a struct would push a union of roughly "
             "200 nullable columns onto every row.\n")

    b.append("### the systems\n")
    for dom in sorted(doms):
        b.append(f"##### {dom}, {DOMAIN_NAME[dom]}\n")
        b.append("| id | system | authority | codes | pattern |\n| --- | --- | --- | --- | --- |")
        for sid in sorted(doms[dom]):
            r = sysrows[sid]
            b.append(f"| `{sid}` | {r['name']} | {r['authority']} | {counts[sid]:,} | "
                     f"`{md_cell(r['code_pattern'])}` |")
        b.append("")

    b.append("### provenance and licensing\n")
    b.append("there is no single license here and the card will not pretend otherwise. every "
             "row of the `systems` config carries its own `license` and a `license_status` of "
             "`ok` or `check`, and `authority` is kept separate from `url` because the two "
             "disagree constantly: a code assigned by the WHO can arrive through a github "
             "scrape, and collapsing those hides the thing worth knowing.\n")
    b.append("sources whose terms block redistribution are parsed by the pipeline and never "
             "uploaded. that currently holds back the WHO ATC index, the BISAC subject "
             "headings, the Dewey summaries, the CUSIP mapping, the ISO 10383 MIC list and "
             "the what3words API surface. reading the terms is also what removed the SIL "
             "ISO 639-3 table, which names its own site as the only authorized distribution "
             "point.\n")
    b.append("two systems ship at `check`: `fin/cfi` and `fin/i42`, both from SIX Group, which "
             "publishes free of charge and then says nothing at all about redistribution.\n")
    b.append("only parquet is published. the raw files stay in the [build repo](https://github.com/brennercruvinel/3char-pipeline) and are refetched "
             "from `url`, which matters for the ITU recommendations and the IUPAC table, where "
             "the facts are free to state and the document is not free to mirror.\n")

    b.append("### things that will bite you\n")
    b.append(f"`trp/unl` has {counts.get('trp/unl',0):,} rows and about 90,000 repeated codes. "
             "a UN/LOCODE three letter code is only unique inside its country, so `ADALV` and "
             "`USALV` both carry `ALV`. the country and the full locode are in `extra`. `code` "
             "is not a key in that system, and it is not a bug.\n")
    b.append("`lng/i63` is not ISO 639-3, and is not labelled as such. it is the three letter "
             "language subtags as IANA publishes them. RFC 5646 omits the three letter form "
             "whenever a two letter subtag exists, so `eng`, `deu` and `por` are absent by "
             "design, the registry carries `en`, `de` and `pt` instead. it also carries 115 "
             "ISO 639-5 collections and 224 deprecated subtags that ISO 639-3 does not.\n")
    b.append("`com/tlg` is a 1901 book scan. the plain OCR text is useless for the job, because "
             "the book sets code number, code word and phrase in three columns and the text "
             "derivative emits the columns as separate runs of lines, which destroys the pairing "
             "that makes a code a code. this parses the djvu xml instead, where every word keeps "
             "a bounding box, and rebuilds the columns from the x coordinate. 92 percent of the "
             "code words come back with their phrase attached. the rest, and the code numbers on "
             "the left, are as good as a hundred and twenty year old scan allows.\n")
    b.append(f"`cmp/sts` carries {counts.get('cmp/sts',0)} rows for a registry that assigns about "
             "64 status codes. IANA writes the gaps as ranges, `105-199`, and those are expanded "
             "to one row each: an assigned code has a description and a null status, an unassigned "
             "one has `status = unassigned` and an empty label. filter on `status` to get the "
             "registry as most people picture it.\n")
    b.append("`trp/olc` is the reference encoder test vectors, not a registry. plus codes are "
             "generated from coordinates, so no complete enumeration exists to ship.\n")
    b.append("`trp/iata` and `trp/icao` both come from the OurAirports public domain file, read "
             "on different columns. neither is an official IATA or ICAO publication.\n")
    b.append("`code_pattern` is enforced: the build fails if any code in a system does not match "
             "it. `pattern_status` says how much that is worth. `derived` means the regex was "
             "written against the real file, `provisional` means it is still loose and will "
             "tighten. writing these patterns caught 13 of my own wrong assumptions and exactly "
             "one malformed row upstream.\n")

    b.append("### what is not here\n")
    b.append(f"all 64 systems parse and validate. {len(man['blocked'])} of them are held back "
             "from upload because their authority forbids redistribution: the WHO ATC index, "
             "the BISAC subject headings, the Dewey summaries, the CUSIP mapping, the ISO 10383 "
             "MIC list and the what3words API surface. the parsers for those live in the "
             "[build repo](https://github.com/brennercruvinel/3char-pipeline) and run locally against the sources you fetch yourself.\n")

    b.append("### build\n")
    b.append("every parser, the schema, the checksum manifest and the license triage with its "
             "verbatim quotes live at "
             "[github.com/brennercruvinel/3char-pipeline](https://github.com/brennercruvinel/3char-pipeline). "
             "`download.py` refetches every source and fails on any checksum drift, `validate.py` "
             "tests every code against its system's regex. the raw files are not in that repo "
             "either, for the same licensing reason they are not here.\n")
    b.append("### citation\n")
    b.append("```bibtex\n@misc{cruvinel_3char,\n  title  = {3char: three character code systems "
             "in one schema},\n  author = {Cruvinel, Brenner},\n  year   = {2026},\n"
             "  url    = {https://huggingface.co/datasets/brennercruvinel/3char}\n}\n```\n")

    (HUB/"README.md").write_text("\n".join(y) + "\n".join(b))
    print(f"README.md: {len(y)} yaml lines, {len(publish)+2} configs")

if __name__ == "__main__":
    sys.exit(main())
