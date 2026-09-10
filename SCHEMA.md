# schema

two tables. `systems` describes each code system, `codes` holds every code from every system. one row per code, `system_id` is the join key.

everything is stored as parquet in the canonical schema. the raw files under `data/<domain>/<id>/raw/` are never rewritten, parsers read them and emit parquet next to them.

### codes

one row per code. built by the per-system parsers, concatenated by `build.py`.

| column | type | null | description |
| --- | --- | --- | --- |
| `system_id` | string | no | `<domain>/<id>`, joins to `systems.system_id` |
| `code` | string | no | the code as the authority writes it, no case folding, no padding stripped |
| `label` | string | no | short human name for the code, one line, no trailing punctuation |
| `description` | string | yes | longer gloss when the source carries one |
| `parent_code` | string | yes | `code` of the parent in the same system, for hierarchical systems (atc, dew, icd, loc, bsc, ec). null when the system is flat |
| `status` | string | yes | one of `current`, `deprecated`, `reserved`, `private`, `unassigned`. null when the source says nothing |
| `aliases` | list\<string\> | yes | other strings that resolve to the same referent, empty list when none |
| `extra` | string | yes | JSON object as a string, holds source-specific fields that do not fit above |

`extra` is a string and not a struct on purpose. the 64 sources disagree about almost every field beyond code and label, and a struct would force a union of ~200 nullable columns onto every row. keeping it as a JSON string means the parquet stays narrow and the arrow schema stays identical across every config, which is what makes `load_dataset("3char", "all")` work at all.

`code` is stored verbatim. normalization is a query-time concern, and the case rule differs per system, which is why `systems.case_sensitive` exists.

### systems

one row per code system. 64 rows. hand maintained, migrated from `SOURCES.tsv`.

| column | type | null | description |
| --- | --- | --- | --- |
| `system_id` | string | no | `<domain>/<id>`, primary key |
| `domain` | string | no | one of the 10 top level buckets |
| `name` | string | no | what the system is called by its authority |
| `authority` | string | no | the body that assigns the codes, not the site the file came from |
| `url` | string | no | exact retrieval url of the raw file |
| `license` | string | no | spdx id when one applies, otherwise a short tag, see `LICENSES.md` |
| `code_pattern` | string | no | anchored regex every `code` in that system must match |
| `case_sensitive` | bool | no | whether two codes differing only in case are distinct codes |
| `raw_file` | string | no | path under `data/<domain>/<id>/raw/` |
| `version` | string | yes | the version string the source publishes, null when it publishes none |
| `retrieved_at` | date | no | date the raw file was fetched |

`authority` and `url` are separate because they disagree often. ISO 639-3 is assigned by SIL International, the file came from a SIL download url, fine. but ATC is assigned by the WHO Collaborating Centre and the file came from a github scrape, and collapsing those two into one column would hide exactly the provenance problem worth knowing about.

### code_pattern

the pattern is anchored (`^...$`) and is the contract the validator enforces. a system whose codes do not all match its own pattern is a bug in the parser or in the pattern, and `validate.py` fails the build rather than emitting the parquet.

three characters is the thesis of the dataset, not a constraint of the schema. plenty of these systems are not three characters (ISO 3166 alpha-2, MIC is four, CFI is six, ATC is seven and hierarchical). the pattern records what each system actually is.
