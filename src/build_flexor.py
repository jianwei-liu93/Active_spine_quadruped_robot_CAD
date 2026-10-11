"""Source-reconciled r02 spine. Lead runs through installed FreeCAD MCP.
Separate native definitions / App::Link instances. All nonreported dimensions
are provisional; no inferred spline or manufacturer mounting pattern.
"""
import FreeCAD as App, FreeCADGui as Gui, Part, Sketcher
import math,json
from pathlib import Path
import cad_common as cc
from build_robot import Builder
from kinematics import load_parameters,spine
V=App.Vector
ROOT=Path(__file__).resolve().parents[1]

def capsule(sk,x,y,length,width):
    """Rounded slot with total length and width; fixed geometry is editable in sketch."""
    r=width/2;a=x+r;b=x+length-r;z=y+r
    geoms=[Part.LineSegment(V(a,y,0),V(b,y,0)),Part.Arc(V(b,y,0),V(b+r,z,0),V(b,y+width,0)),Part.LineSegment(V(b,y+width,0),V(a,y+width,0)),Part.Arc(V(a,y+width,0),V(a-r,z,0),V(a,y,0))]
    for g in geoms:
        i=sk.addGeometry(g,False);sk.addConstraint(Sketcher.Constraint('Block',i))

def profile_part(b,pn,L,W,T,bores=(),window=None,material='PA12',slot=None):
    doc=b.doc;body=doc.addObject('PartDesign::Body',pn);cc.metadata(body,pn,material,'SLS nylon; finish bores / slots' if material=='PA12' else 'machined; provisional fits')
    body.Revision='r02';sk=doc.addObject('Sketcher::SketchObject',pn+'_Profile');body.addObject(sk);capsule(sk,0,0,L,W)
    pad=body.newObject('PartDesign::Pad',pn+'_Pad');pad.Profile=sk;pad.Length=T;doc.recompute();sk.Visibility=False
    if bores or window or slot:
        hs=doc.addObject('Sketcher::SketchObject',pn+'_Cuts');body.addObject(hs);hs.Placement.Base.z=T
        for x,y,d in bores:cc.circle(hs,x,y,d/2)
        if window:capsule(hs,*window)
        if slot:capsule(hs,*slot)
        pk=body.newObject('PartDesign::Pocket',pn+'_Pocket');pk.Profile=hs;pk.Length=T;doc.recompute();hs.Visibility=False;pad.Visibility=False
    b.library.addObject(body);b.sources[pn]=body;return body

def add_link(b,pn,L,W,T,window=False,bore=4.05):
    if pn in b.sources:return b.sources[pn]
    wi=(W+2, W/2-1.2,L-W-4,2.4) if window and L>W*2+5 else None
    return profile_part(b,pn,L+W,W,T,[(W/2,W/2,bore),(L+W/2,W/2,bore)],wi)

def col(o,c):
    # FreeCAD 1.x App::Link uses material overrides for independent appearance.
    try:
        mat=App.Material();mat.DiffuseColor=c
        o.ViewObject.OverrideMaterial=True;o.ViewObject.ShapeAppearance=(mat,)
    except Exception:pass

class FlexorBuilder(Builder):
    def add(self,source,name,placement,group,motion=None):
        o=super().add(source,name,placement,group,motion)
        col(o,(0.88,0.88,0.85) if group=='SpineLinks' and name.startswith('Link') else cc.COLORS.get(source.MaterialName,(.12,.13,.15)))
        return o
    def pin(self,name,P,layers,key=None,diam=1.9):
        lo,hi=min(layers)-.6,max(layers)+.6;length=hi-lo+.4;yc=(hi+lo)/2
        src=self.ring('PIN_D'+str(diam)+'_L'+str(round(length,3)),diam,0,length)
        self.add(src,name+'_Pin',cc.hardware_place(P,yc,length),'SpineHardware',{'kind':'point','point':key,'y':yc,'length':length} if key else None)
        for j,y in enumerate(layers):
            src=self.ring('BRG_2x4x1p2_PROVISIONAL',4,2,1.2)
            self.add(src,name+'_Bearing'+str(j),cc.hardware_place(P,y,1.2),'SpineHardware',{'kind':'point','point':key,'y':y,'length':1.2} if key else None)
        for e,y in enumerate([lo-.5,hi+.5]):
            src=self.ring('RETAINER_2mm',3.6,2.0,.6)
            self.add(src,name+'_Retainer'+str(e),cc.hardware_place(P,y,.6),'SpineHardware',{'kind':'point','point':key,'y':y,'length':.6} if key else None)
        for j,(a,z) in enumerate(zip(sorted(layers),sorted(layers)[1:])):
            gap=z-a-1.2
            if gap>.001:
                yy=(a+z)/2;src=self.ring('SPACER_2mm_L'+str(round(gap,3)),3,2.05,gap)
                self.add(src,name+'_Spacer'+str(j),cc.hardware_place(P,yy,gap),'SpineHardware',{'kind':'point','point':key,'y':yy,'length':gap} if key else None)

def build(root=ROOT,save=True):
    root=Path(root);p=load_parameters(root/'parameters/candidate_r02.json')
    if 'FlexorR02' in App.listDocuments():raise RuntimeError('Save/close FlexorR02 before rebuilding')
    doc=App.newDocument('FlexorR02');b=FlexorBuilder(doc,p);s=spine(p['neutral_phase_rad'],p)
    par=doc.addObject('App::FeaturePython','DesignParameters');par.addProperty('App::PropertyString','Revision');par.Revision='r02'
    par.addProperty('App::PropertyString','ParameterFile');par.ParameterFile='parameters/candidate_r02.json'
    for k,v in p.items():
        par.addProperty('App::PropertyFloat',k,'Parameters');setattr(par,k,float(v))
    # Compact back-to-back direct servo envelopes. Inverted cases extend above O.
    src=cc.simple_shape(doc,'ENV_XL330_r02',Part.makeBox(p['motor_width_mm'],p['motor_depth_mm'],p['motor_height_mm'],V(-10,-13,-7)),'motor','verified case envelope; output datum and horn pattern UNVERIFIED',role='PURCHASED')
    src.addProperty('App::PropertyFloat','PurchasedMass_g');src.PurchasedMass_g=p['XL_mass_g'];b.library.addObject(src);b.sources[src.Name]=src
    # Native open motor face cradles; a 20.8 x 34.8 window clears cases.
    cradle=b.plate('FRM_MOTOR_CRADLE_r02',24,38,1.6,[(2,2,2.2),(22,2,2.2),(2,36,2.2),(22,36,2.2)])
    sk=doc.addObject('Sketcher::SketchObject','CradleOpenings');cradle.addObject(sk);sk.Placement.Base.z=1.6
    cc.rectangle(sk,1.6,1.6,20.8,34.8)
    cut=cradle.newObject('PartDesign::Pocket','CradleWindow');cut.Profile=sk;cut.Length=1.6;doc.recompute();sk.Visibility=False
    for o in cradle.Group:
        if o!=cut:o.Visibility=False
    # Side backbone follows O/A/E and carries two source-style rounded guide bosses.
    for side in [-1,1]:
        b.add(src,'SpineMotor'+str(side),App.Placement(V(0,side*p['motor_y_mm'],0),App.Rotation()),'Actuators')
        b.add(cradle,'MotorCradle'+str(side),cc.plane_placement((-12,-9),side*27.6+.8),'Chassis')
        # Links for fixed side frame: E1-A1-E2-A2 is an open, slender structural loop.
        for j,(a,z) in enumerate([('E1','A1'),('A1','E2'),('E2','A2'),('A2','E1')]):
            L=math.dist(s[a],s[z]);f=add_link(b,'FRM_BACKBONE_'+str(j),L,5,1.6,False,4.05)
            b.add(f,'Backbone'+str(side)+'_'+str(j),cc.line_place(s[a],s[z],side*27.6,5,1.6),'Chassis')
        # Six moving planes, locally narrow. The two rods at G remain independent.
        segs=[(1,'G','B1',2,30.6),(2,'G','B2',2,32.4),(1,'A1','B1',3,32.4),(2,'A2','B2',3,30.6),(1,'B1','C1',4,34.2),(2,'B2','C2',4,34.2),(1,'C1','D1',5,36),(2,'C2','D2',5,36),(1,'E1','D1',6,37.8),(2,'E2','D2',6,37.8)]
        for i,a,z,n,y in segs:
            w=p['link_width_mm'] if n<5 else 5;T=p['link_thickness_mm'];L=p['L'+str(n)+'_mm'];pn='SPN_r02_L'+str(n)
            f=add_link(b,pn,L,w,T,n==4)
            b.add(f,f'Link{i}_L{n}_{side}',cc.line_place(s[a],s[z],side*y,w,T),'SpineLinks',{'kind':'segment','a':a,'b':z,'y':side*y,'width':w,'thickness':T})
        crank=add_link(b,'SPN_DIRECT_HORN_CRANK_r02',5,5,1.2,False,2.05)
        b.add(crank,'DirectCrank'+str(side),cc.line_place(s['O'],s['G'],side*28.8,5,1.2),'SpineLinks',{'kind':'segment','a':'O','b':'G','y':side*28.8,'width':5,'thickness':1.2})
        # Horn adapter is explicitly an unresolved envelope, not an invented spline.
        horn=b.ring('HORN_ADAPTER_UNVERIFIED',8,2.05,1.2)
        b.add(horn,'HornAdapter'+str(side),cc.hardware_place(s['O'],side*27.6,1.2),'Actuators',{'kind':'axialrot','point':'O','y':side*27.6,'length':1.2})
        b.pin('G'+str(side),s['G'],[side*y for y in [28.8,30.6,32.4]],'G')
        for i in [1,2]:
            layers=[30.6,32.4,34.2]
            b.pin('B'+str(i)+'_'+str(side),s[f'B{i}'],[side*y for y in layers],f'B{i}')
            b.pin('A'+str(i)+'_'+str(side),s[f'A{i}'],[side*27.6,side*(32.4 if i==1 else 30.6)])
            b.pin('D'+str(i)+'_'+str(side),s[f'D{i}'],[side*36,side*37.8],f'D{i}')
            b.pin('E'+str(i)+'_'+str(side),s[f'E{i}'],[side*27.6,side*37.8])
            # Guide coordinates are derived from actual full-cycle slider extrema.
            xs=[spine(j*math.tau/720,p)[f'C{i}'][0] for j in range(721)];xc=(min(xs)+max(xs))/2;zc=(1 if i==1 else -1)*p['guide_z_mm']
            travel=p['guide_slot_travel_mm'];sw=p['guide_slot_width_mm'];ow=p['guide_outer_width_mm'];L=travel+ow
            pn='GUIDE_FRAME_r02';guide=b.sources.get(pn) or profile_part(b,pn,L,ow,1.6,slot=((ow-sw)/2,(ow-sw)/2,travel+sw,sw))
            copper=b.sources.get('GUIDE_COPPER_r02') or profile_part(b,'GUIDE_COPPER_r02',travel+sw+1,sw+1,.3,material='copper',slot=(.5,.5,travel+sw,sw))
            copper.Process='machined copper face liner; attachment method UNVERIFIED'
            b.add(guide,f'GuideFrame{i}_{side}',cc.plane_placement((xc-L/2,zc-ow/2),side*40.2+.8),'Chassis')
            for offset in [-.65,.65]:
                b.add(copper,f'GuideLiner{i}_{side}_{offset}',cc.plane_placement((xc-(travel+sw+1)/2,zc-(sw+1)/2),side*40.2+offset+.15),'Chassis')
            b.pin(f'C{i}_{side}',s[f'C{i}'],[side*34.2,side*36,side*40.2],f'C{i}')
            # Slot bosses bolt to short standoffs at the fixed slot ends, outside travel.
            for e in [-1,1]:
                P=(xc+e*(travel/2+sw/2+1),zc)
                tube=b.ring('GUIDE_SUPPORT_L11',2.8,1.2,11)
                b.add(tube,f'GuideSupport{i}_{side}_{e}',cc.hardware_place(P,side*33.9,11),'Chassis')
    # Cross-link synchronization at moving B joints; no shaft passes through servo cases at O.
    for i in [1,2]:
        rod=b.ring('SYNC_SHAFT_1p9_L59',1.9,0,59)
        b.add(rod,f'SyncB{i}',cc.hardware_place(s[f'B{i}'],0,59),'SpineHardware',{'kind':'point','point':f'B{i}','y':0,'length':59})
    meta=doc.addObject('App::FeaturePython','PoseController')
    for key,typ,val in [('ParameterRevision','App::PropertyString','r02'),('SpinePhaseRad','App::PropertyFloat',0.0),('MotionMap','App::PropertyString',json.dumps(b.motion)),('Scope','App::PropertyString','Corrected spine only; dependent torso/legs pending review')]:meta.addProperty(typ,key);setattr(meta,key,val)
    import refine_flexor
    refine_flexor.apply(b)
    import retain_flexor
    retain_flexor.apply(b)
    import slider_plate_flexor
    slider_plate_flexor.apply(b)
    if save:finish(b,root)
    return b

def pose(doc,theta,p=None):
    p=p or load_parameters(ROOT/'parameters/candidate_r02.json');s=spine(theta,p)
    for name,m in json.loads(doc.PoseController.MotionMap).items():
        o=doc.getObject(name)
        if m['kind']=='segment':o.LinkPlacement=cc.line_place(s[m['a']],s[m['b']],m['y'],m['width'],m['thickness'])
        elif m['kind']=='point':o.LinkPlacement=cc.hardware_place(s[m['point']],m['y'],m['length'])
        elif m['kind']=='axialrot':o.LinkPlacement=cc.plane_placement(s[m['point']],m['y']+m['length']/2,theta)
    doc.PoseController.SpinePhaseRad=theta;doc.recompute();return s

def finish(b,root=ROOT):
    b.library.Visibility=False
    for src in b.sources.values():src.Visibility=False
    for o in b.doc.Objects:
        if o.TypeId=='App::Link' and o.Name.startswith('Backbone'):col(o,(.13,.14,.16))
    b.doc.recompute();Gui.activeDocument().activeView().viewAxonometric();Gui.activeDocument().activeView().fitAll()
    b.doc.saveAs(str(root/'cad/flexor_r02_spine.FCStd'))
    Gui.activeDocument().activeView().saveImage(str(root/'reports/views/r02_spine_isometric.png'),1600,1100,'White')
    print(json.dumps({'native':b.doc.FileName,'parts':len(b.sources),'instances':len([o for o in b.doc.Objects if o.TypeId=='App::Link'])}))
