# changelog

## 0.1.1, 2026-09-12

one system rebuilt, one count corrected, one section added. no other parquet changed.

### lng/ioc

`aliases` mixed the ISO 3166 alpha-3 and the FIFA code with no label, and for the United Kingdom the FIFA slot carried `1`, a footnote marker in the source where the UK has four FIFA members. now `extra.iso3` and `extra.fifa` are named fields, and `aliases` holds only the codes that differ from the IOC code, so `GER` lists `DEU` and `BRA` lists nothing. found by consuming the dataset from the retrieval rig, where a hypothesis that every IOC alias resolves in ISO 3166 came back at 84 percent and the missing 16 were this.

### the card

the validator caught 25 wrong assumptions of mine, not 13. the card said 13, the README and this changelog said 25, and 25 is the number in the notes. corrected.

a new section, using it for retrieval, with the measured answer to how to chunk these tables for a retriever and the collision census over the published set: 14,911 of 623,141 distinct codes are claimed by more than one system. the rig behind those numbers is at [github.com/brennercruvinel/bench](https://github.com/brennercruvinel/bench).

## 0.1.0, 2026-09-10

first release. 64 code systems parse and validate, 58 of them published on the Hub, 751,870 codes in one schema.

### what shipped

58 systems across 10 domains, one parquet each plus `systems.parquet`, 60 configs counting `all` and `systems`. every code is tested against its system's regex at build time and the build fails on any mismatch, so the published set has zero codes that do not match their own pattern.

`systems.parquet` carries the provenance next to the data: authority separate from url, license and license status per system, the regex, and how much that regex is worth.

### six systems held back

the WHO ATC index, BISAC subject headings, the Dewey summaries, the CIK to CUSIP mapping, the ISO 10383 MIC list and the what3words API surface parse locally and are never uploaded. their authorities forbid republishing the code set, in language quoted verbatim in `LICENSES.md`.

two of those six were found late. `lng/i63` and `fin/mic` both looked like ordinary standards downloads until someone read the terms: SIL names its own site as the only authorized distribution point for ISO 639-3, and the ISO 10383 registration authority excludes reproducing a substantial part for third parties.

### eight sources replaced

eight systems used to come from github gists and repos with no license. a gist is not the rights holder of the ITU morse table or the POSIX errno list, so the provenance was wrong regardless of what the license said. each was re-derived from the body that assigns the codes: the JCBN Recommendations 1983 for the amino acid symbols, POSIX.1-2024 for errno, the LLVM x86 tablegen for register names, Recommendation ITU-R M.1677-1 for morse, ITU-T S.1 for ITA2, the canonical `rdfs.org/sioc/ns#` namespace, and CLDR for month names.

### two sources were the wrong file entirely

`cls/icd` was an instruction-tuning dataset with ICD codes embedded in question and answer text. that is training data about the codes, not the code list. replaced with the FY2027 order file from the CDC, 98,403 codes with the billable flag that separates a category from a diagnosis you can put on a claim.

`com/tlg` came from the plain OCR text of a 1901 book scan, which is unusable for the job. the book sets code number, code word and phrase in three columns, and the text derivative emits the columns as separate runs of lines, destroying the pairing that makes a code a code. now parsed from the djvu xml, where every word keeps a bounding box, rebuilding the columns from the x coordinate. 92 percent of the code words come back with their phrase attached.

`lng/i63` was rebuilt from the IANA registry that also feeds `lng/b47`, and renamed to say what it is. it is not ISO 639-3: RFC 5646 omits the three letter form whenever a two letter subtag exists, so `eng`, `deu` and `por` are absent, and it carries 115 ISO 639-5 collections and 224 deprecated subtags that ISO 639-3 does not.

### the validator earned its place

writing a regex per system and enforcing it caught 25 wrong assumptions of mine and exactly one malformed row upstream.

mine included the ATC fourth level being one letter and not two, AVX-512 mnemonics using a lowercase x, `*` being a real entry in both the IANA DNS and HTTP method registries, `0` being valid padding in a plus code, preliminary EC numbers carrying an `n` suffix, x87 registers spelled `st(1)`, glottocodes allowing a digit in the first block, and schema.org shipping `3DModel`.

upstream's was `FIC05700`, a BISAC code with five digits where the standard is six. it is listed in `known_exceptions.py` with the reason, still reported by the validator, never silently dropped.

### three parsers were wrong in a way only duplicates revealed

counting duplicate codes per system surfaced three modelling bugs: ATC repeated a code once per administration route, IAU repeated Serpens once per half, and the plus code test vectors repeated a code across wrapped longitudes. all three now collapse to one row per code with the variation in `extra`.

`trp/unl` still has about 90,000 repeated codes and that one is correct: a UN/LOCODE three letter code is only unique inside its country.
