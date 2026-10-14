"""RDF vocabularies: ttl, rdf/xml and json-ld, plus the one plain json config."""
import json, pathlib, sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
from core import parser, row, ROOT, label_file

NS = {  # the namespace whose local names are this system's codes
 "grf/foa": "http://xmlns.com/foaf/0.1/",
 "grf/org": "http://www.w3.org/ns/org#",
 "grf/rdf": "http://www.w3.org/2000/01/rdf-schema#",
 "grf/sch": "https://schema.org/",
 "grf/shc": "http://www.w3.org/ns/shacl#",
 "grf/sio": "http://rdfs.org/sioc/ns#",
 "grf/vcd": "http://www.w3.org/2006/vcard/ns#",
}
FMT = {".ttl": "turtle", ".rdf": "xml", ".jsonld": "json-ld"}

TYPE_LABEL = {
 "http://www.w3.org/2000/01/rdf-schema#Class": "class",
 "http://www.w3.org/2002/07/owl#Class": "class",
 "http://www.w3.org/1999/02/22-rdf-syntax-ns#Property": "property",
 "http://www.w3.org/2002/07/owl#ObjectProperty": "property",
 "http://www.w3.org/2002/07/owl#DatatypeProperty": "property",
 "http://www.w3.org/2002/07/owl#AnnotationProperty": "property",
}

def _vocab(path, sid):
    from rdflib import Graph, RDF, RDFS, URIRef
    g = Graph()
    p = ROOT/path
    g.parse(str(p), format=FMT[p.suffix])
    base = NS[sid]
    terms = {}
    for s, _, o in g.triples((None, RDF.type, None)):
        if not isinstance(s, URIRef) or not str(s).startswith(base): continue
        local = str(s)[len(base):]
        if not local or "/" in local: continue
        t = terms.setdefault(local, {"kind": set(), "label": None, "comment": None,
                                     "sub": set()})
        t["kind"].add(TYPE_LABEL.get(str(o), str(o).rsplit("#", 1)[-1].rsplit("/", 1)[-1]))
    for local, t in terms.items():
        s = URIRef(base + local)
        for _, _, o in g.triples((s, RDFS.label, None)):    t["label"] = str(o)
        for _, _, o in g.triples((s, RDFS.comment, None)):  t["comment"] = str(o)
        for pred in (RDFS.subClassOf, RDFS.subPropertyOf):
            for _, _, o in g.triples((s, pred, None)):
                if isinstance(o, URIRef) and str(o).startswith(base):
                    t["sub"].add(str(o)[len(base):])
    for local in sorted(terms):
        t = terms[local]
        parents = sorted(t["sub"])
        yield row(sid, local, t["label"] or local, description=t["comment"],
                  parent_code=parents[0] if len(parents) == 1 else None,
                  extra={"kind": sorted(k for k in t["kind"] if k),
                         "parents": parents or None, "uri": base + local})

for _sid in NS:
    parser(_sid)(lambda path, sysrow, _s=_sid: _vocab(path, _s))

@parser("grf/oid")
def openid_configuration(path, sysrow):
    """not RDF. the codes are the field names of the discovery document."""
    import html, re
    d = json.loads((ROOT/path).read_text(encoding="utf-8"))
    # the meaning of each field is its <dd> in OpenID Connect Discovery 1.0, section 3; the first
    # sentence after the REQUIRED / OPTIONAL marker is the label, the whole entry the description
    spec = label_file(path, "grf/oid").read_text(encoding="utf-8")
    meaning = {}
    for name, dd in re.findall(r"<dt>([a-z_]+)</dt>\s*<dd>(.*?)</dd>", spec, re.S):
        dd = re.sub(r"<span>\s*\(</span><span class='info'>.*?</span><span>\)</span>", "", dd, flags=re.S)  # citation tooltips
        text = " ".join(html.unescape(re.sub(r"<[^>]+>", "", dd)).split())
        text = re.sub(r"^(REQUIRED|OPTIONAL|RECOMMENDED)\.\s*", "", text)
        meaning.setdefault(name, text)
    # fields defined outside OIDC Discovery (RFC 8414, RFC 8628, RFC 9207) take the description
    # of the IANA OAuth Authorization Server Metadata registry
    iana = label_file(path, "grf/oid", 1).read_text(encoding="utf-8")
    for name, desc in re.findall(r"<name>([a-z_]+)</name>\s*<description>([^<]+)</description>", iana):
        meaning.setdefault(name, " ".join(html.unescape(desc).split()) + ".")
    for k, v in sorted(d.items()):
        kind = type(v).__name__
        text = meaning.get(k, "")
        yield row("grf/oid", k, re.split(r"(?<=\.)\s", text, 1)[0] if text else "",
                  description=text or None, extra={"value_type": kind,
                                           "value": v if kind in ("str","bool") else None,
                                           "cardinality": len(v) if isinstance(v, list) else None})


@parser("grf/act")
def activitystreams(path, sysrow):
    """the published file is the JSON-LD context, not a vocabulary graph. it maps every
    term name onto the as: namespace, so the term names are the codes. capitalised terms
    are types, lowercase ones are properties, which is the convention the spec follows."""
    import rdflib
    # labels and comments come from the vocabulary's OWL rendering, published next to the context
    g = rdflib.Graph().parse(label_file(path, "grf/act"), format="turtle")
    AS = "https://www.w3.org/ns/activitystreams#"
    text = lambda s, p: next((str(o) for o in g.objects(rdflib.URIRef(AS + s), p)), None)
    # the AS2 Vocabulary recommendation gives Notes for terms the OWL leaves uncommented, and the
    # ActivityPub recommendation defines the actor properties and collections the context also maps
    import html as H, re
    clean = lambda s: " ".join(H.unescape(re.sub(r"<[^>]+>", "", s)).split())
    notes = {}
    vocab = label_file(path, "grf/act", 1).read_text(encoding="utf-8")
    for m in re.finditer(r'<dfn[^>]*id="dfn-([a-z0-9]+)"[^>]*>([A-Za-z]+)</dfn>', vocab):
        n = re.search(r"<td>Notes:</td>\s*<td>(.*?)</td>", vocab[m.end():m.end() + 6000], re.S)
        if n: notes.setdefault(m.group(2), clean(n.group(1)))
    ap = label_file(path, "grf/act", 2).read_text(encoding="utf-8")
    for name, dd in re.findall(r"<dt[^>]*>\s*(?:<code>)?([A-Za-z]+)(?:</code>)?\s*</dt>\s*<dd>(.*?)</dd>", ap, re.S):
        notes.setdefault(name, clean(dd))
    for sid, title, body in re.findall(r'<section id="([^"]+)">\s*<h\d[^>]*>(?:<span[^>]*>[^<]*</span>)?([^<]+)</h\d>\s*<p>(.*?)</p>', ap, re.S):
        term = {"public-addressing": "Public", "source-property": "source"}.get(sid, sid)
        notes.setdefault(term, f"{title.strip()}: {clean(body)}")
    ctx = json.loads((ROOT/path).read_text(encoding="utf-8"))["@context"]
    for term, v in sorted(ctx.items()):
        if term.startswith("@"): continue
        iri = v.get("@id") if isinstance(v, dict) else v
        if not isinstance(iri, str) or not iri.startswith("as:"): continue
        local = iri[3:]
        # a vocabulary term's label is its name, as the OWL's rdfs:label gives it; the meaning goes in description
        yield row("grf/act", term, text(local, rdflib.RDFS.label) or term,
                  description=text(local, rdflib.RDFS.comment) or notes.get(term)
                  or "Defined only by the Activity Streams 2.0 JSON-LD context, which maps it to " + AS + local + ".",
                  extra={"kind": ["class" if term[:1].isupper() else "property"],
                         "uri": "https://www.w3.org/ns/activitystreams#" + iri[3:],
                         "container": (v.get("@container") if isinstance(v, dict) else None),
                         "value_type": (v.get("@type") if isinstance(v, dict) else None)})
