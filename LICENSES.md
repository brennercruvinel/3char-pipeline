# licenses

triage of all 64 sources, checked against each authority's own published terms rather than inferred from whichever mirror the file came through. `ok` means redistribution is granted or the content is plain fact from the authority, `check` means no grant exists either way, `problem` means the authority asserts rights that block republishing the code set.

as of 2026-09-10: 55 ok, 2 check, 7 problem. the 57 in the first two groups are what gets published, the 7 in the last are parsed by the pipeline and never uploaded.

### what never reaches the Hub

only parquet is published. the raw files under `data/<domain>/<id>/raw/` stay local, are fetched by the download script, and are never uploaded. that distinction carries real weight for the ITU recommendations and the IUPAC table, where the facts are free to state and the document is not free to mirror.

### problem, blocked by the authority's own terms

| system | authority | what blocks it |
| --- | --- | --- |
| `cls/atc` | WHO Collaborating Centre for Drug Statistics Methodology | WHO CC: "Copying and distribution for commercial purposes is not allowed. Changing or manipulating the material is not allowed." parsing to parquet is manipulation |
| `cls/bsc` | Book Industry Study Group | BISG: "No part of these lists or any attached documents may be distributed or reproduced in any manner whatsoever without the express permission of the Book Industry Study Group, Inc." |
| `cls/dew` | OCLC | OCLC, from the copyright page of the PDF itself: "All rights reserved. No part of this publication may be reproduced, stored in a retrieval system, or transmitted, in any form or by any means" |
| `fin/cus` | CUSIP Global Services / SEC | CUSIP identifiers are licensed by CUSIP Global Services, the github mapping is a derived scrape |
| `fin/mic` | ISO 20022 RA / SWIFT | ISO 20022 RA: "excluding the right to reproduce all or substantial part of this website for the purpose of making such reproductions available to third parties" |
| `lng/i63` | SIL International (RA) | SIL: "the product, system, or device does not provide a means to redistribute the code set", and the SIL site is named the only authorized distribution point |
| `trp/w3w` | what3words | the OpenAPI document describes a commercial API whose word list is the product being sold |

`lng/i63` and `fin/mic` started as `check` and moved here after someone read the terms. both looked like ordinary standards downloads.

### check

| system | authority | status |
| --- | --- | --- |
| `fin/cfi` | SIX Group / ISO | publishes "free of charge" and then says nothing at all about redistribution |
| `fin/i42` | SIX Group / ISO | same silence. ISO 4217 is the most widely mirrored code table on the internet, which is evidence about practice, not permission |

both ship with `license_status` set to `check` in `systems.parquet`, visible to anyone who loads the dataset.

### eight sources replaced

eight systems used to come from github gists and unlicensed repos. a gist is not the rights holder of the ITU morse table or the POSIX errno list, so the provenance was wrong regardless of what the license said. they were re-derived from the body that actually assigns the codes.

| system | was | now | authority |
| --- | --- | --- | --- |
| `bio/aa1` `bio/aa3` | github repo, no LICENSE | JCBN Recommendations 1983, Table 1 | IUPAC-IUB JCBN |
| `cmp/ern` | github gist | POSIX.1-2024 `<errno.h>` | IEEE / The Open Group |
| `cmp/reg` | github gist | `X86RegisterInfo.td` | LLVM Project, Apache-2.0 with LLVM exception |
| `com/mor` | github gist | Recommendation ITU-R M.1677-1 | ITU-R |
| `com/bau` | third party PDF scan | Recommendation ITU-T S.1 | ITU-T |
| `grf/sio` | community mirror | the canonical `rdfs.org/sioc/ns#` namespace | SIOC Project / DERI |
| `lng/mdy` | github gist | CLDR `ca-gregorian.json` | Unicode CLDR |

### ok

55 systems. IANA registries, W3C vocabularies, US government sources (NCBI, PubChem, SEC, CDC), CC licensed corpora (Glottolog, WordNet, HGNC, ENZYME, the PG-Schema paper), public domain dedications (OurAirports, tzdb, edsu/lcco), permissively licensed community repos, and the eight authorities above.

copyleft shows up in four. `cmp/git` and `cmp/frc` come out of GPL-2.0 source trees, `cmp/vim` carries the Vim license, `trp/ica2` is ODbL-1.0 with share-alike. pulling a factual code list out of a GPL source file is not the same as distributing that file, but the attribution obligation travels either way and `systems.parquet` records it.

### the ISO caveat

`lng/i31` (ISO 3166) and `lng/i39` (ISO 639-1) sit at `ok` on the strength of their mirrors, CC-BY-SA-4.0 and ODC-PDDL-1.0. ISO asserts copyright over its code lists as a matter of course, and a permissive license applied by a mirror does not launder upstream terms. they are `ok` because the packaging is licensed and the codes are two and three letter facts in worldwide daily use, not because ISO said yes.
