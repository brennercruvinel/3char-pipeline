# 3char

3char is a curated collection of code systems, identifiers, symbols and controlled vocabularies, each taken from a documented reference source: ISO country and currency codes, IATA airport codes, HGNC gene symbols, IANA registries and 54 other lists, 58 in all.

The name comes from the three-character codes with which the collection began, such as `GRU` for São Paulo's international airport, `BRL` for the Brazilian real and `BRA` for Brazil. Codes like these appear throughout data, yet the lists that define them are spread across standards bodies, registries and projects, each with its own format, edition and terms of use. The collection has since grown to include shorter and longer codes, symbols and vocabulary terms.

Its purpose is to make these lists usable as data. All 751,870 records share one Parquet schema, every record keeps the namespace of the list it comes from, and every list is documented with its source, edition, format and license. A code can therefore be validated, looked up or compared across lists without losing track of who defined it and under which terms it may be reused.

## Contents

The 58 sources span ten domains, from biology and finance to language, transport and time. They are not all the same kind of list, and the difference matters when a record is read:

| Kind | Systems | Examples |
| --- | ---: | --- |
| Codes and identifiers assigned or registered by an authority | 28 | ISO 3166-1 country codes, ICD-10-CM, HGNC gene symbols, PDB entry IDs, IANA media types |
| Symbols and code tables | 9 | Chemical element symbols, amino acid codes, Morse and ITA2 signals, Unicode emoji sequences |
| Vocabulary terms, keywords and names | 18 | schema.org and SHACL terms, x86 instruction mnemonics, CSS named colors, CLDR month abbreviations |
| Conventions maintained by a community | 2 | File extensions, FourCC codec identifiers |
| Test vectors | 1 | The reference test cases of the Open Location Code encoder |

Entries also differ in status within a list. The HTTP status code registry is included together with its unassigned values, one row per unassigned code (436 rows, marked `unassigned`), and five sources keep entries they mark as no longer in use (6,793 rows, marked `deprecated`). Every system is listed, with its kind, authority, size and regular expression, in [All 58 systems](#all-58-systems) at the end of this card; the `systems` configuration holds the rest of its metadata.

## Uses

- **Validating and normalizing codes.** Each list and its regular expression show whether a string is an entry in the recorded edition of the list, and whether it has the form the source defines.
- **Grounding language models and search.** The lists can serve as lookup tables or retrieval corpora that map codes to names and back. [Retrieval](#retrieval) summarizes how the presentation of records affected retrieval in a controlled sample.
- **Studying codes across lists.** The same string often occurs in several lists, sometimes for the same entity and sometimes not; [Analyses](#analyses) measures both. The closed study [poc-nsi](https://github.com/brennercruvinel/poc-nsi) used seven systems in this way to test whether language models confuse such codes.
- **Linking tables.** Country codes stored in `extra`, such as `extra.country` in the airport systems and `extra.iso3` in `lng/ioc`, connect several systems to ISO 3166-1.

For operational work that depends on the latest edition of a list, such as billing with ICD-10-CM, compare `version` and `retrieved_at` with the source's current release.

## Dataset structure

```python
from datasets import load_dataset

ds   = load_dataset("brennercruvinel/3char", "all")        # every system in one table, 751,870 rows
iata = load_dataset("brennercruvinel/3char", "trp-iata")   # a single system
meta = load_dataset("brennercruvinel/3char", "systems")    # 58 rows: authority, URL, license, regex, version, retrieval date
```

The dataset has 60 configurations: `all`, `systems`, and one per system, named `<domain>-<id>`. Configuration names use a hyphen because the Hub does not allow a slash in them; the `system_id` column keeps the slash, so the `trp-iata` configuration returns rows whose `system_id` is `trp/iata`. Each configuration has a single `train` split, and the data has not been divided into training and evaluation sets. For reproducible work, pin a revision with `load_dataset(..., revision="<commit sha>")`.

Every system has the same Arrow schema, with one row per entry:

```json
{"system_id": "trp/iata", "code": "GRU",
 "label": "São Paulo/Guarulhos–Governor André Franco Montoro International Airport",
 "description": null, "parent_code": null, "status": null, "aliases": [],
 "extra": "{\"country\": \"BR\", \"municipality\": \"São Paulo\", \"scheduled\": \"yes\", \"type\": \"large_airport\"}"}
```

| Column | Type | Content |
| --- | --- | --- |
| `system_id` | string | `<domain>/<id>`; joins to the `systems` configuration |
| `code` | string | The entry as the source writes it, without case folding |
| `label` | string | Short name from the source |
| `description` | string | Longer description, when the source provides one |
| `parent_code` | string | Parent entry in the same system; present in `bio/ec`, `cls/icd` and `cls/loc` |
| `status` | string | Status value published by the source, or null |
| `aliases` | list<string> | Other strings that refer to the same entry |
| `extra` | string | JSON object with source-specific fields |

`status` is null in 693,350 rows. Elsewhere it holds the value the source publishes: `approved` for every HGNC symbol (44,997 rows); `deprecated` in `bio/ec`, `cmp/mim`, `lng/b47`, `lng/i63` and `trp/ica2` (6,793 rows); `current` for the remaining airlines in `trp/ica2` (1,069); `unassigned` in `cmp/sts` (436); and the Unicode emoji qualification values in `wrt/uni`: `fully-qualified` (3,944), `minimally-qualified` (1,029), `unqualified` (243) and `component` (9). Because each source has its own vocabulary, filter on `status` within a single system.

`extra` is stored as a JSON string rather than a struct because the sources share few fields beyond the code and the label; a struct would add a union of about 200 nullable columns to every row.

### Identifying a record

`code` is unique within 54 of the 58 systems. In the other four, a record is identified by the fields below, as computed by `keys.py`:

| System | Rows | Distinct codes | Key | Remaining duplicates |
| --- | ---: | ---: | --- | --- |
| `trp/unl` | 116,213 | 26,162 | `extra.locode` (country plus code) | 139 locodes occur on more than one row as bilingual variants of the same name, adding 146 rows |
| `lng/b47` | 9,295 | 9,037 | `code` and `extra.type` | None |
| `wrt/tz` | 806 | 797 | `code` and `extra.kind` | None |
| `wrt/abj` | 84 | 83 | `code` and `label` | None; the repeated code, U+05BC, appears once as `dagesh` and once as `mapiq` |

Across systems, a record is identified by `(system_id, code)`, or by `(system_id, extra.locode)` in `trp/unl`. A code without its system does not identify a record.

## Construction

The data is produced by [3char-pipeline](https://github.com/brennercruvinel/3char-pipeline), which downloads each source, parses it into the common schema and checks the result. A source is included when four conditions hold, each checked by a column or a file in the pipeline:

| Condition | Checked by |
| --- | --- |
| The body that maintains the list is identified, and the file comes from that body or from a derivative whose terms permit redistribution | `systems.authority` and `systems.url`, kept as separate columns |
| A regular expression written against the actual file matches every published entry | `systems.code_pattern`, enforced by `validate.py`; `pattern_status` is `derived` for all 58 systems |
| The source's terms permit redistribution, or state nothing and the entries are plain facts in everyday use | `systems.license` and `systems.license_status`, with the terms quoted in `LICENSES.md` |
| The SHA-256 of the raw file is recorded | `CHECKSUMS.tsv`; `download.py` fails when a file changes |

For the two community conventions, the maintaining project is the one named in `systems.authority` and `systems.url`. A source is excluded, with the reason recorded, when its terms forbid redistribution, when no lawfully redistributable file exists, or when the file describes the codes instead of listing them.

All 58 raw files were retrieved on 2026-09-10. Ten systems come from sources that publish a version string, which the pipeline reads from the file and stores in `systems.version`: ENZYME 28-Jan-2026, ICD-10-CM FY2027, IANA media types 2026-06-05, the ISO 4217 list of 2026-01-01, the IANA Language Subtag Registry of 2026-05-05 (used by both `lng/b47` and `lng/i63`), Open English WordNet 2024, the IANA TLD list 2026060600, tzdb 2026b and Unicode emoji 17.0. For the other 48, `retrieved_at` is the only date. Updates are made by re-running the pipeline, which detects any change in a source through its checksum.

No annotation was added: labels, descriptions and aliases are those of each source, and the curated layer is the `systems` table.

Every build verifies each raw file against its recorded checksum and tests each entry against its system's regular expression; either check stops the build on a mismatch. Only systems whose `license_status` is `ok` or `check` are published (see [Licensing](#licensing)).

## Analyses

These analyses use the published files. Every figure in this section is produced by a script in the pipeline (`census.py`, `keys.py`, `equivalences.py`, `crosscheck_wikidata.py`) and checked against this card by `card_check.py`.

### Codes shared between systems

Codes are compared after case folding, and a code is shared when the same folded string occurs in two or more systems. Of the 623,141 distinct folded codes in the 58 systems:

| Codes | Count |
| --- | ---: |
| In exactly one system | 608,230 |
| In two or more systems | 14,911 |
| In three or more systems | 10,237 |
| In eleven systems, the maximum | 2 (`and`, `car`) |
| In two or more systems, counting the derived pair `lng/b47` and `lng/i63` once | 14,845 |

A shared string is not necessarily a shared meaning. `BRA` is Brazil in both ISO 3166-1 and the IOC list, the Braj language in the IANA Language Subtag Registry, and an airport in the IATA list. The census counts shared strings; whether they refer to the same entity is examined in the next section.

Every code in eight systems also occurs in at least one other system: `bio/aa1`, `bio/aa3`, `bio/cdn`, `lng/i31`, `lng/i39`, `lng/i63`, `lng/mdy` and `wrt/iau`. In `trp/iata`, `lng/ioc`, `lng/i15`, `trp/ica2` and `fin/i42`, more than 98% of codes do. Without case folding there are 632,457 distinct strings, of which 21,255 occur in more than one system. Within `trp/unl`, 18,748 codes repeat because the key is the country plus the code; these repetitions are not counted as sharing between systems.

### Lists that describe the same entities

The same entity often appears in several lists, sometimes under the same code and sometimes under a different one. `equivalences.py` tests each such link with a stated rule. Names are compared after removing accents, case and punctuation, so two spellings of one name count as different.

![Lists in 3char that describe the same entities](https://huggingface.co/datasets/brennercruvinel/3char/resolve/main/figures/equivalences.svg)

*Solid lines: same code, same entity. Dashed lines: different codes, same entity. Dotted line: same code, entity not checked. Each label gives the entries of the first list that pass the test, out of all its entries.*

**Same code, same entity.** The BCP 47 subtag registry contains three other lists: 152 of the 183 ISO 639-1 codes, 182 of the 226 ISO 15924 codes and 233 of the 249 ISO 3166-1 alpha-2 codes are subtags in it with the same name, and `lng/i63` is derived from it. The IOC uses the ISO 3166-1 alpha-3 code for 116 of its 226 countries. The largest overlap is between airport codes and UN/LOCODE: 7,106 of the 9,056 IATA codes are also UN/LOCODE codes in the same country, at a location with the airport function. Names cannot confirm this match, because one list names the airport and the other the place.

**Different codes, same entity.** The one- and three-letter amino acid codes map one to one (20 of 20). Through `extra.iso3`, 94 IOC codes point to a different ISO 3166-1 code with the same name, as `GER` does to `DEU`. In Glottolog, 6,716 glottocodes carry an ISO 639-3 code that is a three-letter subtag with the same name. Of the IATA airports, 7,725 match exactly one ICAO airport with the same name, municipality and country. Finally, 25 characters have both an ITA2 combination and a Morse signal.

The 244 ISO 3166-1 alpha-2 codes that are also top-level domains are shown but not counted as the same entity, because the TLD list carries no country names. Across the whole collection, counting the derived pair once, 491 of the 14,845 shared codes carry the same name in two systems. Name matching misses equivalences whose names differ, the IATA and UN/LOCODE overlap among them, so this count is a lower bound on shared meaning rather than an estimate of it.

### Shared strings by code length

For codes made only of ASCII letters, the table compares the share of claimed strings that more than one system claims with the same share under a null model in which each system draws its codes uniformly at random from the 26^L strings of its length.

| Length | Possible strings | Claimed | In two or more systems | Observed share | Uniform null | Ratio |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | 26 | 26 | 25 | 0.962 | 0.999 | 0.96 |
| 2 | 676 | 522 | 395 | 0.757 | 0.755 | 1.00 |
| 3 | 17,576 | 17,151 | 12,705 | 0.741 | 0.919 | 0.81 |
| 4 | 456,976 | 17,130 | 734 | 0.043 | 0.012 | 3.6 |
| 5 | 11,881,376 | 4,479 | 96 | 0.021 | 0.0001 | 175 |

Up to three letters, the observed share is close to or below the uniform null, and 97.6% of all three-letter strings are claimed by at least one system. From four letters on, the observed share is 3.6 and 175 times the uniform null. The null ignores letter frequencies and word-likeness, and a null matched to those properties has not been computed, so the ratios describe departure from a uniform draw and support no further interpretation.

### Agreement with Wikidata format constraints

Thirteen systems correspond to a Wikidata external-identifier property with a format constraint (P1793). Every code in these systems was tested for a full match against the property's regular expression, as retrieved on 2026-10-13, in the form the property expects: ICD-10-CM codes with the dot (the CDC file omits it), complete UN/LOCODEs, and, for BCP 47, language subtags only, because P305 describes complete tags.

| System | Property | Tested | Rejected | Cause, verified in the source file |
| --- | --- | ---: | ---: | --- |
| `lng/i39`, `lng/i63`, `lng/ioc`, `bio/pdb`, `fin/i42`, `lng/i15`, `wrt/tz`, `cls/loc` | P218, P220, P984, P638, P498, P506, P6687, P1149 | All | 0 | None |
| `trp/unl` | P1937 | 116,213 | 0 | None for the complete locode; the three-character code alone cannot match the pattern |
| `cls/icd` | P4229 | 98,403 | 628 | 600 FY2027 codes have a letter in the third position (`C4A`, `D3A`, `M1A`) and 28 belong to the new `QA0` category; the expression requires digits in the second and third positions |
| `lng/glt` | P1394 | 27,177 | 3 | `b10b1234`, `3adt1234` and `ww2p1234` have a digit in the first block; the expression requires four letters |
| `bio/gen` | P353 | 44,997 | 14 | Approved symbols containing `_` (`C4A_2`) or readthrough segments longer than seven characters (`HSPB2-C11orf52`) |
| `lng/b47` | P305 | 8,275 | 1 | The private-use range `qaa..qtz`, a range entry rather than a subtag |

In each divergence, the rejected codes appear in the source's current file and the Wikidata constraint does not admit them. The comparison is between two snapshots, not an assessment of Wikidata's accuracy in general.

### Retrieval

[3char-bench](https://github.com/brennercruvinel/3char-bench) measured how these lists can be indexed for a dense retriever, on ten systems (2,123 records, seed 20260623) with 51 questions in Portuguese, each with one answer record. It distinguishes two outcomes. When each chunk holds one record, retrieving the chunk retrieves the answer row: with multilingual-e5-small, writing each record as a sentence reached 92.2% recall@1 at 22.6 tokens per answer, against 60.8% for the same fields as key=value pairs, and blocks of 20 records reached 47.1%. With all-MiniLM-L6-v2, an English model, one record per sentence reached 52.9%. When a chunk holds a whole system, a hit only identifies the right list, which a reader must then search; this happened for 90.2% (e5) and 82.4% (MiniLM) of questions, at 6,000 to 7,500 tokens per answer.

In a separate test, a bare code shared by several sampled systems retrieved a record of the intended system in 33.0% of 182 cases, the rate of a random choice among those systems; with the system name in both the chunk and the query, it did so in all cases. With 51 questions, one question is worth 1.96 points of recall, and the results describe this sample only.

## Limitations

Labels come from each source and are not reconciled across systems: the same airport is `São Paulo/Guarulhos–Governor André Franco Montoro International Airport` in `trp/iata` and `trp/icao`, and `Guarulhos Apt / São Paulo`, under `BRGRU`, in `trp/unl`. Airports have no city-name alias.

`trp/unl`: `code` is unique only within a country, and the complete locode is in `extra.locode`. 139 locodes occur on more than one row, as bilingual variants of the same place name.

`lng/b47`: the IANA registry lists subtags, not complete language tags. Seven subtag types are distinguished in `extra.type`, and a code is unique only within its type.

`lng/i63`: the three-letter language subtags published by IANA, not ISO 639-3. RFC 5646 omits the three-letter form when a two-letter subtag exists, so `eng`, `deu` and `por` are absent, and the list includes 115 ISO 639-5 collections and 224 deprecated subtags.

`cls/icd`: codes are stored without the dot, as in the CDC order file. In the FY2027 edition, 628 codes have a letter in the second or third position.

`trp/iata`, `trp/icao`: derived from the public-domain OurAirports file, not from IATA or ICAO publications. `trp/ica2` is named after its OpenFlights source, which lists IATA and ICAO airline codes; it contains 5,840 three-character ICAO designators and one two-character row.

`com/tlg`: parsed from the DjVu XML of a scanned 1901 book; 92% of the code words are recovered together with their phrases.

`cmp/sts`: 500 rows for about 64 assigned status codes, because IANA's unassigned ranges are expanded to one row per code, with `status = unassigned`.

`trp/olc`: the test vectors of the reference encoder, not a registry of assigned codes.

`lng/ioc`: ISO 3166 alpha-3 codes are in `extra.iso3` and FIFA codes in `extra.fifa`; `aliases` contains only codes that differ from the IOC code.

Coverage follows what sources publish under terms that permit redistribution. Standards bodies that publish in English and computing registries are well represented, while national schemes outside the United States and the UN system are not yet included. The collision census describes this collection, so adding a system changes it.

## Licensing

The dataset has no single license. Each row of the `systems` configuration records `license` and `license_status`. The `license` column takes 27 distinct values: an SPDX identifier where one applies, and otherwise a short tag defined in `LICENSES.md`. Of the 58 published systems, 56 have the status `ok` and 2 have the status `check`.

- **No stated terms (`check`).** `fin/cfi` and `fin/i42` come from SIX Group, which publishes both lists free of charge but states no terms for redistribution, so their redistribution status is unconfirmed. They are included because the codes are plain facts in worldwide use; this is the curator's judgment, not a grant of rights. Anyone who redistributes them commercially should first obtain SIX Group's terms.
- **Copyleft and share-alike (seven systems).** `cmp/frc` (GPL-2.0-or-later) and `cmp/git` (GPL-2.0-only) are lists extracted from GPL source trees; `cmp/vim` is under the Vim license; `grf/sch` and `grf/sio` are under CC-BY-SA-3.0; `lng/i31` is under CC-BY-SA-4.0, the license of its mirror; and `trp/ica2` is under ODbL-1.0. Their attribution requirements apply to any redistribution, and the share-alike terms also apply to redistributed copies of the tables.
- **ISO code lists.** `lng/i31` and `lng/i39` have the status `ok` on the basis of their mirrors' licenses. ISO asserts copyright over its code lists, and a mirror's license does not change the upstream terms.
- **Excluded systems.** The WHO ATC index, the BISAC subject headings, the Dewey summaries, the CUSIP mapping, the ISO 10383 MIC list and the what3words API description are parsed but never published, because their terms do not permit redistribution. The SIL ISO 639-3 table was removed for the same reason; `lng/i63` is a different list, the three-letter subtags of the IANA registry.

Only Parquet files are published. Raw source files are downloaded by the pipeline and are not stored in either repository.

## Related resources

| Resource | Contents | Relation to 3char |
| --- | --- | --- |
| [Bioregistry](https://bioregistry.io) (2,936 prefixes, snapshot of 2026-10-13) | A registry of identifier systems, mostly biomedical, with prefixes, regular expressions and resolvers | Describes systems without redistributing their contents; 3char distributes the lists, across ten domains |
| [N2T](https://n2t.net) (511 prefix entries in the full list) | Resolver prefixes | As for the Bioregistry. Four 3char IDs (`elm`, `icd`, `mim`, `pdb`) are also N2T prefixes, and two of them denote other systems there |
| Wikidata external-identifier properties (9,846 with a format constraint, 2026-10-13) | One property per system, with a regular expression and identifiers attached to entities | Identifiers are statements about entities rather than the authority's list; the two are compared in [Agreement with Wikidata format constraints](#agreement-with-wikidata-format-constraints) |
| pycountry 26.2.16 | ISO 3166-1 (249), ISO 3166-2 (5,046), ISO 4217 (178), ISO 639 (7,923) and ISO 15924 (226), as a Python package built from the Debian iso-codes files | Covers five ISO standards; 3char takes ISO 3166-1, 4217, 639-1 and 15924 from other sources and includes 54 other systems |
| `datasets/country-codes`, OurAirports, OpenFlights, IANA registries | Source files for single domains | Sources of individual 3char systems, cited in `systems.url` |

A search of the Hugging Face Hub on 2026-10-14, with queries that included ISO 3166, ISO 4217, IATA, ICAO, ICD-10, HGNC, LOCODE, country codes, currency codes, identifiers, code systems, controlled vocabulary and three letter, returned 29 datasets, each covering a single system. No multi-domain collection of code lists with per-system license status was found. The search was not exhaustive, and this is not a claim of priority.

## Versions and citation

Releases are numbered `MAJOR.MINOR.PATCH`. A change to the schema increments the major version, a change to any Parquet file increments the minor version, and a change limited to the documentation increments the patch version.

Release tags on the Hub and a Zenodo deposit are planned but have not been created yet; until then, a Hub commit identifies the exact files of a release. Each Zenodo version will contain the published Parquet files, `MANIFEST.tsv` (SHA-256, size and row count for each file), `SCHEMA.md`, `LICENSES.md`, the census, key, equivalence and cross-check outputs, and the scripts that produce them.

```bibtex
@misc{cruvinel_3char_2026,
  title   = {3char: 58 code systems and controlled vocabularies in one schema, with per-system provenance and license status},
  author  = {Viana Cruvinel, Brenner},
  year    = {2026},
  version = {0.1.3},
  url     = {https://huggingface.co/datasets/brennercruvinel/3char}
}
```

## All 58 systems

Kinds are those described in [Contents](#contents). Licenses, versions, retrieval dates and curator notes are in the `systems` configuration.

{{SYSTEMS_TABLES}}
