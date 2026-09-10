"""xml registries, ontology-scale json, and the 98M wordnet."""
import json, pathlib, sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
from core import parser, row, ROOT

@parser("cmp/mim")
def media_types(path, sysrow):
    """IANA groups records by top level type. the registered code is type/subtype,
    the <name> alone is ambiguous across trees."""
    from lxml import etree
    NS = {"i": "http://www.iana.org/assignments"}
    tree = etree.parse(str(ROOT/path))
    for reg in tree.getroot().findall("i:registry", NS):
        top = reg.get("id")
        if not top: continue
        for rec in reg.findall("i:record", NS):
            name = (rec.findtext("i:name", namespaces=NS) or "").strip()
            if not name: continue
            note = None
            if " " in name:                      # "name - DEPRECATED" style annotations
                name, _, note = name.partition(" ")
            refs = [f'{x.get("type")}:{x.get("data")}' for x in rec.findall("i:xref", NS)]
            yield row("cmp/mim", f"{top}/{name}", name,
                      status="deprecated" if note and "deprecat" in note.lower() else None,
                      parent_code=top,
                      extra={"tree": top, "subtype": name, "note": note,
                             "references": refs or None,
                             "registered": rec.get("date"),
                             "template": rec.findtext("i:file", namespaces=NS)})

@parser("fin/i42")
def iso4217(path, sysrow):
    """one entry per country, so the same currency repeats. the currency is the code,
    the countries that use it collapse into extra."""
    from lxml import etree
    tree = etree.parse(str(ROOT/path))
    agg, order = {}, []
    for e in tree.getroot().iter("CcyNtry"):
        g = lambda t: (e.findtext(t) or "").strip()
        code = g("Ccy")
        if not code: continue
        if code not in agg:
            order.append(code)
            agg[code] = {"name": g("CcyNm"), "numeric": g("CcyNbr"),
                         "minor": g("CcyMnrUnts"), "countries": []}
        if g("CtryNm"): agg[code]["countries"].append(g("CtryNm").title())
    published = tree.getroot().get("Pblshd")
    for code in order:
        v = agg[code]
        yield row("fin/i42", code, v["name"],
                  extra={"numeric": v["numeric"], "minor_units": v["minor"],
                         "countries": v["countries"], "country_count": len(v["countries"]),
                         "published": published})

@parser("bio/gen")
def hgnc(path, sysrow):
    """HGNC approved gene symbols. previous symbols and aliases are what make this useful,
    a symbol that was withdrawn still shows up in twenty years of literature."""
    docs = json.loads((ROOT/path).read_text(encoding="utf-8"))["response"]["docs"]
    for d in docs:
        sym = (d.get("symbol") or "").strip()
        if not sym: continue
        yield row("bio/gen", sym, d.get("name") or "",
                  status=(d.get("status") or "").lower().replace(" ", "_") or None,
                  aliases=(d.get("alias_symbol") or []) + (d.get("prev_symbol") or []),
                  extra={"hgnc_id": d.get("hgnc_id"), "location": d.get("location"),
                         "locus_group": d.get("locus_group"),
                         "locus_type": d.get("locus_type"),
                         "entrez_id": d.get("entrez_id"),
                         "ensembl_gene_id": d.get("ensembl_gene_id"),
                         "uniprot_ids": d.get("uniprot_ids")})

@parser("nte/wnt")
def wordnet(path, sysrow):
    """WN-LMF, 98 MB, streamed. the synset id is the code: a stable address for one sense
    shared by every word that means it. lemmas attach through Sense elements."""
    from lxml import etree
    src = str(ROOT/path)
    members = {}
    for _, el in etree.iterparse(src, tag="LexicalEntry", events=("end",)):
        lemma = el.find("Lemma")
        form = lemma.get("writtenForm") if lemma is not None else None
        if form:
            for s in el.findall("Sense"):
                members.setdefault(s.get("synset"), []).append(form)
        el.clear()
        while el.getprevious() is not None:
            del el.getparent()[0]
    for _, el in etree.iterparse(src, tag="Synset", events=("end",)):
        sid = el.get("id")
        if sid:
            words = members.get(sid, [])
            defs = [d.text for d in el.findall("Definition") if d.text]
            yield row("nte/wnt", sid, words[0] if words else "",
                      description=defs[0] if defs else None,
                      aliases=words[1:],
                      extra={"pos": el.get("partOfSpeech"), "members": len(words),
                             "ili": el.get("ili") or None,
                             "relations": len(el.findall("SynsetRelation")) or None})
        el.clear()
        while el.getprevious() is not None:
            del el.getparent()[0]
