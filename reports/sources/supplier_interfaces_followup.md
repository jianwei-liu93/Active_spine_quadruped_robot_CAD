# ROBOTIS interface drawing follow-up — 2026-10-11

## Result

No dimensioned motor drawing or STEP file could be recovered into this workspace. The source-faithful body/output interface remains unresolved: output center offset from case datums, output-axis vector in a dimensioned case coordinate frame, exact screw-hole coordinates/diameters/depths, output spline/horn geometry, and dimensioned horn geometry are still unknown. No dimensions were inferred from schematic illustrations.

The official ROBOTIS e-Manual GitHub source does contain two useful, but **non-dimensioned**, X330 assembly illustrations. They apply to the shared XL330/XC330 X330 assembly article and establish only these qualitative observations:

| Observation | Direct source | Safe interpretation |
|---|---|---|
| Front-view horn/output is centered on the illustrated circular front boss. The output/horn axis is drawn normal to that front face (and to the parallel back face). | [`xl330_assembly_integrated.png`](https://raw.githubusercontent.com/ROBOTIS-GIT/emanual/master/assets/images/dxl/x/x330/xl330_assembly_integrated.png), referenced by ROBOTIS [`x330_drawing.md`](https://github.com/ROBOTIS-GIT/emanual/blob/master/_includes/en/dxl/drawing/x330_drawing.md) | Use the output axis normal to the face only as a qualitative orientation. The image gives no center offset from body edges, datum origin, or signed vector. It cannot determine the exact CAD placement or preserve body handedness by itself. |
| Front frame and back frame examples each show four case fastening points in a 2×2 arrangement, with M2 tapping screws called out generically. | Same assembly image | Four positions are visually shown per side. Hole spacing, exact hole diameter, thread depth, screw length, and whether all four positions are required in every supported installation remain unverified. |
| Separate idler assembly shows an “Idler Horn” and “Idler Cap”; the callout reads “M2.6×6 Tapping Screw.” | Same assembly image | This is an idler-side retention schematic, not a dimensioned output horn part drawing. Preserve the screw-callout discrepancy described below. |
| A horn screw illustration labels PHS M2×6 TAP for the intended installation and PHS M2×8 TAP in the crossed-out example. | [`x330_horn_screw.png`](https://raw.githubusercontent.com/ROBOTIS-GIT/emanual/master/assets/images/dxl/x/x330/x330_horn_screw.png), referenced by ROBOTIS [`x330_drawing.md`](https://github.com/ROBOTIS-GIT/emanual/blob/master/_includes/en/dxl/drawing/x330_drawing.md) | This confirms the manual's illustrated screw-length choice only. It does not dimension horn thickness, radial pattern, shaft serration, pilot, screw engagement, or output-center location. |

The ROBOTIS shop pages list six M2×6 TAP screws for horns and ten M2×8 TAP screws for frames in the XL330 and XC330 product packages [S1, S2]. The idler illustration’s M2.6×6 callout differs from that M2×6 package entry. It may refer to a separate idler-retention fastener, but no drawing or parts list located here resolves that; do not silently substitute one callout for the other.

## Retrieval attempts and source identity

1. Opened the official [XL330-M077](https://emanual.robotis.com/docs/en/dxl/x/xl330-m077/) and [XC330-M181](https://emanual.robotis.com/docs/en/dxl/x/xc330-m181/) e-Manual pages and followed their linked `XL330.pdf/.dwg/.stp` and `XC330.pdf/.dwg/.stp` items. ROBOTIS serves these through `https://www.robotis.com/service/download.php?no=1985`, `?no=1986`, and `?no=1987` redirects. The web tool returned only the “Your download will start shortly” interstitial. A direct local Python fetch failed at DNS resolution (`Temporary failure in name resolution`).
2. Opened the migrated official ROBOTIS Docs XL330 page in Chrome and activated its `XL330.stp` link. The browser remained on the manual page and no `XL330.stp` appeared in `/home/jianwei/Downloads`.
3. Searched ROBOTIS-GIT GitHub for model STEP and CAD assets. The official `ROBOTIS-GIT/emanual` repository contains manual markdown and the two image assets above, but the article’s `XL330.pdf/.dwg/.stp` and `XC330.pdf/.dwg/.stp` remain download-center links rather than files in that GitHub repository. The official `ROBOTIS-GIT/docs` repository was also searched for product assets; no model CAD file was surfaced.

Relevant official download page records observed during the search:

| Artifact | ROBOTIS link/record | Status in this workspace |
|---|---|---|
| XL330 PDF, DWG, STEP | [XL330-M077 manual](https://emanual.robotis.com/docs/en/dxl/x/xl330-m077/), Drawings. The PDF/DWG/STEP links resolve to ROBOTIS download records `no=1986`, `no=1985`, and `no=1987` in the checked pages. | Not retrieved; no title-block/revision or binary hash. |
| XC330 PDF, DWG, STEP | [XC330-M181 manual](https://emanual.robotis.com/docs/en/dxl/x/xc330-m181/), Drawings. Its three links resolve to the same three observed ROBOTIS download record numbers; filenames are listed by the manual. | Not retrieved; no title-block/revision or binary hash. |
| X330 idler/horn family drawings | [ROBOTIS Download Center](https://en.robotis.com/service/downloadpage.php?ca_id=70), DYNAMIXEL item “XL330 / XC330 / X330 IDLER”; associated front assembly illustration is in the official GitHub manual source. | Download-center downloads use generic page links; no dimensioned drawing file was obtained. |
| Assembly illustrations | [ROBOTIS-GIT/emanual X330 drawing include](https://github.com/ROBOTIS-GIT/emanual/blob/master/_includes/en/dxl/drawing/x330_drawing.md); raw images linked above. | Visually inspected in browser. Image pixel dimensions: horn-screw illustration 1986×990; assembly illustration 630×816. No file was saved to repository or hashed. |

Source checked: 2026-10-11. The e-Manual repository includes an MIT `LICENSE.txt` (copyright notice names Michael Rose); the live actuator manual page displays a ROBOTIS copyright notice. I did not verify an artifact-specific license for the model drawings. The image files were viewed remotely and are **not redistributed here**. Follow any license or notice attached to later-downloaded engineering drawings; retain the source and notice as provided by ROBOTIS.

Sources checked on 2026-10-11:

- [S1] ROBOTIS, [XL330-M077-T shop/specification page](https://en.robotis.com/shop_en/item.php?it_id=902-0162-000), package fastener list.
- [S2] ROBOTIS, [XC330-M181-T shop/specification page](https://en.robotis.com/shop_en/item.php?it_id=902-0172-000), package fastener list.
- [S3] ROBOTIS-GIT, [e-Manual GitHub repository](https://github.com/ROBOTIS-GIT/emanual) and [`LICENSE.txt`](https://raw.githubusercontent.com/ROBOTIS-GIT/emanual/master/LICENSE.txt).

## Next evidence needed for interface release

- Retrieve the actual `XL330.pdf` and `XC330.pdf` drawings or their variant-applicable STEP assets from the ROBOTIS download center, then hash and inspect their title blocks.
- Establish the case coordinate frame and dimensioned output-center location; record which views/dimensions define the output axis and datum origin.
- Recover the complete front/back four-hole pattern, pilot/thread/depth, and any supported mounting variants.
- Retrieve a dimensioned horn/idler drawing, and reconcile its spline/pilot, fastener, and screw length against the exact package/accessory variant.
- Do not promote the qualitative face-normal axis and visual 2×2 screw arrangement above to `MANUFACTURER_VERIFIED` numeric interface values.

2026-10-12 lead retry: unrestricted public HTTPS curl retrieval (including official download-center referrer) of the official ROBOTIS1987 and2121 endpoints returned an external error page titled404NotFound, not CAD. No downloaded HTML is accepted as vendorgeometry. Mechanical interfaces remain UNKNOWN.
