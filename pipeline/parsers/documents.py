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
    """PG-Schema, arXiv 2211.10962. the keywords are those of the core grammar (Fig. 3), labelled by
    the productions that use them, plus the PG-Keys constraint keywords and the base property types
    the paper writes in its schemas (sections 4.3 and 4.4). counting every all-caps word in the paper
    picked up affiliations and acronyms (ACM, CNRS, USA), which are not part of the language."""
    text = "\n".join(_pages(path))
    words = lambda name: re.sub(r"(?<=[a-z])(?=[A-Z])", " ", name).lower()
    used, prod = {}, None
    for line in text.splitlines():
        m = re.match(r"^(\w+) ::= (.*)$", line.strip())
        if m: prod, body = m.group(1), m.group(2)
        elif prod and line.strip().startswith("|"): body = line
        else:
            prod = None if not line.strip().startswith("|") else prod
            continue
        for k in re.findall(r"\b([A-Z]{2,})\b", body):
            used.setdefault(k, []).append(prod) if prod not in used.get(k, []) else None
    other = {
        "FOR": "Opens a PG-Keys constraint: FOR p(x) <qualifier> q(x, y)",
        "EXCLUSIVE": "PG-Keys qualifier: no result of q is shared by two values of x",
        "MANDATORY": "PG-Keys qualifier: every x has at least one result of q",
        "SINGLETON": "PG-Keys qualifier: every x has at most one result of q",
        "WITHIN": "Marks what a PG-Keys query returns",
        "WHERE": "Condition inside a PG-Keys query",
        "COUNT": "Cardinality constraint, COUNT <lower>..<upper> OF",
        "OF": "Cardinality constraint, COUNT <lower>..<upper> OF",
        "ARRAY": "Array property type, as in STRING ARRAY {1,2}",
    }
    types = {"STRING", "INT", "DATE", "FLOAT", "DOUBLE", "BOOL"}
    for k in sorted(set(used) | set(other) | types):
        if k not in text: continue
        label = ("Keyword in " + ", ".join(words(p) for p in used[k])) if k in used \
            else other.get(k) or "Base property type"
        yield row("grf/lpg", k, label, extra={"occurrences": len(re.findall(rf"\b{k}\b", text)),
                                             "grammar": used.get(k)})


@parser("com/tlg")
def abc_telegraphic(path, sysrow):
    """the ABC Universal Commercial Electric Telegraphic Code, Clauson-Thue 1901.

    each line of the code proper is code number, code word and phrase, in three columns. the
    columns sit at different x positions from page to page, so they are found per page: a column
    starts wherever a word opens a line or follows a wide gap, the code-word column is the first
    one whose words are mostly capitalised, and the phrase column is the next one to the right.
    the code number is the worst OCR on the page (08554 comes out as ^8554), so it rides in extra.

    a page is kept only when its code words run in alphabetical order, as they do in the code
    proper. that drops the front matter and the extended index, which are not alphabetical by
    code word, and pages whose phrases are mostly figures (the index's page numbers and the
    number tables at the end, whose two-up layout the OCR does not keep apart)."""
    from lxml import etree
    import collections, statistics

    def lines_of(page):
        ws = []
        for w in page.findall(".//WORD"):
            t = (w.text or "").strip()
            if not t: continue
            try:
                x1, y2, x2, y1 = (int(v) for v in w.get("coords", "").split(",")[:4])
            except ValueError:
                continue
            ws.append((x1, x2, (y1 + y2) / 2, y2 - y1, t))
        if len(ws) < 20: return []
        tol = max(8, statistics.median(w[3] for w in ws) / 2)
        ws.sort(key=lambda w: (w[2], w[0]))
        lines, cur, mid = [], [], None
        for w in ws:
            if mid is None or abs(w[2] - mid) <= tol:
                cur.append(w); mid = w[2] if mid is None else (mid + w[2]) / 2
            else:
                lines.append(sorted(cur)); cur, mid = [w], w[2]
        if cur: lines.append(sorted(cur))
        return lines

    def column_starts(lines):
        starts = []
        for ln in lines:
            prev = None
            for x1, x2, *_ in ln:
                if prev is None or x1 - prev > 60: starts.append(x1)
                prev = x2
        hist = collections.Counter(x // 40 * 40 for x in starts)
        peaks = sorted(b for b, n in hist.items() if n >= max(5, len(lines) // 4))
        cols = []
        for b in peaks:
            if cols and b - cols[-1][-1] <= 80: cols[-1].append(b)
            else: cols.append([b])
        return [c[0] for c in cols]

    seen = set()
    for _, page in etree.iterparse(str(ROOT/path), tag="OBJECT", events=("end",)):
        lines = lines_of(page)
        page.clear()
        while page.getprevious() is not None:
            del page.getparent()[0]
        if not lines: continue
        cols = column_starts(lines)
        cw = next((c for c in cols
                   if (toks := [w[4] for ln in lines for w in ln if c - 40 <= w[0] < c + 80])
                   and sum(bool(re.match(r"^[A-Z][a-z]{2,}$", t)) for t in toks) / len(toks) > 0.6), None)
        ph = next((c for c in cols if cw is not None and c > cw + 150), None)
        if cw is None or ph is None: continue
        entries = []
        for ln in lines:
            word = [w[4] for w in ln if cw - 50 <= w[0] < ph - 60]
            phrase = " ".join(w[4] for w in ln if w[0] >= ph - 60).strip()
            number = " ".join(w[4] for w in ln if w[0] < cw - 50).strip()
            code = re.sub(r"[^A-Za-z]", "", "".join(word))
            if not (4 <= len(code) <= 22) or not phrase: continue
            if re.match(r"^Code\s*No|^Word", " ".join(word)) or "continued" in phrase.replace(" ", ""):
                continue                                   # running header: "Code No. Code Word  <keyword> — continued."
            entries.append((code, phrase, number))
        if len(entries) < 10: continue
        order = sum(a[0].lower() <= b[0].lower() for a, b in zip(entries, entries[1:])) / (len(entries) - 1)
        figures = sum(bool(re.search(r"\d", e[1])) for e in entries) / len(entries)
        if order < 0.8 or figures > 0.4: continue
        for code, phrase, number in entries:
            if code in seen: continue
            seen.add(code)
            yield row("com/tlg", code, " ".join(phrase.split()),
                      extra={"code_number_ocr": number or None, "phrase_words": len(phrase.split())})
