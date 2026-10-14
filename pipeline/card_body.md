# 3char

3char brings together 751,870 codes from 58 code lists, such as airport, currency, country and language codes, gene symbols and HTTP status codes, in a single Parquet schema. Each list is called a system here, and every record carries the `system_id` of the list it comes from. A companion table records, for every system, who assigns the codes, where the file was obtained, which version it is, the form the codes take and the license. Because the same short string often appears in several lists, a code is identified together with its system.

This card describes release 0.1.3. The data files have not changed since release 0.1.1 (2026-09-12). Each statistic below names the script in the build pipeline that reproduces it from the published files.

## Scope

A system is a list of short codes assigned by a single authority, such as IATA for airport codes, ISO for country and currency codes, HGNC for gene symbols or IANA for HTTP status codes. The 58 systems are grouped into ten domains (see [Systems](#systems)). The name 3char comes from the three-character codes that started the collection; systems with codes of other lengths are included, and each system's regular expression describes the form its codes actually take.

Each system is taken from one source file, and the `systems` table records the date it was retrieved and, when the source publishes one, its version. Updates are made by re-running the build pipeline, which detects any change in a source through its SHA-256 checksum. Six further systems are parsed by the pipeline but not published, because their authorities do not permit redistribution (see [Licensing](#licensing)).

## Uses

- **Validating codes.** Each system's list and regular expression tell whether a string is a well-formed code and whether it is assigned in the recorded edition.
- **Grounding language models and search.** The tables can serve as lookup tables or retrieval corpora that map codes to names and back; [Retrieval](#retrieval) summarizes measurements of how the presentation of records affects retrieval.
- **Studying ambiguous codes.** 14,911 codes, compared without regard to case, are shared by two or more systems, which provides ready-made cases of one string with several meanings.
- **Linking tables.** Country codes stored in `extra`, such as `extra.country` in the airport systems and `extra.iso3` in `lng/ioc`, connect several systems to ISO 3166-1.

For operational work that requires the latest edition of a list, such as billing with ICD-10-CM, compare `version` and `retrieved_at` with the authority's current release.

## Loading the data

```python
from datasets import load_dataset

ds   = load_dataset("brennercruvinel/3char", "all")        # every system in one table, 751,870 rows
iata = load_dataset("brennercruvinel/3char", "trp-iata")   # a single system
meta = load_dataset("brennercruvinel/3char", "systems")    # 58 rows: authority, URL, license, regex, version, retrieval date
```

The dataset has 60 configurations: `all`, `systems`, and one per system, named `<domain>-<id>`. Configuration names use a hyphen because the Hub does not allow a slash in them; the `system_id` column keeps the slash, so the `trp-iata` configuration returns rows whose `system_id` is `trp/iata`. Each configuration has a single `train` split, and the data has not been divided into training and evaluation sets. For reproducible work, pin a revision with `load_dataset(..., revision="<commit sha>")`.

## Records

There is one row per code, and every system has the same Arrow schema.

```json
{"system_id": "trp/iata", "code": "GRU",
 "label": "São Paulo/Guarulhos–Governor André Franco Montoro International Airport",
 "description": null, "parent_code": null, "status": null, "aliases": [],
 "extra": "{\"country\": \"BR\", \"municipality\": \"São Paulo\", \"scheduled\": \"yes\", \"type\": \"large_airport\"}"}
```

| Column | Type | Content |
| --- | --- | --- |
| `system_id` | string | `<domain>/<id>`; joins to the `systems` configuration |
| `code` | string | The code as the authority writes it, without case folding |
| `label` | string | Short name from the source |
| `description` | string | Longer description, when the source provides one |
| `parent_code` | string | Parent code in the same system; present in `bio/ec`, `cls/icd` and `cls/loc` |
| `status` | string | Status value published by the source, or null; the vocabulary differs by system |
| `aliases` | list<string> | Other strings that refer to the same entity |
| `extra` | string | JSON object with source-specific fields |

`status` is null in 693,350 rows. Where a source publishes a status, it is kept verbatim: `approved` (44,997 rows, all from HGNC), `deprecated` (6,793), `fully-qualified` (3,944), `current` (1,069), `minimally-qualified` (1,029), `unassigned` (436), `unqualified` (243) and `component` (9). The emoji qualification values come from `wrt/uni`. Because each system has its own vocabulary, filter on `status` only within a single system.

`extra` is stored as a JSON string rather than a struct because the sources share few fields beyond the code and the label; a struct would add a union of about 200 nullable columns to every row.

### Identifying a record

`code` is unique within 54 of the 58 systems. For the other four, the table below gives the fields that identify a record, as computed by `keys.py`.

| System | Rows | Distinct codes | Key | Remaining duplicates |
| --- | --- | --- | --- | --- |
| `trp/unl` | 116,213 | 26,162 | `extra.locode` (country plus code) | 139 locodes occur on more than one row as bilingual variants of the same name, adding 146 rows |
| `lng/b47` | 9,295 | 9,037 | `code` and `extra.type` | None |
| `wrt/tz` | 806 | 797 | `code` and `extra.kind` | None |
| `wrt/abj` | 84 | 83 | `code` and `label` | None; the repeated code, U+05BC, appears once as `dagesh` and once as `mapiq` |

Across systems, a record is identified by `(system_id, code)`, or by `(system_id, extra.locode)` in `trp/unl`. A bare code does not identify a record: 14,911 literals belong to two or more systems (see [Collisions between systems](#collisions-between-systems)).

### Systems

{{SYSTEMS_TABLES}}

## Construction

A system is included when four conditions hold. Each condition is checked by a column or a file in the [build pipeline](https://github.com/brennercruvinel/3char-pipeline).

| Condition | Checked by |
| --- | --- |
| An identifiable authority assigns the codes, and the file comes from that authority or from a derivative whose terms permit redistribution | `systems.authority` and `systems.url`, kept as separate columns |
| A regular expression written against the actual file matches every published code | `systems.code_pattern`, enforced by `validate.py`; `pattern_status` is `derived` for all 58 systems |
| The authority's terms permit redistribution, or state nothing and the codes are plain facts in everyday use | `systems.license` and `systems.license_status`, with the terms quoted in `LICENSES.md` |
| The SHA-256 of the raw file is recorded | `CHECKSUMS.tsv`; `download.py` fails when a file changes |

A system is excluded, with the reason recorded, when its authority forbids redistribution, when no lawfully redistributable file exists, or when the file describes the codes instead of listing them. The first ICD-10-CM source, for example, was an instruction-tuning dataset; it was replaced by the CDC order file.

All 58 raw files were retrieved on 2026-09-10. Ten systems come from sources that publish a version string, which the pipeline reads from the file and stores in `systems.version`: ENZYME 28-Jan-2026, ICD-10-CM FY2027, IANA media types 2026-06-05, the ISO 4217 list of 2026-01-01, the IANA Language Subtag Registry of 2026-05-05 (used by both `lng/b47` and `lng/i63`), Open English WordNet 2024, the IANA TLD list 2026060600, tzdb 2026b and Unicode emoji 17.0. The other 48 sources publish no version, so `retrieved_at` is their only date.

Eight systems first taken from secondary copies (gists, unlicensed repositories, a third-party scan and a community mirror) were re-derived from the bodies that assign the codes, and two systems built from the wrong kind of file were rebuilt from the right one. [CHANGELOG.md](CHANGELOG.md) records each case. No human annotation was added: labels, descriptions and aliases are those published by each source, and the curated layer is the `systems` table.

## Quality checks

Every build verifies each raw file against its recorded SHA-256 (`download.py`) and tests each code against its system's regular expression (`validate.py`); either script exits with an error on any mismatch. All systems share one schema, and `build_hub.py` publishes only systems whose `license_status` is `ok` or `check` (see [Licensing](#licensing)).

## Licensing

The dataset has no single license. Each row of the `systems` configuration records `license` and `license_status`. The `license` column takes 27 distinct values: an SPDX identifier where one applies, and otherwise a short tag defined in `LICENSES.md`. Of the 58 published systems, 56 have the status `ok` and 2 have the status `check`.

- **No stated terms (`check`).** `fin/cfi` and `fin/i42` come from SIX Group, which publishes both lists free of charge but states no terms for redistribution, so their redistribution status is unconfirmed. They are included because the codes are plain facts in worldwide use; this is the curator's judgment, not a grant of rights. Anyone who redistributes them commercially should first obtain SIX Group's terms.
- **Copyleft and share-alike (seven systems).** `cmp/frc` (GPL-2.0-or-later) and `cmp/git` (GPL-2.0-only) are lists extracted from GPL source trees; `cmp/vim` is under the Vim license; `grf/sch` and `grf/sio` are under CC-BY-SA-3.0; `lng/i31` is under CC-BY-SA-4.0, the license of its mirror; and `trp/ica2` is under ODbL-1.0. Their attribution requirements apply to any redistribution, and the share-alike terms also apply to redistributed copies of the tables.
- **ISO code lists.** `lng/i31` and `lng/i39` have the status `ok` on the basis of their mirrors' licenses. ISO asserts copyright over its code lists, and a mirror's license does not change the upstream terms.
- **Excluded systems.** The WHO ATC index, the BISAC subject headings, the Dewey summaries, the CUSIP mapping, the ISO 10383 MIC list and the what3words API description are parsed but never published, because their authorities' terms do not permit redistribution. The SIL ISO 639-3 table was removed for the same reason; `lng/i63` is a different list, the three-letter subtags of the IANA registry.

Only Parquet files are published. Raw source files are downloaded by the pipeline and are not stored in either repository.

## Statistics

Every figure in this section is produced by a script in the pipeline (`census.py`, `keys.py`, `crosscheck_wikidata.py`) and checked against this card by `card_check.py`.

### Collisions between systems

Codes are compared without regard to case: a literal is a code after case folding, and a literal collides when it occurs in two or more systems. The denominator is the 623,141 distinct literals in the 58 published systems.

| Literals | Count |
| --- | --- |
| In exactly one system | 608,230 |
| In two or more systems | 14,911 |
| In three or more systems | 10,237 |
| In eleven systems, the maximum | 2 (`and`, `car`) |
| In two or more systems, after collapsing the one derived family (`lng/i63` is built from `lng/b47`) | 14,845 |

Eight systems are fully covered by the others: every code in `bio/aa1`, `bio/aa3`, `bio/cdn`, `lng/i31`, `lng/i39`, `lng/i63`, `lng/mdy` and `wrt/iau` also occurs in at least one other system. In `trp/iata`, `lng/ioc`, `lng/i15`, `trp/ica2` and `fin/i42`, more than 98% of codes do.

Case folding merges, for example, `Ala` (an amino acid) with `ALA` (an airport). Without case folding there are 632,457 distinct strings, of which 21,255 collide. Collisions are counted only between systems; within `trp/unl`, 18,748 bare codes repeat because the key is the country plus the code.

### Collisions by code length

This analysis is restricted to ASCII alphabetic literals. The null model draws each system's literals uniformly at random from the 26^L strings of length L and gives the expected share of claimed strings that more than one system claims.

| Length | Possible strings | Claimed | In two or more systems | Observed rate | Null rate | Ratio |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | 26 | 26 | 25 | 0.962 | 0.999 | 0.96 |
| 2 | 676 | 522 | 395 | 0.757 | 0.755 | 1.00 |
| 3 | 17,576 | 17,151 | 12,705 | 0.741 | 0.919 | 0.81 |
| 4 | 456,976 | 17,130 | 734 | 0.043 | 0.012 | 3.6 |
| 5 | 11,881,376 | 4,479 | 96 | 0.021 | 0.0001 | 175 |

Up to three letters, the observed rate is close to or below the null rate: 97.6% of all three-letter strings are claimed by at least one system, so collisions follow from the small number of strings available. From four letters on, the observed rate exceeds the null rate by factors of 3.6 and 175. The null ignores letter frequencies and word-likeness, both of which make chance collisions more likely, so it underestimates the rate expected by chance and the ratios are upper bounds on the excess over chance. A frequency-matched null has not been computed.

### Agreement with Wikidata format constraints

Thirteen published systems correspond to a Wikidata external-identifier property with a format constraint (P1793). Every published code in these systems was tested for a full match against the property's regular expression, as retrieved on 2026-10-13, in the form the property expects: ICD-10-CM codes with the dot (the CDC file omits it), complete UN/LOCODEs, and, for BCP 47, language subtags only, because P305 describes complete tags.

| System | Property | Tested | Rejected | Cause, verified in the source file |
| --- | --- | --- | --- | --- |
| `lng/i39`, `lng/i63`, `lng/ioc`, `bio/pdb`, `fin/i42`, `lng/i15`, `wrt/tz`, `cls/loc` | P218, P220, P984, P638, P498, P506, P6687, P1149 | All | 0 | None |
| `trp/unl` | P1937 | 116,213 | 0 | None for the complete locode; the bare three-character code cannot match the pattern |
| `cls/icd` | P4229 | 98,403 | 628 | The FY2027 file has 600 codes with a letter in the third position (`C4A`, `D3A`, `M1A`) and 28 in the new `QA0` category; the expression requires digits in the second and third positions |
| `lng/glt` | P1394 | 27,177 | 3 | `b10b1234`, `3adt1234` and `ww2p1234` are glottocodes with a digit in the first block; the expression requires four letters |
| `bio/gen` | P353 | 44,997 | 14 | Approved HGNC symbols containing `_` (`C4A_2`) or readthrough segments longer than seven characters (`HSPB2-C11orf52`) |
| `lng/b47` | P305 | 8,275 | 1 | The private-use range `qaa..qtz`, which is a range entry rather than a subtag |

In every divergence, the rejected codes appear in the authority's current file and the Wikidata constraint does not admit them. The comparison is between two snapshots; it is not an assessment of Wikidata's accuracy in general.

### Retrieval

A separate experimental rig, [3char-bench](https://github.com/brennercruvinel/3char-bench), measured how these tables can be presented to a dense retriever. It used 10 systems (2,123 records, seed 20260623), 51 questions in Portuguese with exactly one answer each, two small embedders and 24 configurations. With multilingual-e5-small, the best configuration was one record per chunk written as a sentence: 92.2% recall@1 at 22.6 tokens per answer, against 60.8% for the same fields written as key=value pairs and 47.1% for blocks of 20 records. The whole system as a single chunk reached 90.2% at 7,467 tokens per answer. With all-MiniLM-L6-v2 the ranking differed: the whole system as a single chunk did best (82.4%), and one record per sentence reached 52.9%. Because all-MiniLM-L6-v2 was trained on English text, the difference between the embedders may reflect language as much as model quality.

In a routing test over 182 (literal, system) pairs from the sampled systems, a bare literal retrieved a record of the intended system in 33.0% of cases, the rate expected from a random choice among the systems that share the literal. With the system name in both the chunk and the query, routing reached 100% with both embedders. One question corresponds to 1.96 points of recall, and the ten systems were chosen to cover domains and code lengths, so these results do not estimate performance on other systems or models.

## Relation to existing resources

| Resource | Contents | Relation to 3char |
| --- | --- | --- |
| [Bioregistry](https://bioregistry.io) (2,936 prefixes, snapshot of 2026-10-13) | A registry of identifier systems, mostly biomedical, with prefixes, regular expressions and resolvers | Registers systems rather than their code lists; 3char stores the lists themselves, across ten domains |
| [N2T](https://n2t.net) (511 prefix entries in the full list) | Resolver prefixes | Same distinction as for the Bioregistry. Four 3char IDs (`elm`, `icd`, `mim`, `pdb`) are also N2T prefixes, and two of them denote other systems there |
| Wikidata external-identifier properties (9,846 with a format constraint, 2026-10-13) | One property per system, with a regular expression and identifiers attached to entities | No list of valid codes per system; 3char's lists come from the authorities' files, and the two are compared in [Agreement with Wikidata format constraints](#agreement-with-wikidata-format-constraints) |
| pycountry 26.2.16 | ISO 3166-1 (249), ISO 3166-2 (5,046), ISO 4217 (178), ISO 639 (7,923) and ISO 15924 (226), as a Python package built from the Debian iso-codes files | Covers five ISO standards; 3char takes ISO 3166-1, 4217, 639-1 and 15924 from other sources and includes 54 other systems |
| `datasets/country-codes`, OurAirports, OpenFlights, IANA registries | Source files for single domains | Sources of individual 3char systems, cited in `systems.url` |

A search of the Hugging Face Hub on 2026-10-14, with fourteen queries including ISO 3166, ISO 4217, IATA, ICAO, ICD-10, HGNC, LOCODE, country codes, currency codes, identifiers, code systems, controlled vocabulary and three letter, returned 29 datasets, each covering a single system. No multi-domain collection of code lists with per-system license status was found. The search was not exhaustive, and this is not a claim of priority.

## Versions and citation

Releases are numbered `MAJOR.MINOR.PATCH`. A change to the schema increments the major version, a change to any Parquet file increments the minor version, and a change limited to the card or the changelog increments the patch version. The changelog is maintained in the pipeline repository and copied here. Upstream changes are detected by SHA-256 and adopted deliberately, never silently.

Release tags on the Hub and a Zenodo deposit are planned but have not been created yet; until then, a Hub commit identifies the exact files of a release. Each Zenodo version will contain the published Parquet files, `MANIFEST.tsv` (SHA-256, size and row count for each file), `SCHEMA.md`, `LICENSES.md`, the census, key and cross-check outputs, and the scripts that produce them.

```bibtex
@misc{cruvinel_3char_2026,
  title   = {3char: 58 identifier systems in one schema, with per-system provenance and license status},
  author  = {Viana Cruvinel, Brenner},
  year    = {2026},
  version = {0.1.3},
  url     = {https://huggingface.co/datasets/brennercruvinel/3char}
}
```

## Known limitations

Labels come from each source and are not reconciled across systems: the same airport is `São Paulo/Guarulhos–Governor André Franco Montoro International Airport` in `trp/iata` and `trp/icao`, and `Guarulhos Apt / São Paulo`, under `BRGRU`, in `trp/unl`. Airports have no city-name alias.

`trp/unl`: `code` is unique only within a country, and the complete locode is in `extra.locode`. 139 locodes occur on more than one row, as bilingual variants of the same place name.

`lng/b47`: the IANA registry lists subtags, not complete language tags. Seven subtag types are distinguished in `extra.type`, and a code is unique only within its type.

`lng/i63`: the three-letter language subtags published by IANA, not ISO 639-3. RFC 5646 omits the three-letter form when a two-letter subtag exists, so `eng`, `deu` and `por` are absent, and the list includes 115 ISO 639-5 collections and 224 deprecated subtags.

`cls/icd`: codes are stored without the dot, as in the CDC order file. In the FY2027 edition, 628 codes have a letter in the second or third position.

`trp/iata`, `trp/icao`: derived from the public-domain OurAirports file, not from IATA or ICAO publications. `trp/ica2` is named after its OpenFlights source, which lists IATA and ICAO airline codes; it contains 5,840 three-character ICAO designators and one two-character row.

`com/tlg`: parsed from the DjVu XML of a scanned 1901 book; 92% of the code words are recovered together with their phrases.

`cmp/sts`: 500 rows for about 64 assigned status codes, because IANA's unassigned ranges are expanded to one row per code, with `status = unassigned`.

`trp/olc`: the test vectors of the reference encoder, not a registry.

`lng/ioc`: ISO 3166 alpha-3 codes are in `extra.iso3` and FIFA codes in `extra.fifa`; `aliases` contains only codes that differ from the IOC code. Release 0.1.0 shipped these aliases unlabelled, with a footnote marker stored as a code; release 0.1.1 corrected this.

Coverage follows what authorities publish under terms that permit redistribution. Standards bodies that publish in English and computing registries are well represented, while national schemes outside the United States and the UN system are not yet included. The collision census describes this collection, so adding a system changes it.
