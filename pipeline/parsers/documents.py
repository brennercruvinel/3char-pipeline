"""pdf sources. the documents themselves are never redistributed, only the facts."""
import pathlib, re, sys, warnings
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
from core import parser, row, ROOT
warnings.filterwarnings("ignore")

def _pages(path):
    import pdfplumber
    with pdfplumber.open(ROOT/path) as pdf:
        for p in pdf.pages:
            yield p.extract_text() or ""

@parser("com/mor")
def morse(path, sysrow):
    """Recommendation ITU-R M.1677-1, Annex 1. the table sets characters in three columns
    across the page, so a single extracted line holds several entries. dot and dash come
    out as ASCII period and U+2212 minus, which are normalised here to . and -"""
    text = "\n".join(_pages(path))
    section = None
    seen = set()
    ENTRY = re.compile(r"([A-Za-z0-9é]|accented e|[^\s\w]{1,3})\s+((?:[.−–\-]\s*){1,6})(?=\s|$)")
    for line in text.splitlines():
        s = line.strip()
        m = re.match(r"1\.1\.(\d)\s+(.+)", s)
        if m: section = m.group(2).strip().lower(); continue
        if not section or not s: continue
        if re.match(r"^\d+(\.\d+)*\s", s) and "−" not in s and "." not in s: continue
        for m in ENTRY.finditer(s):
            ch, sig = m.group(1).strip(), m.group(2)
            sig = re.sub(r"\s+", "", sig).replace("−", "-").replace("–", "-")
            if not sig or len(sig) > 6 or not ch: continue
            key = "\u00c9" if ch.lower().startswith("accented") else ch.upper()
            if len(key) > 1 and key[0] == "[" and key[-1] == "]":
                key = key[1:-1]                     # the table brackets its punctuation
            if not key or key in seen: continue
            if re.fullmatch(r"[.\u2212\u2013\-()\s]+", key):
                continue                            # the character column caught signal, not a character
            seen.add(key)
            yield row("com/mor", key, sig,
                      description=f"international morse code signal for {ch}",
                      extra={"signal": sig, "section": section,
                             "dots": sig.count("."), "dashes": sig.count("-"),
                             "length": len(sig)})

@parser("com/bau")
def baudot(path, sysrow):
    """Recommendation ITU-T S.1, TABLE 1/S.1. five columns of Z and A give the coding,
    Z is mark and A is space, so the combination reads as five bits. the code is that
    bit pattern, which is the thing the machine actually puts on the wire."""
    text = "\n".join(_pages(path))
    ROWLINE = re.compile(r"^_*\s*(\d{1,2})\s+(.+?)\s+([ZA])\s+([ZA])\s+([ZA])\s+([ZA])\s+([ZA])\s*_*$")
    seen = set()
    for line in text.splitlines():
        m = ROWLINE.match(line.strip())
        if not m: continue
        num, mid, *bits = m.groups()
        bitstr = "".join("1" if b == "Z" else "0" for b in bits)
        if bitstr in seen: continue
        seen.add(bitstr)
        mid = re.sub(r"\(cid:\d+\)", "", mid).strip()
        parts = mid.split(None, 1)
        letter = parts[0] if parts else ""
        figure = parts[1].strip() if len(parts) > 1 else None
        if figure and figure.startswith("(subclause"): figure = None
        yield row("com/bau", bitstr, letter,
                  description=f"ITA2 combination {num}",
                  aliases=[letter] if len(letter) == 1 else [],
                  extra={"combination": int(num), "letter_case": letter,
                         "figure_case": figure,
                         "mark_count": bitstr.count("1")})

@parser("cls/dew")
def dewey(path, sysrow):
    """the three summaries: ten classes, hundred divisions, thousand sections.
    pipeline only, OCLC does not permit redistribution of this table."""
    text = "\n".join(_pages(path))
    seen = set()
    for m in re.finditer(r"^\s*(\d{3})\s+([A-Z(\[][^\n]{2,90})$", text, re.M):
        code, label = m.group(1), m.group(2).strip()
        if code in seen: continue
        seen.add(code)
        parent = None
        if code[1:] != "00": parent = code[0] + "00" if code[2] != "0" else code[0] + "00"
        if code[2] != "0": parent = code[:2] + "0"
        elif code[1] != "0": parent = code[0] + "00"
        yield row("cls/dew", code, label, parent_code=parent if parent != code else None,
                  extra={"level": 1 if code[1:] == "00" else (2 if code[2] == "0" else 3)})

@parser("grf/lpg")
def pg_schema(path, sysrow):
    """PG-Schema, arXiv 2211.10962. the paper defines a schema language, and its keywords
    are set in all caps throughout. those keywords are the codes."""
    text = "\n".join(_pages(path))
    counts = {}
    for m in re.finditer(r"\b([A-Z][A-Z]{2,})\b", text):
        k = m.group(1)
        counts[k] = counts.get(k, 0) + 1
    for k in sorted(counts):
        if counts[k] < 3: continue
        yield row("grf/lpg", k, "", extra={"occurrences": counts[k]})


@parser("com/tlg")
def abc_telegraphic(path, sysrow):
    """the ABC Universal Commercial Electric Telegraphic Code, Clauson-Thue 1901.

    the plain OCR text of this scan is unusable for the job: the book sets code number,
    code word and phrase in three columns, and the text derivative emits the columns as
    separate runs of lines, so the pairing that makes the code a code is gone. the djvu
    xml keeps a bounding box per word, which puts the columns back. the code word sits
    around x=410, the phrase starts past x=700, and the code number on the left is the
    worst OCR on the page, 08554 comes out as ^8554, so it rides in extra rather than
    being trusted as the code."""
    from lxml import etree
    import statistics
    CODEWORD_X, PHRASE_X = 380, 700
    seen = set()
    for _, page in etree.iterparse(str(ROOT/path), tag="OBJECT", events=("end",)):
        words = []
        for w in page.findall(".//WORD"):
            txt = (w.text or "").strip()
            if not txt: continue
            try:
                x1, y2, x2, y1 = (int(v) for v in w.get("coords", "").split(",")[:4])
            except ValueError:
                continue
            words.append((x1, (y1 + y2) / 2, y2 - y1, txt))
        if len(words) < 20:
            page.clear(); continue
        tol = max(8, statistics.median(h for *_, h, _ in words) / 2)
        words.sort(key=lambda w: (w[1], w[0]))
        lines, cur, last = [], [], None
        for w in words:
            if last is None or abs(w[1] - last) <= tol:
                cur.append(w)
            else:
                lines.append(cur); cur = [w]
            last = w[1] if last is None else (last + w[1]) / 2 if abs(w[1]-last) <= tol else w[1]
        if cur: lines.append(cur)

        for ln in lines:
            ln.sort(key=lambda w: w[0])
            num = " ".join(t for x, *_, t in ln if x < CODEWORD_X)
            cw = [t for x, *_, t in ln if CODEWORD_X <= x < PHRASE_X]
            phrase = " ".join(t for x, *_, t in ln if x >= PHRASE_X)
            if len(cw) != 1: continue
            code = re.sub(r"[^A-Za-z]", "", cw[0])
            if len(code) < 4 or code in seen: continue
            seen.add(code)
            yield row("com/tlg", code, " ".join(phrase.split()),
                      extra={"code_number_ocr": num.strip() or None,
                             "phrase_words": len(phrase.split()) or None})
        page.clear()
        while page.getprevious() is not None:
            del page.getparent()[0]
