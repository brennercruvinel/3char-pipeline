# versioning, releases and citation

## what is data and what is software

| artefact | kind | where | identifier |
| --- | --- | --- | --- |
| the 58 parquet files, `systems.parquet`, README (card), CHANGELOG | data | Hugging Face Hub, Zenodo deposit | Hub revision sha; Zenodo DOI per version plus a concept DOI |
| 3char-pipeline | software | GitHub | git tag; CITATION.cff; optional Zenodo DOI via GitHub release archiving |
| 3char-bench | software and its measured output (`rig/out/*.json`) | GitHub | git tag; CITATION.cff |
| poc-nsi | software, raw model outputs, documents | GitHub | git tag; CITATION.cff |

## version numbers

- `MAJOR.MINOR.PATCH` for the dataset. a release that changes any parquet, including a new or removed system, increments MINOR; a release that changes only the card or the changelog increments PATCH; a change to the schema increments MAJOR.
- the pipeline tag equals the dataset version it builds. the bench and the probe have their own versions.
- every dataset version is a Zenodo version under one concept DOI; the Hub keeps the same files at the tagged revision. `CHANGELOG.md` is the single changelog, maintained in the pipeline and copied to the Hub by `build_hub.py`.

## what a dataset release contains

1. the publishable parquet files and `systems.parquet`, exactly the files on the Hub at the tagged revision.
2. `MANIFEST.tsv`: sha256, bytes and row count per file; `manifest.py` regenerates it.
3. `README.md` (the card), `CHANGELOG.md`, `SCHEMA.md`, `LICENSES.md`.
4. `census.json`, `keys.json`, `crosscheck_wikidata.json` with the scripts that produce them and the external regex table with its retrieval date.
5. `zenodo_metadata.json` as deposited.

## cadence

there is no fixed cadence. sources with yearly editions (ICD-10-CM, tz) are refreshed when the edition changes; `download.py` detects any upstream change by sha256 and nothing is absorbed silently.

## citation

cite the dataset by its version DOI. cite the pipeline, the bench or the probe by their CITATION.cff. the card's bibtex names the Hub URL and the version.
