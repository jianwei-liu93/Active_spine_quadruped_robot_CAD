"""Lead-only native local-clevis / recessed-bar revision from Movie S1.

No new planar links, coordinate commands, implicit reflections or automatic saves.
Metric sections and bearing fits are engineering assumptions, not film dimensions.
Source datum (3,3) at first bore and legacy 6 x 1.2 pose frame are preserved.
"""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def parameters():
    return json.loads((ROOT/'parameters/assembly_r11.json').read_text())['spine_link_sections_r11']

def _finish(doc,body,feature,sketch,old):
    doc.recompute();sketch.Visibility=False
    if old:old.Visibility=False
    if not sketch.FullyConstrained or any('Invalid' in str(s) or 'Error' in str(s) for s in feature.State):
        raise RuntimeError(feature.Name+': failed native profile/feature')
    if feature.Shape.isNull() or not feature.Shape.isValid() or len(feature.Shape.Solids)!=1:
        raise RuntimeError(feature.Name+': not one valid native solid')
    return feature

def _pad(doc,body,label,face,z,depth,reverse=False):
    from refine_flexor import sketch_face
    old=body.Tip
    sk=sketch_face(doc,body,body.Name+'_'+label+'Sketch',face,z)
    pad=body.newObject('PartDesign::Pad',body.Name+'_'+label)
    pad.Profile=sk;pad.Length=depth;pad.Reversed=reverse
    return _finish(doc,body,pad,sk,old)

def _circles(doc,body,label,centers,z,depth,diameter):
    import cad_common as cc
    old=body.Tip;sk=body.newObject('Sketcher::SketchObject',body.Name+'_'+label+'Sketch')
    sk.Placement.Base.z=z
    for x,y in centers:cc.circle(sk,x,y,diameter/2)
    cut=body.newObject('PartDesign::Pocket',body.Name+'_'+label)
    cut.Profile=sk;cut.Length=depth
    return _finish(doc,body,cut,sk,old)

def fork(b,name,length,side,layer,cfg):
    import FreeCAD as App
    import cad_common as cc
    from refine_flexor import pill_face,rect
    doc=b.doc
    if doc.getObject(name):raise ValueError('Duplicate native fork source: '+name)
    body=doc.addObject('PartDesign::Body',name)
    cc.metadata(body,name,'PA12','SLS PA12 local clevis; finish bores; leaf/bridge strength, fits and bearing retention UNVERIFIED')
    body.Revision='r11';b.library.addObject(body);b.sources[name]=body
    w=cfg['outline_width_mm'];t=cfg['base_leaf_mm'];leaf=cfg['fork_leaf_mm']
    depth=cfg['fork_opening_depth_from_pivot_mm'];reach=cfg['fork_bridge_end_from_pivot_mm']
    _pad(doc,body,'MainCheek',pill_face((3,3),(length+3,3),w),0,t)
    section={}
    for end,target in (('A',cfg['A_added_cheek_abs_y_mm']),('B',cfg['B_added_cheek_abs_y_mm'])):
        # Legacy local +Z maps to world -Y on both sides; handed geometry,
        # rather than a negative instance scale, supplies the axial sections.
        zc=t/2+side*(layer-target);lo,hi=zc-leaf/2,zc+leaf/2
        if end=='A':
            face=pill_face((3,3),(3+reach,3),w)
            web=rect(3+depth,3-w/2,reach-depth,w)
        else:
            face=pill_face((length+3-reach,3),(length+3,3),w)
            web=rect(length+3-reach,3-w/2,reach-depth,w)
        if lo<0:_pad(doc,body,end+'Bridge',web,0,-lo,True)
        else:_pad(doc,body,end+'Bridge',web,t,hi-t)
        _pad(doc,body,end+'AddedCheek',face,lo,leaf)
        section[end]={'added_cheek_local_z_bounds_mm':[lo,hi],
                      'added_cheek_world_abs_y_mm':target,'opening_depth_from_pivot_mm':depth}
    _circles(doc,body,'CoaxialBearingBores',[(3,3),(length+3,3)],15,30,cfg['link_bore_mm'])
    body.addProperty('App::PropertyString','SectionContract','R11');body.SectionContract=json.dumps(section)
    body.addProperty('App::PropertyLength','CenterDistance','R11');body.CenterDistance=length
    return body

def long_link(b,cfg):
    import Part,Sketcher
    import cad_common as cc
    from build_flexor import capsule
    from spine_bar_profile_r10 import rounded_rectangle_geometry
    doc=b.doc;body=doc.getObject('SPN_r02_L4');length=b.p['L4_mm'];w=cfg['outline_width_mm']
    profile=doc.getObject(body.Name+'_Profile');bores=doc.getObject(body.Name+'_Cuts')
    for sk in (profile,bores):
        for j in range(sk.GeometryCount-1,-1,-1):sk.delGeometry(j)
    # The wider physical profile stays centered on the legacy (3,3) bore datum.
    capsule(profile,3-w/2,3-w/2,length+w,w)
    for x in (3,length+3):cc.circle(bores,x,3,cfg['link_bore_mm']/2)
    doc.recompute()
    old=body.Tip;sk=body.newObject('Sketcher::SketchObject',body.Name+'_BlindReliefSketch')
    sk.Placement.Base.z=cfg['base_leaf_mm']
    inset=cfg['relief_end_inset_mm'];rw=cfg['relief_width_mm']
    for g in rounded_rectangle_geometry(3+inset,3-rw/2,length-2*inset,rw,cfg['relief_corner_radius_mm']):
        i=sk.addGeometry(g,False);sk.addConstraint(Sketcher.Constraint('Block',i))
    cut=body.newObject('PartDesign::Pocket',body.Name+'_BlindRelief')
    cut.Profile=sk;cut.Length=cfg['long_relief_depth_mm']
    _finish(doc,body,cut,sk,old)
    body.PartNumber='SPN_LONG_BC_RECESSED_r11';body.Revision='r11'
    body.Process='SLS PA12 recessed B-C bar; blind 0.6 mm pocket retains 0.6 mm floor; bores finish-machined; strength/fits UNVERIFIED'
    return body

def _shaft(doc,source,length,span):
    # Preserve its native identity, end-groove sections and source origin.
    pads=[o for o in source.Group if o.TypeId=='PartDesign::Pad']
    main=pads[0];shoulder=pads[-1]
    main.Length=length
    groove_sketches=[o for o in source.Group if o.TypeId=='Sketcher::SketchObject' and '_Groove1' in o.Name]
    if len(groove_sketches)!=1:raise RuntimeError('Expected one native outer groove sketch')
    groove_sketches[0].Placement.Base.z=length-.2
    shoulder_profile=shoulder.Profile[0] if isinstance(shoulder.Profile,tuple) else shoulder.Profile
    shoulder_profile.Placement.Base.z=(length-span)/2;shoulder.Length=span
    source.Revision='r11';source.PartNumber=source.Name+'_R11'
    source.Process='turned stepped journal; r11 clevis stack; nominal inner-race spacers; vendor groove/clip/fit/thrust UNVERIFIED'
    doc.recompute()
    if not source.Shape.isValid() or len(source.Shape.Solids)!=1:raise RuntimeError('Revised shaft invalid')

def apply(b):
    import FreeCAD as App
    import cad_common as cc
    from kinematics import spine
    cfg=parameters();doc=b.doc
    if 'LinkSectionsR11' in doc.PoseController.PropertiesList:raise ValueError('r11 already integrated')
    before={o.Name:tuple(o.LinkPlacement.toMatrix().A) for o in doc.Objects if o.TypeId=='App::Link'}
    old_map=json.loads(doc.PoseController.MotionMap);b.motion=dict(old_map)
    state=spine(float(doc.PoseController.SpinePhaseRad),b.p)
    changed=[];new=[];records=[]
    for obj in list(doc.Objects):
        if obj.TypeId!='App::Link' or not obj.Name.startswith('Link') or '_L3_' not in obj.Name:continue
        m=b.motion[obj.Name];side=1 if m['y']>0 else -1;branch=1 if m['a']=='A1' else 2
        name='SPN_AB_LOCAL_FORK_r11_B'+str(branch)+('_POS' if side>0 else '_NEG')
        source=fork(b,name,b.p['L3_mm'],side,abs(m['y']),cfg)
        obj.setLink(source);changed.append(obj.Name)
        records.append({'instance':obj.Name,'source':source.Name,'motion':m,'section':json.loads(source.SectionContract)})
    long_link(b,cfg)
    changed += [o.Name for o in doc.Objects if o.TypeId=='App::Link' and o.LinkedObject.Name=='SPN_r02_L4']
    bearing=doc.getObject('BRG_2x4x1p2_PROVISIONAL')
    spacer=doc.getObject('SPACER_2mm_L0_6')
    if bearing is None or spacer is None:raise RuntimeError('Expected retained bearing/spacer native definitions')
    for branch in (1,2):
        A='A'+str(branch);B='B'+str(branch)
        shaft=doc.getObject('Through'+A);_shaft(doc,shaft.LinkedObject,85.6,cfg['A_shoulder_span_mm']);changed.append(shaft.Name)
        shaft=doc.getObject('Sync'+B);L=cfg['B_shaft_length_mm']
        _shaft(doc,shaft.LinkedObject,L,cfg['B_shoulder_span_mm'])
        shaft.LinkPlacement=cc.hardware_place(state[B],0,L);b.motion[shaft.Name].update(y=0,length=L);changed.append(shaft.Name)
        for side in (-1,1):
            suffix='1' if side==1 else '_1'
            for key,kind,source,y,t in ((A,'ForkInnerBearing',bearing,cfg['A_added_cheek_abs_y_mm'],1.2),
                                      (B,'ForkOuterBearing',bearing,cfg['B_added_cheek_abs_y_mm'],1.2),
                                      (A,'ForkInnerSpacer',spacer,cfg['A_inner_spacer_abs_y_mm'],.6),
                                      (B,'ForkOuterSpacer',spacer,cfg['B_outer_spacer_abs_y_mm'],.6)):
                name=key+'_'+suffix+'_'+kind
                desc={'kind':'point','point':key,'y':side*y,'length':t}
                obj=b.add(source,name,cc.hardware_place(state[key],side*y,t),'SpineHardware',desc);new.append(obj.Name)
            ret=doc.getObject(B+'_'+suffix+'_Retainer'+('1' if side==1 else '0'))
            ret.LinkPlacement=cc.hardware_place(state[B],side*cfg['B_retainer_abs_y_mm'],.6)
            b.motion[ret.Name].update(y=side*cfg['B_retainer_abs_y_mm'],length=.6);changed.append(ret.Name)
    used={o.LinkedObject.Name for o in doc.Objects if o.TypeId=='App::Link'}
    retired=[]
    for source in list(b.library.Group):
        if source.Name=='SPN_r02_L3' and source.Name not in used:
            obsolete_name=source.Name;retired.append(obsolete_name)
            for child in reversed(list(source.Group)):doc.removeObject(child.Name)
            doc.removeObject(obsolete_name);b.sources.pop(obsolete_name,None)
    doc.PoseController.MotionMap=json.dumps(b.motion)
    doc.PoseController.addProperty('App::PropertyString','LinkSectionsR11','R11')
    report={'revision':'r11','classification':'RECONSTRUCTED_CANDIDATE_NOT_FABRICATION_RELEASE',
            'changed_existing':sorted(changed),'new_instances':sorted(new),'retired_sources':retired,
            'retired_physical_instances':[],'fork_sections':records,'parameters':cfg,
            'preserved_source_frame':'first pivot (3,3), local +Z -> world -Y; MotionMap 6 x 1.2 frame unchanged',
            'long_relief':'blind pocket with retained floor; through bores are separate native feature',
            'joint_stack':'A local fork encloses fixed ground lug; B local fork encloses independent incident members; added cheek bearings and inner-race spacers; bearing outer-race retention/fits/thrust remain UNVERIFIED'}
    doc.PoseController.LinkSectionsR11=json.dumps(report)
    for source in b.library.Group:source.Visibility=False
    b.library.Visibility=False;doc.recompute()
    for n,P in before.items():
        if n not in changed and tuple(doc.getObject(n).LinkPlacement.toMatrix().A)!=P:raise RuntimeError('Unrelated placement changed: '+n)
    return report

def resume(doc):
    """Explicit existing-document integration context; no new document/groups."""
    from build_flexor import FlexorBuilder
    import robot_pose_r03
    b=FlexorBuilder.__new__(FlexorBuilder);b.doc=doc;b.p=robot_pose_r03._parameters(doc)
    b.library=doc.PartsLibrary;b.assembly=doc.RobotAssembly
    b.sources={o.Name:o for o in b.library.Group}
    b.motion=json.loads(doc.PoseController.MotionMap)
    b.groups={name:doc.getObject(name) for name in ('SpineHardware','SpineLinks')}
    return b
