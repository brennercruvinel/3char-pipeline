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
    b.append(f"{len(publish)} code systems in one schema, {total:,} codes. airport and currency "
             "codes, amino acid symbols, assembly mnemonics, media types, constellation "
             "abbreviations, HTTP status codes, and the other short identifiers that standards "
             "bodies assign. three characters is the organizing thesis, not a filter. systems "
             "with two, four or seven character codes are included, each with the regex that "
             "describes its actual form.\n")
    b.append("the collection documents how many independent authorities converged on short "
             "fixed width identifiers, and gathers them under one schema so they can be joined, "
             "validated and retrieved together.\n")

    b.append("### loading\n")
    b.append("```python\nfrom datasets import load_dataset\n\n"
             '# every system, one table\nds = load_dataset("brennercruvinel/3char", "all")\n\n'
             '# one system\niata = load_dataset("brennercruvinel/3char", "trp-iata")\n\n'
             '# the registry of systems: authority, license, regex, provenance\n'
             'sysinfo = load_dataset("brennercruvinel/3char", "systems")\n```\n')

    b.append("### schema\n")
    b.append("one row per code. the arrow schema is identical across every config, which is "
             "what allows the `all` config to concatenate them.\n")
    b.append("| column | type | description |\n| --- | --- | --- |")
    for c, t, d in [
        ("system_id","string","`<domain>/<id>`, joins to the `systems` config"),
        ("code","string","the code as the authority writes it, verbatim, no case folding"),
        ("label","string","short human readable name"),
        ("description","string","longer gloss when the source provides one"),
        ("parent_code","string","parent code in the same system, for hierarchical systems"),
        ("status","string","`current`, `deprecated`, `reserved`, `unassigned`, or null"),
        ("aliases","list<string>","other strings that resolve to the same referent"),
        ("extra","string","JSON object with source specific fields not covered above")]:
        b.append(f"| `{c}` | {t} | {d} |")
    b.append("")
    b.append("`extra` is stored as a JSON string rather than a struct. the sources share few "
             "fields beyond code and label, and a struct would require a union of roughly 200 "
             "nullable columns on every row.\n")

    b.append("### systems\n")
    for dom in sorted(doms):
        b.append(f"##### {dom}, {DOMAIN_NAME[dom]}\n")
        b.append("| id | system | authority | codes | pattern |\n| --- | --- | --- | --- | --- |")
        for sid in sorted(doms[dom]):
            r = sysrows[sid]
            b.append(f"| `{sid}` | {r['name']} | {r['authority']} | {counts[sid]:,} | "
                     f"`{md_cell(r['code_pattern'])}` |")
        b.append("")

    b.append("### provenance and licensing\n")
    b.append("there is no single license. every row of the `systems` config carries its own "
             "`license` and a `license_status` of `ok` or `check`. `authority` is kept separate "
             "from `url` because the body that assigns a code and the site that serves the file "
             "frequently differ, and that distinction is part of the provenance.\n")
    b.append("sources whose terms prohibit redistribution are parsed by the pipeline and not "
             "uploaded: the WHO ATC index, the BISAC subject headings, the Dewey summaries, the "
             "CUSIP mapping, the ISO 10383 MIC list and the what3words API surface. the SIL "
             "ISO 639-3 table was removed on the same basis, since its terms name the SIL site "
             "as the only authorized distribution point.\n")
    b.append("two systems are published with `license_status = check`: `fin/cfi` and `fin/i42`, "
             "both from SIX Group, which publishes the lists free of charge without stating "
             "redistribution terms.\n")
    b.append("only parquet is published. raw files are retrieved from `url` by the "
             "[build repo](https://github.com/brennercruvinel/3char-pipeline) and are not "
             "stored in either repository. this matters for the ITU recommendations and the "
             "IUPAC table, where the facts are freely usable and the documents are not freely "
             "mirrorable.\n")

    b.append("### known limitations\n")
    b.append(f"`trp/unl` has {counts.get('trp/unl',0):,} rows and about 90,000 repeated codes. "
             "a UN/LOCODE location code is unique only within its country, so `ADALV` and "
             "`USALV` both carry `ALV`. the country and the full locode are in `extra`. `code` "
             "is not a unique key in that system.\n")
    b.append("`lng/i63` is not ISO 639-3 and is not labelled as such. it holds the three letter "
             "language subtags as published by IANA. RFC 5646 omits the three letter form "
             "whenever a two letter subtag exists, so `eng`, `deu` and `por` are absent and the "
             "registry carries `en`, `de` and `pt` instead. it also includes 115 ISO 639-5 "
             "collections and 224 deprecated subtags that ISO 639-3 does not.\n")
    b.append("`com/tlg` is parsed from a 1901 book scan. the plain OCR text emits the three "
             "columns (code number, code word, phrase) as separate runs of lines, which loses "
             "the pairing between them. the parser reads the djvu xml instead, where every word "
             "keeps a bounding box, and rebuilds the columns from the x coordinate. 92 percent "
             "of code words are recovered with their phrase. the remainder, and the code numbers "
             "in the left column, are limited by the quality of the scan.\n")
    b.append(f"`cmp/sts` carries {counts.get('cmp/sts',0)} rows for a registry that assigns about "
             "64 status codes. IANA publishes the gaps as ranges such as `105-199`, and these are "
             "expanded to one row each. an assigned code has a description and a null status. an "
             "unassigned one has `status = unassigned` and an empty label. filter on `status` to "
             "obtain the assigned codes only.\n")
    b.append("`trp/olc` contains the reference encoder test vectors, not a registry. plus codes "
             "are generated from coordinates and no complete enumeration exists.\n")
    b.append("`trp/iata` and `trp/icao` are both derived from the OurAirports public domain file, "
             "read on different columns. neither is an official IATA or ICAO publication.\n")
    b.append("`lng/ioc` carries the ISO 3166 alpha-3 code in `extra.iso3` and the FIFA code in "
             "`extra.fifa`. `aliases` holds only the codes that differ from the IOC code. release "
             "0.1.0 placed both in `aliases` without labels, including a footnote marker from the "
             "source for the United Kingdom. corrected in 0.1.1.\n")
    b.append("`code_pattern` is enforced at build time: the build fails if any code in a system "
             "does not match its pattern. `pattern_status` records how the pattern was obtained. "
             "`derived` means the regex was written against the actual file. `provisional` means "
             "it is still loose and may tighten in a later release. writing these patterns "
             "identified 25 incorrect assumptions in the parsers and one malformed row upstream.\n")

    b.append("### retrieval\n")
    b.append("the tables were evaluated as retrieval corpora on this parquet, using a 51 question "
             "answer key verified against the data and a grid that varies one factor at a time: "
             "chunk granularity (record, block of 20, whole system), chunk form (key=value or "
             "one sentence of prose), key form (`GRU` or `iata:GRU`) and embedder "
             "(all-MiniLM-L6-v2, multilingual-e5-small). the rig and its raw output are at "
             "[github.com/brennercruvinel/3char-bench](https://github.com/brennercruvinel/3char-bench).\n")
    b.append("| configuration | result |\n| --- | --- |")
    b.append("| one record per chunk, prose, e5 | 92.2% recall@1, 100% recall@5, 22.6 tokens per answer |")
    b.append("| same, with `system:code` as key | 88.2% recall@1, 27.0 tokens |")
    b.append("| block of 20 records | 47.1% recall@1, 460 tokens |")
    b.append("| whole system as one chunk | 90.2% recall@1, 7,467 tokens |")
    b.append("| prose vs the same fields as key=value | +37 points of recall@1 for 1.3x the tokens |")
    b.append("| faiss scalar quantizer, 8 bit | 4x smaller index, identical recall |")
    b.append("")
    b.append("the main result is that `code` should not be indexed on its own. a literal without "
             "its system is ambiguous by construction. across the 58 published systems, case "
             "folded, 14,911 of the 623,141 distinct codes are claimed by two or more systems, "
             "and `AND` and `CAR` by eleven. given a bare literal, the retriever selects the "
             "correct system 33% of the time, which equals the combinatorial floor. with the "
             "system name in the query or in the key, routing accuracy is 99 to 100%. "
             "`system_id` should be carried in the chunk, in the key, or in both.\n")

    b.append("### excluded systems\n")
    b.append(f"all 64 systems parse and validate. {len(man['blocked'])} are held back from upload "
             "because their authority prohibits redistribution: the WHO ATC index, the BISAC "
             "subject headings, the Dewey summaries, the CUSIP mapping, the ISO 10383 MIC list "
             "and the what3words API surface. their parsers are in the "
             "[build repo](https://github.com/brennercruvinel/3char-pipeline) and run locally "
             "against sources fetched by the user.\n")

    b.append("### build\n")
    b.append("the parsers, the schema, the checksum manifest and the license triage with its "
             "verbatim quotes are at "
             "[github.com/brennercruvinel/3char-pipeline](https://github.com/brennercruvinel/3char-pipeline). "
             "`download.py` refetches every source and fails on checksum drift. `validate.py` "
             "tests every code against its system's regex. raw files are not stored in that "
             "repository either, for the same licensing reasons.\n")
    b.append("changes are recorded in [CHANGELOG.md](CHANGELOG.md), including the two sources "
             "that were replaced because the original file was wrong and the eight that were "
             "re-derived from the assigning authority.\n")
    b.append("### citation\n")
    b.append("```bibtex\n@misc{cruvinel_3char,\n  title  = {3char: three character code systems "
             "in one schema},\n  author = {Cruvinel, Brenner},\n  year   = {2026},\n"
             "  url    = {https://huggingface.co/datasets/brennercruvinel/3char}\n}\n```\n")

    (HUB/"README.md").write_text("\n".join(y) + "\n".join(b))
    print(f"README.md: {len(y)} yaml lines, {len(publish)+2} configs")

if __name__ == "__main__":
    sys.exit(main())
