"""Render/encode the immutable, reviewed r14 coordination scene; one GPU job."""
from pathlib import Path
import hashlib
import json
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
NAME = 'spine_leg_coordination_s2_r14'
BLENDER = '/snap/blender/current/blender'


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def run():
    start = time.monotonic()
    scene = ROOT/'animation/scenes'/(NAME+'.blend')
    scene_sha = sha(scene)
    reports = ROOT/'reports/animation'
    readback = json.loads((reports/(NAME+'_readback.json')).read_text())
    preview = json.loads((reports/(NAME+'_preview_review.json')).read_text())
    clearance = json.loads((reports/'coordination_r14_changed_clearance.json').read_text())
    assert readback['status'] == 'PASS' and readback['blend_sha256'] == scene_sha
    assert preview['status'] == 'PASS_LEAD_PREVIEW_REVIEW' and preview['blend_sha256'] == scene_sha
    assert clearance['status'] == 'PASS_BOUNDED_CHANGED_PAIRS' and clearance['phases_completed'] == 9
    native = ROOT/'cad/flexor_r14_robot.FCStd'
    native_sha = sha(native)
    assert native_sha == clearance['native_sha256']
    folder = ROOT/'reports/tmp/r14_animation'
    folder.mkdir(parents=True, exist_ok=True)
    with (folder/'render.log').open('w') as log:
        subprocess.run([BLENDER, '-b', str(scene), '--python',
                        str(ROOT/'animation/blender/render_frames.py'), '--', '--scene', NAME],
                       cwd=ROOT, stdout=log, stderr=subprocess.STDOUT, check=True)
    assert sha(scene) == scene_sha and sha(native) == native_sha
    with (reports/(NAME+'_video.json')).open('w') as log:
        subprocess.run([sys.executable, str(ROOT/'animation/blender/encode_verify.py'),
                        '--input-pattern', str(ROOT/'animation/output/frames'/NAME/'frame_%06d.png'),
                        '--output', str(ROOT/'animation/output'/(NAME+'.mp4')),
                        '--frame-count', '1500', '--fps', '60', '--overwrite'],
                       cwd=ROOT, stdout=log, check=True)
    assert sha(scene) == scene_sha and sha(native) == native_sha
    record = {'status':'ENCODE_AND_FULL_DECODE_PASS', 'scene':NAME,
              'blend_sha256':scene_sha, 'native_sha256':native_sha,
              'native_file_unchanged':True, 'elapsed_seconds':time.monotonic()-start,
              'frames':1500, 'fps':60, 'duration_s':25,
              'runner_sha256':sha(__file__)}
    (reports/(NAME+'_production.json')).write_text(json.dumps(record, indent=2)+'\n')
    print(json.dumps(record), flush=True)
    return record


if __name__ == '__main__':
    run()
