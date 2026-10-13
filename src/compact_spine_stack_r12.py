"""Lead-only compact axial stack; S9 planar datums and motor envelopes retained.

Starts from r10, never from the rejected r11 fork. Retire explicit obsolete
physical instances, preserving every surviving instance ID and source frame.
All fits/retention/load capacities remain engineering assumptions.
"""
import json
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]


def _shaft(doc, source, length, span=None):
    pads = [o for o in source.Group if o.TypeId == 'PartDesign::Pad']
    pads[0].Length = length
    outer = [o for o in source.Group if o.TypeId == 'Sketcher::SketchObject' and '_Groove1' in o.Name]
    if len(outer) != 1:
        raise RuntimeError('One outer groove required: '+source.Name)
    outer[0].Placement.Base.z = length-.2
    if span is not None:
        shoulder = pads[-1]
        profile = shoulder.Profile[0] if isinstance(shoulder.Profile, tuple) else shoulder.Profile
        profile.Placement.Base.z = (length-span)/2
        shoulder.Length = span
    source.Revision = 'r12'
    source.PartNumber = source.Name+'_R12'
    source.Process += '; r12 reduced end stack; groove/fit/thrust/load UNVERIFIED'


def apply(b, config=None):
    import FreeCAD as App
    import cad_common as cc
    from kinematics import spine
    from retain_flexor import grooves
    import spine_frame_r12
    doc=b.doc; p=b.p
    if 'CompactFrameR12' in doc.PoseController.PropertiesList:
        raise ValueError('r12 already integrated')
    if 'LinkSectionsR11' in doc.PoseController.PropertiesList:
        raise ValueError('r12 must start from r10, never rejected r11 fork')
    before={o.Name:tuple(o.LinkPlacement.toMatrix().A) for o in doc.Objects if o.TypeId=='App::Link'}
    b.motion=json.loads(doc.PoseController.MotionMap)
    s=spine(float(doc.PoseController.SpinePhaseRad),p)
    changed=[]; retired=[]

    def move(name, P, y, length, source=None):
        obj=doc.getObject(name)
        if obj is None or obj.TypeId!='App::Link': raise ValueError('Missing physical ID '+name)
        if source is not None: obj.setLink(source)
        obj.LinkPlacement=cc.hardware_place(P,y,length)
        if name in b.motion: b.motion[name].update(y=y,length=length)
        changed.append(name)

    def ring(name, length):
        source=b.ring(name,3,2.05,length)
        source.Revision='r12';source.Process='Separate inner-race spacer; axial fit/thrust UNVERIFIED'
        return source

    link=doc.LumbarIntegrated1; original_source=link.LinkedObject.Name
    placement=App.Placement(link.LinkPlacement)
    frame, frame_report=spine_frame_r12.build(doc,p,config)
    b.library.addObject(frame);b.sources[frame.Name]=frame
    link.setLink(frame);link.LinkPlacement=placement;changed.append(link.Name)

    # Central E bearing/clevis system now owns this revolute axis exclusively.
    for key in ('E1','E2'):
        for suffix in ('_1','__1'):
            for end in ('Pin','Bearing0','Bearing1','TorsoBearing','Spacer0','TorsoSpacer','Retainer0','Retainer1'):
                name=key+suffix+'_'+end
                if doc.getObject(name) is None: raise ValueError('Expected legacy E hardware '+name)
                b.motion.pop(name,None);doc.removeObject(name);retired.append(name)

    # Remove unsupported L6-era D bearings; the torso itself is the E-D link.
    dsource=b.ring('TORSO_D_JOURNAL_D1p9_L24_r12',1.9,0,24)
    grooves(b,dsource,24);dsource.Revision='r12'
    for key in ('D1','D2'):
        for side in (-1,1):
            pref=key+('_1' if side==1 else '__1')
            for end in ('Bearing1','Spacer0'):
                name=pref+'_'+end
                if doc.getObject(name) is None: raise ValueError('Expected orphan D hardware '+name)
                b.motion.pop(name,None);doc.removeObject(name);retired.append(name)
            move(pref+'_Pin',s[key],side*25.6,24,dsource)
            move(pref+'_Retainer'+('1' if side==1 else '0'),s[key],side*37.1,.6)

    # Four complete A/C stacks move their outer support inward by 1.6 per side.
    for key in ('A1','A2','C1','C2'):
        shaft=doc.getObject('Through'+key)
        _shaft(doc,shaft.LinkedObject,82.4,54.0 if key.startswith('A') else 67.2)
        move(shaft.Name,s[key],0,82.4)
        for side in (-1,1):
            pref=key+('_1' if side==1 else '__1')
            move(pref+'_Retainer'+('1' if side==1 else '0'),s[key],side*40.7,.6)
            cap=pref+('_CaptureCap' if key.startswith('A') else '_CaptureWasher')
            move(cap,s[key],side*40.8,2.4)
            if key.startswith('A'):
                move(pref+'_OuterBearing',s[key],side*38.6,1.2)
                inner=33.0 if key=='A1' else 31.2
                length=38.0-inner
                source=ring('A_OUTER_SPACER_L'+str(round(length,1))+'_r12',length)
                move(pref+'_OuterSpacer',s[key],side*(inner+38.0)/2,length,source)
            else:
                move(pref+'_Bearing2',s[key],side*38.6,1.2)
                spacer=[doc.getObject(pref+'_Spacer'+str(i)) for i in (0,1)]
                spacer=[o for o in spacer if abs(b.motion[o.Name]['length']-3.0)<1e-6]
                if len(spacer)!=1:raise RuntimeError('One outer C spacer required')
                move(spacer[0].Name,s[key],side*37.3,1.4,ring('C_OUTER_SPACER_L1p4_r12',1.4))
    liners=[]
    for obj in doc.Objects:
        if obj.TypeId=='App::Link' and obj.Name.startswith('GuideLiner'):
            old=obj.LinkPlacement;delta=-1.6 if old.Base.y>0 else 1.6
            new=App.Placement(old);new.Base.y+=delta;obj.LinkPlacement=new
            if obj.Name in b.motion:raise RuntimeError('Grounded liner has unexpected motion')
            changed.append(obj.Name);liners.append(obj.Name)
    if len(liners)!=8:raise RuntimeError('Expected 8 separate guide liners')
    doc.PoseController.MotionMap=json.dumps(b.motion)
    doc.recompute()
    used={o.LinkedObject.Name for o in doc.Objects if o.TypeId=='App::Link'}
    removed_sources=[]
    for source in list(b.library.Group):
        if source.Name in used:continue
        name=source.Name;children=[o.Name for o in getattr(source,'Group',[])]
        b.library.removeObject(source);doc.removeObject(name)
        for child in reversed(children):
            if doc.getObject(child):doc.removeObject(child)
        b.sources.pop(name,None);removed_sources.append(name)
    doc.recompute()
    report={'revision':'r12','frame':frame_report,'frame_source':frame.Name,
            'replaced_frame_source':original_source,'changed_existing':sorted(set(changed)),
            'retired_physical_instances':sorted(retired),'retired_unused_sources':removed_sources,
            'new_physical_instances':[], 'baseline_count':len(before),
            'physical_instance_count':sum(o.TypeId=='App::Link' for o in doc.Objects),
            'ground_transverse_span_mm':78.8,'previous_ground_transverse_span_mm':82.0,
            'housing_transverse_span_mm':56.8,'capture_transverse_span_mm':84.0,
            'E_support':'Central r10 bearing lug and torso clevis only; old lateral E journal system retired',
            'limits':'Metric reconstruction; strength, supplier fits, thrust and retention UNVERIFIED'}
    doc.PoseController.addProperty('App::PropertyString','CompactFrameR12','R12')
    doc.PoseController.CompactFrameR12=json.dumps(report)
    return report
