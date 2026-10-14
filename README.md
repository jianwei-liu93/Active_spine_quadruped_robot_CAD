# FLEXOR-inspired active-spine quadruped

Editable **FreeCAD robot CAD**, coupled spine and compliant leg mechanisms, and **Blender animations** built from the CAD geometry and kinematics.

This independent research reconstruction is inspired by **FLEXOR-F** from Wang et al., [*Unlocking fast robotic locomotor propulsion through dynamic spine-leg synergy*](https://doi.org/10.1126/sciadv.aed5603), *Science Advances* **12**(39), eaed5603 (2026). The paper, supplementary kinematic diagrams, and Movies S1/S2 guide the design. This repository contains our reconstruction and engineering assumptions; it is not the authors' original CAD or a validated reproduction of their experimental performance.

**Latest checkpoint: r14 · 14 October 2026 · Research CAD candidate**

## Spine–leg coordination

[![R14 quadruped: coupled spine, moving forelegs and hind legs, and illustrative body motion](docs/media/spine_leg_coordination_r14.gif)](animation/output/spine_leg_coordination_s2_r14.mp4)

The looping GIF shows one complete cycle of the latest r14 design. **Both the spine and legs move.** The full [25-second, 1080p/60-fps video](animation/output/spine_leg_coordination_s2_r14.mp4) includes whole-robot and mechanism close-ups in a Movie S2-inspired studio presentation.

Motion is **illustrative kinematics**: approximately 69° of full hip excursion, separately prescribed 20° knee excursion, independent winding-wheel motion, and prescribed body pitch/translation. It is not a dynamics simulation or a prediction of ground contact, speed, or running performance. Springs regenerate from their anchors; cable graphics show routing, with loaded slack shape unresolved. See [motion assumptions and reproduction](animation/README.md) and [video verification](reports/animation/spine_leg_coordination_s2_r14_qa.json).

## Latest CAD design

![R14 assembled FreeCAD robot with compact central frame and distinct foreleg and hind-leg assemblies](docs/media/robot_assembled_r14.png)

| Coupled spine and torso attachments | Organic A–B rocker |
| :---: | :---: |
| ![R14 coupled spine, oval slider guides and torso mounting plates](docs/media/spine_mechanism_r14.png) | ![R14 rocker with a single A eye and a fork only at B](docs/media/rocker_r14.png) |

The current assembly has **455 physical component instances** and **108 source definitions**. The r14 revision narrows the central frame to a 78.8 mm transverse span, uses a connected lumbar frame, smooth rockers forked only at B, recessed B–C links, and rounded front/rear mounting profiles. Foreleg and hind-leg assemblies retain their distinct layouts.

| Mechanical feature | Implementation |
| --- | --- |
| Spine | Two coupled sagittal outputs driven through one closed linkage/slider mechanism |
| Spine actuation | 2 × DYNAMIXEL **XL330-M077-T**, synchronized redundant drive |
| Leg actuation | 5 × DYNAMIXEL **XC330-M181-T**: four proximal joints and one shared hind-knee winding wheel |
| Coordinates | **7 physical motors, 6 commanded coordinates**, with passive/prescribed knee states represented separately |
| Legs | Four three-segment compliant legs, tension/compression springs, and bilateral hind-leg cable routing |
| CAD-to-animation interface | Stable instance IDs, separate source geometry, explicit local-to-world transforms, and procedural spring/cable geometry |

The animation consumes the verified CAD mechanism and its closure solution. It does not replace the mechanism with independently posed decorative links.

## Open the model

```bash
git clone https://github.com/jianwei-liu93/Active_spine_quadruped_robot_CAD.git
cd Active_spine_quadruped_robot_CAD
```

Open [**cad/flexor_r14_robot.FCStd**](cad/flexor_r14_robot.FCStd) in FreeCAD for the native editable assembly. Use [**exports/step/r14/flexor_r14_robot.step**](exports/step/r14/flexor_r14_robot.step) for CAD exchange. Start with these r14 files; older revisions and unsuccessful trials are retained for traceability.

The animation files use Blender 5.2.2 LTS. Large `.blend` scenes and render caches are kept local and ignored by Git; tracked meshes, motion samples, configuration and scripts support regeneration. See [the animation guide](animation/README.md) for the installed MCP workflow, scene building, rendering and verification. Viewing the GIF or MP4 does not require either application.

CAD uses millimetres and a right-handed robot frame: **+X forward, +Y left, +Z up**. Animation meshes and translations use metres; conversion and instance transforms are applied once at the export boundary.

## Verification and remaining work

The following checks were executed for r14:

| Check | Recorded result |
| --- | --- |
| Native editability and recompute | Passed saved-file reopen, forced recompute and parameter edit/restore probes |
| STEP exchange | 455 valid closed solids matched one-to-one |
| AX0/AX1 animation interface | All 455 instances mapped; neutral plus two non-neutral poses; rotations and source-to-world transforms verified |
| Spine-cycle clearance screen | 91 sampled phases at 4° intervals; affected pairs checked with legs and wheel held neutral |
| Coordination animation | Saved-scene, transform, spring/cable, leg articulation, framing and full video decode checks passed; nine coordinated phases screened for affected-pair clearance |

Evidence: [r14 CAD checkpoint](reports/verification/r14_checkpoint_summary.json), [design changes and limits](docs/24_clearance_corrected_reference_r14.md), [AX0/AX1](reports/animation/ax01_r14.json), and [coordination video QA](reports/animation/spine_leg_coordination_s2_r14_qa.json).

**This is a research design candidate, not a fabrication release.** Finite pose checks do not establish continuous or loaded clearance. Exact supplier mounting/output datums, bearing fits and retention/thrust, strength/fatigue, central support stiffness, insertion/tool access, and physical spring/cable characterization remain unresolved. A complete rebuild through the historical source chain is also not yet qualified. Manufacturing drawings and assembly documentation are deferred; no hardware locomotion performance is claimed.

## Repository guide

| Path | Contents |
| --- | --- |
| [`cad/`](cad/) | Native FreeCAD checkpoints; r14 is current |
| [`src/`](src/) | Part generation, mechanism solvers, pose/export adapters and verification helpers |
| [`parameters/`](parameters/) | Versioned dimensions, component interfaces and explicit assumptions |
| [`exports/step/r14/`](exports/step/r14/) | Latest STEP exchange model |
| [`animation/`](animation/) | Blender builders, source meshes, motion data, videos and reproduction guide |
| [`docs/`](docs/) | Specification, source interpretation, kinematics, workflow and acceptance criteria |
| [`reports/`](reports/) | Revision-specific checks, failures, screenshots and provenance |
| [`references/`](references/) | Source citation and attributed reference stills; original PDFs/videos are not bundled |
| [`docs/media/`](docs/media/) | Lightweight README previews and their source/hash manifest |

For development, read [AGENTS.md](AGENTS.md), [the specification](docs/00_project_specification.md), [reference evidence](docs/01_reference_evidence.md), [spine kinematics](docs/02_spine_kinematics.md), [leg/cable/spring kinematics](docs/03_leg_cable_spring_kinematics.md), and [the development plan](docs/07_development_plan.md). Follow the [FreeCAD MCP workflow](docs/05_freecad_mcp_workflow.md), [agent ownership rules](docs/08_agent_orchestration.md), and [animation interface contract](docs/20_animation_and_visualisation_pipeline.md). The lead exclusively owns the live CAD session; reviewers and workers use assigned files and static evidence.

README media can be regenerated from existing verified screenshots and the r14 MP4, without opening FreeCAD or Blender:

```bash
python3 animation/blender/build_readme_media.py
```

This uses Pillow and local FFmpeg/FFprobe. Source and output hashes, GIF timing and decode checks are recorded in [the media manifest](docs/media/manifest_r14.json).

## Inspiration and citation

Please credit the original research when discussing the FLEXOR mechanism:

> Ruochao Wang, Weitao Zhang, Xiaolong Quan, Rongjie Du, Zhenshan Bing, Gang Wang, Jian Sun, Zhiqiang Yu, and Qing Shi. **Unlocking fast robotic locomotor propulsion through dynamic spine-leg synergy.** *Science Advances* **12**(39), eaed5603, 25 September 2026. DOI: [10.1126/sciadv.aed5603](https://doi.org/10.1126/sciadv.aed5603).

[Publisher article and supplementary materials](https://www.science.org/doi/10.1126/sciadv.aed5603) · [PubMed record](https://pubmed.ncbi.nlm.nih.gov/42789728/) · [BibTeX](references/flexor_paper.bib) · [Local source setup and provenance](references/README.md)

The README previews are generated from this project's r14 CAD and Blender outputs. Third-party paper/movie reference stills and the ROBOTIS reference image have separate attribution and notices in [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md). No project-wide open-source license has been selected yet; public visibility does not assign a new license to this work or to third-party material.
