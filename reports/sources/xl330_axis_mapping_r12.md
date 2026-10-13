# XL330 output-axis check — R12

Checked 2026-10-13 for the XL330-M077-T supplier-axis question raised during the center-frame width review.

## Finding

ROBOTIS publishes the XL330 case envelope as **W × H × D = 20 × 34 × 26 mm**. Its official XL330-series product image shows the output boss on the broad case face. That face is the 20 × 34 mm face, so the output axis is normal to that face and parallel to the 26 mm depth. This is a strong manufacturer-source inference from the named envelope axes and product image; it is not a dimensioned-view confirmation because the linked exact-model drawing could not be retrieved.

For the current CAD mapping `(local X, Y, Z) = (20, 26, 34) mm`, **local Y is the only plausible output-axis/depth direction**. This mapping is consistent if the CAD's local Y is the motor shaft axis. The 26 mm dimension should not be treated as an in-plane thickness perpendicular to the shaft: the in-plane case dimensions are 20 mm and 34 mm.

With two motors opposed along world Y, preserving orientation and the existing output-axis datum positions means the 26 mm case depth remains along Y. Substituting 20 mm for that dimension to narrow the Y span would put the wrong case dimension on the shaft axis. A materially smaller overall Y body envelope is therefore not supported by this evidence without moving the output datums or changing motor orientation. The exact minimum envelope, case-to-output-face offset, connector keep-out, and assembly clearance remain unverified without the dimensioned drawing/STEP; 56.8 mm itself is not established here as a manufacturer requirement.

## Evidence and limits

| Evidence | Observation | Use and limit |
|---|---|---|
| ROBOTIS [XL330-M077-T e-Manual](https://emanual.robotis.com/docs/en/dxl/x/xl330-m077/), Specifications | Dimensions are explicitly listed as `W x H x D: 20.0 x 34.0 x 26.0 mm`. Drawings section links `XL330.pdf`, `XL330.dwg`, and `XL330.stp`. | Gives the named envelope axes and exact-model drawing links, but the table does not itself state the output-axis vector. |
| ROBOTIS [XL330 series product image](https://emanual.robotis.com/assets/images/dxl/x/x330/xl330-series_product.png) | The horn/output boss is shown on the broad rectangular case face; visible side faces establish that the boss face is not the depth face. | Qualitative orientation only; no dimension lines or case/output datum offset. It is a series image, not a model-specific engineering drawing. |
| Exact XL330 STEP link from the manual, [`https://www.robotis.com/service/download.php?no=1987`](https://www.robotis.com/service/download.php?no=1987) | Direct retrieval on 2026-10-13 returned a 1,272-byte ROBOTIS `404 Not Found` HTML page, not STEP data. The page's download behavior also redirected the browser to a blocked Dropbox download. The erroneous HTML response was removed and is not retained as geometry. | Exact-model STEP not inspected; no STEP hash is claimed. The manual's `XL330.pdf` link resolves to record `no=1986`; the web fetch timed out. No drawing hash/title-block revision could be verified locally. |

The official product image was saved as [`xl330-series_product.png`](../../vendor/verified_interfaces/xl330_r12/xl330-series_product.png). SHA-256: `3430ea5465dc097b9ab9587c965b41bfdff086cb43a524e5be99f8e9cd2468d4`. Image dimensions: 345 × 236 px. The source URL is recorded in the evidence table above.

## Decision boundary

Use the mapping **20 mm across the output face, 34 mm along the other in-face direction, and 26 mm parallel to the output shaft** for packaging interpretation, marked provisional pending drawing retrieval. Do not call 56.8 mm a supplier-mandated body width or reduce it by assigning 20 mm to the output direction. To resolve the remaining datum question, obtain the exact XL330 PDF/STEP from ROBOTIS and read the front, side, and back views together, including output-face-to-case-back dimensions. This note is supplier-axis research only and is not a fabrication or supplier-release claim.
