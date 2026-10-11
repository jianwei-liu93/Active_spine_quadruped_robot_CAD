"""Positive axial capture for r02 journals: turned grooves and split clips.
Clip dimensions are engineering assumptions; supplier selection remains open.
"""
import FreeCAD as App,Part,Sketcher,json,math
import cad_common as cc
V=App.Vector

def clip_source(b):
    pn='RETAINING_CLIP_1p7x3p6_T0p6_PROVISIONAL'
    if pn in b.sources:return b.sources[pn]
    body=b.doc.addObject('PartDesign::Body',pn);cc.metadata(body,pn,'steel','spring steel split clip envelope; vendor/groove standard UNVERIFIED','HARDWARE');body.Revision='r02'
    sk=b.doc.addObject('Sketcher::SketchObject','ClipProfile');body.addObject(sk);a=math.pi/6;r=1.8;ri=.85
    for g in [Part.ArcOfCircle(Part.Circle(V(),V(0,0,1),r),a,math.tau-a),Part.LineSegment(V(r*math.cos(a),-r*math.sin(a),0),V(ri*math.cos(a),-ri*math.sin(a),0)),Part.ArcOfCircle(Part.Circle(V(),V(0,0,1),ri),a,math.tau-a),Part.LineSegment(V(ri*math.cos(a),ri*math.sin(a),0),V(r*math.cos(a),r*math.sin(a),0))]:
        j=sk.addGeometry(g,False);sk.addConstraint(Sketcher.Constraint('Block',j))
    pd=body.newObject('PartDesign::Pad','ClipPad');pd.Profile=sk;pd.Length=.6;b.doc.recompute();sk.Visibility=False;b.library.addObject(body);b.sources[pn]=body;return body

def grooves(b,source,length):
    """Annular pockets from z=.2 to .8 and z=L-.8 to L-.2."""
    body=source
    if 'HasEndGrooves' in body.PropertiesList:return
    base=body.Tip;base.Length=length;b.doc.recompute()
    for end,z in enumerate([.8,length-.2]):
        sk=b.doc.addObject('Sketcher::SketchObject',body.Name+'_Groove'+str(end));body.addObject(sk);sk.Placement.Base.z=z
        cc.circle(sk,0,0,1.05);cc.circle(sk,0,0,.85)
        pk=body.newObject('PartDesign::Pocket',body.Name+'_GroovePocket'+str(end));pk.Profile=sk;pk.Length=.6;b.doc.recompute();base.Visibility=False;sk.Visibility=False;base=pk
    body.addProperty('App::PropertyBool','HasEndGrooves');body.HasEndGrooves=True;body.Revision='r02'
    body.Process='turned 1.9mm journal; 1.7mm groove roots; provisional spring clip fit; inspect fatigue root'

def apply(b):
    doc=b.doc
    if 'RetainersRefined' in doc.PoseController.PropertiesList:return b
    mm=json.loads(doc.PoseController.MotionMap);clip=clip_source(b)
    pinlinks=[o for o in doc.Objects if o.TypeId=='App::Link' and (o.Name.endswith('_Pin') or o.Name in ['SyncB1','SyncB2'])]
    done=set()
    # Freeze original journal lengths before any shared definition receives pockets.
    original={o.Name:(mm[o.Name]['length'] if o.Name in mm else next(f.Length.Value for f in o.LinkedObject.Group if f.TypeId=='PartDesign::Pad')) for o in pinlinks}
    for o in pinlinks:
        src=o.LinkedObject;m=mm.get(o.Name);old=original[o.Name]
        length=8 if o.Name.startswith('G') else (72 if o.Name.startswith('SyncB') else old+1.6)
        if src.Name not in done:
            grooves(b,src,length);src.PartNumber='JOURNAL_D1p9_L'+str(round(length,2))+'_GROOVED';done.add(src.Name)
        # Static A/E journals are not in motion map; preserve actual center.
        center=o.LinkPlacement.multVec(V(0,0,old/2));P=(center.x,center.z);yc=center.y
        o.LinkPlacement=cc.hardware_place(P,yc,length)
        if m:m['length']=length
    for o in list(doc.Objects):
        if o.TypeId!='App::Link' or '_Retainer' not in o.Name:continue
        n=o.Name;side=-1 if '__1' in n or n.startswith('G_1_') or n.startswith('A1__1') or n.startswith('A2__1') or n.startswith('E1__1') or n.startswith('E2__1') else 1
        if n.startswith(('B1_','B2_')):
            inner=n.endswith('Retainer1' if side==-1 else 'Retainer0')
            if inner:mm.pop(n,None);doc.removeObject(n);continue
            yc=side*35.5
        elif n.startswith('G'):
            yc=side*34.1
        else:yc=mm[n]['y'] if n in mm else o.LinkPlacement.multVec(V(0,0,.3)).y
        P=o.LinkPlacement.multVec(V(0,0,.3));o.setLink(clip);o.LinkPlacement=cc.hardware_place((P.x,P.z),yc,.6)
        if n in mm:mm[n]['y']=yc;mm[n]['length']=.6
    doc.PoseController.MotionMap=json.dumps(mm);b.motion=mm
    doc.PoseController.addProperty('App::PropertyBool','RetainersRefined');doc.PoseController.RetainersRefined=True
    used={o.LinkedObject.Name for o in doc.Objects if o.TypeId=='App::Link'}
    b.sources={k:v for k,v in b.sources.items() if v.Name in used}
    for obsolete in list(b.library.Group):
        if obsolete.Name in used:continue
        if obsolete.TypeId=='PartDesign::Body':
            for ch in reversed(list(obsolete.Group)):doc.removeObject(ch.Name)
        doc.removeObject(obsolete.Name)
    b.library.Visibility=False
    for o in b.sources.values():o.Visibility=False
    doc.recompute()
    if doc.FileName:doc.save()
    print('grooved journals',len(done),'clip valid',clip.Shape.isValid(),len(clip.Shape.Solids))
    return b
