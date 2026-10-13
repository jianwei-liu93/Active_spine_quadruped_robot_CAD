"""Organic A-B rocker with one B-end terminal fork and recessed B-C bars."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]


def apply(b, config=None):
    import Sketcher
    import cad_common as cc
    from build_flexor import capsule
    from spine_bar_profile_r10 import rounded_rectangle_geometry
    doc=b.doc;cfg=(config or json.loads((ROOT/'parameters/assembly_r12.json').read_text()))['spine_bar_r12']
    w=cfg['outline_width_mm'];result=[]
    for key in ('L4',):
        if doc.getObject('SPN_r02_L4_BlindReliefR12'):continue
        body=doc.getObject('SPN_r02_'+key);length=b.p[key+'_mm']
        sk=doc.getObject(body.Name+'_Profile')
        for i in range(sk.GeometryCount-1,-1,-1):sk.delGeometry(i)
        capsule(sk,3-w/2,3-w/2,length+w,w)
        bore=doc.getObject(body.Name+'_Cuts')
        for i in range(bore.GeometryCount-1,-1,-1):bore.delGeometry(i)
        for x in (3,length+3):cc.circle(bore,x,3,cfg['link_bore_mm']/2)
        doc.recompute()
        if key=='L4':
            previous=body.Tip
            pocket_sk=body.newObject('Sketcher::SketchObject',body.Name+'_BlindReliefR12Sketch')
            pocket_sk.Placement.Base.z=cfg['thickness_mm']
            inset=cfg['long_relief_end_inset_mm'];rw=cfg['long_relief_width_mm']
            for g in rounded_rectangle_geometry(3+inset,3-rw/2,length-2*inset,rw,cfg['long_relief_corner_radius_mm']):
                j=pocket_sk.addGeometry(g,False);pocket_sk.addConstraint(Sketcher.Constraint('Block',j))
            pocket=body.newObject('PartDesign::Pocket',body.Name+'_BlindReliefR12')
            pocket.Profile=pocket_sk;pocket.Length=cfg['long_relief_depth_mm']
            doc.recompute();pocket_sk.Visibility=False;previous.Visibility=False
        body.PartNumber='SPN_'+('AB_CONTINUOUS' if key=='L3' else 'BC_RECESSED')+'_r12'
        body.Revision='r12';body.Process='SLS PA12 continuous single-leaf bar; finish bores; strength/fit/retention UNVERIFIED'
        sk.Visibility=False;bore.Visibility=False
        if not body.Shape.isValid() or len(body.Shape.Solids)!=1:raise RuntimeError(body.Name+' invalid')
        if not all(o.FullyConstrained for o in body.Group if o.TypeId=='Sketcher::SketchObject'):raise RuntimeError('Unconstrained bar')
        result.append({'source':body.Name,'part_number':body.PartNumber,'instances':[o.Name for o in doc.Objects if o.TypeId=='App::Link' and o.LinkedObject==body],
                       'center_distance_mm':length,'width_mm':w,'thickness_mm':1.2,'local_bores_mm':[[3,3],[length+3,3]]})
    terminal=terminals(b,cfg)
    terminal['bars']=result
    doc.PoseController.addProperty('App::PropertyString','BarDetailR12','R12')
    doc.PoseController.BarDetailR12=json.dumps(terminal)
    return terminal


def terminals(b,cfg):
    import cad_common as cc
    from refine_flexor import pill_face,rect
    from spine_link_sections_r11 import _pad,_circles
    from compact_spine_stack_r12 import _shaft
    from kinematics import spine
    doc=b.doc;s=spine(float(doc.PoseController.SpinePhaseRad),b.p)
    length=b.p['L3_mm'];w=cfg['outline_width_mm'];t=1.2
    whole=organic_face(length,w,cfg['waist_width_mm'])
    changed=[];new=[];records=[]
    for obj in list(doc.Objects):
        if obj.TypeId!='App::Link' or not obj.Name.startswith('Link') or '_L3_' not in obj.Name:continue
        m=b.motion[obj.Name];side=1 if m['y']>0 else -1;layer=abs(m['y']);branch=1 if m['a']=='A1' else 2
        name='SPN_AB_TERMINAL_r12_B'+str(branch)+('_POS' if side>0 else '_NEG')
        body=doc.addObject('PartDesign::Body',name)
        cc.metadata(body,name,'PA12','SLS PA12 compact terminal fork; finish bores; fits, retention and strength UNVERIFIED')
        body.Revision=cfg.get('component_revision','r12')
        if body.Revision!='r12':body.PartNumber=name.replace('_r12','_'+body.Revision)
        b.library.addObject(body);b.sources[body.Name]=body
        _pad(doc,body,'ContinuousWeb',whole,0,t)
        sections={}
        reach=cfg['terminal_reach_mm'];depth=cfg['terminal_opening_depth_mm']
        for end,target in (('B',cfg['B_added_cheek_abs_y_mm']),):
            zc=t/2+side*(layer-target);lo,hi=zc-t/2,zc+t/2
            if end=='A':
                face=whole.common(rect(3-w/2,3-w/2,reach+w/2,w))
                web=rect(3+depth,3-w/2,reach-depth,w)
            else:
                face=whole.common(pill_face((length+3-(reach-w/2),3),(length+3,3),w))
                web=face.common(rect(length+3-reach,3-w/2,reach-depth,w))
            if lo<0:_pad(doc,body,end+'TerminalBridge',web,0,-lo,True)
            else:_pad(doc,body,end+'TerminalBridge',web,t,hi-t)
            _pad(doc,body,end+'TerminalLeaf',face,lo,t)
            sections[end]={'added_cheek_local_z_bounds_mm':[lo,hi],
                           'added_cheek_world_abs_y_mm':target,
                           'opening_depth_from_pivot_mm':depth,'maximum_inward_reach_mm':reach}
        _circles(doc,body,'CoaxialBores',[(3,3),(length+3,3)],15,30,cfg['link_bore_mm'])
        body.addProperty('App::PropertyLength','CenterDistance','R12');body.CenterDistance=length
        body.addProperty('App::PropertyString','SectionContract','R12');body.SectionContract=json.dumps(sections)
        obj.setLink(body);changed.append(obj.Name)
        records.append({'instance':obj.Name,'source':body.Name,'section':sections,'motion':m})
    bearing=doc.getObject('BRG_2x4x1p2_PROVISIONAL');spacer=doc.getObject('SPACER_2mm_L0_6')
    if bearing is None or spacer is None:raise RuntimeError('Retained small bearing/spacer sources required')
    for branch in (1,2):
        A='A'+str(branch);B='B'+str(branch)
        shaft=doc.getObject('Through'+A);_shaft(doc,shaft.LinkedObject,82.4,54.0);changed.append(shaft.Name)
        shaft=doc.getObject('Sync'+B);_shaft(doc,shaft.LinkedObject,76,60)
        shaft.LinkPlacement=cc.hardware_place(s[B],0,76);b.motion[shaft.Name].update(y=0,length=76);changed.append(shaft.Name)
        for side in (-1,1):
            pref='_1' if side==1 else '__1'
            for key,label,source,y,thick in ((B,'ForkOuterBearing',bearing,36,1.2),(B,'ForkOuterSpacer',spacer,36.9,.6)):
                name=key+pref+'_'+label
                o=b.add(source,name,cc.hardware_place(s[key],side*y,thick),'SpineHardware',
                        {'kind':'point','point':key,'y':side*y,'length':thick})
                new.append(o.Name)
            name=B+pref+'_Retainer'+('1' if side==1 else '0')
            o=doc.getObject(name);o.LinkPlacement=cc.hardware_place(s[B],side*37.5,.6)
            b.motion[name].update(y=side*37.5,length=.6);changed.append(name)
    old=doc.getObject('SPN_r02_L3')
    if old and not any(o.TypeId=='App::Link' and o.LinkedObject==old for o in doc.Objects):
        children=[o.Name for o in old.Group];b.library.removeObject(old);doc.removeObject(old.Name)
        for child in reversed(children):
            if doc.getObject(child):doc.removeObject(child)
        b.sources.pop('SPN_r02_L3',None)
    doc.PoseController.MotionMap=json.dumps(b.motion);doc.recompute()
    return {'revision':'r12','changed_existing':sorted(changed)+[o.Name for o in doc.Objects if o.TypeId=='App::Link' and o.LinkedObject.Name=='SPN_r02_L4'],
            'new_instances':sorted(new),'terminal_sections':records,'parameters':cfg,
            'source_evidence':'Movie S1 54–55 s and latest user close-up: B-end fork only, single-eye A; metric organic section assumed',
            'frame_convention':'Legacy (3,3) datum and 6x1.2 placement frame retained',
            'limits':'Terminal fork morphology revised; no capacity, fit, race-retention or fabrication qualification'}


def organic_face(length,width,waist):
    """Four tangent circular arcs: round eyes, smooth concave waist, no splines.

    The sides are circles externally tangent to both end-eye circles. Source
    first eye stays (3,3); the neck width is independent of the pose frame.
    """
    import FreeCAD as App, Part
    if not 0<waist<width or length<=width:raise ValueError('Invalid organic rocker section')
    radius=width/2;half=waist/2;dx=length/2
    cy=(dx*dx-(radius-half)**2)/(2*(radius-half))
    sr=cy-half;scale=radius/(sr+radius)
    tx=scale*dx;ty=scale*cy
    V=lambda x,y:App.Vector(x+3,y+3,0)
    a,b,c,d=V(tx,ty),V(length-tx,ty),V(length-tx,-ty),V(tx,-ty)
    edges=[Part.Arc(a,V(length/2,half),b).toShape(),
           Part.Arc(b,V(length+radius,0),c).toShape(),
           Part.Arc(c,V(length/2,-half),d).toShape(),
           Part.Arc(d,V(-radius,0),a).toShape()]
    return Part.Face(Part.Wire(edges))
