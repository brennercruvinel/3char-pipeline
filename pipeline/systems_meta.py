import urllib.parse

# curated metadata for the 64 code systems.
# license_status triage: ok = clearly redistributable, check = needs verification,
# problem = authority asserts rights that likely block redistribution.

SYSTEMS = {
# system_id: (name, authority, code_pattern, case_sensitive, license, license_status)
"bio/aa1": ("amino acid 1-letter codes", "IUPAC-IUB JCBN", r"^[A-Z]$", True, "iupac-recommendations", "ok"),
"bio/aa3": ("amino acid 3-letter codes", "IUPAC-IUB JCBN", r"^[A-Z][a-z]{2}$", True, "iupac-recommendations", "ok"),
"bio/cdn": ("NCBI genetic codes (codons)", "NCBI", r"^[ACGTU]{3}$", True, "public-domain-usgov", "ok"),
"bio/ec":  ("enzyme commission numbers", "IUBMB / ExPASy", r"^\d+\.\d+\.\d+\.(n?\d+|-)$", False, "CC-BY-4.0", "ok"),
"bio/gen": ("HGNC gene symbols", "HUGO Gene Nomenclature Committee", r"^[A-Za-z0-9@#\-\._]+$", True, "CC0-1.0", "ok"),
"bio/pdb": ("PDB entry IDs", "wwPDB / RCSB", r"^[1-9][A-Z0-9]{3}$", True, "CC0-1.0", "ok"),
"cls/atc": ("WHO ATC drug classification", "WHO Collaborating Centre for Drug Statistics Methodology", r"^[A-V](\d{2}([A-Z]([A-Z](\d{2})?)?)?)?$", True, "proprietary", "problem"),
"cls/bsc": ("BISAC subject headings", "Book Industry Study Group", r"^[A-Z]{3}\d{6}$", True, "proprietary", "problem"),
"cls/dew": ("Dewey decimal summaries", "OCLC", r"^\d{3}$", False, "proprietary", "problem"),
"cls/elm": ("chemical element symbols", "IUPAC", r"^[A-Z][a-z]{0,2}$", True, "public-domain-usgov", "ok"),
"cls/icd": ("ICD-10-CM", "US CDC / NCHS", r"^[A-Z][A-Z0-9]{2,6}$", True, "public-domain-usgov", "ok"),
"cls/loc": ("Library of Congress classification outline", "Library of Congress", r"^[A-Z]{1,3}$", True, "CC0-1.0", "ok"),
"cmp/asm": ("x86 instruction mnemonics", "Intel / AMD", r"^[A-Z][A-Za-z0-9]{1,15}$", False, "MIT", "ok"),
"cmp/css": ("CSS functions", "W3C CSSWG / MDN", r"^[a-zA-Z][a-zA-Z0-9\-]*$", False, "CC0-1.0", "ok"),
"cmp/dns": ("DNS resource record types", "IANA", r"^([A-Z][A-Z0-9\-]*|\*)$", True, "iana-registry", "ok"),
"cmp/ern": ("POSIX errno names", "IEEE / The Open Group", r"^E[A-Z0-9]+$", True, "posix-spec", "ok"),
"cmp/ext": ("file extensions", "community", r"^[a-z0-9][a-z0-9.+\-]*$", False, "Unlicense", "ok"),
"cmp/frc": ("FourCC codec identifiers", "community / VLC", r"^[A-Za-z0-9\-.:_]{2,4}$", True, "GPL-2.0-or-later", "ok"),
"cmp/git": ("git subcommands", "git project", r"^[a-z][a-z0-9\-]{1,17}$", True, "GPL-2.0-only", "ok"),
"cmp/hex": ("CSS named colors", "W3C CSSWG", r"^[a-z]{3,20}$", False, "MIT", "ok"),
"cmp/htt": ("HTTP methods", "IANA", r"^([A-Z][A-Z\-]*|\*)$", True, "iana-registry", "ok"),
"cmp/mim": ("media types", "IANA", r"^[a-z]+/[a-zA-Z0-9!#$&\-\^_\.\+]+$", False, "iana-registry", "ok"),
"cmp/reg": ("x86-64 register names", "LLVM Project", r"^[a-z][a-z0-9.()]*$", False, "Apache-2.0-WITH-LLVM-exception", "ok"),
"cmp/sts": ("HTTP status codes", "IANA", r"^\d{3}$", False, "iana-registry", "ok"),
"cmp/vim": ("vim motion commands", "vim project", r"^\S{1,40}$", True, "Vim", "ok"),
"com/bau": ("Baudot / ITA2 teleprinter codes", "ITU-T", r"^[A-Z0-9\-]+$", True, "itu-recommendation", "ok"),
"com/mor": ("morse code", "ITU-R", r"^([A-Z0-9\u00c9]|[^\w\s]{1,2})$", False, "itu-recommendation", "ok"),
"com/tlg": ("ABC universal commercial telegraphic code", "William Clauson-Thue (1901)", r"^[A-Za-z]{4,22}$", False, "public-domain-expired", "ok"),
"fin/cfi": ("ISO 10962 CFI codes", "SIX Group / ISO", r"^[A-Z]{6}$", True, "six-silent", "check"),
"fin/cus": ("CIK to CUSIP mapping", "CUSIP Global Services / SEC", r"^[0-9A-Za-z]{6}$", True, "proprietary", "problem"),
"fin/i42": ("ISO 4217 currency codes", "SIX Group / ISO", r"^[A-Z]{3}$", True, "six-silent", "check"),
"fin/mic": ("ISO 10383 market identifier codes", "ISO 20022 RA / SWIFT", r"^[A-Z0-9]{4}$", True, "proprietary", "problem"),
"fin/tck": ("SEC company tickers", "US SEC", r"^[A-Z][A-Z\-]{0,6}$", True, "public-domain-usgov", "ok"),
"grf/act": ("ActivityStreams 2.0 terms", "W3C", r"^[A-Za-z][A-Za-z0-9]*$", True, "W3C-Document", "ok"),
"grf/foa": ("FOAF vocabulary terms", "FOAF project", r"^[A-Za-z][A-Za-z0-9_]*$", True, "CC-BY-1.0", "ok"),
"grf/gql": ("openCypher keywords", "openCypher / Neo4j", r"^[A-Z][A-Z_]*$", False, "Apache-2.0", "ok"),
"grf/lpg": ("property graph schema terms", "arXiv 2211.10962", r"^[A-Z]{2,9}$", True, "CC-BY-4.0", "ok"),
"grf/oid": ("OpenID Connect discovery fields", "OpenID Foundation", r"^[a-z][a-z0-9_]*$", True, "no-license-factual", "ok"),
"grf/org": ("W3C Organization ontology terms", "W3C", r"^[a-zA-Z][A-Za-z0-9]*$", True, "W3C-Document", "ok"),
"grf/rdf": ("RDF Schema terms", "W3C", r"^[a-zA-Z][A-Za-z0-9]*$", True, "W3C-Document", "ok"),
"grf/sch": ("schema.org types and properties", "schema.org / W3C CG", r"^[A-Za-z0-9][A-Za-z0-9]*$", True, "CC-BY-SA-3.0", "ok"),
"grf/shc": ("SHACL vocabulary terms", "W3C", r"^[A-Za-z][A-Za-z0-9\-]*$", True, "W3C-Document", "ok"),
"grf/sio": ("SIOC vocabulary terms", "SIOC Project / DERI", r"^[A-Za-z][A-Za-z0-9_]*$", True, "CC-BY-SA-3.0", "ok"),
"grf/vcd": ("vCard ontology terms", "W3C", r"^[a-zA-Z][A-Za-z0-9\-]*$", True, "W3C-Document", "ok"),
"lng/b47": ("BCP 47 language subtags", "IANA", r"^[A-Za-z0-9\-]+(\.\.[A-Za-z0-9\-]+)?$", False, "iana-registry", "ok"),
"lng/glt": ("Glottolog languoid codes", "MPI-EVA Leipzig", r"^[a-z0-9]{4}\d{4}$", True, "CC-BY-4.0", "ok"),
"lng/i15": ("ISO 15924 script codes", "Unicode Consortium (RA)", r"^[A-Z][a-z]{3}$", True, "unicode-terms", "ok"),
"lng/i31": ("ISO 3166-1 country codes", "ISO 3166/MA", r"^[A-Z]{2,3}$", True, "CC-BY-SA-4.0", "ok"),
"lng/i39": ("ISO 639-1 language codes", "ISO 639/RA", r"^[a-z]{2}$", True, "ODC-PDDL-1.0", "ok"),
"lng/i63": ("BCP 47 three-letter language subtags", "IANA", r"^[a-z]{3}$", False, "iana-registry", "ok"),
"lng/ioc": ("country codes composite", "community / datasets.io", r"^[A-Z]{2,3}$", True, "ODC-PDDL-1.0", "ok"),
"lng/mdy": ("month names", "Unicode CLDR", r"^[A-Z][a-z]{2}$", False, "unicode-terms", "ok"),
"nte/wnt": ("English WordNet 2024 synset IDs", "Global WordNet Association", r"^oewn-\d{8}-[nvasr]$", True, "CC-BY-4.0", "ok"),
"trp/iata": ("IATA airport codes", "IATA", r"^[A-Z]{3}$", True, "public-domain-ourairports", "ok"),
"trp/ica2": ("IATA and ICAO airline codes", "IATA / ICAO", r"^[A-Z0-9]{2,3}$", True, "ODbL-1.0", "ok"),
"trp/icao": ("ICAO airport codes", "ICAO", r"^[A-Z]{4}$", True, "public-domain-ourairports", "ok"),
"trp/olc": ("Open Location Code (plus codes)", "Google", r"^[023456789CFGHJMPQRVWX]{4,}\+[23456789CFGHJMPQRVWX]*$", True, "Apache-2.0", "ok"),
"trp/tld": ("top level domains", "IANA", r"^[A-Z0-9\-]+$", False, "iana-registry", "ok"),
"trp/unl": ("UN/LOCODE location codes", "UNECE", r"^[A-Z0-9]{3}$", True, "ODC-PDDL-1.0", "ok"),
"trp/w3w": ("what3words API surface", "what3words", r"^[a-zA-Z][a-zA-Z0-9_]*$", True, "proprietary", "problem"),
"wrt/abj": ("Hebrew script characters", "Unicode / community", r"^\S$", True, "MIT", "ok"),
"wrt/iau": ("IAU constellation abbreviations", "International Astronomical Union", r"^[A-Z][A-Za-z]{2}$", True, "BSD-3-Clause", "ok"),
"wrt/tz":  ("tz database zone names and abbreviations", "IANA / tzdb", r"^[A-Za-z0-9+\-_/]{1,32}$", True, "public-domain-tzdb", "ok"),
"wrt/uni": ("Unicode emoji sequences", "Unicode Consortium", r"^[0-9A-F]{4,6}( [0-9A-F]{4,6})*$", True, "unicode-terms", "ok"),
}

# pattern_status: provisional = placeholder solto, aperta quando o parser existir.
# derived = escrito olhando o arquivo real. confirmed = so validate.py promove,
# depois de bater contra 100% dos codigos emitidos.
DERIVED_PATTERN = set(SYSTEMS)   # every regex is measured against its own parquet

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
 "cls/icd":  ("the FY2027 order file straight from the CDC. the previous source was an instruction-tuning dataset with ICD codes embedded in question and answer text, which is training data about the codes, not the code list.\n"),
 "fin/cfi":  "SIX publishes free of charge and says nothing about redistribution",
 "fin/i42":  "SIX publishes free of charge and says nothing about redistribution",
}

NOTES["cmp/sts"] = ("the IANA registry assigns about 64 status codes and leaves the rest of the "
                    "100 to 599 space unassigned. both are here: an assigned code carries its "
                    "description and a null status, an unassigned one carries status unassigned "
                    "and an empty label. IANA writes the gaps as ranges, 105-199, and those are "
                    "expanded to one row per code.")
NOTES["wrt/abj"] = ("the source covers the Hebrew block, not only the alphabet: 22 letters plus "
                    "19 points, 30 cantillation accents, 6 punctuation marks, 3 marks, 1 sign "
                    "and 3 Yiddish ligatures. the group is in extra.")
NOTES["bio/pdb"] = ("entry IDs are four characters starting with a digit 1 to 9, uppercase. "
                    "the four character space is nearly exhausted, and the wwPDB has an extended "
                    "pdb_00001abc form waiting for it.")

NOTES["cmp/sts"] = ("the IANA registry assigns about 64 status codes and leaves the rest of the "
                    "100 to 599 space unassigned. both are here: an assigned code carries its "
                    "description and a null status, an unassigned one carries the label Unassigned, "
                    "status unassigned and the range IANA writes it in, such as 105-199, in extra.range.")

# Further files per system, read only for labels and descriptions when the main source lists bare codes.
# system_id: [(file name in raw/, url, retrieval date), ...]. Each file is kept as downloaded, archives included.
# PDB IDs of the holdings list that the wwPDB entries index does not carry (mmCIF-only and recent entries);
# their titles come from the RCSB GraphQL API, queried for exactly these IDs
PDB_IDS_NOT_IN_INDEX = """
8ZZ1 8ZZ2 8ZZ3 8ZZ4 8ZZ5 8ZZ6 8ZZ7 8ZZ8 8ZZ9 8ZZA 8ZZB 8ZZC 8ZZD 8ZZE 8ZZF 8ZZG 8ZZH 8ZZI 8ZZJ 8ZZK 8ZZL 8ZZM
8ZZN 8ZZO 8ZZP 8ZZQ 8ZZR 8ZZS 8ZZT 8ZZU 8ZZV 8ZZW 8ZZX 8ZZY 8ZZZ 9A00 9A01 9A02 9A03 9A04 9A05 9A06 9A07 9A08
9A0A 9A0B 9A0C 9A0D 9A0E 9A0F 9A0G 9A0H 9A0I 9A0J 9A0K 9A0L 9A0M 9A0N 9A0O 9A0P 9A0Q 9A0R 9A0T 9A0U 9A0V 9A0W
9A0X 9A0Y 9A0Z 9A10 9A11 9A12 9A13 9A14 9A15 9A16 9A17 9A18 9A19 9A1A 9A1B 9A1C 9A1D 9A1E 9A1F 9A1G 9A1H 9A1I
9A1J 9A1K 9A1L 9A1M 9A1N 9A1O 9A1P 9A1Q 9A1R 9A1S 9A1T 9A1U 9A1V 9A1Y 9A1Z 9A20 9A21 9A22 9A23 9A24 9A25 9A26
9A27 9A28 9A29 9A2A 9A2B 9A2C 9A2D 9A2E 9A2F 9A2G 9A2H 9A2I 9A2J 9A2K 9A2L 9A2M 9A2N 9A2O 9A2P 9A2Q 9A2R 9A2S
9A2T 9A2U 9A2V 9A2W 9A2X 9A2Y 9A2Z 9A30 9A31 9A32 9A33 9A34 9A35 9A36 9A37 9A38 9A39 9A3A 9A3B 9A3C 9A3D 9A3E
9A3F 9A3G 9A3I 9A3J 9A3K 9A3L 9A3M 9A3N 9A3O 9A3P 9A3Q 9A3R 9A3S 9A3T 9A3U 9A3V 9A3W 9A3X 9A3Y 9A3Z 9A40 9A41
9A42 9A43 9A44 9A45 9A46 9A47 9A48 9A49 9A4A 9A4B 9A4C 9A4D 9A4E 9A4F 9A4G 9A4H 9A4I 9A4J 9A4K 9A4L 9A4M 9A4N
9A4O 9A4P 9A4Q 9A4R 9A4S 9A4T 9A4U 9A4V 9A4W 9A4X 9A4Y 9A4Z 9A50 9A51 9A52 9A53 9A54 9A55 9A56 9A57 9A58 9A59
9A5A 9A5B 9A5C 9A5D 9A5E 9A5F 9A5G 9A5H 9A5I 9A5J 9A5K 9A5L 9A5M 9A5N 9A5O 9A5P 9A5Q 9A5R 9A5S 9A5T 9A5U 9A5V
9A5W 9A5X 9A5Y 9A5Z 9A60 9A61 9A62 9A63 9A64 9A65 9A66 9A67 9A68 9A69 9A6A 9A6B 9A6C 9A6D 9A6E 9A6F 9A6G 9A6H
9A6I 9A6J 9A6K 9A6L 9A6M 9A6N 9A6O 9A6P 9A6Q 9A6R 9A6S 9A6T 9A6U 9A6V 9A6W 9A6X 9A6Y 9A6Z 9A70 9A71 9A72 9A73
9A74 9A75 9A76 9A77 9A78 9A79 9A7A 9A7B 9A7C 9A7D 9A7E 9A7F 9A7G 9A7H 9A7I 9A7J 9A7K 9A7L 9A7M 9A7N 9A7O 9A7P
9A7Q 9A7R 9A7S 9A7T 9A7U 9A7V 9A7W 9A7X 9A7Y 9A7Z 9A80 9A81 9A82 9A83 9A84 9A85 9A86 9A87 9A88 9A89 9A8A 9A8B
9A8C 9A8D 9A8E 9A8F 9A8G 9A8I 9A8K 9A8L 9A8M 9A8N 9A8S 9A8T 9A8U 9A8V 9A8W 9A8X 9A8Y 9A8Z 9A90 9A91 9A92 9A93
9A94 9A95 9A96 9A97 9A98 9A99 9A9A 9A9B 9A9C 9A9D 9A9E 9A9F 9A9G 9A9J 9A9K 9A9L 9A9M 9A9N 9A9O 9A9P 9A9Q 9A9R
9A9S 9A9T 9A9U 9A9V 9A9W 9A9X 9A9Y 9A9Z 9AA0 9AA1 9AA2 9AA3 9AAA 9AAL 9AAM 9AAN 9AAO
""".split()
_PDB_QUERY = ("{entries(entry_ids:[%s]){rcsb_id struct{title} struct_keywords{pdbx_keywords} "
              "rcsb_accession_info{deposit_date} exptl{method} rcsb_entry_info{resolution_combined}}}"
              % ",".join(f'"{i}"' for i in PDB_IDS_NOT_IN_INDEX))

LABEL_SOURCES = {
 "bio/pdb": [("pdb-entry-titles.idx",
              "https://files.wwpdb.org/pub/pdb/derived_data/index/entries.idx", "2026-10-14"),
             ("pdb-removed-entries.json.gz",
              "https://files.wwpdb.org/pub/pdb/holdings/all_removed_entries.json.gz", "2026-10-14"),
             ("rcsb-titles-not-in-index.json",
              "https://data.rcsb.org/graphql?query=" + urllib.parse.quote(_PDB_QUERY, safe=""), "2026-10-14")],
 "trp/tld": [("iana-root-zone-db.html", "https://www.iana.org/domains/root/db", "2026-10-14")],
 "fin/cus": [("cik-lookup-data.txt", "https://www.sec.gov/Archives/edgar/cik-lookup-data.txt", "2026-10-14")],
 "cmp/ext": [("freedesktop.org.xml.in", "https://gitlab.freedesktop.org/xdg/shared-mime-info/-/raw/"
              "8fd96fce80a95c48cb1fb8140345a1d8c8859495/data/freedesktop.org.xml.in", "2026-10-14"),
             ("linguist-languages.yml", "https://raw.githubusercontent.com/github-linguist/linguist/"
              "73ee9a3b277f398c37ca4ab0dea0193849de6460/lib/linguist/languages.yml", "2026-10-14"),
             ("mime-db.json", "https://raw.githubusercontent.com/jshttp/mime-db/"
              "ba120a7f71bc8ab7d5299e88c0049063239029a7/db.json", "2026-10-14")],
 "cmp/dns": [("rfc6742.txt", "https://www.rfc-editor.org/rfc/rfc6742.txt", "2026-10-14"),
             ("rfc7208.txt", "https://www.rfc-editor.org/rfc/rfc7208.txt", "2026-10-14")],
 "cmp/git": [("git-686213114e573ca31e2715982ac9f2a3ce197d31.tar.gz",
             "https://codeload.github.com/git/git/tar.gz/686213114e573ca31e2715982ac9f2a3ce197d31", "2026-10-14")],
 "grf/act": [("activitystreams-owl.ttl", "https://www.w3.org/ns/activitystreams-owl", "2026-10-14"),
             ("as2vocab.html", "https://www.w3.org/TR/activitystreams-vocabulary/", "2026-10-14"),
             ("activitypub.html", "https://www.w3.org/TR/activitypub/", "2026-10-14")],
 "grf/oid": [("openid-connect-discovery-1_0.html",
             "https://openid.net/specs/openid-connect-discovery-1_0.html", "2026-10-14"),
             ("oauth-parameters.xml", "https://www.iana.org/assignments/oauth-parameters/oauth-parameters.xml",
              "2026-10-14")],
}
