"""Native feature factories. Part-local XY section, Pad along +Z.
Fully constrained dimensional sketches; no face-mapped references.
"""
import FreeCAD as App, Part, Sketcher, math
V=App.Vector
COLORS={'PA12':(0.25,0.44,0.58),'steel':(0.67,0.7,0.74),'brass':(0.8,0.59,0.22),'copper':(0.8,0.59,0.22),'rubber':(0.12,0.13,0.15),'motor':(0.21,0.22,0.25),'cable':(0.95,0.65,0.15),'spring':(0.55,0.65,0.75)}

def metadata(o,pn,material,process,role='CUSTOM'):
    for n,val in [('PartNumber',pn),('Revision','r01'),('MaterialName',material),('Process',process),('ReleaseStatus','PROVISIONAL'),('Role',role)]:
        o.addProperty('App::PropertyString',n,'Identity'); setattr(o,n,val)
    o.ViewObject.ShapeColor=COLORS.get(material,COLORS['PA12'])
    return o

def rectangle(sk,x,y,L,W):
    pts=[V(x,y,0),V(x+L,y,0),V(x+L,y+W,0),V(x,y+W,0)]
    for i in range(4):sk.addGeometry(Part.LineSegment(pts[i],pts[(i+1)%4]),False)
    for i in range(4):sk.addConstraint(Sketcher.Constraint('Coincident',i,2,(i+1)%4,1))
    for i in (0,2):sk.addConstraint(Sketcher.Constraint('Horizontal',i))
    for i in (1,3):sk.addConstraint(Sketcher.Constraint('Vertical',i))
    sk.addConstraint(Sketcher.Constraint('Distance',0,L))
    sk.addConstraint(Sketcher.Constraint('Distance',1,W))
    if abs(x)<1e-10 and abs(y)<1e-10:sk.addConstraint(Sketcher.Constraint('Coincident',0,1,-1,1))
    else:
        sk.addConstraint(Sketcher.Constraint('DistanceX',0,1,x))
        sk.addConstraint(Sketcher.Constraint('DistanceY',0,1,y))


def circle(sk,x,y,r):
    i=sk.addGeometry(Part.Circle(V(x,y,0),V(0,0,1),r),False)
    sk.addConstraint(Sketcher.Constraint('Radius',i,r))
    if abs(x)<1e-10 and abs(y)<1e-10:sk.addConstraint(Sketcher.Constraint('Coincident',i,3,-1,1))
    elif abs(y)<1e-10:
        sk.addConstraint(Sketcher.Constraint('DistanceX',i,3,x));sk.addConstraint(Sketcher.Constraint('DistanceY',i,3,0.0))
    elif abs(x)<1e-10:
        sk.addConstraint(Sketcher.Constraint('DistanceX',i,3,0.0));sk.addConstraint(Sketcher.Constraint('DistanceY',i,3,y))
    else:
        sk.addConstraint(Sketcher.Constraint('DistanceX',i,3,x));sk.addConstraint(Sketcher.Constraint('DistanceY',i,3,y))
    return i

def plate(doc,name,L,W,T,holes=(),material='PA12',pn=None):
    b=doc.addObject('PartDesign::Body',name)
    metadata(b,pn or name,material,'SLS PA12; finish critical bores' if material=='PA12' else 'machined')
    sk=doc.addObject('Sketcher::SketchObject',name+'_Profile');b.addObject(sk)
    rectangle(sk,0,0,L,W)
    for key,v in [('SectionLength',L),('SectionWidth',W)]:
        sk.addProperty('App::PropertyLength',key,'Dimensions');setattr(sk,key,v)
    sk.setExpression('Constraints[8]','SectionLength')
    sk.setExpression('Constraints[9]','SectionWidth')
    pad=b.newObject('PartDesign::Pad',name+'_Pad');pad.Profile=sk;pad.Length=T
    sk.Visibility=False
    doc.recompute()
    if holes:
        hs=doc.addObject('Sketcher::SketchObject',name+'_Bores');b.addObject(hs)
        hs.Placement.Base.z=T;hs.setExpression('Placement.Base.z',pad.Name+'.Length')
        for h in holes:
            x,y,dia=h[:3]
            if len(h)==4:d_profile(hs,x,y,dia/2,h[3])
            else:circle(hs,x,y,dia/2)
        pocket=b.newObject('PartDesign::Pocket',name+'_Pocket');pocket.Profile=hs;pocket.Length=T
        pocket.setExpression('Length',pad.Name+'.Length');doc.recompute();hs.Visibility=False;pad.Visibility=False
    b.Tip.Visibility=True
    return b

def ring(doc,name,od,id_,length,material='steel',pn=None):
    b=doc.addObject('PartDesign::Body',name);metadata(b,pn or name,material,'purchased envelope' if material=='steel' else 'machined',role='HARDWARE')
    sk=doc.addObject('Sketcher::SketchObject',name+'_Section');b.addObject(sk)
    circle(sk,0,0,od/2)
    if id_:circle(sk,0,0,id_/2)
    pad=b.newObject('PartDesign::Pad',name+'_Pad');pad.Profile=sk;pad.Length=length
    doc.recompute();sk.Visibility=False
    return b

def instance(doc,source,name,placement):
    o=doc.addObject('App::Link',name);o.setLink(source);o.LinkPlacement=placement
    if 'ShapeColor' in o.ViewObject.PropertiesList:o.ViewObject.ShapeColor=source.ViewObject.ShapeColor
    return o

def plane_placement(point,y,angle=0):
    c,s=math.cos(angle),math.sin(angle)
    rot=App.Rotation(V(c,0,s),V(-s,0,c),V(0,-1,0),'ZXY')
    return App.Placement(V(point[0],y,point[1]),rot)

def line_place(P,Q,y,width,thickness):
    a=math.atan2(Q[1]-P[1],Q[0]-P[0]);c,s=math.cos(a),math.sin(a)
    # plate starts half-width before pivot, half-width below centerline
    p=(P[0]-width/2*c+width/2*s,P[1]-width/2*s-width/2*c)
    return plane_placement(p,y+thickness/2,a)

def hardware_place(point,y,length):return plane_placement(point,y+length/2)

def simple_shape(doc,name,shape,material,process,pn=None,role='ENVELOPE'):
    o=doc.addObject('PartDesign::Feature',name);o.Shape=shape
    metadata(o,pn or name,material,process,role)
    return o

def gear(doc,name,module,teeth,pressure,T,bore):
    """Native pad of sampled involute teeth, straight-sided root transitions.
    6 involute samples per flank; review geometry, no gear-load certification.
    """
    rp=module*teeth/2;rb=rp*math.cos(pressure);ra=rp+module;rf=rp-1.25*module
    inv=lambda r: math.sqrt(max((r/rb)**2-1,0))-math.acos(min(rb/r,1))
    phi=math.pi/(2*teeth)+inv(rp)
    pts=[]
    for t in range(teeth):
        a=t*math.tau/teeth
        for side,rs in [(-1,[rf]+[rb+(ra-rb)*j/5 for j in range(6)]),(1,[rb+(ra-rb)*j/5 for j in range(5,-1,-1)]+[rf])]:
            for r in rs:
                q=a+side*(phi-inv(max(r,rb)));pts.append(V(r*math.cos(q),r*math.sin(q),0))
    b=doc.addObject('PartDesign::Body',name);metadata(b,name,'PA12','SLS PA12 prototype gear; tooth/root finishing review required')
    sk=doc.addObject('Sketcher::SketchObject',name+'_Involute');b.addObject(sk)
    for i in range(len(pts)):
        g=sk.addGeometry(Part.LineSegment(pts[i],pts[(i+1)%len(pts)]),False);sk.addConstraint(Sketcher.Constraint('Block',g))
    d_profile(sk,0,0,bore/2,1.50)
    pad=b.newObject('PartDesign::Pad',name+'_Pad');pad.Profile=sk;pad.Length=T;doc.recompute();sk.Visibility=False
    for n,v in [('Module',module),('PressureAngleRad',pressure)]:b.addProperty('App::PropertyFloat',n,'Gear');setattr(b,n,v)
    b.addProperty('App::PropertyInteger','Teeth','Gear');b.Teeth=teeth
    return b


def d_profile(sk,x,y,r,flat):
    a=math.acos(flat/r);h=math.sqrt(r*r-flat*flat)
    g=sk.addGeometry(Part.ArcOfCircle(Part.Circle(V(x,y,0),V(0,0,1),r),a,math.tau-a),False)
    sk.addConstraint(Sketcher.Constraint('Block',g))
    g=sk.addGeometry(Part.LineSegment(V(x+flat,y-h,0),V(x+flat,y+h,0)),False)
    sk.addConstraint(Sketcher.Constraint('Block',g))

def d_shaft(doc,name,diameter,flat,length):
    b=doc.addObject('PartDesign::Body',name);metadata(b,name,'steel','turned 4mm shaft; mill D flat; inspect journal fits','HARDWARE')
    sk=doc.addObject('Sketcher::SketchObject',name+'_Dsection');b.addObject(sk);d_profile(sk,0,0,diameter/2,flat)
    pad=b.newObject('PartDesign::Pad',name+'_Pad');pad.Profile=sk;pad.Length=length;doc.recompute();sk.Visibility=False
    return b
