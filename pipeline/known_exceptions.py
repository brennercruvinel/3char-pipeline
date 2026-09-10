"""codes that fail their system's pattern because the source itself is malformed.

each entry is a deliberate, documented exception. the validator still reports them,
it just does not fail the build on them. anything not listed here is a real failure.
"""
KNOWN = {
 "cls/bsc": {"FIC05700": "BISAC codes are three letters plus six digits. this row carries "
                         "five digits and is malformed in the BISG source itself."},
}
