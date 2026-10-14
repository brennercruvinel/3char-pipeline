"""fetch every raw file named in systems.tsv, then verify it against CHECKSUMS.tsv.

a checksum mismatch is a hard failure. upstream moving is real and normal, but it is
not something a build gets to absorb silently: the parquet would change underneath
whoever is reading it. re-run with --accept-new to rewrite CHECKSUMS.tsv on purpose.
"""
import argparse, csv, hashlib, io, os, pathlib, sys, tarfile, urllib.request, zipfile

ROOT = pathlib.Path(__file__).resolve().parent.parent
UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36")

def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for blk in iter(lambda: fh.read(1 << 20), b""):
            h.update(blk)
    return h.hexdigest()

def read_tsv(path):
    with open(path, encoding="utf-8") as fh:
        return list(csv.DictReader(fh, delimiter="\t"))

def fetch(url):
    # sec.gov refuses requests without a declared contact; set CH3_SEC_USER_AGENT to "Name email"
    ua = os.environ.get("CH3_SEC_USER_AGENT", UA) if "sec.gov" in url else UA
    req = urllib.request.Request(url, headers={"User-Agent": ua})
    with urllib.request.urlopen(req, timeout=120) as r:
        return r.read()

def systems_to_fetch():
    """one entry per url. derived systems have no download of their own, and
    systems that share a raw file each keep their own copy on disk."""
    for r in read_tsv(ROOT/"systems.tsv"):
        if r["derived_from"]:
            continue
        yield r["system_id"], r["url"], ROOT/r["raw_file"]

def label_sources():
    """files read only for labels, kept as downloaded next to the main source."""
    sys.path.insert(0, str(ROOT/"pipeline"))
    from systems_meta import LABEL_SOURCES
    for sid, files in LABEL_SOURCES.items():
        for name, url, _ in files:
            yield sid, url, ROOT/"data"/sid/"raw"/name

def download_all():
    for sid, url, dest in label_sources():
        dest.parent.mkdir(parents=True, exist_ok=True)
        try:
            dest.write_bytes(fetch(url))
        except Exception as e:
            print(f"  FAIL {sid} labels: {e}", file=sys.stderr); yield sid; continue
        print(f"  ok   {sid}  labels")
    for sid, url, dest in systems_to_fetch():
        dest.parent.mkdir(parents=True, exist_ok=True)
        try:
            blob = fetch(url)
        except Exception as e:
            print(f"  FAIL {sid}: {e}", file=sys.stderr); yield sid; continue
        if url.endswith(".tar.gz"):
            root = dest if dest.is_dir() else dest.parent
            root.mkdir(parents=True, exist_ok=True)
            with tarfile.open(fileobj=io.BytesIO(blob)) as tf:
                tf.extractall(root, filter="data")
        elif url.endswith(".zip"):
            # the CDC ships ICD-10-CM as a zip of several files; only the one named in raw_file is kept
            with zipfile.ZipFile(io.BytesIO(blob)) as zf:
                member = next(n for n in zf.namelist() if n.rsplit("/", 1)[-1] == dest.name)
                dest.write_bytes(zf.read(member))
        else:
            dest.write_bytes(blob)
        print(f"  ok   {sid}  {len(blob):>9,} bytes")

def verify(accept_new=False):
    manifest = ROOT/"CHECKSUMS.tsv"
    expected = {r["path"]: (r["sha256"], int(r["bytes"])) for r in read_tsv(manifest)}
    # only raw sources are in the manifest. the parquet next to them is built output,
    # and sweeping it in here made every successful build look like manifest drift.
    on_disk = sorted(str(p.relative_to(ROOT)) for p in (ROOT/"data").rglob("raw/**/*")
                     if p.is_file())

    missing = [p for p in expected if p not in set(on_disk)]
    extra = [p for p in on_disk if p not in expected]
    changed = []
    for p in on_disk:
        if p not in expected: continue
        want, want_n = expected[p]
        got = sha256(ROOT/p)
        if got != want:
            changed.append((p, want, got, want_n, (ROOT/p).stat().st_size))

    if accept_new:
        rows = [{"sha256": sha256(ROOT/p), "bytes": (ROOT/p).stat().st_size, "path": p}
                for p in on_disk]
        with open(manifest, "w", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=["sha256","bytes","path"], delimiter="\t",
                               lineterminator="\n")
            w.writeheader(); w.writerows(rows)
        print(f"CHECKSUMS.tsv rewritten: {len(rows)} files")
        return 0

    for p in missing: print(f"MISSING  {p}", file=sys.stderr)
    for p in extra:   print(f"UNTRACKED {p}", file=sys.stderr)
    for p, want, got, wn, gn in changed:
        print(f"CHANGED  {p}\n  expected {want} ({wn:,} bytes)\n  got      {got} ({gn:,} bytes)",
              file=sys.stderr)

    bad = len(missing) + len(extra) + len(changed)
    if bad:
        print(f"\n{bad} file(s) do not match CHECKSUMS.tsv. the build stops here.\n"
              f"if upstream legitimately moved, re-run with --accept-new to adopt the new "
              f"bytes on purpose.", file=sys.stderr)
        return 1
    print(f"verified {len(on_disk)} files against CHECKSUMS.tsv")
    return 0

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--skip-download", action="store_true", help="verify what is already on disk")
    ap.add_argument("--accept-new", action="store_true", help="rewrite CHECKSUMS.tsv from disk")
    a = ap.parse_args()
    if not a.skip_download:
        failed = list(download_all())
        if failed:
            print(f"\n{len(failed)} download(s) failed: {failed}", file=sys.stderr)
            return 1
    return verify(accept_new=a.accept_new)

if __name__ == "__main__":
    sys.exit(main())
