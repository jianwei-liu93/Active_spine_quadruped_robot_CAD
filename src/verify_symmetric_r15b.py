"""Read-only identity, depth-symmetry and bounded changed-pair r15b gates."""
import hashlib
import json
import math
import time
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]


def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def identity(old,new):
    import FreeCAD as App
    from verify_frame_revision_r09 import _strict_shape_identity
    import package_sculpted_r15 as native
    record=json.loads((ROOT/'reports/verification/r15b_integration.json').read_text())
    a={o.Name:o for o in old.Objects if o.TypeId=='App::Link'}
    b={o.Name:o for o in new.Objects if o.TypeId=='App::Link'}
    assert set(a)==set(b) and len(b)==455
    sa={o.LinkedObject.Name:o.LinkedObject for o in a.values()}
    sb={o.LinkedObject.Name:o.LinkedObject for o in b.values()}
    assert set(sa)==set(sb) and len(sb)==108
    expected=set(record['changed_sources']);moved=set(record['moved_instances'])
    same=[];changed=[];symmetry=[]
    for name in sorted(sa):
        x,y=sa[name],sb[name]
        assert tuple(x.Placement.toMatrix().A)==tuple(y.Placement.toMatrix().A)
        sx=x.Shape.copy(copyGeom=True,copyMesh=False);sy=y.Shape.copy(copyGeom=True,copyMesh=False)
        assert sy.isValid() and len(sy.Solids)==1,name
        if name not in expected:
            _strict_shape_identity(sx,sy,name);same.append(name)
        else:
            changed.append({'source':name,'old_volume_mm3':sx.Volume,'new_volume_mm3':sy.Volume})
        if name.startswith('SPN_AB_TERMINAL'):
            section=json.loads(y.SectionContract);mid=section['symmetry_plane_source_z_mm']
            matrix=App.Matrix();matrix.A33=-1;matrix.A34=2*mid
            reflection=sy.transformGeometry(matrix)
            missing=sy.cut(reflection).Volume;extra=reflection.cut(sy).Volume
            assert max(abs(missing),abs(extra))<1e-5,(name,missing,extra)
            symmetry.append({'source':name,'symmetry_plane_source_z_mm':mid,
                             'reflection_difference_mm3':[missing,extra],**section})
    actual_moved=[]
    for name in sorted(a):
        assert a[name].LinkedObject.Name==b[name].LinkedObject.Name
        error=max(abs(x-y) for x,y in zip(a[name].LinkPlacement.toMatrix().A,b[name].LinkPlacement.toMatrix().A))
        if error>1e-12: actual_moved.append(name)
        assert not b[name].LinkTransform and b[name].Scale==1
    assert set(actual_moved)==moved
    assert old.PoseController.MotionMap==new.PoseController.MotionMap
    assert all(name not in json.loads(new.PoseController.MotionMap) for name in moved)
    assert all(name not in actual_moved for name in ('Link1_L3_1','Link1_L3__1','Link2_L3_1','Link2_L3__1'))
    assert all(getattr(old.PoseController,k)==getattr(new.PoseController,k) for k in
               ('SpinePhaseRad','LegAnglesR03','WheelAngleR07'))
    import robot_pose_r03 as pose
    assert pose._parameters(old)==pose._parameters(new)
    return {'status':'PASS','native_sha256':sha(new.FileName),'baseline_sha256':sha(old.FileName),
            'physical_instances':455,'sources':108,'strict_unchanged_sources':same,
            'changed_sources':changed,'moved_instances':actual_moved,'rocker_depth_symmetry':symmetry,
            'rocker_instance_and_source_frames_preserved':True,'motion_map_unchanged':True,
            'native_states':native._native_state_guard(new),'sketches':native._fully_constrained(new)}


def native_probe(doc):
    """Use only a separately reopened disposable copy, never save it."""
    from verify_frame_revision_r09 import _strict_shape_identity
    body=doc.SPN_AB_TERMINAL_r12_B1_POS
    feature=doc.getObject(body.Name+'_CoaxialBoresR15b')
    before=body.Shape.copy(copyGeom=True,copyMesh=False)
    sk=feature.Profile[0] if isinstance(feature.Profile,tuple) else feature.Profile
    original=sk.Placement
    # A through-bore sketch moves 0.025 mm in X: meaningful native geometry edit.
    changed=original.copy();changed.Base.x+=.025;sk.Placement=changed;doc.recompute()
    assert body.Shape.isValid() and len(body.Shape.Solids)==1
    difference=before.cut(body.Shape).Volume+body.Shape.cut(before).Volume
    assert difference>1e-5
    sk.Placement=original;doc.recompute()
    _strict_shape_identity(before,body.Shape.copy(copyGeom=True,copyMesh=False),'rocker native edit restore')
    source=doc.A1_1_Spacer0.LinkedObject;feature=source.Tip;length=feature.Length.Value
    old_shape=source.Shape.copy(copyGeom=True,copyMesh=False)
    feature.Length=length+.025;doc.recompute();assert source.Shape.isValid()
    assert abs(source.Shape.Volume-old_shape.Volume)>1e-5
    feature.Length=length;doc.recompute()
    _strict_shape_identity(old_shape,source.Shape.copy(copyGeom=True,copyMesh=False),'spacer native edit restore')
    return {'status':'PASS','rocker_bore_native_shift_mm':.025,'bore_edit_volume_difference_mm3':difference,
            'spacer_native_length_edit_mm':.025,'both_edits_restored':True,'probe_file_saved':False}


def motion(doc,output):
    """91 cycle poses + nine paper-profile poses; all 16 changed instances vs455.

    Conservative transformed source AABBs exclude pairs before BRep creation.
    Geometry/relative-transform keys reuse exact rigid pair results. No contact
    exemptions or previously accepted overlaps are silently discarded.
    """
    import FreeCAD as App
    import animation_pose_export as ax
    import animation_coordination_v2 as coordination
    import leg_motion_r07 as api
    import robot_pose_r03 as pose
    from kinematics import spine,residuals
    from verify_sculpted_r15 import _pairs,_bbox_disjoint,_pose_metrics,_neutral
    start=time.time();before=ax.snapshot(doc);native_sha=sha(doc.FileName)
    cfg=json.loads(doc.PoseController.PrescribedMotionConfigR07)
    assert cfg==json.loads((ROOT/'parameters/assembly_r15b.json').read_text())
    record=json.loads((ROOT/'reports/verification/r15b_integration.json').read_text())
    selected=set(record['repacked_instances'])|{r['instance'] for r in record['rockers']}
    links={o.Name:o for o in doc.Objects if o.TypeId=='App::Link'}
    pairs=_pairs(sorted(links),selected);assert len(pairs)==7144
    sources={o.LinkedObject.Name:o.LinkedObject.Shape.copy(copyGeom=True,copyMesh=False) for o in links.values()}
    neutral,wheel=_neutral(doc);generator_cache={};pair_cache={};rows=[];paper=[]
    def screen(theta,angles,wheel):
        plan=api.descriptor(doc,theta,angles,wheel,config=cfg)
        generated=api.regenerate_sources(plan,generator_cache)
        local={name:generated.get(name,sources[obj.LinkedObject.Name]) for name,obj in links.items()}
        bounds={};world={};excluded=hits=checks=0;bad=[]
        for name,shape in local.items():
            bb=shape.BoundBox;p=plan['placements'][name]
            points=[p.multVec(App.Vector(x,y,z)) for x in (bb.XMin,bb.XMax)
                    for y in (bb.YMin,bb.YMax) for z in (bb.ZMin,bb.ZMax)]
            bounds[name]=[f(getattr(pt,axis) for pt in points) for axis in ('x','y','z') for f in (min,max)]
        def placed(name):
            if name not in world:
                x=local[name].copy(copyGeom=True,copyMesh=False)
                x.Placement=plan['placements'][name].multiply(x.Placement);world[name]=x
            return world[name]
        for a,b in pairs:
            if _bbox_disjoint(bounds[a],bounds[b]): excluded+=1;continue
            # Only rigid sources are cached. A changed procedural route always gets a new boolean.
            key=None
            if a not in generated and b not in generated:
                relative=plan['placements'][a].inverse().multiply(plan['placements'][b])
                key=(a,b,tuple(round(v,11) for v in relative.toMatrix().A))
            if key is not None and key in pair_cache: volume=pair_cache[key];hits+=1
            else:
                common=placed(a).common(placed(b));checks+=1
                assert common.isNull() or common.isValid(),(a,b)
                volume=0 if common.isNull() else common.Volume
                assert math.isfinite(volume) and volume>=-1e-8
                if key is not None: pair_cache[key]=volume
            if volume>1e-5: bad.append({'a':a,'b':b,'intersection_mm3':volume})
        assert excluded+hits+checks==len(pairs)
        return {'pair_count':len(pairs),'bbox_excluded':excluded,'cached_rigid_pairs':hits,
                'occ_checks':checks,'forbidden_overlaps':bad,**_pose_metrics(doc,theta,plan)}
    for degree in range(0,361,4):
        row={'phase_deg':degree,**screen(math.radians(degree),neutral,wheel)};rows.append(row)
        print('R15B_CYCLE',degree,row['occ_checks'],len(row['forbidden_overlaps']),flush=True)
        Path(output).write_text(json.dumps({'status':'RUNNING','native_sha256':native_sha,'cycle':rows},indent=2)+'\n')
        if row['forbidden_overlaps']: break
    with coordination.paper_descriptor_context():
        for degree in (0,18,90,135,180,198,240,270,330):
            t=degree/(360*coordination.PROFILE['presentation_frequency_hz'])
            theta,angles,wheel=coordination.trajectory('coordinated_spine_legs',t,neutral)
            row={'profile_phase_deg':degree,'theta_rad':theta,'leg_angles_rad':angles,
                 'wheel_angle_rad':wheel,**screen(theta,angles,wheel)};paper.append(row)
            print('R15B_PAPER',degree,row['occ_checks'],len(row['forbidden_overlaps']),flush=True)
            if row['forbidden_overlaps']: break
    p=pose._parameters(doc);numeric=[max(abs(r) for r in residuals(spine(math.radians(i),p),p)) for i in range(361)]
    assert ax.snapshot(doc)==before and sha(doc.FileName)==native_sha
    all_rows=rows+paper
    passed=(len(rows)==91 and len(paper)==9 and not any(r['forbidden_overlaps'] or r['guide_warnings'] for r in all_rows)
            and max(numeric)<1e-6 and max(r['leg_closure_max_residual_mm'] for r in all_rows)<1e-6)
    result={'status':'PASS_FINITE_CHANGED_PAIRS' if passed else 'FAIL','native_sha256':native_sha,
            'elapsed_s':time.time()-start,'selected_instances':sorted(selected),'physical_instance_count':len(links),
            'source_count':len(sources),'pairs_per_pose':len(pairs),'cycle_step_deg':4,
            'cycle':rows,'paper_profile':paper,'numeric_cycle_samples':361,
            'numeric_spine_closure_max_mm':max(numeric),'document_and_native_unchanged':True,
            'limits':['Finite sampled poses, not continuous collision certification.',
                      'Only pairs involving the 16 changed physical instances; earlier r15 evidence retained for other pairs.',
                      'Prescribed knees, springs and cable regeneration; no loaded equilibrium or structural/fit qualification.']}
    Path(output).write_text(json.dumps(result,indent=2)+'\n')
    return result
