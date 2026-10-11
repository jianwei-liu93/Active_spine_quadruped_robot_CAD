# Vendor source artifacts

Baseline date: 2026-10-11. This folder currently contains no supplier CAD or datasheet binaries. The source links below are the vendor's live download records; the supplier-interface report records what can and cannot be supported without inspecting the files.

| Part/source | Vendor artifact identity | Source | Retrieval/hash status |
|---|---|---|---|
| XL330-M077-T | `XL330.pdf`, `XL330.dwg`, `XL330.stp` | [ROBOTIS XL330-M077-T manual, Drawings](https://emanual.robotis.com/docs/en/dxl/x/xl330-m077/) | Listed by the manual; PDF redirect observed at `https://www.robotis.com/service/download.php?no=1986`. The redirect did not yield the attachment to this runtime; no bytes or SHA-256 captured. |
| XC330-M181-T | `XC330.pdf`, `XC330.dwg`, `XC330.stp` | [ROBOTIS XC330-M181-T manual, Drawings](https://emanual.robotis.com/docs/en/dxl/x/xc330-m181/) | Listed by the manual; download redirect observed, but attachment retrieval was unavailable. No bytes or SHA-256 captured. |
| OpenRB-150 | 2D drawing PDF/DWG, 3D STL/STEP, BOM, schematic | [ROBOTIS OpenRB-150 documentation, Downloads](https://docs.robotis.com/docs/parts/controller/openrb-150/) | Official files listed; PDF download redirect observed at `https://www.robotis.com/service/download.php?no=2120`. Attachment unavailable; no bytes or SHA-256 captured. |
| HNX330-N101 horn (candidate) | STEP/PDF/DWG listed | [ROBOTIS Download Center](https://en.robotis.com/service/downloadpage.php?ca_id=70), Horn section | Listing indicates XL330/XC330 compatibility. Exact attachment not retrieved; no bytes or SHA-256 captured. |
| MR42 2×4 bearing (provisional candidate) | Catalog product page only; no controlled drawing selected | [Chenghui Bearing MR42](https://www.chenghuibearing.com/product-model/MR42/) | Listing states 2×4×1.2 mm. Not accepted as an orderable exact part; no drawing/hash. The 2×4×2 mm variant is a distinct, conflicting nonstandard listing and is not selected. |

Retrieval attempt: opening the ROBOTIS download redirect returned only a page saying the download should start. A direct Python URL fetch was also attempted, but this environment could not resolve `www.robotis.com`; therefore the drawing files could not be inspected or hashed. This limitation is recorded so the manual's drawing link is not mistaken for verified interface geometry. No substitute dimensions were inferred from product photographs, bounding boxes, or third-party CAD.

When the source files become accessible, preserve the downloaded file unchanged, record its retrieval date, exact filename, displayed revision/title block if present, and SHA-256. Inspect variant applicability and drawing datums before populating motor mount/output or board mounting parameters. Do not treat STEP as dimensionally controlling when it conflicts with a dimensioned PDF.
