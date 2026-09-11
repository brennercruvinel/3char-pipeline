# 3char, build pipeline

the pipeline that produces [brennercruvinel/3char](https://huggingface.co/datasets/brennercruvinel/3char) on the Hugging Face Hub: 64 code systems parsed into one schema, 58 of them published, 751,870 codes.

this repo holds the parsers and the provenance. it does not hold the data. raw sources are fetched from the urls in `systems.tsv` and checked against `CHECKSUMS.tsv`, and several of them carry terms that forbid redistribution, so keeping them out of git is a licensing requirement, not tidiness.

### how it runs

```bash
uv venv .venv && uv pip install --python .venv/bin/python -r pipeline/requirements.txt

python pipeline/download.py        # fetch every raw source, verify against CHECKSUMS.tsv
python pipeline/build.py           # run all 64 parsers, one parquet per system
python pipeline/validate.py        # every code against its system's regex
python pipeline/build_hub.py       # drop the license-blocked systems, assemble the upload
python pipeline/build_card.py      # generate README.md from systems.parquet
```

`download.py` fails hard when a file's sha256 does not match the manifest. upstream moving is normal, absorbing it silently is not, because the parquet would change underneath whoever is reading it. `--accept-new` adopts the new bytes on purpose.

### layout

| path | what it is |
| --- | --- |
| `pipeline/systems_meta.py` | the curated table: name, authority, regex, license, notes, per system |
| `pipeline/parsers/` | one module per source family, registered with the `@parser` decorator |
| `pipeline/core.py` | the canonical row, the parser registry, csv helpers |
| `systems.tsv` | generated from `systems_meta.py` plus disk state, 64 rows |
| `CHECKSUMS.tsv` | sha256 and size of every raw file |
| `SCHEMA.md` | the `codes` and `systems` schemas, and why `extra` is a JSON string |
| `LICENSES.md` | the triage, with verbatim quotes from each authority |

### writing a parser

register a function against one or more system ids and yield canonical rows.

```python
from core import parser, row, read_csv

@parser("cmp/sts")
def http_status(path, sysrow):
    for r in read_csv(path):
        yield row("cmp/sts", r["Value"], r["Description"],
                  extra={"reference": r.get("Reference")})
```

`validate.py` then tests every code you emit against that system's `code_pattern` and fails the build on any mismatch. that gate is worth more than it sounds: writing these regexes caught 25 wrong assumptions of mine and exactly one malformed row upstream. `pattern_status` records how much each regex is worth, `derived` means it was written against the real file, `provisional` means it is still loose.

### licensing

there is no single license here. every system carries its own in `systems.tsv`, and `LICENSES.md` quotes the terms. six systems parse locally and are never uploaded, because their authority forbids republishing the code set: the WHO ATC index, BISAC, the Dewey summaries, the CUSIP mapping, the ISO 10383 MIC list and the what3words API surface.

the code in this repo is MIT. that covers the parsers, not the code systems they read.

this is maintained by brenner cruvinel (brenner@hoffresearch.com). all contributions are welcome.

