"""AX2 streaming checks extending AX01's numeric conventions, not its solver.

Usage: python src/animation_production_validate.py animation/motion/production_r10.json
No FreeCAD or Blender imports are required for validation.
"""
import gzip
import hashlib
import json
import math
import sys
from pathlib import Path
import animation_manifest_validate as ax1

ROOT = Path(__file__).resolve().parents[1]


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read_frames(path):
    opener = gzip.open if str(path).endswith('.gz') else open
    with opener(path, 'rt', encoding='utf-8') as stream:
        for line in stream:
            yield json.loads(line)


def validate_frame(frame, instances, previous=None):
    """Reuse AX1 SO(3), units, quaternion and owner-anchor checks."""
    ax1._walk_finite(frame)
    count = len(instances)
    order = list(instances)
    assert frame['commanded_order'] == list(ax1.COMMAND_ORDER)
    assert len(frame['commanded_rad']) == 6
    assert len(frame['transforms_mm']) == len(frame['transforms_m']) == len(frame['quaternions_wxyz']) == count
    index = {iid: i for i, iid in enumerate(order)}
    for i, (mm, metres, q) in enumerate(zip(frame['transforms_mm'], frame['transforms_m'], frame['quaternions_wxyz'])):
        ax1._mat4(mm, order[i]); ax1._mat4(metres, order[i])
        assert mm[3] == metres[3] == [0., 0., 0., 1.]
        ax1._check_rotation([r[:3] for r in mm[:3]], order[i])
        qr = ax1._quat_rotation(q, order[i])
        assert max(abs(qr[r][c]-mm[r][c]) for r in range(3) for c in range(3)) < 1e-8
        assert max(abs(mm[r][c]-metres[r][c]) for r in range(3) for c in range(3)) < 1e-9
        assert max(abs(mm[r][3]*.001-metres[r][3]) for r in range(3)) < 1e-9
        if previous:
            assert sum(a*b for a,b in zip(q,previous['quaternions_wxyz'][i])) >= -1e-12
    expected = {iid for iid, row in instances.items() if row['geometry_kind'] == 'length_route_dependent'}
    assert {row['instance_id'] for row in frame['procedural_shapes']} == expected
    assert len(frame['procedural_shapes']) == len(expected)
    error = 0.
    for row in frame['procedural_shapes']:
        assert row['frame_id'] == frame['frame_id']
        assert row['generator'] in ('spring', 'cable')
        assert len(row['shape_parameters_sha256']) == 64
        if row['generator'] == 'spring':
            assert row['coil_length_mm'] > 0
            assert abs(math.sqrt(sum(v*v for v in row['axis_world']))-1.) < 1e-8
            assert abs(math.dist(*row['coil_seats_world_mm'])-row['coil_length_mm']) < 1e-7
        else:
            assert len(row['owner_anchors']) == 6
            assert {a['name'] for a in row['owner_anchors']} == ax1.REQUIRED_CABLE_ANCHORS
            for a,b in zip(row['primitives'],row['primitives'][1:]):
                assert math.dist(a['end_world_mm'],b['start_world_mm']) < 1e-7
            assert row['route_length_mm'] > 0
        for anchor in row.get('anchors',row.get('owner_anchors',[])):
            ax1._owner_anchor(anchor, 'timeline anchor', instances)
            M = frame['transforms_mm'][index[anchor['owner_instance_id']]]
            local = anchor['owner_local_mm']
            world = [sum(M[r][c]*local[c] for c in range(3))+M[r][3] for r in range(3)]
            error = max(error,math.dist(world,anchor['world_mm']))
    assert error < .02
    check = frame['validation']
    assert check['spine_closure_max_residual_mm'] <= 1e-6
    assert check['leg_loop_max_residual_mm'] <= 1e-6
    assert check['spine_min_branch_margin_mm'] > 0
    assert not check['guide_warnings']
    return error


def validate(path, root=ROOT):
    path = Path(path)
    data = json.loads(path.read_text())
    baseline_path = root/data['production']['ax01_path']
    assert sha(baseline_path) == data['production']['ax01_sha256']
    baseline = ax1.load_and_validate(baseline_path)
    for key in ('source', 'instances', 'instance_order', 'conventions', 'frames'):
        assert data[key] == baseline[key], 'AX01 source truth changed: '+key
    assert data['schema_version'] == baseline['schema_version'] == '1.0'
    ax1._walk_finite(data)
    for rel, digest in data['production']['source_files_sha256'].items():
        assert sha(root/rel) == digest, 'Source drift: '+rel
    assert sha(root/data['source']['cad_path']) == data['source']['cad_sha256']
    instances = {row['instance_id']:row for row in data['instances']}
    assert list(instances) == data['instance_order']
    assert len(data['meshes']) == len(baseline['meshes'])
    expected_rigid = {row['mesh_id'] for row in instances.values() if row['geometry_kind'] == 'rigid'}
    actual_rigid = set()
    triangles = 0
    for row in data['meshes']:
        if row['asset_status'] == 'PROCEDURAL_DOWNSTREAM':
            continue
        actual_rigid.add(row['mesh_id'])
        asset = root/row['path']
        assert sha(asset) == row['sha256']
        mesh = json.loads(asset.read_text())
        assert mesh['local_units'] == row['local_units'] == 'm'
        assert row['tessellation_tolerance_mm'] == .03
        ax1._walk_finite(mesh)
        assert mesh['vertices_m'] and mesh['triangles']
        assert all(len(v)==3 for v in mesh['vertices_m'])
        assert all(len(t)==3 and all(isinstance(i,int) and 0<=i<len(mesh['vertices_m']) for i in t) for t in mesh['triangles'])
        triangles += len(mesh['triangles'])
    assert actual_rigid == expected_rigid
    summaries = {}
    for name, timeline in data['production']['timelines'].items():
        asset = root/timeline['path']
        assert sha(asset) == timeline['sha256']
        first = previous = None; count = 0; error = 0.
        for frame in read_frames(asset):
            assert abs(frame['time_s']-count/timeline['fps']) < 1e-12
            error = max(error, validate_frame(frame, instances, previous))
            if first is None:first=frame
            previous=frame; count+=1
        assert count == timeline['sample_count'] == timeline['render_frame_count']+1
        assert abs(previous['time_s']-timeline['duration_s']) < 1e-12
        loop_error = max(abs(a-b) for M,N in zip(first['transforms_mm'],previous['transforms_mm']) for r,s in zip(M,N) for a,b in zip(r,s))
        assert loop_error < 1e-7
        assert abs((previous['commanded_rad'][0]-first['commanded_rad'][0])-math.tau*timeline['cycles']) < 1e-10
        summaries[name] = {'samples':count,'loop_matrix_max_error':loop_error,'anchor_max_error_mm':error}
    return {'status':'PASS','physical_instances':len(instances),'rigid_source_meshes':len(actual_rigid),'triangles':triangles,'timelines':summaries}


if __name__ == '__main__':
    print(json.dumps(validate(sys.argv[1]),indent=2))
