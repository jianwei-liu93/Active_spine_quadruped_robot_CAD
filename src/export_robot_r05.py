"""Export and verify the r05 robot package from an already-open FreeCAD document.

This module performs no document construction, mutation, or save. Call ``run``
from the lead-owned FreeCAD session after the intended r05 build and checks.
Exports and checks are evidence about the serialized CAD package only; they do
not certify physical interfaces or release the design for fabrication.
"""
from __future__ import annotations

import hashlib
import json
import math
import re
import traceback
import uuid
from pathlib import Path


VOLUME_REL_TOL = 1e-6
BBOX_ABS_TOL_MM = 1e-5
MESH_LINEAR_DEFLECTION_MM = 0.1
MESH_ANGULAR_DEFLECTION_RAD = 0.25


def _shape(obj):
    shape = getattr(obj, "Shape", None)
    if shape is None:
        raise ValueError(f"{getattr(obj, 'Name', obj)!s} has no Shape")
    try:
        if shape.isNull():
            raise ValueError(f"{getattr(obj, 'Name', obj)!s} has a null Shape")
    except AttributeError:
        pass
    if not shape.isValid():
        raise ValueError(f"{getattr(obj, 'Name', obj)!s} has an invalid Shape")
    return shape


def _bbox(shape):
    # Reparameterized STEP splines can have different pole hull bounds.
    # Compare actual extrema without triangulation or shape-tolerance padding.
    box = shape.optimalBoundingBox(False,False)
    values = {
        "XMin": float(box.XMin), "XMax": float(box.XMax),
        "YMin": float(box.YMin), "YMax": float(box.YMax),
        "ZMin": float(box.ZMin), "ZMax": float(box.ZMax),
        "XLength": float(box.XLength), "YLength": float(box.YLength),
        "ZLength": float(box.ZLength),
    }
    if not all(math.isfinite(value) for value in values.values()):
        raise ValueError("Shape has non-finite bounding-box values")
    return values


def _solid_count(shape):
    return len(shape.Solids)


def _volume(shape):
    value = float(shape.Volume)
    if not math.isfinite(value) or value < 0:
        raise ValueError("Shape has invalid volume")
    return value


def _relative_error(actual, expected):
    if expected == 0:
        return 0.0 if actual == 0 else math.inf
    return abs(actual - expected) / abs(expected)


def _check_shape(actual, expected, label, expected_solids=None):
    """Compare imported STEP geometry to the source with declared tolerances."""
    if actual.isNull() or not actual.isValid():
        raise ValueError(f"{label}: imported STEP shape is null or invalid")
    actual_solids = _solid_count(actual)
    if expected_solids is not None and actual_solids != expected_solids:
        raise ValueError(
            f"{label}: STEP solid count {actual_solids} != expected {expected_solids}"
        )
    actual_volume = _volume(actual)
    expected_volume = _volume(expected)
    volume_error = _relative_error(actual_volume, expected_volume)
    if volume_error > VOLUME_REL_TOL:
        raise ValueError(
            f"{label}: volume relative error {volume_error:.12g} exceeds {VOLUME_REL_TOL}"
        )
    actual_box = _bbox(actual)
    expected_box = _bbox(expected)
    bbox_errors = {
        key: abs(actual_box[key] - expected_box[key])
        for key in ("XMin", "XMax", "YMin", "YMax", "ZMin", "ZMax")
    }
    largest_bbox_error = max(bbox_errors.values(), default=0.0)
    if largest_bbox_error > BBOX_ABS_TOL_MM:
        raise ValueError(
            f"{label}: bounding-box absolute error {largest_bbox_error:.12g} mm "
            f"exceeds {BBOX_ABS_TOL_MM} mm"
        )
    return {
        "solid_count": actual_solids,
        "expected_solid_count": expected_solids,
        "volume_mm3": actual_volume,
        "expected_volume_mm3": expected_volume,
        "volume_relative_error": volume_error,
        "bounding_box_mm": actual_box,
        "expected_bounding_box_mm": expected_box,
        "bounding_box_absolute_errors_mm": bbox_errors,
        "maximum_bounding_box_absolute_error_mm": largest_bbox_error,
    }


def _safe_stem(value):
    stem = re.sub(r"[^A-Za-z0-9._-]+", "_", str(value).strip())
    stem = stem.strip(" ._")
    return stem or "UNSPECIFIED_PART_NUMBER"


def _file_record(path, root):
    path = Path(path)
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return {
        "path": path.resolve().relative_to(Path(root).resolve()).as_posix(),
        "bytes": path.stat().st_size,
        "sha256": digest.hexdigest(),
    }


def _write_diagnostics(root, stage, exc, artifacts):
    """Best-effort failure log; callers still receive the original exception."""
    target = Path(root) / "reports" / "verification" / "r05_export_diagnostics.json"
    try:
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps({
            "revision": "r05",
            "status": "FAIL",
            "stage": stage,
            "error_type": type(exc).__name__,
            "error": str(exc),
            "traceback": traceback.format_exc(),
            "artifacts_written_before_failure": [str(p) for p in artifacts],
            "note": "A failed export/round-trip run is not a package pass or fabrication release.",
        }, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    except Exception:
        # Preserve the actionable export/verification exception if diagnostics
        # cannot be written (for example, a read-only destination).
        pass


def _validate_part_step(source, path, Part, root):
    source_shape = _shape(source)
    expected_solids = _solid_count(source_shape)
    if expected_solids != 1:
        raise ValueError(
            f"Part source {source.Name} has {expected_solids} solids; per-part export expects one"
        )
    Part.export([source], str(path))
    if not path.is_file() or path.stat().st_size == 0:
        raise IOError(f"Per-part STEP was not written: {path}")
    imported = Part.read(str(path))
    checks = _check_shape(imported, source_shape, f"part STEP {source.Name}", expected_solids)
    return checks, _file_record(path, root)


def _validate_part_stl(source, path, MeshPart, root):
    source_shape = _shape(source)
    mesh = MeshPart.meshFromShape(
        Shape=source_shape,
        LinearDeflection=MESH_LINEAR_DEFLECTION_MM,
        AngularDeflection=MESH_ANGULAR_DEFLECTION_RAD,
        Relative=False,
    )
    mesh.write(str(path))
    if not path.is_file() or path.stat().st_size == 0:
        raise IOError(f"PA12 STL was not written: {path}")
    return _file_record(path, root)


def _clean_roundtrip(shape, App, original_doc):
    """Place imported assembly shape in a disposable clean Part::Feature doc."""
    name = "R05_STEP_Roundtrip_" + uuid.uuid4().hex[:12]
    temp_doc = App.newDocument(name)
    try:
        feature = temp_doc.addObject("Part::Feature", "ImportedRobotSTEP")
        feature.Label = "Imported r05 robot STEP for clean-document round-trip"
        feature.Shape = shape.copy()
        temp_doc.recompute()
        imported_shape = _shape(feature)
        if _solid_count(imported_shape) != _solid_count(shape):
            raise ValueError("Clean-document round-trip changed the STEP solid count")
        _check_shape(imported_shape, shape, "clean-document round-trip", _solid_count(shape))
        return {
            "temporary_document": name,
            "feature_type": feature.TypeId,
            "solid_count": _solid_count(imported_shape),
            "closed_without_save": True,
        }
    finally:
        App.closeDocument(temp_doc.Name)
        if original_doc is not None:
            try:
                if App.getDocument(original_doc.Name) is not None:
                    App.setActiveDocument(original_doc.Name)
            except Exception:
                pass


def run(doc, root):
    """Export and validate the open r05 assembly without changing or saving it.

    Raises on the first export/check failure and writes a best-effort diagnostic
    record. Success writes assembly/per-part STEP, PA12-only STL, BOM/mass data,
    and a SHA-256 package manifest beneath ``root``.
    """
    import FreeCAD as App
    import Import
    import MeshPart
    import Part

    from package_bom_r02 import build_bom

    root = Path(root).resolve()
    artifacts = []
    stage = "invalidate_previous_success_manifest"
    try:
        # Avoid leaving an older success manifest that could be mistaken for
        # the result of a run that fails partway through.
        previous_manifest = root / "reports" / "package_manifest_r05.json"
        if previous_manifest.exists():
            previous_manifest.unlink()
        previous_diagnostics = root / "reports" / "verification" / "r05_export_diagnostics.json"
        if previous_diagnostics.exists():
            previous_diagnostics.unlink()

        stage = "enumerate_instances"
        links = [obj for obj in doc.Objects if getattr(obj, "TypeId", None) == "App::Link"]
        if not links:
            raise ValueError("r05 document has no physical App::Link instances")
        link_sources = {}
        source_objects = {}
        instance_shapes = {}
        for link in links:
            source = getattr(link, "LinkedObject", None)
            if source is None:
                raise ValueError(f"App::Link {link.Name} has no LinkedObject")
            source_name = str(source.Name)
            link_sources.setdefault(source_name, []).append(link)
            source_objects[source_name] = source
            link_shape = _shape(link)
            source_shape = _shape(source)
            if _solid_count(link_shape) != 1:
                raise ValueError(f"Physical instance {link.Name} is not exactly one solid")
            if _solid_count(source_shape) != 1:
                raise ValueError(f"Native definition {source_name} is not exactly one solid")
            instance_shapes[link.Name] = link_shape

        stage = "prepare_output_directories"
        assembly_dir = root / "exports" / "step" / "r05"
        parts_dir = assembly_dir / "parts"
        stl_dir = root / "exports" / "print" / "r05"
        assembly_dir.mkdir(parents=True, exist_ok=True)
        parts_dir.mkdir(parents=True, exist_ok=True)
        stl_dir.mkdir(parents=True, exist_ok=True)
        assembly_path = assembly_dir / "flexor_r05_robot.step"

        stage = "export_assembly_step"
        # Import.export preserves App::Link instances in the installed exporter;
        # Part.export on these links was observed to drop assembly instances.
        Import.export(links, str(assembly_path))
        if not assembly_path.is_file() or assembly_path.stat().st_size == 0:
            raise IOError(f"Assembly STEP was not written: {assembly_path}")
        artifacts.append(assembly_path)

        stage = "validate_assembly_step"
        assembly_shape = Part.read(str(assembly_path))
        expected_volume = sum(_volume(shape) for shape in instance_shapes.values())
        # Sum placements' actual world-coordinate extents without fusing parts.
        boxes = [_bbox(shape) for shape in instance_shapes.values()]
        expected_box = {
            "XMin": min(box["XMin"] for box in boxes),
            "XMax": max(box["XMax"] for box in boxes),
            "YMin": min(box["YMin"] for box in boxes),
            "YMax": max(box["YMax"] for box in boxes),
            "ZMin": min(box["ZMin"] for box in boxes),
            "ZMax": max(box["ZMax"] for box in boxes),
        }
        expected_box.update({
            "XLength": expected_box["XMax"] - expected_box["XMin"],
            "YLength": expected_box["YMax"] - expected_box["YMin"],
            "ZLength": expected_box["ZMax"] - expected_box["ZMin"],
        })
        assembly_checks = _check_shape(
            assembly_shape,
            # A Part compound of physical instances gives the expected aggregate
            # volume and world bounding box without altering the source doc.
            Part.makeCompound(list(instance_shapes.values())),
            "assembly STEP",
            expected_solids=len(links),
        )
        if _relative_error(assembly_checks["volume_mm3"], expected_volume) > VOLUME_REL_TOL:
            raise ValueError("Assembly STEP volume differs from summed physical link volume")
        # Make the explicit pre-export expectations visible in the report.
        assembly_checks["expected_volume_mm3"] = expected_volume
        assembly_checks["expected_bounding_box_mm"] = expected_box

        stage = "clean_document_roundtrip"
        roundtrip = _clean_roundtrip(assembly_shape, App, doc)

        stage = "export_unique_definition_steps_and_pa12_stls"
        # Filenames are PartNumber-based; append the native source name only
        # when distinct definitions share a PartNumber, preventing overwrite.
        pn_by_source = {}
        sources_by_pn = {}
        for source_name, source in source_objects.items():
            pn = str(getattr(source, "PartNumber", "") or "UNSPECIFIED_PART_NUMBER").strip()
            pn = pn or "UNSPECIFIED_PART_NUMBER"
            pn_by_source[source_name] = pn
            sources_by_pn.setdefault(pn, []).append(source_name)

        part_rows = []
        for source_name in sorted(source_objects):
            source = source_objects[source_name]
            pn = pn_by_source[source_name]
            stem = _safe_stem(pn)
            if len(sources_by_pn[pn]) > 1:
                stem += "__" + _safe_stem(source_name)
            row_files = []

            step_path = parts_dir / f"{stem}.step"
            part_checks, step_record = _validate_part_step(source, step_path, Part, root)
            artifacts.append(step_path)
            row_files.append(step_record)

            material = str(getattr(source, "MaterialName", "")).strip().casefold()
            if material == "pa12":
                stl_path = stl_dir / f"{stem}.stl"
                stl_record = _validate_part_stl(source, stl_path, MeshPart, root)
                artifacts.append(stl_path)
                row_files.append(stl_record)

            part_rows.append({
                "part_number": pn,
                "native_source": source_name,
                "quantity": len(link_sources[source_name]),
                "files": [record["path"] for record in row_files],
                "bytes": sum(record["bytes"] for record in row_files),
                "sha256": {record["path"]: record["sha256"] for record in row_files},
                "step_geometry_check": part_checks,
            })

        stage = "build_bom_and_mass_envelope"
        mass_report = build_bom(doc, root, revision="r05")
        bom_paths = [
            root / "bom" / "bom_r05.csv",
            root / "bom" / "instances_r05.csv",
            root / "reports" / "verification" / "r05_mass_envelope.json",
        ]
        for path in bom_paths:
            if not path.is_file():
                raise IOError(f"Expected BOM/mass output was not written: {path}")
            artifacts.append(path)

        stage = "write_package_manifest"
        assembly_record = _file_record(assembly_path, root)
        bom_records = [_file_record(path, root) for path in bom_paths]
        manifest = {
            "revision": "r05",
            "status": "EXPORTS_AND_STEP_ROUNDTRIP_VALIDATED_NO_FABRICATION_RELEASE",
            "assembly_step": assembly_record,
            "assembly_geometry_check": assembly_checks,
            "clean_document_roundtrip": roundtrip,
            "physical_link_count": len(links),
            "unique_used_definition_count": len(source_objects),
            "parts": part_rows,
            "bom_and_mass_files": bom_records,
            "bom_mass_summary": {
                "status": mass_report.get("status"),
                "instance_count": mass_report.get("instance_count"),
                "part_number_count": mass_report.get("part_number_count"),
                "known_purchased_mass_g": mass_report.get("known_purchased_mass_g"),
                "all_geometry_mass_estimate_g": mass_report.get("all_geometry_mass_estimate_g"),
                "unknown_mass_instance_count": mass_report.get("unknown_mass_instance_count"),
                "actual_assembled_bbox_mm": mass_report.get("actual_assembled_bbox_mm"),
            },
            "export_settings": {
                "volume_relative_tolerance": VOLUME_REL_TOL,
                "bbox_absolute_tolerance_mm": BBOX_ABS_TOL_MM,
                "pa12_stl_linear_deflection_mm": MESH_LINEAR_DEFLECTION_MM,
                "pa12_stl_angular_deflection_rad": MESH_ANGULAR_DEFLECTION_RAD,
                "pa12_selection": "unique used native definitions with MaterialName casefolded to PA12",
            },
            "limitations": [
                "STEP and STL validity checks concern serialized CAD geometry only.",
                "Motor output splines, mounting datums, fasteners, and torque interfaces remain provisional or unknown.",
                "Bearing/shaft fits, spring specifications, cable terminations/guides, and structural loads remain unresolved.",
                "OpenRB-150 mounting and wiring interfaces remain unresolved; its footprint alone is not a mount definition.",
                "No physical build, load validation, or fabrication release is claimed.",
            ],
        }
        manifest_path = root / "reports" / "package_manifest_r05.json"
        manifest_path.parent.mkdir(parents=True, exist_ok=True)
        manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        artifacts.append(manifest_path)
        return manifest
    except Exception as exc:
        _write_diagnostics(root, stage, exc, artifacts)
        raise
