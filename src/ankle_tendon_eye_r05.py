"""Lead-executed provisional ankle cable eye/extended journal, mm/rad.

Native steel eye radial hole, swivel fit, knot/securing, shaft bending, groove
fatigue and material strength are UNVERIFIED engineering assumptions. Routes
remain unchanged: a later caller truncates cable at A+1.5*towardHip, inside
the radial Ø.4 hole. No source math/schema edits, save or automatic execution.
"""
import json
import math


def apply(b,routes,transform=None,tag='HindTendon'):
    """Extend existing hind A journals/clips; add exactly one eye+spacer/side.

    routes are torso-local neutral-u0 hind routes at plane57, wheelX-50.
    Preserve shaft/clip leg motion kinds; new rigid eye/spacer placements are
    captured for the existing fixed-hind-state pose guard. No duplicate clips
    or journals are instantiated. Repeated application rejects before mutation.
    """
    import FreeCAD as App
    import cad_common as cc
    from build_leg_r02 import _journal_source
    from tendon_r03 import _transformers
    V=lambda p:App.Vector(*p)
    tf,tv=_transformers(transform)
    if set(routes)!= {-1,1}:raise ValueError('Both hind routes are required')
    names=[tag+'_'+label+'_'+part for label in ('L','R') for part in ('AnkleEye','AnkleSpacer')]
    if any(b.doc.getObject(n) for n in names):raise ValueError('Ankle termination already applied for '+tag)
    targets={};local={}
    # Resolve all existing hardware and validate frozen route inputs first.
    for side,r in routes.items():
        if abs(r['wheel_angle_rad'])>1e-12 or abs(r['wheel']['axle_center'][0]+50)>1e-9:
            raise ValueError('r05 eye requires neutral wheelX-50 routes')
        g=r['geometry'];A=g['A'];anchor=r['ankle_anchor']
        if abs(anchor[1]-side*57)>1e-9:raise ValueError('r05 eye requires cable plane57')
        lines=[p for p in r['primitives'] if p['type']=='line']
        if not lines:raise ValueError('Ankle route needs final incoming line')
        start=lines[-1]['start'];dx,dz=start[0]-A[0],start[2]-A[1]
        if math.hypot(dx,dz)<1e-9:raise ValueError('Undefined ankle eye direction')
        local[side]=(A,math.atan2(dz,dx))
        matches=[(n,m) for n,m in b.motion.items() if m.get('leg_type')=='hind' and m.get('side')==side and m.get('point')=='A']
        journals=[(n,m) for n,m in matches if n.endswith('A_Journal')]
        clips=[(n,m) for n,m in matches if 'A_Clip' in n and abs(m.get('y',0))>50]
        if len(journals)!=1 or len(clips)!=1:raise ValueError('Expected one existing A journal and outer clip per hind leg')
        for n,m in journals+clips:
            o=b.doc.getObject(n)
            if o is None or o.TypeId!='App::Link':raise ValueError('Missing ankle hardware link '+n)
        targets[side]=(journals[0],clips[0])
    pn='LEG_r05_ANKLE_SWIVEL_EYE_OD4_ID2p05_T1p2_RADIALp4'
    if pn not in b.sources:
        body=b.ring(pn,4,2.05,1.2)
        old=body.Tip
        sk=b.doc.addObject('Sketcher::SketchObject',pn+'_RadialHoleSketch');body.addObject(sk)
        # Pocket normal +sourceX: begins at X2.2 and cuts inward to X1.0.
        # Source sketch XY maps to eye source(Y,Z), so center lies at Z.6.
        sk.Placement=App.Placement(V((2.2,0,.6)),App.Rotation(V((0,1,0)),V((0,0,1)),V((1,0,0)),'ZXY'))
        cc.circle(sk,0,0,.2)
        cut=body.newObject('PartDesign::Pocket',pn+'_RadialCrossHole');cut.Profile=sk;cut.Length=1.2
        b.doc.recompute();sk.Visibility=False;old.Visibility=False
        body.Revision='r05';body.Process='DESIGN_ASSUMPTION steel swivel annulus; radial Ø.4 drill; knot/securing/strength UNVERIFIED'
    eye=b.sources[pn]
    spacer=b.ring('LEG_r05_ANKLE_SPACER_OD3_ID2p05_L2p6',3,2.05,2.6)
    spacer.Revision='r05';spacer.Process='DESIGN_ASSUMPTION turned steel spacer; axial fit/strength UNVERIFIED'
    # Request the exact native journal helper, then reserve this new geometry
    # under an r05 identity without modifying an already-instanced shared part.
    journal=_journal_source(b,13.75)
    users=[o for o in b.doc.Objects if o.TypeId=='App::Link' and o.LinkedObject==journal]
    if users:raise ValueError('13.75mm helper source already instanced; require fresh r05 journal source')
    journal.PartNumber='LEG_r05_ANKLE_JOURNAL_D1p9_L13p75_GROOVED'
    journal.Revision='r05';journal.Process='DESIGN_ASSUMPTION extended ankle journal; groove fatigue/fit/material strength UNVERIFIED'
    parent=App.Rotation(V(tv((1,0,0))),V(tv((0,1,0))),V(tv((0,0,1))),'ZXY')
    motion={};instances=[];modified=[]
    def install(src,name,placement):
        data={'base_xyz_mm':tuple(placement.Base),'rotation_xyzw':tuple(placement.Rotation.Q)}
        desc={'kind':'torso_r04_rigid','torso':'hind','tag':tag,'wheel_angle_rad':0,
              'local_placement_json':json.dumps(data),'provenance':'DESIGN_ASSUMPTION'}
        origin=tuple(placement.Base);x,z=transform((origin[0],origin[2])) if transform else (origin[0],origin[2])
        world=App.Placement(V((x,origin[1],z)),parent.multiply(placement.Rotation))
        o=b.add(src,name,world,'Tendons',desc);instances.append(o.Name);motion[o.Name]=desc
    for side,(A,angle) in local.items():
        worldA=tf((A[0],0,A[1]));P=(worldA[0],worldA[2])
        (jn,jm),(cn,cm)=targets[side]
        j=b.doc.getObject(jn);j.setLink(journal);j.LinkPlacement=cc.hardware_place(P,side*51.625,13.75)
        jm.update(y=side*51.625,length=13.75);motion[jn]=dict(jm)
        clip=b.doc.getObject(cn);clip.LinkPlacement=cc.hardware_place(P,side*58,.6)
        cm.update(y=side*58,length=.6);motion[cn]=dict(cm);modified.extend((jn,cn))
        label='L' if side==1 else 'R'
        install(eye,tag+'_'+label+'_AnkleEye',cc.plane_placement(A,side*57+.6,angle))
        install(spacer,tag+'_'+label+'_AnkleSpacer',cc.hardware_place(A,side*55.1,2.6))
    b.doc.recompute()
    return {'instances':tuple(instances),'modified_instances':tuple(modified),'motion':motion,
            'dimensions_mm':{'journal_inner_abs_y':44.75,'journal_outer_abs_y':58.5,'journal_length':13.75,'clip_inner_abs_y':45.25,'clip_outer_abs_y':58,'spacer_center_abs_y':55.1,'spacer_length':2.6,'eye_center_abs_y':57,'eye_thickness':1.2,'radial_hole_diameter':.4,'future_cable_termination_radius':1.5},
            'limits':('CAD validity/interference NOT_RUN by worker','Cable route unchanged; later truncate inside radial hole','Swivel journal fit, knot/securing, strength and fatigue UNVERIFIED')}
