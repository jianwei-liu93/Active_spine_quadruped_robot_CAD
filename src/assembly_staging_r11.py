"""Read-only sampled A/B shaft insertion in the bare S1 assembly stage.

Input is detached verifier capture. No document or GUI calls. Bearings, race
spacers and clips are fitted AFTER the stepped shaft passes the empty4.05mm
bar/ground bores. This is an assembly-stage screen, not whole-robot servicing,
continuous access, press-fit, race retention or tool certification.
"""
import math,json

def run(capture,step_mm=1.):
    import FreeCAD as App
    from verify_link_sections_r11 import _overlap
    from verify_frame_revision_r09 import _bbox,_matrix
    current=capture['current'];objects=current['instances']
    prefixes=('LumbarIntegrated','SpineMotor','MotorCenterShim','Link','Through','Sync',
              'DirectCrank','HornAdapter','GuideLiner','HornGapWasher','HornClampScrew')
    core={n:o['shape'].copy() for n,o in objects.items() if n.startswith(prefixes)}
    shafts=('ThroughA1','ThroughA2','SyncB1','SyncB2')
    report={'status':'RUNNING','native_sha256':capture['native_sha256'],'assembly_phase_rad':0.,
            'assembly_stage':'Bare frame/motor/crank/link/liner skeleton; torso/legs, all A/B bearings/spacers/caps/retainers deferred',
            'included_instances':sorted(core),'stage_exclusions':sorted(set(objects)-set(core)),
            'sample_step_mm_max':step_mm,'samples':[],'overlaps':[],'occ_checks':0,
            'continuous_access':False,'whole_robot_service_access':False,
            'bearing_press_installation_and_outer_race_retention':'UNVERIFIED',
            'fabrication_release':False}
    for name in shafts:
        original=core[name]
        # Start with the entire shaft beyond all retained bare-stage material.
        maxy=max(s.BoundBox.YMax for n,s in core.items() if n!=name)
        travel=maxy-original.BoundBox.YMin+1.
        count=math.ceil(travel/step_mm)
        for i in range(count+1):
            dy=travel*(1-i/count);shape=original.copy();shape.translate(App.Vector(0,dy,0))
            a=_bbox(shape);tested=0
            for other,obstacle in core.items():
                if other==name or not _overlap(a,_bbox(obstacle)):continue
                common=shape.common(obstacle);v=float(common.Volume)
                if not math.isfinite(v) or v<0 or (not common.isNull() and not common.isValid()):
                    raise RuntimeError('Invalid insertion Boolean')
                tested+=1;report['occ_checks']+=1
                if v>1e-5:report['overlaps'].append({'shaft':name,'dy_mm':dy,'obstacle':other,'intersection_mm3':v})
            report['samples'].append({'shaft':name,'dy_mm':dy,'occ_checks':tested})
    report['status']='FAIL_SAMPLED_INSERTION' if report['overlaps'] else 'PASS_SAMPLED_BARE_STAGE_ONLY'
    return report
