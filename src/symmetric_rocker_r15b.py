"""Lead-only symmetric-depth A-B rockers, native pads/pockets, r15b.

Keep both accepted B-cheek layers and all sagittal pivots. A thin, centred
single-eye web flows through two tangent-arc ramps into a B-only clevis.
Source-local datum and LinkPlacement remain unchanged. Local +Z is world -Y.
Section dimensions are design assumptions; the video supplies morphology.
"""
import hashlib
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _section_sketch(doc, body, label, wires):
    import FreeCAD as App
    import Sketcher
    sk = body.newObject('Sketcher::SketchObject', body.Name+'_'+label+'Sketch')
    # Sketch XY -> source XZ; pocket cuts +source Y through the whole outline.
    sk.Placement = App.Placement(App.Vector(0, -2, 0), App.Rotation(App.Vector(1, 0, 0), 90))
    for wire in wires:
        for geometry in wire:
            index = sk.addGeometry(geometry, False)
            sk.addConstraint(Sketcher.Constraint('Block', index))
    return sk


def _cut(doc, body, label, wires):
    from spine_link_sections_r11 import _finish
    old = body.Tip
    sk = _section_sketch(doc, body, label, wires)
    feature = body.newObject('PartDesign::Pocket', body.Name+'_'+label)
    feature.Profile = sk
    feature.Length = 12
    return _finish(doc, body, feature, sk, old)


def _depth_relief(x0, x1, mid, half_web, half_span, sign):
    """Two equal-radius tangent arcs; zero slope at both thickness plateaus."""
    import FreeCAD as App
    import Part
    h = half_span-half_web
    radius = ((x1-x0)**2+h*h)/(4*h)
    z0, z1 = half_web, half_span
    pts = ((x0, z0), ((x0+x1)/2, (z0+z1)/2), (x1, z1))
    centres = ((x0, z0+radius), (x1, z1-radius))
    def v(p): return App.Vector(p[0], mid+sign*p[1], 0)
    def arc(a, b, c):
        u = App.Vector(a[0]-c[0]+b[0]-c[0], a[1]-c[1]+b[1]-c[1], 0)
        u.normalize()
        return Part.Arc(v(a), v((c[0]+radius*u.x, c[1]+radius*u.y)), v(b))
    left, upper_left, upper_right = (-3, z0), (-3, half_span+1), (x1, half_span+1)
    return [Part.LineSegment(v(left), v(pts[0])),
            arc(pts[0], pts[1], centres[0]), arc(pts[1], pts[2], centres[1]),
            Part.LineSegment(v(pts[2]), v(upper_right)),
            Part.LineSegment(v(upper_right), v(upper_left)),
            Part.LineSegment(v(upper_left), v(left))]


def build_section(doc, body, length, side, layer, cfg, *, frame_thickness_mm):
    import FreeCAD as App
    import Part
    from spine_bars_r12 import organic_face
    from spine_link_sections_r11 import _pad, _circles
    t = cfg['web_thickness_mm']; leaf = cfg['cheek_thickness_mm']
    outer = cfg['outer_cheek_abs_y_mm']
    # The pose-frame thickness is inherited from MotionMap, independently of
    # a future physical web thickness edit. Keep the original local datum.
    cheek_centres = (frame_thickness_mm/2, frame_thickness_mm/2+side*(layer-outer))
    mid = sum(cheek_centres)/2
    span = abs(cheek_centres[1]-cheek_centres[0])+leaf
    lo = mid-span/2
    whole = organic_face(length, cfg['outline_width_mm'], cfg['waist_width_mm'])
    _pad(doc, body, 'SymmetricBlankR15b', whole, lo, span)
    B = length+3
    x0, x1 = B-cfg['ramp_start_from_B_mm'], B-cfg['ramp_end_from_B_mm']
    _cut(doc, body, 'BalancedDepthR15b', [
        _depth_relief(x0,x1,mid,t/2,span/2,sign) for sign in (1,-1)])
    # Semicircular slot root lies inward of the unchanged 8 mm open zone.
    gap = span-2*leaf
    r = gap/2
    root_x = B-cfg['opening_depth_from_B_mm']
    end_x = B+cfg['outline_width_mm']/2+1
    v = lambda x,z: App.Vector(x,z,0)
    slot = [Part.Arc(v(root_x,mid-r), v(root_x-r,mid), v(root_x,mid+r)),
            Part.LineSegment(v(root_x,mid+r), v(end_x,mid+r)),
            Part.LineSegment(v(end_x,mid+r), v(end_x,mid-r)),
            Part.LineSegment(v(end_x,mid-r), v(root_x,mid-r))]
    _cut(doc, body, 'BOnlyRoundedSlotR15b', [slot])
    _circles(doc, body, 'CoaxialBoresR15b', [(3,3),(B,3)], mid+span/2+1,
             span+2, cfg['bore_diameter_mm'])
    body.SectionContract = json.dumps({
        'revision':'r15b', 'symmetry_plane_source_z_mm':mid,
        'A_single_eye_world_abs_y_mm':(layer+outer)/2,
        'B_cheek_centres_world_abs_y_mm':[layer,outer],
        'web_mm':t, 'cheek_mm':leaf, 'total_depth_mm':span,
        'B_gap_mm':gap, 'B_minimum_open_depth_mm':cfg['opening_depth_from_B_mm'],
        'ramp_source_x_mm':[x0,x1], 'slot_root_radius_mm':r,
        'provenance':'DESIGN_ASSUMPTION; Movie S1 morphology and user symmetry correction'})
    body.Revision = 'r15b'
    body.PartNumber = body.Name.replace('_r12', '_r15b')
    body.Process = 'SLS PA12 symmetric single-eye rocker with B-only fork; finish bores; strength, fits, retention UNVERIFIED'
    return json.loads(body.SectionContract)


def integrate(doc):
    """Apply to an unsaved disposable copy of r15, then save a NEW checkpoint."""
    import FreeCAD as App
    import cad_common as cc
    from kinematics import spine
    import robot_pose_r03 as pose
    baseline = ROOT/'cad/flexor_r15_robot.FCStd'
    target = ROOT/'cad/flexor_r15b_robot.FCStd'
    cfg = json.loads((ROOT/'parameters/assembly_r15b.json').read_text())
    detail = cfg['symmetric_rocker_r15b']
    if hashlib.sha256(baseline.read_bytes()).hexdigest() != detail['baseline_native_sha256']:
        raise RuntimeError('Preserved r15 checkpoint changed')
    if target.exists(): raise RuntimeError('r15b checkpoint already exists; preserve it')
    old_links = {o.Name:tuple(o.LinkPlacement.toMatrix().A) for o in doc.Objects if o.TypeId=='App::Link'}
    mm = json.loads(doc.PoseController.MotionMap)
    rocker_rows = []
    changed_sources = []; moved = []; layers = {}
    p = pose._parameters(doc); state = spine(float(doc.PoseController.SpinePhaseRad),p)
    doc.openTransaction('r15b symmetric rocker and A stack')
    try:
        for name,m in mm.items():
            if not (name.startswith('Link') and '_L3_' in name): continue
            link=doc.getObject(name);body=link.LinkedObject
            side=1 if m['y']>0 else -1;layer=abs(m['y'])
            for child in reversed(list(body.Group)): doc.removeObject(child.Name)
            branch=int(m['a'].removeprefix('A'))
            if branch in layers and abs(layers[branch]-layer)>1e-9:
                raise RuntimeError('Handed rocker layers disagree')
            layers[branch]=layer
            section = build_section(doc,body,p['L3_mm'],side,layer,detail,
                                    frame_thickness_mm=float(m['thickness']))
            rocker_rows.append({'instance':name,'source':body.Name,'section':section})
            changed_sources.append(body.Name)
        for branch,layer in sorted(layers.items()):
            mid=(layer+detail['outer_cheek_abs_y_mm'])/2
            # Derive the retained stack stops from the actual unmodified
            # fixed bearing envelopes, rather than a second hardcoded stack.
            inner_stop=doc.getObject('A%d_1_Bearing0'%branch).Shape.BoundBox.YMax
            outer_stop=doc.getObject('A%d_1_OuterBearing'%branch).Shape.BoundBox.YMin
            bounds = {'inner':(inner_stop,mid-detail['web_thickness_mm']/2),
                      'outer':(mid+detail['web_thickness_mm']/2,outer_stop)}
            for kind,suffix in (('inner','Spacer0'),('outer','OuterSpacer')):
                source=doc.getObject('A%d_1_%s'%(branch,suffix)).LinkedObject
                users=[o.Name for o in doc.Objects if o.TypeId=='App::Link' and o.LinkedObject==source]
                expected={'A%d%s_%s'%(branch,pref,suffix) for pref in ('_1','__1')}
                if set(users)!=expected: raise RuntimeError('Unexpected shared A-spacer source '+source.Name)
                start,end=bounds[kind];length=end-start
                source.Tip.Length=length
                source.Revision='r15b';source.PartNumber='A%d_%s_SPACER_L%g_r15b'%(branch,kind.upper(),length)
                source.Process='Nominal inner-race spacer; turn and finish; bearing/fit/thrust qualification outstanding'
                changed_sources.append(source.Name)
                for sign,pref in ((1,'_1'),(-1,'__1')):
                    obj=doc.getObject('A%d%s_%s'%(branch,pref,suffix))
                    obj.LinkPlacement=cc.hardware_place(state['A'+str(branch)],sign*(start+end)/2,length)
                    moved.append(obj.Name)
            for sign,pref in ((1,'_1'),(-1,'__1')):
                obj=doc.getObject('A%d%s_Bearing1'%(branch,pref))
                obj.LinkPlacement=cc.hardware_place(state['A'+str(branch)],sign*mid,detail['web_thickness_mm'])
                moved.append(obj.Name)
        doc.recompute()
        if mm!=json.loads(doc.PoseController.MotionMap): raise RuntimeError('MotionMap unexpectedly changed')
        for name,matrix in old_links.items():
            if name not in moved and matrix!=tuple(doc.getObject(name).LinkPlacement.toMatrix().A):
                raise RuntimeError('Unexpected instance movement '+name)
        doc.Label='FLEXOR r15b symmetric-depth A-B rockers and matched A-pivot stack'
        doc.DesignParameters.Revision='r15b'
        doc.DesignParameters.ParameterFile='parameters/assembly_r15b.json; parameters/candidate_r02.json'
        doc.PoseController.ParameterRevision='r15b'
        doc.PoseController.PrescribedMotionConfigR07=json.dumps(cfg)
        doc.commitTransaction()
    except Exception:
        doc.abortTransaction()
        raise
    doc.saveAs(str(target))
    report={'status':'INTEGRATED_PENDING_GATES','native_path':str(target.relative_to(ROOT)),
            'baseline_sha256':detail['baseline_native_sha256'],
            'native_sha256':hashlib.sha256(target.read_bytes()).hexdigest(),
            'changed_sources':sorted(changed_sources),'repacked_instances':sorted(moved),
            'moved_instances':sorted(name for name in moved if max(abs(x-y) for x,y in zip(
                old_links[name],doc.getObject(name).LinkPlacement.toMatrix().A))>1e-12),
            'rockers':rocker_rows,'motion_map_unchanged':True,
            'limits':'Source-informed assumed sections; no strength, fit, race-capture or continuous clearance qualification'}
    (ROOT/'reports/verification/r15b_integration.json').write_text(json.dumps(report,indent=2)+'\n')
    return report
