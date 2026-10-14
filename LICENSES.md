# Licenses

This document records the license triage of all 64 sources. Each source was checked against the published terms of the authority that assigns the codes, not inferred from the mirror the file came through. The status values are:

- `ok`: redistribution is granted, or the content is plain fact published by the authority.
- `check`: no grant or prohibition has been found; redistribution is not confirmed.
- `problem`: the authority asserts rights that prevent republishing the code set.

As of 2026-09-10, the triage stands at 55 `ok`, 2 `check` and 7 `problem`, out of 64 sources. 58 systems are published: the 55 `ok`, the 2 `check`, and `lng/i63`. `lng/i63` was in the `problem` group as the SIL ISO 639-3 table; it is now built from `lng/b47`, the IANA registry, and published under IANA terms. It is not ISO 639-3, and the dataset card says so. The remaining 6 `problem` systems are parsed by the pipeline and never written to `hub/`.

## What is never published

Only Parquet files are published. The raw files under `data/<domain>/<id>/raw/` stay local: they are fetched by the download script and never uploaded. The distinction matters most for the ITU recommendations and the IUPAC table, where the facts may be stated freely but the documents may not be mirrored.

## Problem: blocked by the authority's own terms

| System | Authority | What blocks it |
| --- | --- | --- |
| `cls/atc` | WHO Collaborating Centre for Drug Statistics Methodology | WHO CC: "Copying and distribution for commercial purposes is not allowed. Changing or manipulating the material is not allowed." Converting the index to Parquet counts as manipulation |
| `cls/bsc` | Book Industry Study Group | BISG: "No part of these lists or any attached documents may be distributed or reproduced in any manner whatsoever without the express permission of the Book Industry Study Group, Inc." |
| `cls/dew` | OCLC | OCLC, on the copyright page of the PDF itself: "All rights reserved. No part of this publication may be reproduced, stored in a retrieval system, or transmitted, in any form or by any means" |
| `fin/cus` | CUSIP Global Services / SEC | CUSIP identifiers are licensed by CUSIP Global Services; the GitHub mapping is a derived scrape |
| `fin/mic` | ISO 20022 RA / SWIFT | ISO 20022 RA: "excluding the right to reproduce all or substantial part of this website for the purpose of making such reproductions available to third parties" |
| `lng/i63` | SIL International (RA) | SIL: "the product, system, or device does not provide a means to redistribute the code set"; the SIL site is named as the only authorized distribution point |
| `trp/w3w` | what3words | The OpenAPI document describes a commercial API whose word list is the product being sold |

`lng/i63` and `fin/mic` were first classified as `check` and moved here once their terms were read; both had looked like ordinary downloads of standards.

## Check

| System | Authority | Status |
| --- | --- | --- |
| `fin/cfi` | SIX Group / ISO | Published "free of charge", with no statement on redistribution |
| `fin/i42` | SIX Group / ISO | Published with no statement on redistribution. ISO 4217 is among the most widely mirrored code tables, but that is evidence of practice, not permission |

Both systems carry `license_status` `check` in `systems.parquet`, visible to anyone who loads the dataset. Anyone who redistributes them commercially should first obtain SIX Group's terms.

## Eight sources replaced

Eight systems were first taken from secondary copies: GitHub gists, unlicensed repositories, a third-party scan and a community mirror. A gist is not the rights holder of the ITU Morse table or the POSIX errno list, so the provenance was wrong whatever license the copy carried. Each system was re-derived from the body that assigns the codes.

| System | Previous source | Current source | Authority |
| --- | --- | --- | --- |
| `bio/aa1`, `bio/aa3` | GitHub repository without a license | JCBN Recommendations 1983, Table 1 | IUPAC-IUB JCBN |
| `cmp/ern` | GitHub gist | POSIX.1-2024 `<errno.h>` | IEEE / The Open Group |
| `cmp/reg` | GitHub gist | `X86RegisterInfo.td` | LLVM Project, Apache-2.0 with LLVM exception |
| `com/mor` | GitHub gist | Recommendation ITU-R M.1677-1 | ITU-R |
| `com/bau` | Third-party PDF scan | Recommendation ITU-T S.1 | ITU-T |
| `grf/sio` | Community mirror | The canonical `rdfs.org/sioc/ns#` namespace | SIOC Project / DERI |
| `lng/mdy` | GitHub gist | CLDR `ca-gregorian.json` | Unicode CLDR |

## OK

55 sources: IANA registries, W3C vocabularies, US government sources (NCBI, PubChem, SEC, CDC), CC-licensed corpora (Glottolog, WordNet, HGNC, ENZYME, the PG-Schema paper), public domain dedications (OurAirports, tzdb, edsu/lcco), permissively licensed community repositories, and the authorities of the eight replaced sources above.

Copyleft and share-alike terms apply to seven published systems: `cmp/frc` (GPL-2.0-or-later) and `cmp/git` (GPL-2.0-only) are code lists extracted from GPL source trees; `cmp/vim` is under the Vim license; `grf/sch` and `grf/sio` are under CC-BY-SA-3.0; `lng/i31` is under CC-BY-SA-4.0 through its mirror; and `trp/ica2` is under ODbL-1.0. Extracting a factual code list from a GPL source file is not the same as distributing that file, but the attribution requirement applies either way, and `systems.parquet` records it. A downstream collection that includes these tables inherits the attribution requirements and, for the share-alike licenses, the share-alike terms for the tables themselves.

## The ISO caveat

`lng/i31` (ISO 3166) and `lng/i39` (ISO 639-1) are `ok` on the basis of their mirrors' licenses, CC-BY-SA-4.0 and ODC-PDDL-1.0 respectively. ISO routinely asserts copyright over its code lists, and a permissive license applied by a mirror does not override upstream terms. The two systems are `ok` because the packaging is licensed and the codes are two- and three-letter facts in worldwide daily use, not because ISO has granted permission.
