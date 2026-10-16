"""Lead-only native and STEP package checks for the sculpted r15 candidate.

``native_checks(doc)`` reopens the saved r15 file as a disposable copy, forces
recompute there, compares used source definitions and placements to the saved
r14 checkpoint, then performs three reversible native-feature edits.
``export_step(doc)`` exports all 455 physical links and strictly round-trips
the placed solids. Neither function saves or edits the caller's document.
"""
import hashlib
import json
import shutil
import time
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
R14_NATIVE = ROOT / "cad" / "flexor_r14_robot.FCStd"
NATIVE_REPORT = ROOT / "reports" / "verification" / "r15_native_checks.json"
STEP_REPORT = ROOT / "reports" / "verification" / "r15_assembly_export.json"
PROBE_PATH = ROOT / "reports" / "tmp" / "r15" / "native_recompute_probe.FCStd"
EXPECTED_LINKS = 455
EXPECTED_USED_SOURCES = 108
CHANGED_SOURCE = "FRM_LUMBAR_COMPACT_CAGE_r12"
TARGET_LINK = "LumbarIntegrated1"
EDIT_PROBES = (
    ("RootBlendShortEarR15", "Radius", 0.05),
    ("RootBlendGuidesR15", "Radius", 0.05),
    # Increasing length grows into the existing 1.6 mm platform, so exercise
    # an exposed region by shortening the shoulder in the disposable copy.
    ("ShelfShoulderPositiveNearR15", "Length", -0.05),
)


def _sha(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _matrix(placement):
    return tuple(float(value) for value in placement.toMatrix().A)


def _links(doc):
    result = {obj.Name: obj for obj in doc.Objects if obj.TypeId == "App::Link"}
    if len(result) != EXPECTED_LINKS:
        raise RuntimeError("Expected exactly 455 physical App::Link instances, got %d" % len(result))
    return result


def _source_map(links):
    """Return one source object per name; never inspect 455 repeated link BReps."""
    result = {}
    for link in links.values():
        source = link.LinkedObject
        if source is None:
            raise RuntimeError(link.Name + ": unresolved LinkedObject")
        previous = result.setdefault(source.Name, source)
        if previous is not source:
            raise RuntimeError(source.Name + ": duplicate source objects use the same name")
    if len(result) != EXPECTED_USED_SOURCES:
        raise RuntimeError("Expected 108 used source definitions, got %d" % len(result))
    return result


def _doc_fingerprint(doc):
    """Bounded mutation guard: hash each used source once and record every pose."""
    import animation_pose_export as ax

    links = _links(doc)
    sources = _source_map(links)
    return {
        "objects": tuple(obj.Name for obj in doc.Objects),
        "controller": tuple((name, str(getattr(doc.PoseController, name))) for name in
                            ("MotionMap", "SpinePhaseRad", "LegAnglesR03", "WheelAngleR07")),
        "links": tuple((name, link.LinkedObject.Name, _matrix(link.LinkPlacement))
                       for name, link in sorted(links.items())),
        "source_hashes": tuple((name, ax.shape_hash(source.Shape))
                               for name, source in sorted(sources.items())),
    }


def _native_state_guard(doc):
    """Reject persisted Invalid/Error states anywhere in the native feature tree."""
    import json as _json

    bodies = [obj for obj in doc.Objects if obj.TypeId == "PartDesign::Body"]
    pending = list(bodies)
    checked = {}
    failures = []
    while pending:
        obj = pending.pop()
        if obj.Name in checked:
            continue
        states = [str(value) for value in obj.State]
        checked[obj.Name] = states
        if any("invalid" in value.lower() or "error" in value.lower() for value in states):
            failures.append({"name": obj.Name, "type": obj.TypeId, "state": states})
        pending.extend(getattr(obj, "Group", []))
    if not bodies:
        raise RuntimeError("Native state guard found no PartDesign Bodies")
    if failures:
        raise RuntimeError("Invalid/Error native Body feature state: " + _json.dumps(failures, sort_keys=True))
    return {"status": "PASS_NATIVE_STATE_ONLY", "body_count": len(bodies),
            "body_and_member_count": len(checked), "invalid_or_error_count": 0}


def _fully_constrained(doc):
    sketches = [obj for obj in doc.Objects if obj.TypeId == "Sketcher::SketchObject"]
    bad = [obj.Name for obj in sketches if not obj.FullyConstrained]
    if bad:
        raise RuntimeError("Underconstrained native sketches: " + ", ".join(bad))
    return {"status": "PASS", "sketch_count": len(sketches), "underconstrained": []}


def _compare_revision_sources(r14, r15):
    """Strictly compare each used source once; the one intended source is additive."""
    from verify_frame_revision_r09 import _strict_shape_identity

    old_links = _links(r14)
    new_links = _links(r15)
    if set(old_links) != set(new_links):
        raise RuntimeError("r14/r15 physical instance identities differ")
    placement_rows = []
    for name in sorted(old_links):
        old, new = old_links[name], new_links[name]
        if old.LinkedObject.Name != new.LinkedObject.Name:
            raise RuntimeError(name + ": source object identity changed")
        if _matrix(old.LinkPlacement) != _matrix(new.LinkPlacement):
            raise RuntimeError(name + ": LinkPlacement changed")
        placement_rows.append(name)

    old_sources = _source_map(old_links)
    new_sources = _source_map(new_links)
    if set(old_sources) != set(new_sources) or CHANGED_SOURCE not in old_sources:
        raise RuntimeError("r14/r15 source inventory differs from the one-source change contract")
    unchanged_rows = []
    for name in sorted(set(old_sources) - {CHANGED_SOURCE}):
        old_obj, new_obj = old_sources[name], new_sources[name]
        if _matrix(old_obj.Placement) != _matrix(new_obj.Placement):
            raise RuntimeError(name + ": source-local Placement changed")
        _strict_shape_identity(old_obj.Shape.copy(copyGeom=True, copyMesh=False),
                               new_obj.Shape.copy(copyGeom=True, copyMesh=False),
                               name + " r14/r15 source")
        unchanged_rows.append(name)

    old_frame = old_sources[CHANGED_SOURCE]
    new_frame = new_sources[CHANGED_SOURCE]
    changed_instances = sorted(name for name, link in new_links.items()
                               if link.LinkedObject.Name == CHANGED_SOURCE)
    if changed_instances != [TARGET_LINK]:
        raise RuntimeError("Only LumbarIntegrated1 may use the refined lumbar source")
    if _matrix(old_frame.Placement) != _matrix(new_frame.Placement):
        raise RuntimeError("Changed lumbar source-local Placement moved")
    before = old_frame.Shape.copy(copyGeom=True, copyMesh=False)
    after = new_frame.Shape.copy(copyGeom=True, copyMesh=False)
    removed = float(before.cut(after).Volume)
    added = float(after.cut(before).Volume)
    if removed > 1e-5 or added <= 1e-5:
        raise RuntimeError("Lumbar source must be strictly additive: removed=%g added=%g" % (removed, added))
    if not after.isValid() or len(after.Solids) != 1:
        raise RuntimeError("r15 lumbar source is not one valid solid")
    return {
        "r14_links": len(old_links), "r15_links": len(new_links),
        "exact_link_placements": len(placement_rows),
        "unchanged_source_count": len(unchanged_rows),
        "unchanged_source_names": unchanged_rows,
        "changed_source": CHANGED_SOURCE,
        "changed_source_instances": changed_instances,
        "changed_source_material_removed_mm3": removed,
        "changed_source_material_added_mm3": added,
        "source_geometry_comparisons": EXPECTED_USED_SOURCES,
    }


def _edit_restore(probe):
    from verify_frame_revision_r09 import _strict_shape_identity

    rows = []
    for name, property_name, delta in EDIT_PROBES:
        feature = probe.getObject(name)
        if feature is None:
            raise RuntimeError("Required r15 editable feature is missing: " + name)
        body = feature.getParentGeoFeatureGroup()
        if body is None or body.Name != CHANGED_SOURCE:
            raise RuntimeError(name + ": feature is not owned by the lumbar source Body")
        original_value = float(getattr(feature, property_name))
        original_shape = body.Shape.copy(copyGeom=True, copyMesh=False)
        setattr(feature, property_name, original_value + delta)
        probe.recompute(None, True, True)
        changed_shape = body.Shape
        if (changed_shape.isNull() or not changed_shape.isValid() or len(changed_shape.Solids) != 1
                or "Error" in feature.State or feature.getStatusString() != "Valid"):
            raise RuntimeError(name + ": temporary native edit produced an invalid feature")
        volume_delta = abs(float(changed_shape.Volume) - float(original_shape.Volume))
        if volume_delta <= 1e-5:
            raise RuntimeError(name + ": temporary edit did not change the source solid")
        setattr(feature, property_name, original_value)
        probe.recompute(None, True, True)
        restored = body.Shape.copy(copyGeom=True, copyMesh=False)
        restored_proof = _strict_shape_identity(original_shape, restored, name + " edit/restore")
        rows.append({"feature": name, "property": property_name,
                     "original_value": original_value, "temporary_delta": delta,
                     "temporary_volume_change_mm3": volume_delta,
                     "restored_geometry": restored_proof})
    return rows


def native_checks(doc):
    """Run saved-copy native gates; the caller's document/file remain untouched."""
    import FreeCAD as App

    native_path = Path(doc.FileName).resolve()
    if not native_path.is_file() or native_path.name != "flexor_r15_robot.FCStd":
        raise ValueError("Save the candidate as cad/flexor_r15_robot.FCStd before native checks")
    if native_path != ROOT / "cad" / "flexor_r15_robot.FCStd":
        raise ValueError("Native checks are bound to this project's r15 checkpoint path")
    native_sha = _sha(native_path)
    if not R14_NATIVE.is_file():
        raise FileNotFoundError("Accepted r14 native checkpoint is missing: %s" % R14_NATIVE)
    before = _doc_fingerprint(doc)
    r14_sha = _sha(R14_NATIVE)
    PROBE_PATH.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(native_path, PROBE_PATH)

    docs = []
    report = {"status": "RUNNING", "native_path": str(native_path.relative_to(ROOT)),
              "native_sha256": native_sha, "r14_native_sha256": r14_sha,
              "probe_path": str(PROBE_PATH.relative_to(ROOT)),
              "probe_is_disposable_copy": True, "edit_tests": [],
              "scope": "Native reopen/recompute/source identity/editability only; no fit, strength, clearance or release claim"}
    try:
        old = App.openDocument(str(R14_NATIVE))
        docs.append(old)
        probe = App.openDocument(str(PROBE_PATH))
        docs.append(probe)
        old_links = _links(old)
        probe_links = _links(probe)
        if set(old_links) != set(probe_links):
            raise RuntimeError("Saved r15 copy does not preserve the exact 455-instance inventory")
        saved_source_shapes = {
            name: source.Shape.copy(copyGeom=True, copyMesh=False)
            for name, source in _source_map(probe_links).items()
        }
        report["native_state_guard_before_recompute"] = _native_state_guard(probe)
        probe.recompute(None, True, True)
        report["native_guard"] = _native_state_guard(probe)
        report["fully_constrained_sketches"] = _fully_constrained(probe)
        report["reopened_recomputed_instances"] = len(probe_links)
        report["r14_to_r15_identity"] = _compare_revision_sources(old, probe)

        from verify_frame_revision_r09 import _strict_shape_identity
        saved_sources = _source_map(probe_links)
        # Forced recompute must reproduce the saved r15 source geometry. Compare
        # the 108 source definitions once each, not the 455 repeated instances.
        for name in sorted(saved_sources):
            _strict_shape_identity(saved_source_shapes[name],
                                   probe.getObject(name).Shape.copy(copyGeom=True, copyMesh=False),
                                   name + " saved/forced-recompute")
        report["forced_recompute_source_comparisons"] = EXPECTED_USED_SOURCES
        report["edit_tests"] = _edit_restore(probe)
        report["status"] = "PASS"
    except Exception as error:
        report["status"] = "FAIL"
        report["error"] = repr(error)
    finally:
        for opened in reversed(docs):
            try:
                App.closeDocument(opened.Name)
            except Exception:
                pass
        App.setActiveDocument(doc.Name)

    report["native_file_unchanged"] = native_sha == _sha(native_path)
    report["native_document_unchanged"] = before == _doc_fingerprint(doc)
    report["r14_file_unchanged"] = r14_sha == _sha(R14_NATIVE)
    if not (report["native_file_unchanged"] and report["native_document_unchanged"]
            and report["r14_file_unchanged"]):
        report["status"] = "FAIL"
        report["error"] = report.get("error", "Native/package probes changed a protected file or caller document")
    NATIVE_REPORT.parent.mkdir(parents=True, exist_ok=True)
    NATIVE_REPORT.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report


def export_step(doc):
    """Export all physical links and prove strict one-to-one placed-solid round-trip."""
    import FreeCAD as App
    import Import
    import Part
    from adaptive_volume_r07 import validate_solids

    native_path = Path(doc.FileName).resolve()
    if not native_path.is_file() or native_path != ROOT / "cad" / "flexor_r15_robot.FCStd":
        raise ValueError("Save the candidate at cad/flexor_r15_robot.FCStd before STEP export")
    native_sha = _sha(native_path)
    before = _doc_fingerprint(doc)
    links = _links(doc)
    target = links.get(TARGET_LINK)
    if target is None or target.LinkedObject.Name != CHANGED_SOURCE:
        raise RuntimeError("LumbarIntegrated1 no longer uses the intended sculpted source")
    folder = ROOT / "exports" / "step" / "r15"
    folder.mkdir(parents=True, exist_ok=True)
    step_path = folder / "flexor_r15_robot.step"
    start = time.monotonic()
    if not App.ParamGet("User parameter:BaseApp/Preferences/Mod/Part/STEP").GetBool("WriteSurfaceCurveMode", True):
        raise ValueError("STEP WriteSurfaceCurveMode=True is required")
    Part.setStaticValue("write.surfacecurve.mode", 1)
    ordered_links = [links[name] for name in sorted(links)]
    # STEP may attach pcurves to its input TopoShapes. Deep-copy placed native
    # BReps into a temporary exchange document so exporter bookkeeping cannot
    # alter the caller's source BRep serialization or physical placements.
    exchange=App.newDocument('R15_TransientSTEPExchange')
    try:
        exported=[]
        for link in ordered_links:
            item=exchange.addObject('Part::Feature',link.Name)
            item.Label=link.Label
            item.Shape=link.Shape.copy(copyGeom=True,copyMesh=False)
            exported.append(item)
        exchange.recompute()
        Import.export(exported, str(step_path))
    finally:
        App.closeDocument(exchange.Name)
        App.setActiveDocument(doc.Name)
    shape = Part.read(str(step_path))
    if len(shape.Solids) != EXPECTED_LINKS or not shape.isValid():
        raise RuntimeError("STEP import did not round-trip to 455 valid solids")
    geometry_result = validate_solids(shape, [obj.Shape for obj in ordered_links], ROOT,
                                      [obj.Name for obj in ordered_links])
    report = {
        "status": "PASS", "revision": "r15",
        "native_path": str(native_path.relative_to(ROOT)), "native_sha256": native_sha,
        "step_path": str(step_path.relative_to(ROOT)), "step_sha256": _sha(step_path),
        "physical_instances": EXPECTED_LINKS, "physical_solids": len(shape.Solids),
        "changed_instance": TARGET_LINK, "changed_source": CHANGED_SOURCE,
        "geometry_roundtrip": geometry_result, "seconds": time.monotonic() - start,
        "write_surfacecurve_mode": 1,
        "export_inputs":"455 deep-copied placed native BReps in temporary exchange document; no additional transform",
        "native_file_unchanged": native_sha == _sha(native_path),
        "native_document_unchanged": before == _doc_fingerprint(doc),
        "scope": "Candidate assembly STEP exchange; no drawings, fabrication release or structural qualification",
    }
    if not (report["native_file_unchanged"] and report["native_document_unchanged"]):
        report["status"] = "FAIL"
        raise RuntimeError("STEP export changed the native file or caller document")
    STEP_REPORT.parent.mkdir(parents=True, exist_ok=True)
    STEP_REPORT.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report
