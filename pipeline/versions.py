"""pull the version each source publishes out of the raw file itself.

hardcoding a version string means it goes stale the moment download.py refetches it.
reading it from the bytes on disk means systems.tsv always says what is actually there.
a source that publishes no version gets an empty string, which is honest: retrieved_at
still records when the file was taken.
"""
import pathlib, re

def _head(path, n=8192):
    return path.read_bytes()[:n].decode("utf-8", "replace")

def _grep(rx, path, n=8192):
    m = re.search(rx, _head(path, n))
    return m.group(1).strip() if m else ""

def _year(path):
    """the CDC ships the fiscal year in the filename and nowhere in the file."""
    m = re.search(r"(20\d{2})", path.name)
    return m.group(1) if m else ""

def _tz(path):
    """raw_file points at the extracted tree, the release is in its version file."""
    root = path if path.is_dir() else path.parent
    f = root/"version"
    return f.read_text(encoding="utf-8").strip() if f.exists() else ""

EXTRACT = {
 "trp/tld": lambda p: _grep(r"#\s*Version\s+(\S+?),", p),
 "fin/i42": lambda p: _grep(r'Pblshd="([^"]+)"', p),
 "wrt/uni": lambda p: _grep(r"#\s*Version:\s*(\S+)", p),
 "nte/wnt": lambda p: _grep(r'version="(\d{4})"', p),
 "lng/b47": lambda p: _grep(r"File-Date:\s*(\S+)", p),
 "lng/i63": lambda p: _grep(r"File-Date:\s*(\S+)", p),
 "bio/ec":  lambda p: _grep(r"Release of\s+(\S+)", p),
 "cmp/mim": lambda p: _grep(r"<updated>([^<]+)</updated>", p, n=4096),
 "cls/icd": _year,
 "wrt/tz":  _tz,
}

def version_of(system_id, raw_path):
    fn = EXTRACT.get(system_id)
    if not fn: return ""
    try:
        return " ".join(str(fn(pathlib.Path(raw_path))).split())
    except Exception:
        return ""
