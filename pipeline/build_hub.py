"""assemble what actually gets uploaded: systems.parquet plus the publishable subset."""
import csv, json, pathlib, shutil, sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import pyarrow as pa, pyarrow.parquet as pq
from core import ROOT, systems

HUB = ROOT/"hub"
SYS_SCHEMA = pa.schema([(c, pa.bool_() if c == "case_sensitive" else pa.string())
                        for c in ["system_id","domain","name","authority","url","license",
                                  "license_status","code_pattern","pattern_status",
                                  "case_sensitive","raw_file","derived_from","version",
                                  "retrieved_at","notes"]])

def main():
    sysmap = systems()
    built = {s for s in sysmap if (ROOT/"data"/f"{s}.parquet").exists()}
    blocked = {s for s, r in sysmap.items() if r["license_status"] == "problem"}
    publish = sorted(built - blocked)

    if HUB.exists(): shutil.rmtree(HUB)
    (HUB/"data").mkdir(parents=True)

    counts = {}
    for sid in publish:
        src = ROOT/"data"/f"{sid}.parquet"
        dst = HUB/"data"/f"{sid}.parquet"
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
        counts[sid] = pq.read_metadata(src).num_rows

    rows = []
    for sid in publish:
        r = dict(sysmap[sid])
        r["case_sensitive"] = r["case_sensitive"] == "true"
        r.pop("raw_file", None); r["raw_file"] = ""      # raw never ships
        rows.append({f.name: r.get(f.name) or ("" if f.type == pa.string() else False)
                     for f in SYS_SCHEMA})
    pq.write_table(pa.Table.from_pylist(rows, schema=SYS_SCHEMA),
                   HUB/"systems.parquet", compression="zstd")

    (ROOT/"pipeline"/"hub_manifest.json").write_text(json.dumps(
        {"publish": publish, "blocked": sorted(blocked & built),
         "not_built": sorted(set(sysmap) - built), "counts": counts}, indent=2))
    print(f"publish {len(publish)} systems, {sum(counts.values()):,} codes")
    print(f"held back (license): {sorted(blocked & built)}")
    print(f"no parser yet: {len(set(sysmap) - built)}")

if __name__ == "__main__":
    sys.exit(main())
