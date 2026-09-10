# curated metadata for the 64 code systems.
# license_status triage: ok = clearly redistributable, check = needs verification,
# problem = authority asserts rights that likely block redistribution.

SYSTEMS = {
# system_id: (name, authority, code_pattern, case_sensitive, license, license_status)
"bio/aa1": ("amino acid 1-letter codes", "IUPAC-IUB JCBN", r"^[A-Z]$", True, "iupac-recommendations", "ok"),
"bio/aa3": ("amino acid 3-letter codes", "IUPAC-IUB JCBN", r"^[A-Z][a-z]{2}$", True, "iupac-recommendations", "ok"),
"bio/cdn": ("NCBI genetic codes (codons)", "NCBI", r"^[ACGTU]{3}$", True, "public-domain-usgov", "ok"),
"bio/ec":  ("enzyme commission numbers", "IUBMB / ExPASy", r"^\d+\.\d+\.\d+\.(\d+|-)$", False, "CC-BY-4.0", "ok"),
"bio/gen": ("HGNC gene symbols", "HUGO Gene Nomenclature Committee", r"^[A-Za-z0-9@#\-\.]+$", True, "CC0-1.0", "ok"),
"bio/pdb": ("PDB entry IDs", "wwPDB / RCSB", r"^[0-9][A-Za-z0-9]{3}$", False, "CC0-1.0", "ok"),
"cls/atc": ("WHO ATC drug classification", "WHO Collaborating Centre for Drug Statistics Methodology", r"^[A-V](\d{2}([A-Z]{2}(\d{2})?)?)?$", True, "proprietary", "problem"),
"cls/bsc": ("BISAC subject headings", "Book Industry Study Group", r"^[A-Z]{3}\d{6}$", True, "proprietary", "problem"),
"cls/dew": ("Dewey decimal summaries", "OCLC", r"^\d{3}$", False, "proprietary", "problem"),
"cls/elm": ("chemical element symbols", "IUPAC", r"^[A-Z][a-z]{0,2}$", True, "public-domain-usgov", "ok"),
"cls/icd": ("ICD-10-CM", "US CDC / NCHS", r"^[A-Z]\d{2}[A-Z0-9]{0,5}$", True, "public-domain-usgov", "ok"),
"cls/loc": ("Library of Congress classification outline", "Library of Congress", r"^[A-Z]{1,3}$", True, "CC0-1.0", "ok"),
"cmp/asm": ("x86 instruction mnemonics", "Intel / AMD", r"^[A-Z][A-Z0-9]{1,15}$", False, "MIT", "ok"),
"cmp/css": ("CSS functions", "W3C CSSWG / MDN", r"^[a-z][a-z0-9\-]*$", False, "CC0-1.0", "ok"),
"cmp/dns": ("DNS resource record types", "IANA", r"^[A-Z][A-Z0-9\-\*]*$", True, "iana-registry", "ok"),
"cmp/ern": ("POSIX errno names", "IEEE / The Open Group", r"^E[A-Z0-9]+$", True, "posix-spec", "ok"),
"cmp/ext": ("file extensions", "community", r"^[a-z0-9]+$", False, "Unlicense", "ok"),
"cmp/frc": ("FourCC codec identifiers", "community / VLC", r"^.{1,4}$", True, "GPL-2.0-or-later", "ok"),
"cmp/git": ("git subcommands", "git project", r"^[a-z][a-z0-9\-]*$", True, "GPL-2.0-only", "ok"),
"cmp/hex": ("CSS named colors", "W3C CSSWG", r"^[a-z]+$", False, "MIT", "ok"),
"cmp/htt": ("HTTP methods", "IANA", r"^[A-Z][A-Z\-]*$", True, "iana-registry", "ok"),
"cmp/mim": ("media types", "IANA", r"^[a-zA-Z0-9][a-zA-Z0-9!#$&\-\^_\.\+]*$", False, "iana-registry", "ok"),
"cmp/reg": ("x86-64 register names", "LLVM Project", r"^[a-z][a-z0-9]*$", False, "Apache-2.0-WITH-LLVM-exception", "ok"),
"cmp/sts": ("HTTP status codes", "IANA", r"^\d{3}$", False, "iana-registry", "ok"),
"cmp/vim": ("vim motion commands", "vim project", r"^\S+$", True, "Vim", "ok"),
"com/bau": ("Baudot / ITA2 teleprinter codes", "ITU-T", r"^[A-Z0-9\-]+$", True, "itu-recommendation", "ok"),
"com/mor": ("morse code", "ITU-R", r"^[A-Za-z0-9]$", False, "itu-recommendation", "ok"),
"com/tlg": ("ABC universal commercial telegraphic code", "William Clauson-Thue (1901)", r"^[A-Za-z]+$", False, "public-domain-expired", "ok"),
"fin/cfi": ("ISO 10962 CFI codes", "SIX Group / ISO", r"^[A-Z]{6}$", True, "six-silent", "check"),
"fin/cus": ("CIK to CUSIP mapping", "CUSIP Global Services / SEC", r"^[0-9A-Z]{6,9}$", True, "proprietary", "problem"),
"fin/i42": ("ISO 4217 currency codes", "SIX Group / ISO", r"^[A-Z]{3}$", True, "six-silent", "check"),
"fin/mic": ("ISO 10383 market identifier codes", "ISO 20022 RA / SWIFT", r"^[A-Z0-9]{4}$", True, "proprietary", "problem"),
"fin/tck": ("SEC company tickers", "US SEC", r"^[A-Z0-9\.\-]{1,10}$", True, "public-domain-usgov", "ok"),
"grf/act": ("ActivityStreams 2.0 terms", "W3C", r"^[A-Za-z][A-Za-z0-9]*$", True, "W3C-Document", "ok"),
"grf/foa": ("FOAF vocabulary terms", "FOAF project", r"^[a-z][A-Za-z0-9]*$", True, "CC-BY-1.0", "ok"),
"grf/gql": ("openCypher keywords", "openCypher / Neo4j", r"^[A-Z][A-Z_]*$", False, "Apache-2.0", "ok"),
"grf/lpg": ("property graph schema terms", "arXiv 2211.10962", r"^\S+$", True, "CC-BY-4.0", "ok"),
"grf/oid": ("OpenID Connect discovery fields", "OpenID Foundation", r"^[a-z][a-z0-9_]*$", True, "no-license-factual", "ok"),
"grf/org": ("W3C Organization ontology terms", "W3C", r"^[a-zA-Z][A-Za-z0-9]*$", True, "W3C-Document", "ok"),
"grf/rdf": ("RDF Schema terms", "W3C", r"^[a-zA-Z][A-Za-z0-9]*$", True, "W3C-Document", "ok"),
"grf/sch": ("schema.org types and properties", "schema.org / W3C CG", r"^[a-zA-Z][A-Za-z0-9]*$", True, "CC-BY-SA-3.0", "ok"),
"grf/shc": ("SHACL vocabulary terms", "W3C", r"^[A-Za-z][A-Za-z0-9]*$", True, "W3C-Document", "ok"),
"grf/sio": ("SIOC vocabulary terms", "SIOC Project / DERI", r"^[a-z][A-Za-z0-9_]*$", True, "CC-BY-SA-3.0", "ok"),
"grf/vcd": ("vCard ontology terms", "W3C", r"^[a-zA-Z][A-Za-z0-9\-]*$", True, "W3C-Document", "ok"),
"lng/b47": ("BCP 47 language subtags", "IANA", r"^[A-Za-z0-9\-]+$", False, "iana-registry", "ok"),
"lng/glt": ("Glottolog languoid codes", "MPI-EVA Leipzig", r"^[a-z]{4}\d{4}$", True, "CC-BY-4.0", "ok"),
"lng/i15": ("ISO 15924 script codes", "Unicode Consortium (RA)", r"^[A-Z][a-z]{3}$", True, "unicode-terms", "ok"),
"lng/i31": ("ISO 3166-1 country codes", "ISO 3166/MA", r"^[A-Z]{2,3}$", True, "CC-BY-SA-4.0", "ok"),
"lng/i39": ("ISO 639-1 language codes", "ISO 639/RA", r"^[a-z]{2}$", True, "ODC-PDDL-1.0", "ok"),
"lng/i63": ("BCP 47 three-letter language subtags", "IANA", r"^[a-z]{3}$", False, "iana-registry", "ok"),
"lng/ioc": ("country codes composite", "community / datasets.io", r"^[A-Z]{2,3}$", True, "ODC-PDDL-1.0", "ok"),
"lng/mdy": ("month names", "Unicode CLDR", r"^\d{1,2}$", False, "unicode-terms", "ok"),
"nte/wnt": ("English WordNet 2024 synset and sense IDs", "Global WordNet Association", r"^\S+$", True, "CC-BY-4.0", "ok"),
"trp/iata": ("IATA airport codes", "IATA", r"^[A-Z]{3}$", True, "public-domain-ourairports", "ok"),
"trp/ica2": ("IATA and ICAO airline codes", "IATA / ICAO", r"^[A-Z0-9]{2,3}$", True, "ODbL-1.0", "ok"),
"trp/icao": ("ICAO airport codes", "ICAO", r"^[A-Z0-9]{4}$", True, "public-domain-ourairports", "ok"),
"trp/olc": ("Open Location Code (plus codes)", "Google", r"^[23456789CFGHJMPQRVWX]{4,}\+[23456789CFGHJMPQRVWX]*$", True, "Apache-2.0", "ok"),
"trp/tld": ("top level domains", "IANA", r"^[A-Z0-9\-]+$", False, "iana-registry", "ok"),
"trp/unl": ("UN/LOCODE location codes", "UNECE", r"^[A-Z0-9]{3}$", True, "ODC-PDDL-1.0", "ok"),
"trp/w3w": ("what3words API surface", "what3words", r"^[a-z][a-z0-9_]*$", True, "proprietary", "problem"),
"wrt/abj": ("Hebrew alphabet letters", "Unicode / community", r"^\S+$", True, "MIT", "ok"),
"wrt/iau": ("IAU constellation abbreviations", "International Astronomical Union", r"^[A-Z][A-Za-z]{2}$", True, "BSD-3-Clause", "ok"),
"wrt/tz":  ("tz database zone names and abbreviations", "IANA / tzdb", r"^\S+$", True, "public-domain-tzdb", "ok"),
"wrt/uni": ("Unicode emoji sequences", "Unicode Consortium", r"^[0-9A-F]{4,6}( [0-9A-F]{4,6})*$", True, "unicode-terms", "ok"),
}

# pattern_status: provisional = placeholder solto, aperta quando o parser existir.
# derived = escrito olhando o arquivo real. confirmed = so validate.py promove,
# depois de bater contra 100% dos codigos emitidos.
DERIVED_PATTERN = {
 "bio/aa3","cls/elm","cmp/htt","cmp/sts","wrt/iau","lng/i39","cls/atc","cls/bsc",
 "cls/loc","lng/i15","trp/tld","cmp/dns","trp/unl","cmp/ern","cmp/reg","lng/mdy",
 "grf/sio","lng/i31","lng/ioc","lng/glt","lng/i63","bio/aa1",
}

# derived_from: sistema cujo raw alimenta este, quando nao tem raw proprio
DERIVED_FROM = {
 "lng/i63": "lng/b47",
}

NOTES = {
 "lng/i63": ("three-letter language subtags as IANA publishes them, extracted from the BCP 47 "
             "registry that also feeds lng/b47. this is not ISO 639-3 and is not labelled as such. "
             "RFC 5646 omits the three-letter form whenever a two-letter subtag exists, so eng, deu "
             "and por are absent by design, the registry carries en, de and pt instead. it also "
             "carries 115 ISO 639-5 collections and 224 deprecated subtags that ISO 639-3 does not. "
             "the SIL published table is the authority for ISO 639-3 proper and its terms forbid "
             "redistribution, so it is neither shipped nor used as a source here."),
 "trp/icao": "same OurAirports file as trp/iata, read on a different column",
 "bio/aa1":  "same IUPAC JCBN Table 1 as bio/aa3, read on the one-letter symbol column",
 "fin/cfi":  "SIX publishes free of charge and says nothing about redistribution",
 "fin/i42":  "SIX publishes free of charge and says nothing about redistribution",
}
