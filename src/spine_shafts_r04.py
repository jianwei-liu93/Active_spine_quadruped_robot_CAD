"""Movie S1 58-60s transverse A/B/C members, native stepped journals.
Visible continuity is source evidence. All diameters, shoulders, cap recesses
and clip fits below are DESIGN_ASSUMPTION, not recovered machining drawings.
No extra planar linkage is introduced: A fixed, B/C share existing point motion.
"""
import json
import FreeCAD as App
import cad_common as cc
from kinematics import spine
from retain_flexor import grooves
from spine_attachments_r02 import _pad
from refine_flexor import disk

def stepped(b,pn,length,shoulder_span):
    if pn in b.sources:return b.sources[pn]
    body=b.ring(pn,1.9,0,length);grooves(b,body,length)
    _pad(b,body,pn+'_CenterShoulder',disk(0,0,1.8),(length-shoulder_span)/2,shoulder_span)
    body.Revision='r04';body.Process='turned steel stepped cross-shaft; clip standard and stiffness UNVERIFIED'
    return body

def cap(b,side):
    pn='SPINE_r04_CAPTURE_CAP_'+('POS' if side==1 else 'NEG')
    if pn in b.sources:return b.sources[pn]
    body=b.ring(pn,6,2.05,.6)
    if side==1:
        # cc.hardware_place points local +Z inward on positive-Y side.
        body.Group[0].Placement.Base.z=1.8;b.doc.recompute()
        _pad(b,body,pn+'_ClipCavityWall',disk(0,0,2.5).cut(disk(0,0,1.9)),1.8,1.8,True)
    else:_pad(b,body,pn+'_ClipCavityWall',disk(0,0,2.5).cut(disk(0,0,1.9)),.6,1.8)
    body.Revision='r04';body.Process='candidate silver capture collar; shoulder plus recessed split clip; exact source nut/thread/retention interface UNKNOWN'
    return body

def apply(b):
    d=b.doc;s=spine(d.PoseController.SpinePhaseRad,b.p)
    if 'MovieS1Shafts' in d.PoseController.PropertiesList:raise RuntimeError('Transverse shafts already integrated')
    removed=[];added=[]
    for key in ('A1','A2','C1','C2'):
        moving=key.startswith('C');length=85.6;span=67.2 if moving else 54.0
        src=stepped(b,'SPINE_r04_'+key+'_STEPPED_CROSS_SHAFT_L85p6',length,span)
        o=b.add(src,'Through'+key,cc.hardware_place(s[key],0,length),'SpineHardware',{'kind':'point','point':key,'y':0,'length':length} if moving else None);added.append(o.Name)
        for side in (-1,1):
            prefix=key+'_'+str(side).replace('-','_')
            for suffix in ('_Pin','_Retainer'+('0' if side==1 else '1')):
                old=d.getObject(prefix+suffix)
                if old:b.motion.pop(old.Name,None);removed.append(old.Name);d.removeObject(old.Name)
            outer=d.getObject(prefix+'_Retainer'+('1' if side==1 else '0'))
            outer.LinkPlacement=cc.hardware_place(s[key],side*42.3,.6)
            if moving:b.motion[outer.Name].update(y=side*42.3,length=.6)
            capture=cap(b,side)
            old=d.getObject(prefix+'_CaptureWasher') if moving else None
            place=cc.hardware_place(s[key],side*42.4,2.4)
            if old:
                old.setLink(capture);old.LinkPlacement=place;b.motion[old.Name].update(y=side*42.4,length=2.4)
            else:
                o=b.add(capture,prefix+'_CaptureCap',place,'SpineHardware');added.append(o.Name)
    # B shafts already join both copies. Add a visible larger central shoulder.
    for key in ('B1','B2'):
        old=d.getObject('Sync'+key)
        src=stepped(b,'SPINE_r04_'+key+'_STEPPED_CROSS_SHAFT_L72',72,60)
        old.setLink(src);old.LinkPlacement=cc.hardware_place(s[key],0,72)
        b.motion[old.Name].update(y=0,length=72)
    d.PoseController.addProperty('App::PropertyString','MovieS1Shafts')
    report={'source':'Movie S1 58-60s; supplementary fabrication text pp16-17','axes':{'A1/A2':'fixed Y cross-shafts','B1/B2':'existing B point translations','C1/C2':'existing horizontal slider translations'},'introduced_planar_edges':[], 'added_instances':added,'removed_instances':removed,'dimensions':'all selected engineering assumptions','limits':'Unverified catalog retention, press fits, fatigue, strength and sampled motion clearance'}
    d.PoseController.MovieS1Shafts=json.dumps(report);d.PoseController.MotionMap=json.dumps(b.motion)
    for src in b.sources.values():src.Visibility=False
    d.recompute();return report
