"""Lead-only 24-frame native r10 CAD preview with exact restoration guards.

Import/preparation has no effects. run() calls the existing GUI CAD renderer;
no CAD save, geometry helper edits, Blender export or physical solver.
"""
from pathlib import Path
import hashlib
import json
import math
import traceback

NATIVE_SHA256 = 'd90c7dba99b8a5f0825160d4c1d2058509ce64401e95b49aa4101fc66b8e9ad9'
TAGS = ('foreL', 'foreR', 'hindL', 'hindR')


def _require(value, message):
    if not value:
        raise RuntimeError(message)


def _sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _number(value):
    value = float(value.Value if hasattr(value, 'Value') else value)
    _require(math.isfinite(value), 'Nonfinite prescribed state')
    return value


def fixed_state(controller):
    """Saved hip/knee pairs and separate wheel coordinate; never infer knees."""
    raw = str(controller.LegAnglesR03)
    legs = json.loads(raw)
    _require(set(legs) == set(TAGS), 'Expected four explicit saved hip/knee pairs')
    _require(all(isinstance(legs[t], (tuple, list)) and len(legs[t]) == 2 for t in TAGS),
             'Saved leg angles must be explicit (hip,knee) pairs')
    legs = {t: [_number(q) for q in legs[t]] for t in TAGS}
    return {'leg_angles_rad': legs, 'wheel_angle_rad': _number(controller.WheelAngleR07),
            'provenance': 'Exact saved PoseController.LegAnglesR03 and separate WheelAngleR07',
            'leg_coordinate_order': ['hip', 'prescribed_knee'],
            'knees': 'PRESCRIBED_SAVED_COORDINATES; not inferred from wheel angle',
            'wheel': 'SEPARATE_SAVED_COORDINATE; no cable/elastic equilibrium solution',
            'physical_motors': 7, 'commanded_coordinates': 6, 'prescribed_knees': 4,
            'loaded_passive_motion': 'NOT_SOLVED'}


def torso_samples(parameters, torso_angle):
    """Pure exact24-sample angle derivation using the authoritative callback."""
    samples = []
    for frame, degree in enumerate(range(0, 360, 15)):
        theta = math.radians(degree)
        fore = _number(torso_angle(theta, 'fore', parameters))
        hind = _number(torso_angle(theta, 'hind', parameters))
        relative = math.atan2(math.sin(fore - hind), math.cos(fore - hind))
        samples.append({'frame': frame, 'spine_phase_deg': degree,
                        'fore_torso_angle_rad': fore, 'hind_torso_angle_rad': hind,
                        'relative_fore_minus_hind_rad': relative})
    return samples


def matched_extrema(samples):
    """Sampled extrema only; explicit CAD sign convention, deterministic ties."""
    _require(len(samples) == 24 and [r['frame'] for r in samples] == list(range(24)) and
             [r['spine_phase_deg'] for r in samples] == list(range(0, 360, 15)),
             'Expected exact24 sampled spine phases')
    values = [_number(r['relative_fore_minus_hind_rad']) for r in samples]
    _require(max(values) - min(values) > 1e-9 and max(values) - min(values) < math.pi,
             'Degenerate or branch-discontinuous relative torso-angle samples')
    flex = min(range(24), key=lambda i: (values[i], i))
    extend = max(range(24), key=lambda i: (values[i], -i))
    return {'flex_frame': flex, 'extend_frame': extend,
            'flex_sample': samples[flex], 'extend_sample': samples[extend],
            'coordinate_convention': 'World +X forward,+Y left,+Z up; positive torso angle rotates local +X toward +Z in sagittal XZ; relative=atan2(sin(fore-hind),cos(fore-hind)) radians',
            'label_convention': 'Flex=min signed fore-minus-hind angle; extend=max; sampled CAD presentation convention, not a source-paper or loaded-motion classification',
            'selection': 'Actual sampled extrema among24 captured phases; deterministic earliest frame on ties',
            'continuous_extrema_claim': False}


def run(doc, root, expected_native_sha256=NATIVE_SHA256):
    """Lead runs on the canonical GUI document; produces PNGs and manifest only."""
    import FreeCAD as App
    import FreeCADGui as Gui
    import animation_pose_export as ax
    import robot_pose_r03 as pose
    import motion_views_r07
    root = Path(root).resolve()
    native = (root / 'cad/flexor_r10_robot.FCStd').resolve()
    _require(Path(doc.FileName).resolve() == native and _sha(native) == expected_native_sha256,
             'Open the exact lead-frozen canonical r10 GUI document')
    controller = doc.PoseController
    state = fixed_state(controller)
    _require(abs(state['wheel_angle_rad']) <= 1e-12,
             'Existing native renderer supports the saved fixed wheel u=0 only')
    parameters = pose._parameters(doc)
    samples = torso_samples(parameters, pose.torso_angle)
    matched = matched_extrema(samples)
    links = [o for o in doc.Objects if o.TypeId == 'App::Link']
    names = {o.Name for o in links}
    _require(len(links) == len(names) == 487, 'Expected complete487 physical CAD instances')
    # Read-only preflight: the fixed leg/spring state must not trigger source
    # regeneration or unsupported motion during the GUI presentation sweep.
    for row in samples:
        _require(set(pose.placements(doc, math.radians(row['spine_phase_deg']))) == names,
                 'Read-only fixed-state pose inventory mismatch')
    before = ax.snapshot(doc)
    original_controller = {key: getattr(controller, key) for key in
                           ('MotionMap', 'SpinePhaseRad', 'LegAnglesR03', 'WheelAngleR07')}
    placements = {o.Name: App.Placement(o.LinkPlacement) for o in links}
    visibility = [(o, bool(o.Visibility)) for o in doc.Objects if hasattr(o, 'Visibility')]
    App.setActiveDocument(doc.Name)
    view = Gui.activeDocument().activeView()
    camera = view.getCamera()
    out = root / 'reports/motion/r10'
    report = None
    failure = None
    restore_errors = []
    try:
        group = doc.getObject('ReferenceClearances')
        if group is not None:
            group.Visibility = False
        report = motion_views_r07.render(doc, root, step_deg=15, revision='r10')
    except Exception:
        failure = traceback.format_exc()
    finally:
        # First restore analytically, then actual saved bits. No source rebuild.
        try:
            pose.apply_pose(doc, _number(original_controller['SpinePhaseRad']))
        except Exception:
            restore_errors.append('Analytical restore: ' + traceback.format_exc())
        try:
            for obj in links:
                obj.LinkPlacement = placements[obj.Name]
            for key, value in original_controller.items():
                setattr(controller, key, value)
        except Exception:
            restore_errors.append('Exact placement/controller restore: ' + traceback.format_exc())
        for obj, visible in visibility:
            try:
                obj.Visibility = visible
            except Exception:
                restore_errors.append('Visibility restore ' + obj.Name + ': ' + traceback.format_exc())
        try:
            view.setCamera(camera)
            Gui.updateGui()
        except Exception:
            restore_errors.append('Camera restore: ' + traceback.format_exc())
    native_unchanged = _sha(native) == expected_native_sha256
    try:
        pose_restored = before == ax.snapshot(doc)
        visibility_restored = all(bool(o.Visibility) == value for o, value in visibility)
        camera_restored = view.getCamera() == camera
        state_restored = fixed_state(controller) == state
    except Exception:
        pose_restored = visibility_restored = camera_restored = state_restored = False
        restore_errors.append('Restoration verification: ' + traceback.format_exc())
    report = dict(report or {})
    report.update(revision='r10', native_sha256=expected_native_sha256,
        native_file_unchanged=native_unchanged, pose_restored=pose_restored,
        visibility_restored=visibility_restored, camera_restored=camera_restored,
        fixed_saved_state_restored=state_restored, pose_provenance='PRESCRIBED_KINEMATIC',
        fixed_leg_wheel_state=state, sampled_torso_angles=samples,
        native_visual_capture=True, Blender='NOT_RUN', video='NOT_RUN',
        wrapper_source_sha256=_sha(Path(__file__)),
        renderer_source_sha256=_sha(root / 'src/motion_views_r07.py'),
        restoration_errors=restore_errors,
        limits='24 visual CAD samples; no continuous clearance, loaded equilibrium, physical performance or fabrication release claim')
    matched.update(same_camera=False, fixed_leg_wheel_state=False,
        camera_provenance='Unchanged motion_views_r07.render explicitly sets the same orientation,position,height,clip/focal distances for every15-degree capture; source hash recorded',
        saved_state_provenance=state)
    report['matched_flex_extend'] = matched
    frames = report.get('frames', [])
    complete = len(frames) == 24 and [r['frame'] for r in frames] == list(range(24)) and [r['spine_phase_deg'] for r in frames] == list(range(0, 360, 15))
    try:
        for row in frames:
            path = (root / row['path']).resolve()
            _require(path.is_relative_to(out) and path.is_file() and _sha(path) == row['sha256'],
                     'Missing/stale/out-of-scope actual CAD frame')
    except Exception:
        complete = False
        failure = (failure or '') + traceback.format_exc()
    passed = failure is None and not restore_errors and complete and native_unchanged and pose_restored and visibility_restored and camera_restored and state_restored
    matched['same_camera'] = bool(passed)
    matched['fixed_leg_wheel_state'] = bool(passed)
    if complete:
        matched['flex_capture'] = dict(frames[matched['flex_frame']])
        matched['extend_capture'] = dict(frames[matched['extend_frame']])
    report['status'] = 'PASS_CAPTURED_RESTORED' if passed else 'FAIL_CAPTURE_OR_RESTORE'
    if failure:
        report['exception'] = failure
    out.mkdir(parents=True, exist_ok=True)
    (out / 'capture_manifest.json').write_text(json.dumps(report, indent=2, allow_nan=False) + '\n')
    _require(passed, 'Native r10 capture/restoration failed; inspect reports/motion/r10/capture_manifest.json')
    return report
