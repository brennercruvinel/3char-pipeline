# Schema

The dataset has two tables. `systems` describes each code system; `codes` holds every code from every system, one row per code, and joins to `systems` on `system_id`. Both are stored as Parquet. The Arrow schema of `codes` is identical across systems, which is what allows the `all` configuration on the Hub to concatenate them.

## codes

| Column | Type | Nullable | Description |
| --- | --- | --- | --- |
| `system_id` | string | no | `<domain>/<id>`; joins to `systems.system_id` |
| `code` | string | no | The code as the authority writes it, without case folding or stripped padding |
| `label` | string | no | Short human-readable name, on one line |
| `description` | string | yes | Longer description, when the source provides one |
| `parent_code` | string | yes | `code` of the parent in the same system, for hierarchical systems; among published systems, `bio/ec`, `cls/icd` and `cls/loc` |
| `status` | string | yes | Status value published by the source; the vocabulary differs by system (see below) |
| `aliases` | list<string> | yes | Other strings that refer to the same entity; an empty list when there are none |
| `extra` | string | yes | JSON object, stored as a string, with source-specific fields |

`extra` is a string rather than a struct. The sources share almost no fields beyond the code and the label, so a struct would force a union of about 200 nullable columns onto every row and break the identity of the schema across configurations.

### Status vocabulary

`status` is not a closed list. The counts below cover the published set, which is unchanged since release 0.1.1.

| Value | Rows | Systems |
| --- | --- | --- |
| null | 693,350 | All systems that publish no status |
| `approved` | 44,997 | `bio/gen` (HGNC symbol status) |
| `deprecated` | 6,793 | IANA registries, Glottolog, tz |
| `fully-qualified` | 3,944 | `wrt/uni` (Unicode emoji qualification) |
| `current` | 1,069 | IANA registries |
| `minimally-qualified` | 1,029 | `wrt/uni` |
| `unassigned` | 436 | `cmp/sts` expanded ranges and IANA gaps |
| `unqualified` | 243 | `wrt/uni` |
| `component` | 9 | `wrt/uni` |

Filter on `status` only within a single system, after reading that system's `notes` in `systems`.

### Record identification

`code` is unique within 54 of the 58 published systems. The four exceptions, and the fields that identify a record in each, are:

| System | Rows | Distinct codes | Key | Remaining duplicates |
| --- | --- | --- | --- | --- |
| `trp/unl` | 116,213 | 26,162 | `extra.locode` (country plus code) | 139 locodes occur on more than one row as bilingual variants of the same name, adding 146 rows |
| `lng/b47` | 9,295 | 9,037 | `code` and `extra.type` (language, extlang, script, region, variant, grandfathered, redundant) | None |
| `wrt/tz` | 806 | 797 | `code` and `extra.kind` (zone name or abbreviation) | None |
| `wrt/abj` | 84 | 83 | `code` and `label` | None; U+05BC appears twice, as `dagesh` and as `mapiq`, two names for one mark. Folding them into one row with an alias is planned for a later release |

`keys.py` regenerates this table. Across systems, 14,911 literals are claimed by more than one system, so `(system_id, code)` is the only cross-system key; in `trp/unl` it is `(system_id, extra.locode)`.

## systems

One row per code system: 64 rows in `systems.tsv` and 58 in `hub/systems.parquet`.

| Column | Type | Nullable | Description |
| --- | --- | --- | --- |
| `system_id` | string | no | `<domain>/<id>`; primary key |
| `domain` | string | no | One of `bio`, `cls`, `cmp`, `com`, `fin`, `grf`, `lng`, `nte`, `trp`, `wrt` |
| `name` | string | no | The name the authority gives the system |
| `authority` | string | no | The body that assigns the codes |
| `url` | string | no | Exact retrieval URL of the raw file |
| `license` | string | no | SPDX identifier where one applies, otherwise a short tag defined in `LICENSES.md` |
| `license_status` | string | no | `ok`, `check` or `problem`; only `ok` and `check` are published |
| `code_pattern` | string | no | Anchored regular expression that every `code` in the system matches |
| `pattern_status` | string | no | `derived` (written against the real file) or `provisional` |
| `case_sensitive` | bool | no | Whether two codes that differ only in case are distinct codes |
| `raw_file` | string | no | Path of the raw file under `data/` |
| `derived_from` | string | yes | The system this one is built from; `lng/i63` is built from `lng/b47` |
| `version` | string | yes | Version string published by the source, read from the file by `versions.py`; empty when the source publishes none |
| `retrieved_at` | date | no | Fetch date of the raw file |
| `notes` | string | yes | Curator notes, including how to read `status` and `extra` for the system |

`authority` and `url` are kept separate because they often differ. ISO 3166, for example, is assigned by the ISO 3166 Maintenance Agency, while the file comes from a CC-BY-SA mirror. Merging the two columns would hide exactly the provenance worth knowing.

## code_pattern

Every pattern is anchored and enforced by `validate.py`, which exits with an error on any mismatch not listed in `known_exceptions.py`. Three characters is the organizing theme of the collection, not a constraint of the schema; each pattern records the form the system's codes actually take.
