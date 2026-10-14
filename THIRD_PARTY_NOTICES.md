# Third-party attribution and notices

This repository is an independent reconstruction inspired by the following research. Its README previews are rendered from the project's own CAD/animation outputs. The research authors and ROBOTIS have not endorsed this reconstruction.

## FLEXOR paper and supplementary Movie S1

Ruochao Wang, Weitao Zhang, Xiaolong Quan, Rongjie Du, Zhenshan Bing, Gang Wang, Jian Sun, Zhiqiang Yu, and Qing Shi, **Unlocking fast robotic locomotor propulsion through dynamic spine-leg synergy**, *Science Advances* 12(39), eaed5603 (25 September 2026).

- Source: [DOI 10.1126/sciadv.aed5603](https://doi.org/10.1126/sciadv.aed5603), including the associated supplementary materials and Movie S1.
- Copyright © 2026 The Authors; exclusive licensee American Association for the Advancement of Science.
- The reviewed article's first-page and end-page notices identify **Creative Commons Attribution-NonCommercial 4.0** ([CC BY-NC 4.0](https://creativecommons.org/licenses/by-nc/4.0/)). Retain source-specific notices and any separately credited third-party rights. This attribution does not relicense the repository's own code or CAD.
- Reference images under `references/visual/movie_s1/`, `movie_s1_attachment/` and `r11_movie_s1/` are extracted Movie S1 frames for noncommercial mechanism comparison. Changes consist of frame extraction and, for contact sheets, resizing and tiling. Their `provenance.json` files record source identity, extraction times and methods.
- `references/visual/r13_user_closeup/one_end_rocker.png` is a user-supplied crop of the same Movie S1 mechanism close-up. The modification is cropping; it is a source-reference image, not an original project render.
- The original article PDFs and full supplementary movies are not distributed in this repository. Obtain them from the publication.

## ROBOTIS e-Manual reference image

`vendor/verified_interfaces/xl330_r12/xl330-series_product.png` is an unmodified official XL330-series product reference image from [ROBOTIS e-Manual](https://emanual.robotis.com/assets/images/dxl/x/x330/xl330-series_product.png), used to establish qualitative case/output-axis orientation. Its SHA-256 and limitations are recorded in [the source review](reports/sources/xl330_axis_mapping_r12.md).

The corresponding [ROBOTIS-GIT e-Manual repository](https://github.com/ROBOTIS-GIT/emanual) supplies an [MIT license notice](https://github.com/ROBOTIS-GIT/emanual/blob/master/LICENSE.txt), copyright © 2017 Michael Rose. A verbatim copy is retained in [vendor/verified_interfaces/ROBOTIS-emanual-LICENSE.txt](vendor/verified_interfaces/ROBOTIS-emanual-LICENSE.txt). The live e-Manual also identifies ROBOTIS copyright; retain any artifact-specific terms. This repository does not claim a separate engineering-drawing license or distribute supplier CAD/PDF/DWG downloads.

## Project license status

No project-wide license has been selected. The notices above apply to their identified third-party sources and do not grant blanket rights to all repository contents. Historical reports retain local workstation paths for provenance; these are not portable setup instructions.
