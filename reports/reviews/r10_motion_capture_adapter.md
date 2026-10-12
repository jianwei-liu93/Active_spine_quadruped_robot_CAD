# r10 native motion capture wrapper

Status: PREPARATION ONLY. `src/motion_capture_r10.py` is ready for the lead to run after the drawing GUI operation. No FreeCAD/MCP runtime, CAD save, image capture, native pose change, manifest publication or video generation occurred during preparation. Only this review and the new wrapper were added.

The wrapper calls the unchanged `motion_views_r07.render(doc, root, step_deg=15, revision='r10')` to produce exactly 24 actual native CAD PNG frames at 0,15,…,345 degrees. This is a prescribed CAD preview, not Blender or a clearance/dynamics campaign. The frozen canonical SHA defaults to `d90c7dba99b8a5f0825160d4c1d2058509ce64401e95b49aa4101fc66b8e9ad9`; the actual open document path and disk SHA must match before capture.

## Restoration and state provenance

Before rendering, the wrapper records an exact `animation_pose_export.snapshot`, every saved App::Link placement, raw controller properties, all object visibility values and the camera. Read-only `robot_pose_r03.placements` preflights all 24 fixed-state poses for all 487 instances, so an unsupported or mismatched leg/spring state fails before capture. `ReferenceClearances` is explicitly hidden for the whole capture call.

An outer `finally` restores the analytical spine phase, then restores the exact saved LinkPlacement values and controller properties to avoid analytical floating-bit drift. It restores every visibility value and camera even if the inner renderer raises. Acceptance requires exact before/after AX snapshot equality, separate fixed-state equality, exact visibility and camera restoration, unchanged canonical bytes, complete frame indices/phases and current frame hashes. Restoration or capture failure produces a failing capture manifest and raises; it cannot retain a successful wrapper status.

Saved `LegAnglesR03` must explicitly contain four `(hip,prescribed_knee)` pairs. These are recorded separately from `WheelAngleR07`, with no knee-from-wheel inference. The existing native renderer supports fixed wheel u=0; a saved nonzero wheel state fails closed. The manifest retains seven physical motors, six commanded coordinates, four prescribed knees and loaded passive motion NOT_SOLVED.

## Matched flex/extend markers

For each captured phase, the wrapper calls the authoritative `robot_pose_r03.torso_angle(theta,kind,p)` using actual native parameters. It records fore and hind angles and signed relative angle `atan2(sin(fore-hind),cos(fore-hind))`, radians. The presentation convention is explicit: flex is the sampled minimum signed relative angle and extend the sampled maximum. Positive torso angle rotates local +X toward +Z in the world sagittal XZ plane (+X forward,+Y left,+Z up). This is a CAD label convention rather than an asserted source-paper or loaded-motion classification.

The markers reference actual captured frame indices, phase, path and SHA, and include actual corresponding angle values. They are sampled extrema among the 24 frames, not continuous extrema. Degenerate or branch-discontinuous angle ranges fail. `same_camera=true` and `fixed_leg_wheel_state=true` are emitted only after successful capture/restoration; camera provenance identifies the existing renderer's identical explicit camera setup on every frame and records that helper's source hash.

The successful manifest satisfies `package_delivery_r10.validate_native_preview`: revision r10, `PASS_CAPTURED_RESTORED`, matching native SHA, native bytes unchanged, `pose_restored=true`, `visibility_restored=true`, `pose_provenance=PRESCRIBED_KINEMATIC`, exact 24 frame coverage, and distinct matched extrema markers. No GIF is required by that validator; none is produced. Blender and video remain NOT_RUN.

## Lead entry point

```python
import motion_capture_r10
report = motion_capture_r10.run(doc, root)
```

The lead must execute this in the installed canonical FreeCAD GUI, inspect the 24 images and the matched pair, and retain their actual hashes/review. No current capture or visual acceptance is claimed by this code preparation.

## Checks actually performed

- In-memory compile/import passed without importing FreeCAD or changing canonical/native renderer bytes.
- Pure fixed-state tests verified independent saved hip/knee and wheel provenance.
- A synthetic sinusoidal authoritative-callback fixture produced exactly 24 phases and the expected sampled minimum/maximum markers.
- Negative tests rejected missing/nonfinite saved state, incomplete phase coverage, degenerate angle range, nonfinite relative angles and branch-discontinuous extrema.
- A pure-math smoke using `robot_pose_r03.torso_angle` and repository parameter JSON passed without CAD imports. Its predicted marker frames were 16 and 4; these are math-test outputs, not actual native captured-frame evidence. Runtime selection uses the actual document parameters.

Frozen geometry, pose, animation and capture helpers were not edited. No runtime output or existing artifact was changed.
