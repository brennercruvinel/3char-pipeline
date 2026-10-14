# schema

two tables. `systems` describes each code system; `codes` holds every code from every system, one row per code, joined on `system_id`. everything is parquet; the arrow schema of `codes` is identical across systems, which is what lets the `all` config on the Hub concatenate them.

## codes

| column | type | null | description |
| --- | --- | --- | --- |
| `system_id` | string | no | `<domain>/<id>`; joins to `systems.system_id` |
| `code` | string | no | the code as the authority writes it; no case folding, no padding stripped |
| `label` | string | no | short human readable name, one line |
| `description` | string | yes | longer gloss when the source carries one |
| `parent_code` | string | yes | `code` of the parent in the same system, for hierarchical systems; among published systems: `bio/ec`, `cls/icd`, `cls/loc` |
| `status` | string | yes | the status word the source publishes; vocabulary per system, see below |
| `aliases` | list<string> | yes | other strings that resolve to the same referent; empty list when none |
| `extra` | string | yes | JSON object as a string with source specific fields |

`extra` is a string, not a struct. the sources disagree on almost every field beyond code and label; a struct would force a union of about 200 nullable columns onto every row and break schema identity across configs.

### status vocabulary

`status` is not a closed list. counts on the published set, release 0.1.1:

| value | rows | systems |
| --- | --- | --- |
| null | 693,350 | all systems that publish no status |
| `approved` | 44,997 | `bio/gen` (HGNC symbol status) |
| `deprecated` | 6,793 | IANA registries, Glottolog, tz |
| `fully-qualified` | 3,944 | `wrt/uni` (Unicode emoji qualification) |
| `current` | 1,069 | IANA registries |
| `minimally-qualified` | 1,029 | `wrt/uni` |
| `unassigned` | 436 | `cmp/sts` expanded ranges and IANA gaps |
| `unqualified` | 243 | `wrt/uni` |
| `component` | 9 | `wrt/uni` |

filter on `status` only per system, after reading that system's `notes` in `systems`.

### record identification

`code` is unique within 54 of the 58 published systems. the four exceptions and the field that resolves a record:

| system | rows | distinct codes | key | residual |
| --- | --- | --- | --- | --- |
| `trp/unl` | 116,213 | 26,162 | `extra.locode` (country plus code) | 139 locodes appear on more than one row as bilingual name variants, 146 extra rows |
| `lng/b47` | 9,295 | 9,037 | `code` plus `extra.type` (language, extlang, script, region, variant, grandfathered, redundant) | none |
| `wrt/tz` | 806 | 797 | `code` plus `extra.kind` (zone name or abbreviation) | none |
| `wrt/abj` | 84 | 83 | `code` plus `label` | U+05BC appears twice, as `dagesh` and as `mapiq`, two names of one mark; a later release folds them into one row with an alias |

`keys.py` regenerates this table. across systems the same literal is claimed by more than one system 14,911 times; `(system_id, code)` is the only cross-system key, and in `trp/unl` it is `(system_id, extra.locode)`.

## systems

one row per code system; 64 in `systems.tsv`, 58 in `hub/systems.parquet`.

| column | type | null | description |
| --- | --- | --- | --- |
| `system_id` | string | no | `<domain>/<id>`, primary key |
| `domain` | string | no | one of bio, cls, cmp, com, fin, grf, lng, nte, trp, wrt |
| `name` | string | no | what the system is called by its authority |
| `authority` | string | no | the body that assigns the codes |
| `url` | string | no | exact retrieval url of the raw file |
| `license` | string | no | spdx id when one applies, otherwise a short tag defined in `LICENSES.md` |
| `license_status` | string | no | `ok`, `check` or `problem`; only `ok` and `check` are published |
| `code_pattern` | string | no | anchored regex every `code` in the system matches |
| `pattern_status` | string | no | `derived` (written against the real file) or `provisional` |
| `case_sensitive` | bool | no | whether two codes differing only in case are distinct codes |
| `raw_file` | string | no | path of the raw file under `data/` |
| `derived_from` | string | yes | system this one is built from; `lng/i63` from `lng/b47` |
| `version` | string | yes | version string the source publishes, read from the file by `versions.py`; empty when it publishes none |
| `retrieved_at` | date | no | fetch date of the raw file |
| `notes` | string | yes | curator notes, including how to read `status` and `extra` for that system |

`authority` and `url` are separate because they disagree often: ISO 3166 is assigned by the ISO 3166 Maintenance Agency and the file comes from a CC-BY-SA mirror; collapsing the two would hide exactly the provenance worth knowing.

## code_pattern

anchored, enforced by `validate.py`, which exits non-zero on any mismatch not listed in `known_exceptions.py`. three characters is the organizing thesis of the collection, not a constraint of the schema; the pattern records what each system actually is.
