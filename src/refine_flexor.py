"""r02 physical stack refinement, integrated native frame, lead-only MCP."""
import FreeCAD as App,Part,Sketcher,math,json
from pathlib import Path
import cad_common as cc
from build_flexor import capsule,profile_part
from kinematics import spine
V=App.Vector

def pill_face(P,Q,W):
    L=math.dist(P,Q);u=((Q[0]-P[0])/L,(Q[1]-P[1])/L);v=(-u[1],u[0]);r=W/2
    def xy(x,y):return V(P[0]+x*u[0]+y*v[0],P[1]+x*u[1]+y*v[1],0)
    wire=Part.Wire([Part.makeLine(xy(0,-r),xy(L,-r)),Part.Arc(xy(L,-r),xy(L+r,0),xy(L,r)).toShape(),Part.makeLine(xy(L,r),xy(0,r)),Part.Arc(xy(0,r),xy(-r,0),xy(0,-r)).toShape()])
    return Part.Face(wire)

def rect(x,y,L,W):return Part.Face(Part.makePolygon([V(x,y,0),V(x+L,y,0),V(x+L,y+W,0),V(x,y+W,0),V(x,y,0)]))
def disk(x,y,r):return Part.Face(Part.Wire([Part.makeCircle(r,V(x,y,0))]))
def sketch_face(doc,body,name,face,z=0):
    sk=doc.addObject('Sketcher::SketchObject',name);body.addObject(sk);sk.Placement.Base.z=z
    for wire in face.Wires:
        for e in wire.Edges:
            if isinstance(e.Curve,Part.Circle) and e.isClosed():g=e.Curve
            elif isinstance(e.Curve,Part.Line):g=Part.LineSegment(e.Vertexes[0].Point,e.Vertexes[-1].Point)
            else:g=Part.ArcOfCircle(e.Curve,e.FirstParameter,e.LastParameter)
            j=sk.addGeometry(g,False);sk.addConstraint(Sketcher.Constraint('Block',j))
    return sk

def apply(b):
    doc=b.doc;p=b.p;s=spine(0,p);mm=json.loads(doc.PoseController.MotionMap)
    # Use normalized actual names on an earlier candidate as well as on fresh builds.
    import re
    mm={re.sub('[^A-Za-z0-9_]','_',n):m for n,m in mm.items()}
    def remove(o):
        mm.pop(o.Name,None);doc.removeObject(o.Name)
    # Replace overlapping fixed plates with one integrated native part per side.
    for o in list(doc.Objects):
        if o.TypeId=='App::Link' and (o.Name.startswith(('Backbone','MotorCradle','GuideFrame','GuideSupport','LumbarIntegrated')) or (o.Name.startswith('G') and o.Name.endswith('_Bearing0')) or (o.Name.startswith(('B1_','B2_')) and o.Name.endswith('_Pin'))):remove(o)
    a=p['spine_case_angle_rad'];c,st=math.cos(a),math.sin(a)
    case=rect(-12,-9,24,38).cut(rect(-10.4,-7.4,20.8,34.8));case.rotate(V(),V(0,0,1),math.degrees(a))
    solid=case.extrude(V(0,0,1.6))
    for A,B in [('E1','A1'),('A1','E2'),('E2','A2'),('A2','E1')]:solid=solid.fuse(pill_face(s[A],s[B],5).extrude(V(0,0,1.6)))
    solid=solid.cut(disk(0,0,6.5).extrude(V(0,0,1.6)))
    for n in ['A1','A2','E1','E2']:solid=solid.cut(disk(*s[n],2.025).extrude(V(0,0,1.6)))
    solid=solid.removeSplitter()
    print('base solid',solid.isValid(),len(solid.Solids))
    face=next(f for f in solid.Faces if f.BoundBox.ZLength<1e-7 and abs(f.CenterOfMass.z)<1e-7)
    body=doc.addObject('PartDesign::Body','FRM_LUMBAR_INTEGRATED_r02');cc.metadata(body,body.Name,'PA12','SLS nylon; integrated guide bosses; finish journal/slot fits');body.Revision='r02'
    sk=sketch_face(doc,body,'LumbarBaseOutline',face);pad=body.newObject('PartDesign::Pad','LumbarBasePad');pad.Profile=sk;pad.Length=1.6;doc.recompute();sk.Visibility=False
    ps=doc.addObject('Sketcher::SketchObject','GuidePostSections');body.addObject(ps)
    guidefaces=[]
    for i,sign in [(1,1),(2,-1)]:
        xs=[spine(j*math.tau/720,p)[f'C{i}'][0] for j in range(721)];xc=(min(xs)+max(xs))/2;zc=sign*p['guide_z_mm']
        for dx in [1.5*sign,4.5*sign]:cc.circle(ps,xc+dx,sign*2.5,1.4)
        f=pill_face((xc-6.5,zc),(xc+6.5,zc),8.2)
        # Fig 1A / Movie S2: the upper-left slot shares a tall outer ear
        # with fixed A2; the lower-right slot shares its ear with A1.
        # This is a structural journal/slot plate, not a capsule on posts.
        ax,az=s['A2' if i==1 else 'A1'];r=p['guide_pivot_radius_mm']
        pts=[V(xc-6.5,zc,0),V(xc+6.5,zc,0),V(ax+r,az,0),V(ax-r,az,0)]
        web=Part.Face(Part.makePolygon(pts+[pts[0]]))
        f=f.fuse(web).fuse(disk(ax,az,r)).removeSplitter()
        f=f.cut(pill_face((xc-6.5,zc),(xc+6.5,zc),5.2)).cut(disk(ax,az,2.025)).removeSplitter();guidefaces.append(f)
    posts=body.newObject('PartDesign::Pad','GuidePostsPad');posts.Profile=ps;posts.Length=11;posts.Reversed=True;doc.recompute();ps.Visibility=False;pad.Visibility=False
    gf=guidefaces[0].fuse(guidefaces[1]);gs=sketch_face(doc,body,'GuideBossProfiles',gf,-11)
    boss=body.newObject('PartDesign::Pad','GuideBossPad');boss.Profile=gs;boss.Length=1.6;boss.Reversed=True;doc.recompute();gs.Visibility=False;posts.Visibility=False
    b.library.addObject(body);b.sources[body.Name]=body
    # Negative side has the same X/Z profile and reflected axial feature stack.
    minus=doc.addObject('PartDesign::Body','FRM_LUMBAR_INTEGRATED_R_r02');cc.metadata(minus,minus.Name,'PA12','SLS nylon; mirrored axial stack');minus.Revision='r02'
    skm=sketch_face(doc,minus,'LumbarBaseOutlineR',face);pdm=minus.newObject('PartDesign::Pad','LumbarBasePadR');pdm.Profile=skm;pdm.Length=1.6;doc.recompute();skm.Visibility=False
    psm=doc.addObject('Sketcher::SketchObject','GuidePostSectionsR');minus.addObject(psm);psm.Placement.Base.z=1.6
    for g in ps.Geometry:
        j=psm.addGeometry(g,False);psm.addConstraint(Sketcher.Constraint('Block',j))
    ppm=minus.newObject('PartDesign::Pad','GuidePostsPadR');ppm.Profile=psm;ppm.Length=11;doc.recompute();psm.Visibility=False;pdm.Visibility=False
    gsm=sketch_face(doc,minus,'GuideBossProfilesR',gf,12.6);gbm=minus.newObject('PartDesign::Pad','GuideBossPadR');gbm.Profile=gsm;gbm.Length=1.6;doc.recompute();gsm.Visibility=False;ppm.Visibility=False
    b.library.addObject(minus);b.sources[minus.Name]=minus
    for side in [-1,1]:
        b.add(body if side==1 else minus,'LumbarIntegrated'+str(side),cc.plane_placement((0,0),side*27.6+.8),'Chassis')
        motor=doc.getObject('SpineMotor_1' if side==-1 else 'SpineMotor1');motor.LinkPlacement=App.Placement(V(0,side*p['motor_y_mm'],0),App.Rotation(V(0,-1,0),math.degrees(a)))
        name='DirectCrank_1' if side==-1 else 'DirectCrank1';m=mm[name];m['y']=side*29.1
        o=doc.getObject(name);o.LinkPlacement=cc.line_place(s['O'],s['G'],m['y'],5,1.2)
        # Source-reported 8mm crank drive pin, fixed to crank, rotates with phase.
        ret=doc.getObject('G_1_Retainer1' if side==-1 else 'G1_Retainer0')
        if ret:remove(ret)
        name='G_1_Pin' if side==-1 else 'G1_Pin';o=doc.getObject(name);o.LinkedObject.PartNumber='CRANK_PIN_D1p9_L8';o.LinkedObject.Revision='r02';o.LinkedObject.Tip.Length=8;o.LinkPlacement=cc.hardware_place(s['G'],side*30.6,8);mm[name]['length']=8
    for side in [-1,1]:
        name='G_1_Spacer1' if side==-1 else 'G1_Spacer0'
        o=doc.getObject(name)
        # New source avoids changing any other joint sharing a 0.6mm spacer definition.
        src=b.ring('G_CRANK_SPACER_L0p3',3,2.05,.3)
        o.setLink(src);o.LinkPlacement=cc.hardware_place(s['G'],side*29.85,.3)
        mm[name].update(y=side*29.85,length=.3)
    for name in ['SyncB1','SyncB2']:
        o=doc.getObject(name);o.LinkedObject.PartNumber='SYNC_SHAFT_D1p9_L70';o.LinkedObject.Revision='r02';o.LinkedObject.Tip.Length=70;o.LinkPlacement=cc.hardware_place(s['B'+name[-1]],0,70);mm[name]['length']=70
    crank=doc.getObject('DirectCrank1').LinkedObject;crank.MaterialName='steel';crank.Process='metal additive crank; finish bores; horn mounting UNVERIFIED';crank.Revision='r02'
    doc.PoseController.MotionMap=json.dumps(mm);b.motion=mm
    # Explicit material overrides are the actual FreeCAD Link API in this version.
    for o in doc.Objects:
        if o.TypeId!='App::Link':continue
        material=o.LinkedObject.MaterialName
        color=(.9,.9,.87) if o.Name.startswith('Link') else ((.12,.13,.15) if o.Name.startswith('Lumbar') else cc.COLORS.get(material,(.5,.5,.5)))
        mat=App.Material();mat.DiffuseColor=color;o.ViewObject.OverrideMaterial=True;o.ViewObject.ShapeAppearance=(mat,)
    b.library.Visibility=False
    for o in b.sources.values():o.Visibility=False
    # Retain only definitions that have physical instances in this revision.
    used={o.LinkedObject.Name for o in doc.Objects if o.TypeId=='App::Link'}
    b.sources={k:v for k,v in b.sources.items() if v.Name in used}
    for obsolete in list(b.library.Group):
        if obsolete.Name in used:continue
        oldname=obsolete.Name
        if obsolete.TypeId=='PartDesign::Body':
            for child in reversed(list(obsolete.Group)):doc.removeObject(child.Name)
        doc.removeObject(oldname)
    doc.recompute();print('integrated frame',body.Shape.isValid(),len(body.Shape.Solids),body.Shape.Volume)
    if doc.FileName:doc.save()
    return b
