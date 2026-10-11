"""Lead-only MCP build of the r01 scripted kinematic candidate.
Sources hidden in PartsLibrary; visible App::Links are physical instances.
"""
import FreeCAD as App, FreeCADGui as Gui, Part
import math,json,os
from pathlib import Path
from kinematics import load_parameters,spine,angle_diff
import cad_common as cc
V=App.Vector
ROOT=Path(__file__).resolve().parents[1]

class Builder:
    def __init__(self,doc,p):
        self.doc=doc;self.p=p;self.sources={};self.motion={};self.groups={}
        self.library=doc.addObject('App::DocumentObjectGroup','PartsLibrary')
        self.assembly=doc.addObject('App::Part','RobotAssembly')
        self.assembly.addProperty('App::PropertyString','AssemblyMethod');self.assembly.AssemblyMethod='Scripted exact geometric placements; six commands plus passive states'
        for name in ['Chassis','SpineLinks','SpineHardware','Actuators','TorsoFrames','Forelegs','Hindlegs','ElasticElements','Tendons','Electronics']:
            g=doc.addObject('App::DocumentObjectGroup',name);self.assembly.addObject(g);self.groups[name]=g
    def plate(self,pn,L,W,T,holes=(),material='PA12'):
        if pn not in self.sources:
            o=cc.plate(self.doc,pn,L,W,T,holes,material,pn);self.library.addObject(o);self.sources[pn]=o
        return self.sources[pn]
    def ring(self,pn,od,id_,length,material='steel'):
        if pn not in self.sources:
            o=cc.ring(self.doc,pn,od,id_,length,material,pn);self.library.addObject(o);self.sources[pn]=o
        return self.sources[pn]
    def add(self,source,name,placement,group,motion=None):
        obj=cc.instance(self.doc,source,name,placement);self.groups[group].addObject(obj)
        if motion:self.motion[obj.Name]=motion
        return obj
    def link(self,pn,L,material='PA12',width=None,T=None,hole=None):
        p=self.p;w=width or p['link_width_mm'];t=T or p['link_thickness_mm'];d=hole or p['bearing_seat_diameter_mm']
        return self.plate(pn,L+w,w,t,[(w/2,w/2,d),(L+w/2,w/2,d)],material)
    def joint(self,name,point,side,layers,anchor=None,shaftdia=None):
        p=self.p;od=p['bearing_od_mm'];bw=p['bearing_width_mm'];dia=shaftdia or p['pin_diameter_mm']
        for j,layer in enumerate(layers):
            self.add(self.ring('BRG_2x4x2_PROVISIONAL',od,2,bw),f'{name}_Bearing{j}',cc.hardware_place(point,side*layer,bw),'SpineHardware',{'kind':'point','point':anchor,'y':side*layer,'length':bw} if anchor else None)
        span=max(layers)-min(layers)+p['link_thickness_mm']+1.0
        center=side*(max(layers)+min(layers))/2
        self.add(self.ring(f'PIN_D{dia:.2f}_L{span:.1f}',dia,0,span),name+'_Pin',cc.hardware_place(point,center,span),'SpineHardware',{'kind':'point','point':anchor,'y':center,'length':span} if anchor else None)
        # Rings represent removable split shaft collars, not ornamental screw heads.
        for end in [-1,1]:
            yy=center+end*(span/2+0.5)
            self.add(self.ring('COLLAR_2mm',3.8,2.0,1.0),f'{name}_Retainer{end+1}',cc.hardware_place(point,yy,1),'SpineHardware',{'kind':'point','point':anchor,'y':yy,'length':1} if anchor else None)
        for a,b in zip(sorted(layers),sorted(layers)[1:]):
            gap=b-a-bw
            if gap>0.01:
                yy=side*(a+b)/2
                self.add(self.ring(f'SPACER_2mm_L{gap:.1f}',3,2.05,gap),f'{name}_Spacer{a:.1f}',cc.hardware_place(point,yy,gap),'SpineHardware',{'kind':'point','point':anchor,'y':yy,'length':gap} if anchor else None)


def build_spine(root=ROOT):
    root=Path(root);p=load_parameters(root/'parameters/candidate_r01.json')
    name='ActiveSpineQuadruped'
    if name in App.listDocuments():
        old=App.getDocument(name)
        if len(old.Objects)>1:raise RuntimeError('Refusing to replace nonempty live candidate; save/close explicitly first')
        App.closeDocument(name)
    doc=App.newDocument(name);builder=Builder(doc,p);s=spine(p['neutral_phase_rad'],p)
    doc.openTransaction('r01 spine build')
    floor=builder.plate('FRM_LUMBAR_FLOOR',98,59,p['plate_thickness_mm'],[(5,5,2.2),(93,5,2.2),(5,54,2.2),(93,54,2.2)])
    builder.add(floor,'LumbarFloor',App.Placement(V(-49,-29.5,p['frame_floor_z_mm']),App.Rotation()),'Chassis')
    holes=[]
    for n,dia in [('O',8.05),('A1',4.05),('A2',4.05),('E1',4.05),('E2',4.05)]:
        x,z=s[n];holes.append((x+49,z-p['frame_floor_z_mm'],dia))
    for x in [-22,22]:holes.append((x+49,-p['frame_floor_z_mm'],6.5))
    for x in [-39.5,-6.5,6.5,39.5]:holes.append((x+49,-5.5-p['frame_floor_z_mm'],2.2))
    holes += [(5,4,2.2),(93,4,2.2)]
    wall=builder.plate('FRM_LUMBAR_SIDE',98,p['frame_side_height_mm'],p['plate_thickness_mm'],holes)
    for side in [-1,1]:
        builder.add(wall,'LumbarSide'+str(side),cc.plane_placement((-49,p['frame_floor_z_mm']),side*29.5+p['plate_thickness_mm']/2),'Chassis')
    # Six segment planes per side; adjacent links have 1.2 mm axial gap.
    base=p['link_layer_base_mm'];pitch=p['layer_pitch_mm'];layers=[base+j*pitch for j in range(6)]
    for side in [-1,1]:
        for i in (1,2):
            local_layers=[layers[0]]+[v+(i-1)*pitch for v in layers[1:]]
            segments=[('G',f'B{i}',2,1),(f'A{i}',f'B{i}',3,2),(f'B{i}',f'C{i}',4,3),(f'C{i}',f'D{i}',5,4),(f'E{i}',f'D{i}',6,5)]
            for a,b,n,j in segments:
                src=builder.link('SPN_L'+str(n),p[f'L{n}_mm'])
                name=f'Chain{i}_L{n}_Side{side}'
                builder.add(src,name,cc.line_place(s[a],s[b],side*local_layers[j],p['link_width_mm'],p['link_thickness_mm']),'SpineLinks',{'kind':'segment','a':a,'b':b,'y':side*local_layers[j],'width':p['link_width_mm'],'thickness':p['link_thickness_mm']})
            for point,js in [(f'B{i}',[1,2,3]),(f'C{i}',[3,4]),(f'D{i}',[4,5])]:
                joint_layers=[local_layers[j] for j in js]
                if point.startswith('C'):joint_layers.append(local_layers[3]+7)
                if point.startswith('D'):joint_layers.append(55.5+(i-1)*3)
                builder.joint(point+f'_S{side}',s[point],side,joint_layers,point)
            builder.joint(f'A{i}_S{side}',s[f'A{i}'],side,[29.5,local_layers[2]])
            builder.joint(f'E{i}_S{side}',s[f'E{i}'],side,[29.5,local_layers[5],55.5+(i-1)*3])
        crank=builder.plate('SPN_CRANK',11,6,2,[(3,3,4.05,1.50),(8,3,4.05)],'steel')
        builder.add(crank,'Crank'+str(side),cc.line_place(s['O'],s['G'],side*layers[0],6,p['link_thickness_mm']),'SpineLinks',{'kind':'segment','a':'O','b':'G','y':side*layers[0],'width':6,'thickness':p['link_thickness_mm']})
        builder.joint('CrankPin'+str(side),s['G'],side,[layers[0],layers[1],layers[1]+pitch],'G')
        # Rail + replaceable copper wear strip + open-bottom sliding shoe, two independent guides.
        for i,xc in [(1,-23),(2,23)]:
            yy=side*(layers[3]+(i-1)*pitch+7)
            rail=builder.plate('GUIDE_RAIL',38,5,3,[(2.5,2.5,2.2),(35.5,2.5,2.2)])
            builder.add(rail,f'Rail{i}_{side}',cc.plane_placement((xc-19,-8),yy+1.5),'Chassis')
            wear=builder.plate('GUIDE_WEAR_STRIP',34,0.5,5,material='brass')
            builder.add(wear,f'Wear{i}_{side}',cc.plane_placement((xc-17,-4.8),yy+2.5),'Chassis')
            shoe=builder.plate('GUIDE_SHOE',8,9,5,[(4,6,4.05)])
            # Rail channel is native rectangular pocket in local XY, through pad depth; opens at lower edge.
            if not hasattr(shoe,'ChannelCutDone'):
                hs=doc.addObject('Sketcher::SketchObject','ShoeChannel');shoe.addObject(hs);hs.Placement.Base.z=5
                cc.rectangle(hs,0,-0.01,8,3.3)
                pk=shoe.newObject('PartDesign::Pocket','ShoeChannelPocket');pk.Profile=hs;pk.Length=5;doc.recompute();hs.Visibility=False
                for o in shoe.Group:
                    if o!=pk:o.Visibility=False
                shoe.addProperty('App::PropertyBool','ChannelCutDone');shoe.ChannelCutDone=True
            P=s[f'C{i}'];off=(-4,-6)
            builder.add(shoe,f'Slider{i}_{side}',cc.plane_placement((P[0]+off[0],off[1]),yy+2.5),'SpineLinks',{'kind':'slider','point':f'C{i}','offset':off,'y':yy+2.5})
            # Spacers bridge rail to side wall; M2 screws pass through rail ends.
            for xe in [xc-16.5,xc+16.5]:
                span=abs(yy)-29.5-2.75
                st=builder.ring(f'RAIL_STANDOFF_L{span:.2f}',5,2.2,span,'brass')
                builder.add(st,f'RailSupport{i}_{side}_{xe}',cc.hardware_place((xe,-5.5),side*(29.5+1.25+span/2),span),'Chassis')
            # End stops are removable with M2 screws; physical travel ±(19-4) around guide center.
            stop=builder.plate('GUIDE_STOP',2.5,6,6,[(1.25,3,2.2)])
            for e in [-1,1]:builder.add(stop,f'Stop{i}_{side}_{e}',cc.plane_placement((xc+e*18-1.25,-5),yy+3),'Chassis')
    # Main through-shaft, four bearings and accessible split collars.
    shaft=cc.d_shaft(doc,'INPUT_SHAFT_D3p99_L110',p['input_shaft_diameter_mm'],1.45,110)
    builder.library.addObject(shaft);builder.sources[shaft.Name]=shaft
    builder.add(shaft,'InputThroughShaft',cc.hardware_place(s['O'],0,110),'SpineHardware',{'kind':'axialrot','point':'O','y':0,'length':110})
    for yy in [-29.5,29.5]:builder.add(builder.ring('BRG_4x8x3_PROVISIONAL',8,4,3),'MainBearing'+str(yy),cc.hardware_place(s['O'],yy,3),'SpineHardware')
    gear=cc.gear(doc,'DRV_GEAR_M1_Z22',p['drive_gear_module_mm'],int(p['drive_gear_teeth']),p['drive_gear_pressure_rad'],p['drive_gear_thickness_mm'],4.05)
    builder.library.addObject(gear);builder.sources[gear.Name]=gear
    for side in [-1,1]:
        yy=side*p['drive_gear_layer_mm']
        builder.add(gear,'DrivenGear'+str(side),cc.hardware_place((0,0),yy,2),'SpineLinks',{'kind':'gear','point':[0,0],'y':yy,'sign':1,'offset':0})
        x=side*p['drive_gear_center_mm']
        builder.add(gear,'MotorPinion'+str(side),cc.plane_placement((x,0),yy+1,math.pi/22),'SpineLinks',{'kind':'gear','point':[x,0],'y':yy,'sign':-1,'offset':math.pi/22})
        add_motor(builder,'SpineMotor'+str(side),(x,0),side*15,'XL',None)
    # Torso cross-frames pivot about E, carry shoulder/hip modules at +/-57 mm.
    torso=builder.plate('FRM_TORSO_CROSS',28,102,3,[(x,y,2.2) for x in [2,26] for y in [1,21,81,101]])
    for i,direction in [(1,-1),(2,1)]:
        E=s[f'E{i}']
        placement=App.Placement(V(E[0]+direction*18-14,-51,E[1]+8),App.Rotation())
        builder.add(torso,'PelvisCross' if i==1 else 'ThoraxCross',placement,'TorsoFrames',{'kind':'torso','chain':i,'origin':[direction*18-14,-51,8]})
        # Rigid output bracket attaches to both E and D; D carries L5 as a bearing pivot.
        dx,dz=s[f'D{i}'][0]-E[0],s[f'D{i}'][1]-E[1]
        bracket=builder.plate(f'FRM_OUTPUT_BRACKET_{i}',24,40,3,[(12,20,4.05),(12+dx,20+dz,2.12),(6,32,2.2),(18,32,2.2)])
        for side in [-1,1]:
            builder.add(bracket,f'TorsoBracket{i}_{side}',cc.plane_placement((E[0]-12,-20),side*(55.5+(i-1)*3)+1.5),'TorsoFrames',{'kind':'torso_cheek','chain':i,'y':side*(55.5+(i-1)*3)+1.5,'offset':[-12,-20]})
            builder.add(builder.ring('BRG_2x4x2_PROVISIONAL',4,2,2),f'TorsoPivotBearing{i}_{side}',cc.hardware_place(E,side*(55.5+(i-1)*3),2),'SpineHardware')
    ctrl=builder.plate('CTRL_TRAY',54,29,2,[(3,3,2.2),(51,3,2.2),(3,26,2.2),(51,26,2.2)])
    builder.add(ctrl,'ControllerTray',App.Placement(V(-27,-14.5,37),App.Rotation()),'Electronics')
    for x in [-24,24]:
        beam=builder.plate('CTRL_SUPPORT_BEAM',4,59,2,[(2,2.5,2.2),(2,56.5,2.2),(2,18,2.2),(2,41,2.2)])
        builder.add(beam,'ControllerBeam'+str(x),App.Placement(V(x-2,-29.5,12),App.Rotation()),'Electronics')
        for y in [-11.5,11.5]:
            post=builder.ring('STANDOFF_OD5_ID2p2_L23',5,2.2,23,'brass')
            builder.add(post,f'ControllerPost{x}_{y}',App.Placement(V(x,y,14),App.Rotation()),'Electronics')
    board=cc.simple_shape(doc,'ENV_OpenRB150',Part.makeBox(50,25,8),'motor','unverified OpenRB-150 keep-out; strap mount; NO guessed board holes',role='ENVELOPE')
    builder.library.addObject(board);builder.sources[board.Name]=board
    builder.add(board,'ControllerCandidate',App.Placement(V(-25,-12.5,39),App.Rotation()),'Electronics')
    finalize(builder,root,'spine')
    doc.commitTransaction();return builder


def add_motor(builder,name,point,y,variant,motion):
    p=builder.p;doc=builder.doc;pn='ENV_'+('XL330_M077_T' if variant=='XL' else 'XC330_M181_T')
    if pn not in builder.sources:
        # Geometric output-center datum provisional: seven mm below upper case face.
        sh=Part.makeBox(p['motor_width_mm'],p['motor_depth_mm'],p['motor_height_mm'],V(-10,-13,-27))
        src=cc.simple_shape(doc,pn,sh,'motor','manufacturer envelope; OUTPUT/MOUNT DATUM PROVISIONAL',role='PURCHASED')
        src.addProperty('App::PropertyFloat','PurchasedMass_g','Mass');src.PurchasedMass_g=p[variant+'_mass_g']
        builder.library.addObject(src);builder.sources[pn]=src
    place=App.Placement(V(point[0],y,point[1]),App.Rotation())
    builder.add(builder.sources[pn],name,place,'Actuators',motion)
    # Adjustable saddle avoids invented supplier case-hole patterns.
    saddle=builder.plate('MOTOR_SADDLE',28,28,2,[(2,3,2.2),(26,3,2.2),(2,25,2.2),(26,25,2.2)])
    builder.add(saddle,name+'_Saddle',App.Placement(V(point[0]-14,y-14,point[1]-29),App.Rotation()),'Actuators',dict(motion,kind='motor_saddle') if motion else None)
    if name.startswith('SpineMotor'):
        for dx in [-12,12]:
            for dy in [-11,11]:
                st=builder.ring('MOTOR_STANDOFF_L7p5',5,2.2,7.5,'brass')
                builder.add(st,name+f'_Support{dx}_{dy}',App.Placement(V(point[0]+dx,y+dy,-36.5),App.Rotation()),'Actuators')
    # Retaining straps are separate removable crossbars with M2 through holes.
    strap=builder.plate('MOTOR_STRAP',28,4,2,[(2,2,2.2),(26,2,2.2)])
    for z in [-24,3]:builder.add(strap,name+'_Strap'+str(z),cc.plane_placement((point[0]-14,point[1]+z),y+14),'Actuators',dict(motion,kind='motor_strap',local_z=z) if motion else None)


def finalize(builder,root,stage):
    doc=builder.doc
    meta=doc.getObject('PoseController') or doc.addObject('App::FeaturePython','PoseController')
    for key,typ,val in [('ParameterRevision','App::PropertyString','r01'),('SpinePhaseRad','App::PropertyFloat',0.0),('MotionMap','App::PropertyString',json.dumps(builder.motion))]:
        if key not in meta.PropertiesList:meta.addProperty(typ,key,'Kinematics')
        setattr(meta,key,val)
    builder.library.Visibility=False
    for src in builder.sources.values():src.Visibility=False
    doc.recompute();Gui.activeDocument().activeView().viewAxonometric();Gui.activeDocument().activeView().fitAll()
    doc.saveAs(str(root/'cad/active_spine_quadruped.FCStd'))
    doc.saveCopy(str(root/f'cad/checkpoints/{stage}_r01.FCStd'))
    Gui.activeDocument().activeView().saveImage(str(root/f'reports/views/{stage}_isometric.png'),1600,1100,'White')
    print(json.dumps({'stage':stage,'native':doc.FileName,'definitions':len(builder.sources),'physical_instances':len([o for o in doc.Objects if o.TypeId=='App::Link'])}))


def pose(doc,theta,p=None):
    p=p or load_parameters();s=spine(theta,p);neutral=spine(p['neutral_phase_rad'],p)
    motion=json.loads(doc.getObject('PoseController').MotionMap)
    for name,m in motion.items():
        o=doc.getObject(name);k=m['kind']
        if k=='segment':o.LinkPlacement=cc.line_place(s[m['a']],s[m['b']],m['y'],m['width'],m['thickness'])
        elif k=='point':o.LinkPlacement=cc.hardware_place(s[m['point']],m['y'],m['length'])
        elif k=='slider':
            P=s[m['point']];o.LinkPlacement=cc.plane_placement((P[0]+m['offset'][0],P[1]+m['offset'][1]),m['y'])
        elif k=='axialrot':o.LinkPlacement=cc.plane_placement(s[m['point']],m['y']+m['length']/2,theta)
        elif k=='gear':o.LinkPlacement=cc.plane_placement(m['point'],m['y']+1,m['sign']*theta+m['offset'])
        elif k in ('torso','torso_cheek'):
            i=m['chain'];E=s[f'E{i}'];q=angle_diff(s[f'beta{i}'],neutral[f'beta{i}']);r=App.Rotation(V(0,-1,0),math.degrees(q))
            if k=='torso':o.LinkPlacement=App.Placement(V(E[0],0,E[1])+r.multVec(V(*m['origin'])),r)
            else:
                dx,dz=m['offset'];c,sn=math.cos(q),math.sin(q)
                o.LinkPlacement=cc.plane_placement((E[0]+c*dx-sn*dz,E[1]+sn*dx+c*dz),m['y'],q)
    pose_legs(doc,theta,p,motion)
    doc.PoseController.SpinePhaseRad=theta
    doc.recompute();return s


def build_legs(builder,root=ROOT):
    from robot_geometry import leg_geometry,tendon_geometry
    p=builder.p;doc=builder.doc
    doc.openTransaction('r01 leg modules and full integration')
    # Root output adapters remain provisional; motor body clamp patterns are independent of guessed case holes.
    for chain in [2,1]:
        direction=1 if chain==2 else -1
        group='Forelegs' if chain==2 else 'Hindlegs'
        for side in [-1,1]:
            tag=('Fore' if chain==2 else 'Hind')+('L' if side==1 else 'R')
            g=leg_geometry(0,chain,side,p);H=g['H'];ybase=side*60
            motor_motion={'kind':'leg_motor','chain':chain,'side':side,'y':side*40}
            add_motor(builder,tag+'_Motor',H,side*40,'XC',motor_motion)
            # Four rods suspend each saddle from torso deck with replaceable M2 tie hardware.
            for dx in [-12,12]:
                for dy in [-10,10]:
                    src=builder.ring('MOTOR_CARRIER_POST_L35',3.5,2.2,35,'brass')
                    origin=[direction*18+dx,side*40+dy,-27]
                    builder.add(src,tag+f'_CarrierPost{dx}_{dy}',App.Placement(V(H[0]+dx,side*40+dy,-27),App.Rotation()),group,{'kind':'torso_3d','chain':chain,'origin':origin})
            adapter=builder.ring('HIP_OUTPUT_ADAPTER_PROVISIONAL',9,4.05,5,'steel')
            builder.add(adapter,tag+'_OutputAdapter',cc.hardware_place(H,side*56,5),group,{'kind':'leg_hardware','chain':chain,'side':side,'point':'H','y':side*56,'length':5})
            for j,(a,b,length) in enumerate([('H','K',p['leg_a1_mm']),('K','A',p['leg_a2_mm']),('A','F',p['leg_a3_mm'])]):
                yy=side*(60+4*j);w=7;t=3
                if chain==1 and j==0:
                    src=builder.plate('LEG_HIND_THIGH',length+6+7,7,3,[(3.5,3.5,4.05),(length+3.5,3.5,4.05),(length+9.5,3.5,4.05)])
                elif chain==1 and j==2:
                    src=builder.plate('LEG_HIND_DISTAL',length+7,7,3,[(3.5,3.5,4.05),(9.5,3.5,4.05),(length+3.5,3.5,2.12)])
                else:src=builder.link(f'LEG_{group}_SEG{j+1}',length,width=w,T=t,hole=4.05)
                builder.add(src,tag+f'_Segment{j+1}',cc.line_place(g[a],g[b],yy,w,t),group,{'kind':'leg_segment','chain':chain,'side':side,'a':a,'b':b,'y':yy,'width':w,'thickness':t})
            if chain==1:
                src=builder.link('LEG_HIND_COUPLER',p['leg_a2_mm'],width=6,T=2,hole=4.05)
                builder.add(src,tag+'_Parallelogram',cc.line_place(g['P1'],g['P2'],side*72,6,2),group,{'kind':'leg_segment','chain':chain,'side':side,'a':'P1','b':'P2','y':side*72,'width':6,'thickness':2})
            for point,layers in [('H',[60]),('K',[60,64]),('A',[64,68])]+([('P1',[60,72]),('P2',[68,72])] if chain==1 else []):
                for j,yy in enumerate(layers):
                    src=builder.ring('BRG_2x4x2_PROVISIONAL',4,2,2)
                    builder.add(src,tag+f'_{point}_Bearing{j}',cc.hardware_place(g[point],side*yy,2),group,{'kind':'leg_hardware','chain':chain,'side':side,'point':point,'y':side*yy,'length':2})
                span=max(layers)-min(layers)+5;center=side*(max(layers)+min(layers))/2
                pin=builder.ring(f'LEG_PIN_D1p99_L{span}',1.99,0,span)
                builder.add(pin,tag+'_'+point+'_Pin',cc.hardware_place(g[point],center,span),group,{'kind':'leg_hardware','chain':chain,'side':side,'point':point,'y':center,'length':span})
                for e in [-1,1]:
                    yy=center+e*(span/2+0.5)
                    builder.add(builder.ring('COLLAR_2mm',3.8,2,1),tag+f'_{point}_Retainer{e}',cc.hardware_place(g[point],yy,1),group,{'kind':'leg_hardware','chain':chain,'side':side,'point':point,'y':yy,'length':1})
                for yy1,yy2 in zip(layers,layers[1:]):
                    gap=yy2-yy1-3
                    if gap>0:
                        yy=side*(yy1+yy2)/2
                        builder.add(builder.ring(f'LEG_SPACER_L{gap}',3,2.05,gap),tag+f'_{point}_Spacer',cc.hardware_place(g[point],yy,gap),group,{'kind':'leg_hardware','chain':chain,'side':side,'point':point,'y':yy,'length':gap})
            # Replaceable TPU foot, with a separate clevis connecting to the distal segment.
            foot=builder.plate('FOOT_TPU',12,8,4,[(6,4,2.2)],material='rubber')
            builder.add(foot,tag+'_FootPad',App.Placement(V(g['F'][0]-6,side*68-4,g['F'][1]-4),App.Rotation()),group,{'kind':'foot','chain':chain,'side':side})
            clevis=builder.plate('FOOT_CLEVIS',8,8,3,[(4,4,2.12)])
            builder.add(clevis,tag+'_FootClevis',cc.plane_placement((g['F'][0]-4,g['F'][1]-4),side*72+1.5),group,{'kind':'leg_clevis','chain':chain,'side':side,'y':side*72+1.5})
            for spring,y in [('extension',side*78),('compression',side*82)]:
                A=g[spring+'_A'];B=g[spring+'_B'];L=math.dist(A,B)
                shape=Part.makeCylinder(2,L).cut(Part.makeCylinder(1.5,L))
                source=cc.simple_shape(doc,tag+'_'+spring+'_SpringEnvelope',shape,'spring','purchased spring working envelope; rate/travel provisional; helix omitted',role='SPRING')
                builder.library.addObject(source);builder.sources[source.Name]=source
                place=axis_placement(A,B,y)
                builder.add(source,tag+'_'+spring+'_Spring',place,'ElasticElements',{'kind':'spring','chain':chain,'side':side,'spring':spring,'y':y,'source':source.Name})
                for e,P in [('A',A),('B',B)]:
                    # Spring hooks/seat eyes captured on dedicated studs carried by thigh and shank.
                    anchor=builder.ring('SPRING_ANCHOR_EYE',4,2.12,2,'steel')
                    builder.add(anchor,tag+'_'+spring+'_Anchor'+e,cc.hardware_place(P,y,2),'ElasticElements',{'kind':'spring_anchor','chain':chain,'side':side,'spring':spring,'end':e,'y':y})
                    stud=builder.ring('SPRING_ANCHOR_STUD_L20',1.99,0,20,'steel')
                    center=side*((78 if spring=='extension' else 82)+64)/2
                    builder.add(stud,tag+'_'+spring+'_Stud'+e,cc.hardware_place(P,center,20),'ElasticElements',{'kind':'spring_stud','chain':chain,'side':side,'spring':spring,'end':e,'y':center})
                if spring=='compression':
                    rod=builder.ring('COMPRESSION_GUIDE_ROD_L20',1,0,20,'steel')
                    builder.add(rod,tag+'_CompressionGuideRod',place,'ElasticElements',{'kind':'spring_guide','chain':chain,'side':side,'y':y})
                    seat=builder.ring('SPRING_SEAT_OD5',5,1.12,1.2,'steel')
                    for e,P in [('A',A),('B',B)]:
                        pp=App.Placement(V(P[0],y,P[1]),place.Rotation)
                        builder.add(seat,tag+'_CompressionSeat'+e,pp,'ElasticElements',{'kind':'spring_seat','chain':chain,'side':side,'end':e,'y':y})
    # Common seventh servo, 13 mm wheel, secured left/right grooves (no differential slip).
    E=spine(0,p)['E1'];W=(E[0]-37,0)
    add_motor(builder,'KneeWindingMotor',W,0,'XC',{'kind':'wheel_motor','chain':1,'origin':[-37,0,0]})
    tray=builder.plate('KNEE_MOTOR_DECK',44,30,3,[(3,3,2.2),(41,3,2.2),(3,27,2.2),(41,27,2.2)])
    builder.add(tray,'KneeMotorDeck',App.Placement(V(W[0]-14,-15,8),App.Rotation()),'TorsoFrames',{'kind':'torso_3d','chain':1,'origin':[-51,-15,8]})
    wheel=builder.ring('WINDING_WHEEL_CORE',11.2,4.05,7,'PA12')
    builder.add(wheel,'CommonKneeWheel',cc.hardware_place(W,19,7),'Tendons',{'kind':'wheel','chain':1,'y':19})
    for yy in [15,23]:builder.add(builder.ring('WINDING_WHEEL_FLANGE_OD13',13,4.05,1,'PA12'),'WheelFlange'+str(yy),cc.hardware_place(W,yy,1),'Tendons',{'kind':'wheel','chain':1,'y':yy})
    for side in [-1,1]:
        t=tendon_geometry(0,side,p)
        for suffix,shape,material,process in [('Cable',cable_shape(t,p),'cable','secured fiber cable, elastic law provisional'),('ShellGuide',shell_guide_shape(t),'brass','replaceable curved eyelet, 2.5mm centerline bend')]:
            src=cc.simple_shape(doc,f'Hind{side}_{suffix}_Source',shape,material,process,role='CABLE' if suffix=='Cable' else 'HARDWARE')
            builder.library.addObject(src);builder.sources[src.Name]=src
            builder.add(src,f'Hind{side}_{suffix}',App.Placement(),'Tendons',{'kind':'tendon_shape','side':side,'part':suffix,'source':src.Name})
        H=t['hip_center'];yy=t['cable_plane_y_mm']
        guide=builder.ring('HIP_CABLE_GUIDE',5.4,2.12,2.5,'brass')
        builder.add(guide,f'Hind{side}_HipGuide',cc.hardware_place(H,yy,2.5),'Tendons',{'kind':'leg_hardware','chain':1,'side':side,'point':'H','y':yy,'length':2.5})
        anchor=builder.plate('CABLE_ANCHOR_TAB',6,6,3,[(3,3,1.0)])
        P=t['leg']['cable_anchor']
        builder.add(anchor,f'Hind{side}_CableAnchor',cc.plane_placement((P[0]-3,P[1]-3),yy+1.5),'Tendons',{'kind':'cable_anchor','chain':1,'side':side,'y':yy+1.5})
    finalize(builder,Path(root),'whole_robot');doc.commitTransaction();return builder


def axis_placement(A,B,y):
    return App.Placement(V(A[0],y,A[1]),App.Rotation(V(0,0,1),V(B[0]-A[0],0,B[1]-A[1])))

def cable_wire(t):
    vv=lambda p:V(*p)
    c=t['corner'];hp=t['hip_points'];r=t['hip_route'];h=t['hip_center'];yy=t['cable_plane_y_mm']
    am=(r['arc_start_rad']+r['arc_end_rad'])/2+t['leg']['torso_rad']
    mid=V(h[0]+r['radius_mm']*math.cos(am),yy,h[1]+r['radius_mm']*math.sin(am))
    edges=[Part.makeLine(vv(t['wheel_contact']),vv(c['entry'])),Part.Arc(vv(c['entry']),vv(c['mid']),vv(c['exit'])).toShape(),Part.makeLine(vv(c['exit']),vv(hp[1])),Part.Arc(vv(hp[1]),mid,vv(hp[2])).toShape(),Part.makeLine(vv(hp[2]),vv(hp[3]))]
    return Part.Wire(edges)

def sweep_wire(w,r):
    start=w.Vertexes[0].Point;tangent=w.Edges[0].tangentAt(w.Edges[0].FirstParameter)
    profile=Part.Wire([Part.makeCircle(r,start,tangent)])
    return w.makePipeShell([profile],True,False)

def cable_shape(t,p):return sweep_wire(cable_wire(t),p['cable_diameter_mm']/2)

def shell_guide_shape(t):
    c=t['corner'];arc=Part.Wire([Part.Arc(V(*c['entry']),V(*c['mid']),V(*c['exit'])).toShape()])
    return sweep_wire(arc,1.3).cut(sweep_wire(arc,0.55))


def pose_legs(doc,theta,p,motion=None,commands=None):
    from robot_geometry import leg_geometry,tendon_geometry
    motion=motion or json.loads(doc.PoseController.MotionMap);commands=commands or {}
    cache={}
    def geo(chain,side):
        if (chain,side) not in cache:
            q=commands.get((chain,side),{})
            cache[(chain,side)]=leg_geometry(theta,chain,side,p,**q)
        return cache[(chain,side)]
    for name,m in motion.items():
        o=doc.getObject(name);k=m['kind']
        if k.startswith('leg_') or k in ['foot','cable_anchor','spring','spring_anchor','spring_stud','spring_guide','spring_seat']:
            g=geo(m['chain'],m['side']);side=m['side'];E=spine(theta,p)[f'E{m["chain"]}'];q=g['torso_rad']
            if k=='leg_segment':o.LinkPlacement=cc.line_place(g[m['a']],g[m['b']],m['y'],m['width'],m['thickness'])
            elif k=='leg_hardware':o.LinkPlacement=cc.hardware_place(g[m['point']],m['y'],m['length'])
            elif k=='leg_motor':o.LinkPlacement=App.Placement(V(g['H'][0],m['y'],g['H'][1]),App.Rotation(V(0,-1,0),math.degrees(q)))
            elif k=='leg_clevis':o.LinkPlacement=cc.plane_placement((g['F'][0]-4,g['F'][1]-4),m['y'])
            elif k=='foot':o.LinkPlacement=App.Placement(V(g['F'][0]-6,side*68-4,g['F'][1]-4),App.Rotation())
            elif k=='cable_anchor':
                P=g['cable_anchor'];o.LinkPlacement=cc.plane_placement((P[0]-3,P[1]-3),m['y'])
            elif k=='spring':
                A=g[m['spring']+'_A'];B=g[m['spring']+'_B'];L=math.dist(A,B)
                doc.getObject(m['source']).Shape=Part.makeCylinder(2,L).cut(Part.makeCylinder(1.5,L));o.LinkPlacement=axis_placement(A,B,m['y'])
            elif k in ['spring_anchor','spring_stud']:
                P=g[m['spring']+'_'+m['end']];o.LinkPlacement=cc.hardware_place(P,m['y'],2 if k=='spring_anchor' else 20)
            elif k=='spring_guide':o.LinkPlacement=axis_placement(g['compression_A'],g['compression_B'],m['y'])
            elif k=='spring_seat':
                P=g['compression_'+m['end']];o.LinkPlacement=App.Placement(V(P[0],m['y'],P[1]),axis_placement(g['compression_A'],g['compression_B'],m['y']).Rotation)
        elif k=='torso_3d' or k=='wheel_motor':
            s=spine(theta,p);n=spine(p['neutral_phase_rad'],p);i=m['chain'];q=angle_diff(s[f'beta{i}'],n[f'beta{i}']);E=s[f'E{i}'];r=App.Rotation(V(0,-1,0),math.degrees(q))
            o.LinkPlacement=App.Placement(V(E[0],0,E[1])+r.multVec(V(*m['origin'])),r)
        elif k=='wheel':
            g=geo(1,1);E=spine(theta,p)['E1'];q=g['torso_rad'];dx=-37*math.cos(q);dz=-37*math.sin(q)
            o.LinkPlacement=cc.hardware_place((E[0]+dx,E[1]+dz),m['y'],7 if name=='CommonKneeWheel' else 1)
        elif k=='tendon_shape':
            qq=commands.get((1,m['side']),{});t=tendon_geometry(theta,m['side'],p,qq.get('qh'),qq.get('qk'))
            doc.getObject(m['source']).Shape=cable_shape(t,p) if m['part']=='Cable' else shell_guide_shape(t)
        elif k in ['motor_saddle','motor_strap'] and 'chain' in m:
            if 'side' in m:g=geo(m['chain'],m['side']);H=g['H'];q=g['torso_rad'];yy=m['y']
            else:
                g=geo(1,1);q=g['torso_rad'];E=spine(theta,p)['E1'];H=(E[0]-37*math.cos(q),E[1]-37*math.sin(q));yy=0
            r=App.Rotation(V(0,-1,0),math.degrees(q))
            if k=='motor_saddle':o.LinkPlacement=App.Placement(V(H[0],yy,H[1])+r.multVec(V(-14,-14,-29)),r)
            else:
                dx,dz=-14,m['local_z'];o.LinkPlacement=cc.plane_placement((H[0]+math.cos(q)*dx-math.sin(q)*dz,H[1]+math.sin(q)*dx+math.cos(q)*dz),yy+14,q)
