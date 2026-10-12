"""Deterministic, read-only BOM and package-manifest helpers for R02.

Call ``build_bom(doc, root, revision='r02')`` from an already-open FreeCAD
document. The module does not import FreeCAD and can be tested with small
duck-typed objects. It only enumerates ``App::Link`` instances; definition
objects in the PartsLibrary are not counted as physical instances.
"""
from __future__ import annotations

import csv
import hashlib
import json
import math
from collections import defaultdict
from pathlib import Path


DENSITY_KG_M3 = {
    "pa12": 1010.0,
    "steel": 7850.0,
    "copper": 8960.0,
    "rubber": 1100.0,
    "aluminum": 2700.0,
    "cable": 970.0,
    "spring": 7850.0,
}
REFERENCE_ENVELOPE_MM = {"X": 110.0, "Y": 99.0, "Z": 84.0}


def _prop(obj, name, default=None):
    """Read a FreeCAD property or an ordinary Python attribute."""
    try:
        props = obj.PropertiesList
    except Exception:
        props = None
    if props is not None and name not in props:
        return default
    try:
        return getattr(obj, name)
    except Exception:
        return default


def _string(value, default=""):
    if value is None:
        return default
    return str(value).strip()


def _number(value):
    try:
        result = float(value)
    except (TypeError, ValueError, OverflowError):
        return None
    return result if math.isfinite(result) else None


def _bbox_values(box):
    if box is None:
        return None
    try:
        values = {
            "XMin": float(box.XMin), "XMax": float(box.XMax),
            "YMin": float(box.YMin), "YMax": float(box.YMax),
            "ZMin": float(box.ZMin), "ZMax": float(box.ZMax),
            "XLength": float(box.XLength), "YLength": float(box.YLength),
            "ZLength": float(box.ZLength),
        }
    except (AttributeError, TypeError, ValueError, OverflowError):
        return None
    if not all(math.isfinite(v) for v in values.values()):
        return None
    return values


def _shape_box(shape):
    if shape is None:return None
    try:return _bbox_values(shape.optimalBoundingBox(False,False))
    except (AttributeError,TypeError):return _bbox_values(getattr(shape,'BoundBox',None))


def _shape(obj):
    try:
        shape = obj.Shape
    except Exception:
        return None
    try:
        if shape.isNull():
            return None
    except Exception:
        pass
    return shape


def _material_density(material):
    key = _string(material).casefold()
    return DENSITY_KG_M3.get(key)


def _instance_row(link, revision):
    source = getattr(link, "LinkedObject", None)
    # PartNumber metadata is authoritative. Never infer a part number from
    # instance/source object names: several legacy bearing names are misleading.
    part_number = _string(_prop(source, "PartNumber"))
    if not part_number:
        part_number = "UNSPECIFIED_PART_NUMBER"
    shape = _shape(link)
    source_shape = _shape(source) if source is not None else None
    volume = _number(getattr(shape, "Volume", None)) if shape is not None else None
    if volume is not None and volume < 0:
        volume = None
    local_box = _shape_box(source_shape)
    assembled_box = _shape_box(shape)

    material = _string(_prop(source, "MaterialName")) or "UNSPECIFIED"
    density = _material_density(material)
    purchased = _number(_prop(source, "PurchasedMass_g"))
    if purchased is not None and purchased < 0:
        purchased = None
    role = _string(_prop(source, "Role"))
    controller_identity = " ".join((part_number, role, _string(getattr(source, "Name", "")), _string(getattr(link, "Name", "")))).casefold()
    is_controller = ("controller" in controller_identity or "openrb" in controller_identity) and role in ("PURCHASED", "ENVELOPE") and material.casefold() not in DENSITY_KG_M3
    if purchased is not None:
        mass_g = purchased
        mass_method = "PURCHASED_NOMINAL"
        mass_unknown_reason = ""
        purchased_mass_g = purchased
        geometry_mass_g = None
    elif is_controller:
        mass_g = None
        mass_method = "UNKNOWN"
        mass_unknown_reason = "controller requires source PurchasedMass_g; geometric envelope is not used as mass"
        purchased_mass_g = None
        geometry_mass_g = None
    elif volume is not None and density is not None:
        # 1 mm^3 = 1e-9 m^3; kg to g multiplies by 1000, hence 1e-6.
        mass_g = volume * density * 1e-6
        mass_method = "GEOMETRY_VOLUME_DENSITY_ESTIMATE"
        mass_unknown_reason = ""
        purchased_mass_g = None
        geometry_mass_g = mass_g
    else:
        mass_g = None
        mass_method = "UNKNOWN"
        if purchased is None and density is None:
            mass_unknown_reason = "no PurchasedMass_g and no recognized material density"
        elif volume is None:
            mass_unknown_reason = "no usable instance shape volume"
        else:
            mass_unknown_reason = "mass source unavailable"
        purchased_mass_g = None
        geometry_mass_g = None

    obj_name = _string(getattr(link, "Name", ""))
    return {
        "instance_name": obj_name,
        "instance_label": _string(getattr(link, "Label", "")),
        "source_name": _string(getattr(source, "Name", "")),
        "part_number": part_number,
        "revision": _string(_prop(source, "Revision")) or revision,
        "role": role or "UNSPECIFIED",
        "material_name": material,
        "process": _string(_prop(source, "Process")) or "UNSPECIFIED",
        "release_status": _string(_prop(source, "ReleaseStatus")) or "UNSPECIFIED",
        "purchased_mass_g": purchased_mass_g,
        "geometry_mass_estimate_g": geometry_mass_g,
        "mass_g": mass_g,
        "mass_method": mass_method,
        "mass_unknown_reason": mass_unknown_reason,
        "density_assumption_kg_m3": density if geometry_mass_g is not None else None,
        "custom_geometry_mass_estimate_g": geometry_mass_g if _string(_prop(source, "Role")).casefold() in {"custom", "spring"} else None,
        "other_geometry_mass_estimate_g": geometry_mass_g if geometry_mass_g is not None and _string(_prop(source, "Role")).casefold() not in {"custom", "spring"} else None,
        "shape_volume_mm3": volume,
        "source_local_bbox_x_mm": local_box["XLength"] if local_box else None,
        "source_local_bbox_y_mm": local_box["YLength"] if local_box else None,
        "source_local_bbox_z_mm": local_box["ZLength"] if local_box else None,
        "assembled_bbox_x_mm": assembled_box["XLength"] if assembled_box else None,
        "assembled_bbox_y_mm": assembled_box["YLength"] if assembled_box else None,
        "assembled_bbox_z_mm": assembled_box["ZLength"] if assembled_box else None,
        "assembled_bbox_xmin_mm": assembled_box["XMin"] if assembled_box else None,
        "assembled_bbox_xmax_mm": assembled_box["XMax"] if assembled_box else None,
        "assembled_bbox_ymin_mm": assembled_box["YMin"] if assembled_box else None,
        "assembled_bbox_ymax_mm": assembled_box["YMax"] if assembled_box else None,
        "assembled_bbox_zmin_mm": assembled_box["ZMin"] if assembled_box else None,
        "assembled_bbox_zmax_mm": assembled_box["ZMax"] if assembled_box else None,
    }


def _fmt(value):
    if value is None:
        return ""
    if isinstance(value, float):
        return format(value, ".12g")
    return str(value)


def _write_csv(path, fieldnames, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fieldnames, extrasaction="ignore", lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({key: _fmt(row.get(key)) for key in fieldnames})


def _aggregate(rows):
    groups = defaultdict(list)
    for row in rows:
        groups[row["part_number"]].append(row)
    out = []
    for part_number in sorted(groups):
        members = groups[part_number]
        def joined(key):
            return " | ".join(sorted({r[key] for r in members if r.get(key)}))
        purchased = [r["purchased_mass_g"] for r in members if r["purchased_mass_g"] is not None]
        geometry = [r["geometry_mass_estimate_g"] for r in members if r["geometry_mass_estimate_g"] is not None]
        custom_geometry = [r["custom_geometry_mass_estimate_g"] for r in members if r["custom_geometry_mass_estimate_g"] is not None]
        other_geometry = [r["other_geometry_mass_estimate_g"] for r in members if r["other_geometry_mass_estimate_g"] is not None]
        total_known = [r["mass_g"] for r in members if r["mass_g"] is not None]
        out.append({
            "part_number": part_number,
            "quantity": len(members),
            "revisions": joined("revision"),
            "roles": joined("role"),
            "material_names": joined("material_name"),
            "processes": joined("process"),
            "release_statuses": joined("release_status"),
            "source_names": joined("source_name"),
            "purchased_mass_total_g": sum(purchased) if purchased else None,
            "geometry_mass_estimate_total_g": sum(geometry) if geometry else None,
            "custom_geometry_mass_estimate_total_g": sum(custom_geometry) if custom_geometry else None,
            "other_geometry_mass_estimate_total_g": sum(other_geometry) if other_geometry else None,
            "known_mass_total_g": sum(total_known) if total_known else None,
            "mass_unknown_quantity": sum(r["mass_g"] is None for r in members),
        })
    return out


def _union_bbox(rows):
    valid = [r for r in rows if r["assembled_bbox_xmin_mm"] is not None]
    if not valid:
        return None
    limits = {
        "xmin": min(r["assembled_bbox_xmin_mm"] for r in valid),
        "xmax": max(r["assembled_bbox_xmax_mm"] for r in valid),
        "ymin": min(r["assembled_bbox_ymin_mm"] for r in valid),
        "ymax": max(r["assembled_bbox_ymax_mm"] for r in valid),
        "zmin": min(r["assembled_bbox_zmin_mm"] for r in valid),
        "zmax": max(r["assembled_bbox_zmax_mm"] for r in valid),
    }
    limits["x_mm"] = limits["xmax"] - limits["xmin"]
    limits["y_mm"] = limits["ymax"] - limits["ymin"]
    limits["z_mm"] = limits["zmax"] - limits["zmin"]
    return limits


def _mass_report(rows, revision):
    purchased = sum(r["purchased_mass_g"] or 0.0 for r in rows)
    geometry_estimate = sum(r["geometry_mass_estimate_g"] or 0.0 for r in rows)
    custom_estimate = sum(r["custom_geometry_mass_estimate_g"] or 0.0 for r in rows)
    other_geometry_estimate = sum(r["other_geometry_mass_estimate_g"] or 0.0 for r in rows)
    unknown = sum(r["mass_g"] is None for r in rows)
    bbox = _union_bbox(rows)
    delta = None if bbox is None else {
        axis.lower() + "_delta_mm": bbox[axis.lower() + "_mm"] - ref
        for axis, ref in REFERENCE_ENVELOPE_MM.items()
    }
    return {
        "revision": revision,
        "status": "COMPUTED_FROM_DOCUMENT" if rows else "NO_PHYSICAL_LINKS",
        "method": "App::Link instances; PurchasedMass_g takes precedence; otherwise instance Shape.Volume times explicit material density. No double counting.",
        "units": {"length": "mm", "mass": "g", "volume": "mm^3"},
        "instance_count": len(rows),
        "part_number_count": len({r["part_number"] for r in rows}),
        "known_purchased_mass_g": purchased,
        "custom_geometry_mass_estimate_g": custom_estimate,
        "other_geometry_mass_estimate_g": other_geometry_estimate,
        "all_geometry_mass_estimate_g": geometry_estimate,
        "known_mass_sum_g": purchased + geometry_estimate,
        "unknown_mass_instance_count": unknown,
        "actual_assembled_bbox_mm": bbox,
        "reference_envelope_mm": dict(REFERENCE_ENVELOPE_MM),
        "actual_minus_reference_mm": delta,
        "density_assumptions_kg_m3": dict(DENSITY_KG_M3),
        "mass_limitations": [
            "Geometry-volume masses are estimates using material-class densities, not weighed masses or validated grades.",
            "PurchasedMass_g is included as nominal purchased mass and suppresses any shape-volume estimate for that instance.",
            "Controller mass remains unknown unless the linked definition provides PurchasedMass_g; it is never filled with zero or an old parameter assumption.",
            "Unknown-mass instances are excluded from known_mass_sum_g.",
            "The 338 g project target is not treated as achieved or as a measured result.",
        ],
        "unknown_mass_instances": [
            {"instance_name": r["instance_name"], "part_number": r["part_number"], "reason": r["mass_unknown_reason"]}
            for r in rows if r["mass_g"] is None
        ],
    }


def build_bom(doc, root, revision="r02"):
    """Enumerate physical links and write grouped/instance CSV plus mass JSON.

    The document is only read. Shapes are read from the link for placed volume
    and assembled bounds, and from its LinkedObject for definition-local size.
    Returns the mass-envelope report dictionary.
    """
    root = Path(root)
    links = [obj for obj in getattr(doc, "Objects", ()) if getattr(obj, "TypeId", None) == "App::Link"]
    rows = [_instance_row(obj, revision) for obj in links]
    rows.sort(key=lambda r: (r["part_number"], r["revision"], r["instance_name"], r["source_name"]))
    grouped = _aggregate(rows)
    instance_fields = list(rows[0]) if rows else [
        "instance_name", "instance_label", "source_name", "part_number", "revision", "role", "material_name", "process", "release_status",
        "purchased_mass_g", "geometry_mass_estimate_g", "mass_g", "mass_method", "mass_unknown_reason", "density_assumption_kg_m3",
        "custom_geometry_mass_estimate_g", "other_geometry_mass_estimate_g",
        "shape_volume_mm3", "source_local_bbox_x_mm", "source_local_bbox_y_mm", "source_local_bbox_z_mm",
        "assembled_bbox_x_mm", "assembled_bbox_y_mm", "assembled_bbox_z_mm", "assembled_bbox_xmin_mm", "assembled_bbox_xmax_mm",
        "assembled_bbox_ymin_mm", "assembled_bbox_ymax_mm", "assembled_bbox_zmin_mm", "assembled_bbox_zmax_mm",
    ]
    group_fields = [
        "part_number", "quantity", "revisions", "roles", "material_names", "processes", "release_statuses", "source_names",
        "purchased_mass_total_g", "geometry_mass_estimate_total_g", "custom_geometry_mass_estimate_total_g",
        "other_geometry_mass_estimate_total_g", "known_mass_total_g", "mass_unknown_quantity",
    ]
    _write_csv(root / "bom" / f"bom_{revision}.csv", group_fields, grouped)
    _write_csv(root / "bom" / f"instances_{revision}.csv", instance_fields, rows)
    report = _mass_report(rows, revision)
    native_path = Path(getattr(doc, "FileName", ""))
    if native_path.is_file():
        report["native_sha256"] = hashlib.sha256(native_path.read_bytes()).hexdigest()
    output = root / "reports" / "verification" / f"{revision}_mass_envelope.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return report


def manifest(root, paths, output="reports/package_manifest_r02.json"):
    """Hash existing caller-selected deliverables under root; never hash self.

    Missing files are listed without a digest. Paths outside ``root`` are
    rejected. The function makes no validation/release claims.
    """
    root = Path(root).resolve()
    out_path = Path(output)
    if out_path.is_absolute():
        try:
            out_rel = out_path.resolve().relative_to(root)
        except ValueError as exc:
            raise ValueError("manifest output must be inside root") from exc
    else:
        resolved_out = (root / out_path).resolve()
        try:
            out_rel = resolved_out.relative_to(root)
        except ValueError as exc:
            raise ValueError("manifest output must be inside root") from exc
    out_rel_posix = out_rel.as_posix()
    entries, missing, skipped = [], [], []
    normalized = sorted({Path(p).as_posix() for p in paths})
    for relative in normalized:
        candidate = Path(relative)
        target = candidate.resolve() if candidate.is_absolute() else (root / candidate).resolve()
        try:
            rel = target.relative_to(root).as_posix()
        except ValueError as exc:
            raise ValueError(f"manifest path is outside root: {relative}") from exc
        if rel == out_rel_posix:
            skipped.append({"path": rel, "reason": "manifest does not hash itself"})
            continue
        if not target.is_file():
            missing.append(rel)
            continue
        digest = hashlib.sha256()
        with target.open("rb") as stream:
            for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                digest.update(chunk)
        entries.append({"path": rel, "size_bytes": target.stat().st_size, "sha256": digest.hexdigest()})
    payload = {
        "status": "HASHES_WRITTEN_NO_GATES_CLAIMED",
        "algorithm": "SHA-256",
        "files": entries,
        "missing_paths": missing,
        "skipped_paths": skipped,
        "note": "Manifest hashes only existing caller-selected deliverables. Hashes establish byte identity, not correctness, validation, or fabrication release.",
    }
    target_out = root / out_rel
    target_out.parent.mkdir(parents=True, exist_ok=True)
    target_out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return payload
