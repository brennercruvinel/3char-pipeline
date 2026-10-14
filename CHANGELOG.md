# Changelog

## 0.1.3, 2026-10-14

Documentation only. No Parquet file has changed since 0.1.1.

### Card

The card was restructured as the description of a scientific data resource. It now opens with a definition of the collection and the reason it exists, describes the five kinds of list it contains (assigned codes, symbols, vocabulary terms, community conventions and test vectors), and then covers uses, loading, construction, findings, licensing and limitations. The full inventory of the 58 systems moved to an appendix that lists each system's kind, authority and size; regular expressions and the other metadata remain in the `systems` configuration. System names are displayed with an initial capital, while the stored values are unchanged. The citation title now reads "58 code systems and controlled vocabularies" instead of "58 identifier systems".

Corrections:

- Shared codes were presented as strings with several meanings. The card now states that a shared string may denote the same entity in different systems (`BRA` is Brazil in both ISO 3166-1 and the IOC list) and that the census does not decide which.
- The ratios against the uniform null are no longer interpreted beyond their departure from a uniform draw.
- Retrieval results now separate record retrieval from system retrieval: a whole-system chunk that ranks first identifies the right list, not the right row.
- The retrieval summary states that the questions and prose chunks are in Portuguese, while all-MiniLM-L6-v2 is an English model.
- Release tags and the Zenodo deposit were described as existing. They are now described as planned.
- `license_link` in the YAML header pointed to a section that did not exist. It now points to the licensing section.
- The inclusion condition on provenance now covers derivatives whose terms permit redistribution and the two community conventions, which matches the sources actually used.
- The eight replaced sources were described as unlicensed gists. The description now matches `LICENSES.md`: gists, unlicensed repositories, a third-party scan and a community mirror.
- The claim that the Wikidata format constraints are older than the codes they reject was removed, because it had not been verified.
- The Hub search was described as fourteen queries while thirteen were listed. The count was removed, because the search record could not be found.

### Pipeline

`README.md`, `SCHEMA.md`, `LICENSES.md` and `deposit/VERSIONING.md` were revised; `SCHEMA.md` attributed the `deprecated` and `current` status values to the wrong systems, and now lists the systems that use them. `LICENSES.md` counted the copyleft systems as both four and seven; the count is seven. `build_card.py` writes the appendix of systems with each system's kind, and the license link points to an existing anchor. `build_systems.py` failed after 0.1.2, which moved `SOURCES.tsv` to `history/` and renamed its key column; it now reads `history/SOURCES.tsv` by `system_id`. `deposit/zenodo_metadata.json` no longer declares an open license for the whole deposit, because two systems have unconfirmed redistribution terms.

## 0.1.2, 2026-10-14

Card only. No Parquet file changed since 0.1.1.

### Card

The card was rewritten as a description of a data resource. Each figure now names the script that reproduces it. The card covers the following:

- How to obtain the data and pin a revision.
- How to identify a record in the four systems where `code` is not unique (`trp/unl`, `lng/b47`, `wrt/tz`, `wrt/abj`).
- The inclusion conditions, and the column or file that checks each.
- The status vocabulary as published, which earlier versions of the card and of `SCHEMA.md` described as a closed list that did not match the data.
- The collision census, with definitions and denominators (14,911 of 623,141 distinct case-folded literals belong to two or more systems; 14,845 after collapsing the one derived family).
- The collision rate by code length against a uniform null.
- The agreement of every published code with the Wikidata format constraint of the corresponding property, with the verified cause of each divergence.
- The retrieval evidence, with its sample and its limits.
- Licensing per system, including the seven copyleft or share-alike systems and the two with no stated terms.
- The relation to the Bioregistry, N2T, Wikidata and pycountry, with counts.
- The versioning and deposit policy.

### Pipeline

`census.py`, `keys.py`, `crosscheck_wikidata.py`, `manifest.py` and `card_check.py` were added. `build_card.py` reads the prose from `card_body.md`. `SCHEMA.md` lists all 15 columns of `systems` and the observed `status` values. `LICENSES.md` explains why 58 systems are published when 57 sources are `ok` or `check`: `lng/i63` is a derivative of `lng/b47`. `SOURCES.tsv` moved to `history/`.

## 0.1.1, 2026-09-12

One system rebuilt, one count corrected and one section added. No other Parquet file changed.

### lng/ioc

`aliases` mixed the ISO 3166 alpha-3 code and the FIFA code without labels. For the United Kingdom, the FIFA slot held `1`, a footnote marker carried over from the source, where the United Kingdom has four FIFA members. `extra.iso3` and `extra.fifa` are now named fields, and `aliases` holds only the codes that differ from the IOC code, so `GER` lists `DEU` and `BRA` lists nothing. The defect was found while using the dataset as a retrieval corpus, when a check that every IOC alias resolves in ISO 3166 returned 84%.

### Card

The validator identified 25 incorrect assumptions, not 13. The card said 13, while the README and this changelog said 25; the card was corrected.

A retrieval section was added, with the measured chunking configuration and the collision census over the published set: 14,911 of 623,141 distinct codes are claimed by more than one system. The rig behind these numbers is [3char-bench](https://github.com/brennercruvinel/3char-bench).

## 0.1.0, 2026-09-10

First release. 64 code systems parse and validate, and 58 of them are published on the Hub: 751,870 codes in one schema.

### Contents

58 systems across 10 domains, one Parquet file each, plus `systems.parquet`; 60 configurations including `all` and `systems`. Every code is tested against its system's regular expression at build time, and the build fails on any mismatch, so no published code fails its own pattern.

`systems.parquet` keeps the provenance next to the data: the authority separately from the URL, the license and license status of each system, the regular expression, and how far that expression has been verified.

### Six systems withheld

The WHO ATC index, the BISAC subject headings, the Dewey summaries, the CIK to CUSIP mapping, the ISO 10383 MIC list and the what3words API description are parsed locally and never uploaded. Their authorities forbid republishing the code sets, in terms quoted verbatim in `LICENSES.md`.

Two of these six were identified late. `lng/i63` and `fin/mic` both looked like ordinary downloads of standards until their terms were read: SIL names its own site as the only authorized distribution point for ISO 639-3, and the ISO 10383 registration authority excludes reproducing a substantial part of the list for third parties.

### Eight sources replaced

Eight systems were first taken from secondary copies: GitHub gists, unlicensed repositories, a third-party scan and a community mirror. A gist is not the rights holder of the ITU Morse table or the POSIX errno list, so the provenance was wrong whatever license the copy carried. Each system was re-derived from the body that assigns the codes: the JCBN Recommendations 1983 for the amino acid symbols, POSIX.1-2024 for errno, the LLVM x86 TableGen definitions for register names, Recommendation ITU-R M.1677-1 for Morse, ITU-T S.1 for ITA2, the canonical `rdfs.org/sioc/ns#` namespace, and CLDR for month names.

### Two sources were the wrong kind of file

`cls/icd` came from an instruction-tuning dataset with ICD codes embedded in question and answer text: training data about the codes, not the code list. It was replaced with the FY2027 order file from the CDC, which has 98,403 codes and the billable flag that distinguishes a category from a diagnosis code that can be used on a claim.

`com/tlg` came from the plain OCR text of a 1901 book scan, which cannot serve the purpose. The book sets the code number, code word and phrase in three columns, and the text derivative emits the columns as separate runs of lines, which destroys the pairing that makes a code a code. The system is now parsed from the DjVu XML, where every word keeps its bounding box, and the columns are rebuilt from the x coordinate. 92% of the code words are recovered with their phrase.

`lng/i63` was rebuilt from the IANA registry that also feeds `lng/b47`, and renamed to reflect what it is. It is not ISO 639-3: RFC 5646 omits the three-letter form whenever a two-letter subtag exists, so `eng`, `deu` and `por` are absent, and it contains 115 ISO 639-5 collections and 224 deprecated subtags that ISO 639-3 does not.

### What the validator found

Writing a regular expression for each system and enforcing it exposed 25 incorrect assumptions in the initial patterns and exactly one malformed row upstream.

The facts that corrected those assumptions include the following: the fourth ATC level has one letter, not two; AVX-512 mnemonics use a lowercase x; `*` is a real entry in both the IANA DNS and HTTP method registries; `0` is valid padding in a plus code; preliminary EC numbers carry an `n` suffix; x87 registers are spelled `st(1)`; glottocodes can have a digit in the first block; and schema.org ships `3DModel`.

The upstream error was `FIC05700`, a BISAC code with five digits where the standard has six. It is listed in `known_exceptions.py` with the reason; the validator still reports it, and it is never dropped silently.

### Three parser bugs revealed by duplicates

Counting duplicate codes per system revealed three modelling bugs: ATC repeated a code once per administration route, IAU repeated Serpens once for each of its two halves, and the plus code test vectors repeated a code across wrapped longitudes. All three now produce one row per code, with the variation recorded in `extra`.

`trp/unl` still has about 90,000 rows that repeat a code, and these are correct: a UN/LOCODE three-letter code is unique only within its country.
