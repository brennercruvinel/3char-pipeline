# plan

state of the 3char build. `[x]` done, `[ ]` open.

### foundation

- [x] canonical `codes` schema (`SCHEMA.md`)
- [x] canonical `systems` schema (`SCHEMA.md`)
- [x] migrate `SOURCES.tsv` into `systems`, 64 rows (`systems.tsv`)
- [x] `code_pattern` per system, derived from the actual files, not from memory
- [x] license of every source verified and triaged (`LICENSES.md`), 56 ok / 2 check / 6 problem
- [x] decide what happens to the blocked sources: parsed locally, never uploaded
- [x] confirm the airports source: OurAirports public domain, not IATA official, and one file feeds both `trp/iata` and `trp/icao`
- [x] read the terms of ISO 639-3, MIC, CFI and ATC. two of the four turned out to block redistribution outright
- [x] re-derive the eight gist and no-license sources from the assigning authority
- [x] reorganize into `data/<domain>/<id>/raw/`
- [x] sha256 of every raw file (`CHECKSUMS.tsv`, 94 files)
- [x] `pattern_status` column, provisional vs derived, confirmed only after the validator runs
- [x] rebuild `lng/i63` off the IANA registry instead of the SIL table, with the derivation note

### pipeline

- [ ] github repo for the pipeline, separate from the Hub repo
- [x] `download.py`, fetches every raw file and hard fails on any checksum drift, `--accept-new` to adopt on purpose
- [ ] `build.py`, runs every parser and concatenates into the canonical schema
- [ ] `validate.py`, tests every emitted code against its system's `code_pattern` and fails the build on mismatch

### parsers

tabular, roughly 30 sources in csv, tab, xlsx and parquet.

- [ ] the csv and tab group
- [ ] the two xlsx (`fin/cfi`, `fin/mic`)
- [ ] `cls/icd` parquet

structured text, one parser each.

- [ ] `lng/b47` language-subtag-registry, record-jar format
- [ ] `wrt/uni` emoji-test.txt
- [ ] `bio/ec` enzyme.dat, SwissProt flat file
- [ ] `trp/ica2` airlines.dat
- [ ] `cls/loc` lc_class.txt
- [ ] `cmp/vim` motion.txt
- [ ] `cmp/ern` POSIX errno.h (html)
- [ ] `cmp/frc` fourcc_list.h (C header)
- [ ] `cmp/reg` X86RegisterInfo.td (LLVM tablegen)
- [ ] `grf/gql` Cypher.g4, extract keywords from the ANTLR grammar
- [ ] the remaining plain txt (`cmp/asm`, `cmp/git`, `trp/tld`, `lng/i15`)

json and xml.

- [ ] `bio/gen` hgnc_complete_set.json, 31M
- [ ] `fin/tck` company_tickers.json
- [ ] `fin/i42` iso4217 list-one.xml
- [ ] `cmp/mim` media-types.xml
- [ ] `nte/wnt` english-wordnet-2024.xml, 98M
- [ ] the small json group (`lng/mdy`, `com/mor` output, `cmp/hex`, `cmp/css`, `cmp/ext`, `wrt/abj`, `bio/pdb`)

rdf and ontologies, one rdflib parser covering all of them.

- [ ] `grf/vcd` `grf/sio` `grf/sch` `grf/org` `grf/foa` `grf/rdf` `grf/act` `grf/shc` `grf/oid`

tzdb.

- [ ] zone files, pull abbreviations out of the Rule and Zone lines
- [ ] the `.tab` files (`zone`, `zone1970`, `zonenow`, `iso3166`)

documents.

- [ ] `com/mor` ITU-R M.1677-1 pdf
- [ ] `com/bau` ITU-T S.1 pdf
- [ ] `grf/lpg` PG-Schema pdf
- [ ] `bio/aa1` `bio/aa3` IUPAC JCBN table (html)
- [ ] `com/tlg` ABC telegraphic code, OCR cleanup on 130k lines
- [ ] `cls/dew` dewey summaries pdf (pipeline only, not published)

### output

- [ ] one parquet per system at `data/<domain>/<id>.parquet`
- [ ] `systems.parquet`
- [ ] run the validator, fix what fails
- [ ] create the Hub dataset repo
- [ ] README yaml: one config per system plus `all`, `license: other`, `pretty_name`, tags, `size_categories`, `language`
- [ ] the card itself: description, usage snippet, schema, methodology, limitations, citation
- [ ] generate the systems table in the card from `systems.parquet`
- [ ] upload parquet and README
- [ ] check the viewer renders every config
- [ ] test `load_dataset` on `all` and on one individual config
- [ ] `CHANGELOG.md`
- [ ] search Space (optional)
- [ ] announce when stable
