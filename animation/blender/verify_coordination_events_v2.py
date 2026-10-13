"""Measure event lag and joint excursion from the serialized solver trajectory."""
from pathlib import Path
import gzip,hashlib,json,math
ROOT=Path(__file__).resolve().parents[2]
manifest_path=ROOT/'animation/motion/production_coordination_v2_r10.json'
manifest=json.loads(manifest_path.read_text());info=manifest['production']['timelines']['coordinated_spine_legs']
path=ROOT/info['path'];profile=manifest['production']['paper_motion_profile']
with gzip.open(path,'rt') as stream:frames=[json.loads(line) for line in stream][:300]
extension=[f['output_angles_rad']['fore']-f['output_angles_rad']['hind'] for f in frames]
extension_start=min(range(300),key=extension.__getitem__)
hind_back=max(range(300),key=lambda i:frames[i]['leg_angles_rad']['hindL'][0])
lag_frames=(hind_back-extension_start)%300;lag_deg=lag_frames*360/300
assert extension_start==150 and hind_back==165
assert abs(math.radians(lag_deg)-profile['hind_backswing_lag_rad'])<1e-10
assert frames[hind_back+1]['leg_angles_rad']['hindL'][0]<frames[hind_back]['leg_angles_rad']['hindL'][0]
excursions={tag:math.degrees(max(f['leg_angles_rad'][tag][0] for f in frames)-min(f['leg_angles_rad'][tag][0] for f in frames)) for tag in frames[0]['leg_angles_rad']}
assert all(abs(v-profile['hip_full_excursion_deg'])<1e-8 for v in excursions.values())
report={'status':'PASS','timeline_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'manifest_sha256':hashlib.sha256(manifest_path.read_bytes()).hexdigest(),'cycle_samples':300,'extension_onset_sample':extension_start,'hind_backswing_onset_sample':hind_back,'lag_frames':lag_frames,'lag_deg':lag_deg,'lag_seconds_at_presentation_rate':lag_frames/60,'hip_full_excursions_deg':excursions,'event_definition':'Spine extension starts at minimum fore-minus-hind torso angle; hind backswing starts at maximum CAD hip angle followed by decreasing angle','source_provenance':'Hip excursion from approximate S27 plot reading; lag from main paper; CAD datums and fore phase are explicit assumptions'}
(ROOT/'reports/animation/coordination_v2_events.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
