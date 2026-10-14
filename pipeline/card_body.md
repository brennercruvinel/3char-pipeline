
# 3char

3char is a harmonized collection of 751,870 records from 58 identifier systems, distributed in a common Parquet schema. Records retain their source namespace, while system-level metadata documents provenance, format constraints and licensing. Identifiers are not globally unique, and some systems require additional fields to resolve a record unambiguously.

Release 0.1.2. Data unchanged since 0.1.1 (2026-09-12); this card and the changelog are new. Every statistic below names the script that reproduces it from the published files.

## 1. scope

An identifier system here is a list of short, fixed-width codes assigned by one authority: airport and airline codes, country, currency and language codes, gene symbols, enzyme numbers, HTTP status codes, DNS record types, vocabulary terms, and others. Ten domains, listed in section 3. Three characters is the organizing theme, not a filter: systems with two, four or seven character codes are included, each with the regex that describes its actual form.

The collection is not an inventory of all such systems, and not a current-to-the-day reference. Each system is a snapshot of one source file at one date, recorded per system. Six further systems are parsed by the build pipeline and are not published because their authorities forbid redistribution (section 6).

## 2. obtaining the data

```python
from datasets import load_dataset

ds   = load_dataset("brennercruvinel/3char", "all")        # every system, one table, 751,870 rows
iata = load_dataset("brennercruvinel/3char", "trp-iata")   # one system
meta = load_dataset("brennercruvinel/3char", "systems")    # 58 rows: authority, url, license, regex, version, retrieval date
```

Sixty configs: `all`, `systems`, and one per system named `<domain>-<id>`. The config name uses a hyphen because the Hub does not allow a slash; the `system_id` in the rows keeps the slash, so `trp-iata` returns rows whose `system_id` is `trp/iata`. Every config has one `train` split; nothing was split. Pin a revision for reproducible work: `load_dataset(..., revision="<commit sha>")`. The same files, with a manifest of sha256 and row counts, form the versioned deposit described in section 9.

## 3. records

One row per code. The Arrow schema is identical across systems.

```json
{"system_id": "trp/iata", "code": "GRU",
 "label": "São Paulo/Guarulhos–Governor André Franco Montoro International Airport",
 "description": null, "parent_code": null, "status": null, "aliases": [],
 "extra": "{\"country\": \"BR\", \"municipality\": \"São Paulo\", \"scheduled\": \"yes\", \"type\": \"large_airport\"}"}
```

| column | type | content |
| --- | --- | --- |
| `system_id` | string | `<domain>/<id>`; joins to the `systems` config |
| `code` | string | the code as the authority writes it; no case folding |
| `label` | string | short name from the source |
| `description` | string | longer gloss when the source has one |
| `parent_code` | string | parent code in the same system; present in `bio/ec`, `cls/icd`, `cls/loc` |
| `status` | string | the status word the source publishes, or null; vocabulary per system |
| `aliases` | list<string> | other strings that resolve to the same referent |
| `extra` | string | JSON object with source-specific fields |

`status` is null on 693,350 rows. Where a source publishes one it is kept verbatim: `approved` (44,997 rows, HGNC), `deprecated` (6,793), `fully-qualified` (3,944), `current` (1,069), `minimally-qualified` (1,029), `unassigned` (436), `unqualified` (243), `component` (9). The emoji qualification values belong to `wrt/uni`; filter on `status` per system only.

`extra` is a JSON string rather than a struct because the sources share few fields beyond code and label; a struct would put a union of about 200 nullable columns on every row.

### identifying a record

`code` is unique within 54 of the 58 systems. The exceptions and the field that resolves a record (`keys.py`):

| system | rows | distinct codes | key | residual |
| --- | --- | --- | --- | --- |
| `trp/unl` | 116,213 | 26,162 | `extra.locode` (country plus code) | 139 locodes appear on more than one row as bilingual name variants, 146 extra rows |
| `lng/b47` | 9,295 | 9,037 | `code` plus `extra.type` | none |
| `wrt/tz` | 806 | 797 | `code` plus `extra.kind` | none |
| `wrt/abj` | 84 | 83 | `code` plus `label` | U+05BC appears as `dagesh` and as `mapiq` |

Across systems the only key is `(system_id, code)`, and in `trp/unl` it is `(system_id, extra.locode)`. A bare code identifies nothing: 14,911 literals belong to two or more systems (section 5).

### systems

{{SYSTEMS_TABLES}}

## 4. construction

A system is included when all four conditions hold; each is checked by a column or a file in the [build pipeline](https://github.com/brennercruvinel/3char-pipeline):

| condition | checked by |
| --- | --- |
| an identifiable authority assigns the codes, and the file comes from it or from a public domain derivative | `systems.authority` and `systems.url`, kept as separate columns |
| a regex written against the actual file matches every published code | `systems.code_pattern`, enforced by `validate.py`; `pattern_status` is `derived` for all 58 |
| the authority's terms allow redistribution, or state nothing and the codes are plain facts in daily use | `systems.license`, `license_status`; verbatim terms in `LICENSES.md` |
| the raw file has a recorded sha256 | `CHECKSUMS.tsv`; `download.py` fails on drift |

A system is excluded, with the reason recorded, when its authority forbids redistribution, when no lawful file exists, or when the file is text about codes rather than the list (the first ICD-10-CM source was an instruction-tuning set and was replaced by the CDC order file).

All 58 raw files were retrieved on 2026-09-10. Ten sources publish a version string, read from the file by the pipeline and stored in `systems.version`: ENZYME 28-Jan-2026, ICD-10-CM FY2027, IANA media types 2026-06-05, ISO 4217 list 2026-01-01, the IANA language subtag registry 2026-05-05 (for both `lng/b47` and `lng/i63`), Open English WordNet 2024, the IANA TLD list 2026060600, tzdb 2026b, Unicode emoji 17.0. The other 48 publish none; `retrieved_at` is their only date.

Eight sources that first came from unlicensed gists were re-derived from the assigning body, and two that were the wrong file were replaced; the record is in [CHANGELOG.md](CHANGELOG.md). There is no human annotation: labels, descriptions and aliases are what each source publishes; the curated layer is the `systems` table.

## 5. what is guaranteed and what is not

Guaranteed by the build: every published code matches its system's regex; every raw file's sha256 is recorded; the schema is identical across systems; the published set contains only `license_status` `ok` or `check` (section 6).

Not guaranteed: currency (snapshots at one date); label reconciliation across systems (the same airport is `São Paulo/Guarulhos–Governor André Franco Montoro International Airport` in `trp/iata` and `trp/icao` and `Guarulhos Apt / São Paulo` as `BRGRU` in `trp/unl`); alias coverage (airports carry no city name alias); completeness of the set of systems; uniqueness of `code` outside the 54 systems where it holds.

## 6. licensing

There is no single license. Each row of the `systems` config carries `license` (27 distinct values: SPDX ids where one applies, otherwise a short tag defined in `LICENSES.md`) and `license_status`. On the published set: 56 `ok`, 2 `check`.

- `check`: `fin/cfi` and `fin/i42`, both from SIX Group, which publishes the lists free of charge and states no redistribution terms. They are published because the codes are plain facts in worldwide use; a user who redistributes them commercially should obtain SIX's terms first.
- Copyleft and share-alike, seven systems: `cmp/frc` (GPL-2.0-or-later) and `cmp/git` (GPL-2.0-only) are lists extracted from GPL source trees; `cmp/vim` carries the Vim license; `grf/sch` and `grf/sio` are CC-BY-SA-3.0; `lng/i31` is CC-BY-SA-4.0 through its mirror; `trp/ica2` is ODbL-1.0. Attribution travels with any redistribution; for the share-alike ones, so does the obligation on the table.
- ISO: `lng/i31` and `lng/i39` are `ok` on the strength of their mirrors' licenses; ISO asserts copyright over its code lists, and a mirror's license does not change upstream terms.
- Excluded by their authority's terms, parsed but never uploaded: the WHO ATC index, the BISAC subject headings, the Dewey summaries, the CUSIP mapping, the ISO 10383 MIC list, the what3words API surface. The SIL ISO 639-3 table was removed on the same basis; `lng/i63` is the IANA registry's three-letter subtags, a different list.
- Only parquet is published. Raw files are fetched by the pipeline and never stored in either repository.

## 7. statistics

Every number here is produced by a script in the pipeline (`census.py`, `keys.py`, `crosscheck_wikidata.py`) and checked against this text by `card_check.py`.

### collisions between systems

Definitions. A literal is a code after case folding. A literal collides when it occurs in two or more systems. Denominator: 623,141 distinct literals over the 58 published systems.

| | count |
| --- | --- |
| literals in exactly one system | 608,230 |
| in two or more | 14,911 |
| in three or more | 10,237 |
| in eleven | 2 (`and`, `car`) |
| in two or more after collapsing the one derived family (`lng/i63` is built from `lng/b47`) | 14,845 |

Eight systems are entirely contained in others: every code of `bio/aa1`, `bio/aa3`, `bio/cdn`, `lng/i31`, `lng/i39`, `lng/i63`, `lng/mdy` and `wrt/iau` is also a code elsewhere. `trp/iata`, `lng/ioc`, `lng/i15`, `trp/ica2` and `fin/i42` are above 98%.

Caveats: case folding merges `Ala` (amino acid) with `ALA` (airport); without it, 632,457 distinct strings and 21,255 collide. Collisions are counted between systems; within `trp/unl`, 18,748 bare codes repeat because the key is the country plus the code.

### collisions by code length

ASCII alphabetic literals only. The null model draws each system's literals uniformly from the 26^L strings of length L and asks how many claimed strings would be claimed twice.

| length | strings | claimed | in two or more systems | observed rate | null rate | ratio |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | 26 | 26 | 25 | 0.962 | 0.999 | 0.96 |
| 2 | 676 | 522 | 395 | 0.757 | 0.755 | 1.00 |
| 3 | 17,576 | 17,151 | 12,705 | 0.741 | 0.919 | 0.81 |
| 4 | 456,976 | 17,130 | 734 | 0.043 | 0.012 | 3.6 |
| 5 | 11,881,376 | 4,479 | 96 | 0.021 | 0.0001 | 175 |

Up to three letters the observed rate is at or below the null: 97.6% of all three-letter strings are claimed, and collision follows from capacity. From four letters on, the observed rate exceeds the null by 3.6 and 175 times. The null ignores letter frequency and word-likeness; a frequency-matched null has not been run, so the ratio is an upper bound on what naming conventions alone would explain.

### agreement with Wikidata format constraints

Thirteen published systems have a Wikidata external-identifier property with a format constraint (P1793). Every published code was tested, full match, against that regex as retrieved on 2026-10-13, in the form the property expects: ICD-10-CM dotted (the CDC file is undotted), UN/LOCODE as the full locode, BCP 47 language-type subtags only (P305 describes full tags).

| system | property | tested | rejected | verified cause |
| --- | --- | --- | --- | --- |
| `lng/i39`, `lng/i63`, `lng/ioc`, `bio/pdb`, `fin/i42`, `lng/i15`, `wrt/tz`, `cls/loc` | P218, P220, P984, P638, P498, P506, P6687, P1149 | all | 0 | agree |
| `trp/unl` | P1937 | 116,213 | 0 | agree on the full locode; the bare code fails by construction |
| `cls/icd` | P4229 | 98,403 | 628 | the FY2027 file has 600 codes with a letter in the third position (`C4A`, `D3A`, `M1A`) and 28 in the new `QA0` category; the regex requires a digit there |
| `lng/glt` | P1394 | 27,177 | 3 | `b10b1234`, `3adt1234`, `ww2p1234` are current glottocodes with a digit in the first block; the regex requires four letters |
| `bio/gen` | P353 | 44,997 | 14 | current HGNC symbols with `_` (`C4A_2`) or readthrough segments over seven characters (`HSPB2-C11orf52`) |
| `lng/b47` | P305 | 8,275 | 1 | the private-use range `qaa..qtz`, which is a range entry, not a subtag |

In every divergence the rejected codes are present in the authority's current file; the constraint on Wikidata is older than the codes. This is a comparison of two snapshots, not a claim about Wikidata's correctness in general.

### retrieval

A separate rig ([3char-bench](https://github.com/brennercruvinel/3char-bench)) measured how to feed these tables to a dense retriever on a sample of 10 systems (2,123 records, seed 20260623) with 51 questions of one answer each, two small embedders, 24 configurations. The ranking of configurations: one record per chunk written as a sentence (92.2% recall@1 at 22.6 tokens per answer with multilingual-e5-small) over the same fields as key=value (60.8%), over blocks of 20 records (47.1%), with the whole system as one chunk close behind at 7,467 tokens. A bare literal routes to the right system in 33.0% of 182 colliding pairs, the combinatorial floor; with the system name in the chunk or the key, 100%. With 51 questions one question is 1.96 points of recall; the sample is ten systems and the numbers do not estimate other systems or models.

## 8. relation to existing resources

| resource | what it holds | relation to 3char |
| --- | --- | --- |
| [Bioregistry](https://bioregistry.io) (2,936 prefixes, snapshot 2026-10-13) | registry of identifier systems: prefix, regex, resolver, mostly biomedical | registers systems, not their code lists; 3char stores the lists, across ten domains; four 3char ids (`elm`, `icd`, `mim`, `pdb`) also exist as N2T prefixes and two name something else there |
| [N2T](https://n2t.net) (511 prefix entries in the full list) | resolver prefixes | same as above |
| Wikidata external-identifier properties (9,846 with a format constraint, 2026-10-13) | one property per system, a regex, and identifiers on entities | no list of valid codes per system; 3char's lists are the authority's files; section 7 compares the two |
| pycountry 26.2.16 | ISO 3166-1 (249), 3166-2 (5,046), 4217 (178), 639 (7,923), 15924 (226) as a Python package | five ISO standards from the Debian iso-codes files; 3char reads 3166-1, 4217, 639-1 and 15924 from other sources and adds 54 non-ISO systems |
| `datasets/country-codes`, OurAirports, OpenFlights, IANA registries | single-domain source files | sources of individual 3char systems, cited in `systems.url` |

A search of the Hugging Face Hub on 2026-10-14 with fourteen queries (ISO 3166, ISO 4217, IATA, ICAO, ICD-10, HGNC, LOCODE, country codes, currency codes, identifiers, code systems, controlled vocabulary, three letter) returned 29 datasets, each covering one system. No multi-domain collection of code lists with per-system license status was found; the search was not exhaustive and this is not a claim of priority.

## 9. versions, deposit and citation

A release that changes any parquet increments the minor version; a card-only release increments the patch version. The data at a release is the Hub revision tagged with the version and a Zenodo deposit with the same files, `MANIFEST.tsv` (sha256, bytes, rows per file), `SCHEMA.md`, `LICENSES.md`, the census, keys and cross-check outputs and the scripts that produce them. The changelog is maintained in the pipeline and copied here. Upstream changes are detected by sha256 and adopted on purpose, never absorbed.

```bibtex
@misc{cruvinel_3char_2026,
  title   = {3char: 58 identifier systems in one schema, with per-system provenance and license status},
  author  = {Viana Cruvinel, Brenner},
  year    = {2026},
  version = {0.1.2},
  url     = {https://huggingface.co/datasets/brennercruvinel/3char}
}
```

## 10. limitations by system

`trp/unl`: `code` is unique only within a country; the full locode is in `extra.locode`; 139 locodes appear on more than one row as bilingual variants of the same place.

`lng/b47`: the IANA registry of subtags, not of tags; seven types in `extra.type`; a code is unique only within its type.

`lng/i63`: three-letter language subtags as published by IANA, not ISO 639-3. RFC 5646 omits the three-letter form when a two-letter subtag exists, so `eng`, `deu`, `por` are absent; 115 ISO 639-5 collections and 224 deprecated subtags are present.

`cls/icd`: codes stored without the dot, as in the CDC order file; 628 codes of the FY2027 edition carry a letter in the second or third position.

`trp/iata`, `trp/icao`: derived from the OurAirports public domain file, not from IATA or ICAO publications. `trp/ica2`: named after the OpenFlights source, which lists IATA and ICAO airline codes; it holds 5,840 three-character ICAO designators and one two-character row.

`com/tlg`: parsed from the djvu xml of a 1901 book scan; 92% of code words are recovered with their phrase.

`cmp/sts`: 500 rows for about 64 assigned status codes; IANA's unassigned ranges are expanded one row each with `status = unassigned`.

`trp/olc`: the reference encoder's test vectors, not a registry.

`lng/ioc`: ISO 3166 alpha-3 in `extra.iso3`, FIFA in `extra.fifa`; `aliases` holds only codes that differ from the IOC code. Release 0.1.0 shipped the aliases unlabelled with a footnote marker as a code; corrected in 0.1.1.

The selection of systems reflects what is published under terms that allow redistribution and what the curator found; English-language standards bodies and computing registries are over-represented, national schemes outside the US and the UN system are absent. The collision census is a census of this collection; adding a system changes it.
