# AX1 animation manifest schema review

**Scope:** JSON interface and standard-library validation only. The live CAD adapter, FreeCAD document, and AX1 pose execution remain owned by the lead.

## Contract

`animation/schema/pose_manifest_v1.schema.json` defines a compact version 1.0 numeric pose manifest. It records the CAD and parameter provenance hashes, motion-map hash, exporter revision, +X forward/+Y left/+Z up conventions, identity axis mapping, mm-to-m conversion, stable physical instance IDs, source mesh records, sorted transform order, and exactly three samples (`neutral_v1`, `smoke_1`, `smoke_2` at 0, 1, and 2 seconds).

Each sample carries the six commanded coordinates in project order, scalar prescribed knee angles for all four standard legs, optional complete hip/knee pairs for audit, provenance, ordered transforms in mm and m, WXYZ quaternions, and frame-tagged procedural state. Every length/route-dependent instance must have one procedural record in every sample; there is no fixed instance-count gate, so the rule covers all ten deforming instances in the current adapter while allowing later inventory changes. AX1 mesh records explicitly use `NOT_EXPORTED_AX01`; they carry geometry hashes and may carry `local_geometry_status`, but do not claim exported geometry assets.

`src/animation_manifest_validate.py` performs the cross-field and numeric checks that JSON Schema cannot express. It fails closed on unknown manifest and instance/mesh/frame fields, incomplete or duplicate source/mesh/instance mappings, mismatched transform ordering, missing procedural records for any length/route-dependent instance, degenerate smoke samples, malformed homogeneous matrices, non-SO(3) rotations, mm/m disagreement, invalid or discontinuous quaternions, hip/knee pair disagreement, and invalid frame identities/timing. Procedural records require recognized spring/cable generators, source-module hashes and shape hashes; spring seats/anchors/axis/lengths; or cable routes/primitives and the six named owner anchors. Anchor owner references and all local/world XYZ coordinates are checked. It uses only the Python standard library.

## Verification

- `python -m unittest tests/test_animation_manifest_validate.py` — PASS (16 tests).
- Parsed `animation/schema/pose_manifest_v1.schema.json` with the Python JSON parser — PASS.
- `python -m py_compile src/animation_manifest_validate.py tests/test_animation_manifest_validate.py` — PASS.

These checks validate the contract and malformed-payload behavior, including a complete cable fixture, empty/unknown procedural records, hip mismatch, and ten dynamic instances covered in all three frames. They do not establish that a live adapter payload or the current FreeCAD document passed AX1; that evidence must be recorded by the lead alongside the exported payload and source hashes.
