"""Minimal isolated r15b source library for the Movie S2 presentation.

The lead executes this builder through the installed Blender MCP. Every
physical instance retains its source-local mesh and exported CAD world pose.
All 300 procedural samples are stored; no frame handlers or CAD writes occur.
"""
from pathlib import Path
import hashlib
import json

import bpy

from build_scenes import (
    bake_channel, bake_mechanics, camera, import_robot, load_manifest, materials, point_camera,
    read_cycle, save_scene, stage, text,
)

ROOT = Path(__file__).resolve().parents[2]
SCENE = 'spine_leg_coordination_r15b'
MANIFEST = 'animation/motion/production_coordination_r15b.json'


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def build():
    data = load_manifest(MANIFEST)
    assert data['source']['cad_revision'] == 'r15b'
    assert len(data['instances']) == len(data['instance_order']) == 455
    assert len(set(data['instance_order'])) == 455
    assert [item['instance_id'] for item in data['instances']] == data['instance_order']
    assert len({item['source_object_name'] for item in data['instances']}) == 108
    assert sum(item['geometry_kind'] != 'rigid' for item in data['instances']) == 10
    assert sha(ROOT / data['source']['cad_path']) == data['source']['cad_sha256']
    info = data['production']['timelines']['coordinated_spine_legs']
    assert sha(ROOT / info['path']) == info['sha256']
    frames = read_cycle(data, 'coordinated_spine_legs')
    if SCENE in bpy.data.scenes:
        old = bpy.data.scenes[SCENE]
        assert old.get('source_manifest') == MANIFEST
        # Only remove objects owned solely by this versioned scene.
        for obj in list(old.objects):
            if len(obj.users_scene) == 1:
                bpy.data.objects.remove(obj, do_unlink=True)
        bpy.data.scenes.remove(old)
    scene = bpy.data.scenes.new(SCENE)
    if bpy.context.window:
        bpy.context.window.scene = scene
    scene.frame_start = 1
    scene.frame_end = 300
    scene.render.fps = 60
    scene['source_manifest'] = MANIFEST
    scene['source_manifest_sha256'] = sha(ROOT / MANIFEST)
    scene['source_cad_sha256'] = data['source']['cad_sha256']
    scene['source_timeline_sha256'] = info['sha256']
    scene['motion_provenance'] = 'PRESCRIBED_KINEMATIC; passive loads not simulated'
    scene['physical_instances'] = 455
    scene['source_definitions'] = 108
    scene['phase_origin_rad'] = frames[0]['commanded_rad'][0]
    scene['motion_blur'] = False
    scene['builder_path'] = str(Path(__file__).relative_to(ROOT))
    scene['builder_sha256'] = sha(__file__)
    mats = materials()
    stage(scene)
    cam = camera(scene)
    objects = import_robot(scene, data, mats)
    assert all(obj.parent is None for obj in objects.values())
    bake_mechanics(scene, data, objects, frames, 300)
    # Blender's read-only absolute-key times accumulate float32 increments.
    # Address each stored sample by its actual time, rather than assuming an
    # exact integer grid and inadvertently interpolating adjacent samples.
    for item in data['instances']:
        if item['geometry_kind'] == 'rigid':
            continue
        keys = objects[item['instance_id']].data.shape_keys
        assert len(keys.key_blocks) == 301
        keys.animation_data_clear()
        bake_channel(keys, 'eval_time', 0, [key.frame for key in list(keys.key_blocks)[1:]])
    scene['procedural_key_time_policy'] = 'Explicit sample lookup; eval_time consumes actual stored key.frame values'
    point_camera(cam, (.20, -.36, .13), (0, 0, -.008), .30)
    text(scene, cam, 'FLEXOR r15b / SPINE + LEG COORDINATION', -.138, .0675, .0066, mats['ink'])
    text(scene, cam, 'Prescribed kinematics | Paper-informed hip cycle (~69 deg)', -.138, .057, .0036, mats['muted'])
    text(scene, cam, 'r15b CAD reconstruction | Passive loads not simulated', -.138, -.069, .0033, mats['muted'])
    path = save_scene(scene)
    print('R15B_COORDINATION_SOURCE_BUILT', json.dumps({
        'scene': SCENE, 'path': path, 'physical_instances': len(objects),
        'source_definitions': 108, 'procedural_instances': 10,
        'cycle_samples': 300, 'handlers_required': False, 'render_status': 'NOT_RUN',
    }), flush=True)
    return scene


if __name__ == '__main__':
    build()
