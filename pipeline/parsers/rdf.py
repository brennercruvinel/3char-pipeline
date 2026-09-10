"""RDF vocabularies: ttl, rdf/xml and json-ld, plus the one plain json config."""
import json, pathlib, sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
from core import parser, row, ROOT

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
    d = json.loads((ROOT/path).read_text(encoding="utf-8"))
    for k, v in sorted(d.items()):
        kind = type(v).__name__
        yield row("grf/oid", k, "", extra={"value_type": kind,
                                           "value": v if kind in ("str","bool") else None,
                                           "cardinality": len(v) if isinstance(v, list) else None})


@parser("grf/act")
def activitystreams(path, sysrow):
    """the published file is the JSON-LD context, not a vocabulary graph. it maps every
    term name onto the as: namespace, so the term names are the codes. capitalised terms
    are types, lowercase ones are properties, which is the convention the spec follows."""
    ctx = json.loads((ROOT/path).read_text(encoding="utf-8"))["@context"]
    for term, v in sorted(ctx.items()):
        if term.startswith("@"): continue
        iri = v.get("@id") if isinstance(v, dict) else v
        if not isinstance(iri, str) or not iri.startswith("as:"): continue
        yield row("grf/act", term, "",
                  extra={"kind": ["class" if term[:1].isupper() else "property"],
                         "uri": "https://www.w3.org/ns/activitystreams#" + iri[3:],
                         "container": (v.get("@container") if isinstance(v, dict) else None),
                         "value_type": (v.get("@type") if isinstance(v, dict) else None)})
