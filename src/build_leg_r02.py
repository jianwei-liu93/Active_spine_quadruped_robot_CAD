"""Reproducible r02 native leg source; lead alone executes in FreeCAD.

Source topology recovery: reports/source_review/leg_recovery.md, original
supplement Figs S17-S19, Movie S2 16.5/26.5 s. Dimensions and rigid ownership
below remain DESIGN_ASSUMPTION, not recovered fabrication dimensions.

build_leg(b,tag,kind,side,transform,pose=None,include_support=True) uses an existing FlexorBuilder.
transform((x,z))->world(x,z) is a rigid proper planar torso transform; its
optional angle_rad must agree. Side is +/-1 and only affects axial Y layers.
Primary hip/shoulder drive is rigid: motor_proximal_angle must equal thigh_angle.
The fixed bent horn arm points at thigh_angle+delta (hind+60deg/fore+60deg,
assumed offsets). Both horn and thigh key to the same shaft; only the ground
H support has a bearing. The return rail pivots lie 6mm TOWARD the hip from
K/A, and the foot enforces the selected parallelogram. Four passive knees/
elbows remain in the primary architecture; no proximal elastic DOF is added.

Motion descriptors use kind='leg_r02_*' and carry tag/leg_type/side, attachment
point names, placement rules and source identity. The lead must reevaluate
leg_contract at new poses and recreate spring shapes using spring_shape;
changing spring source lengths in place across shared instances is forbidden.
Compression free lengths are anchor-equivalent; each seat face is 3.6mm
inward, so physical coil length/free length subtract 7.2mm. Guides are fixed
14mm rod/tube, whose engagement must be checked for every pose.
CAD run, swept interference, supplier fits, fatigue and loaded equilibrium
are NOT verified by this source. Neutral planar morphology follows the frozen
qh seeds; do not infer world camera/servo signs from perspective frames.
"""
import math
from leg_geometry_r02 import leg_geometry


_PLANES = {'thigh':44.4,'shank':46.2,'foot':48.0,'return_rail':49.8,
           'motor_horn':51.4,'hip_support':42.6,'extension':54.4,'compression':53.2}


def _identity(point):
    return tuple(point)


def _stack(layers,eye_layers=()):
    layers=tuple(sorted(set(layers)))
    widths={y:(.5 if y in eye_layers else 1.2) for y in layers}
    lo=layers[0]-widths[layers[0]]/2-.85
    hi=layers[-1]+widths[layers[-1]]/2+.85
    return {'layers_y_mm':layers,'shaft_bounds_y_mm':(lo,hi),
            'shaft_center_y_mm':(lo+hi)/2,'shaft_length_mm':hi-lo,
            'shaft_diameter_mm':1.9,'bearing_width_mm':1.2,
            'clip_centers_y_mm':(lo+.5,hi-.5),'groove_width_mm':.6,
            'groove_root_diameter_mm':1.7,
            'layer_widths_mm':widths,
            'spacers':[{'center_y_mm':(a+widths[a]/2+b-widths[b]/2)/2,'length_mm':b-a-(widths[a]+widths[b])/2}
                       for a,b in zip(layers,layers[1:]) if b-a>(widths[a]+widths[b])/2+1e-9]}


def leg_contract(kind,side,transform=None,pose=None):
    """Pure geometry/stack contract consumed by build_leg and pose integration."""
    if side not in (-1,1):
        raise ValueError('side must be +/-1')
    transform=transform or _identity
    t0,tx,tz=(tuple(transform(p)) for p in ((0,0),(1,0),(0,1)))
    ux=(tx[0]-t0[0],tx[1]-t0[1]);uz=(tz[0]-t0[0],tz[1]-t0[1])
    if not all(math.isfinite(v) for p in (t0,tx,tz) for v in p):
        raise ValueError('transform must be finite')
    if max(abs(math.hypot(*ux)-1),abs(math.hypot(*uz)-1),abs(ux[0]*uz[0]+ux[1]*uz[1]),abs(ux[0]*uz[1]-ux[1]*uz[0]-1))>1e-9:
        raise ValueError('transform must be a proper rigid planar transform')
    angle=math.atan2(ux[1],ux[0])
    if hasattr(transform,'angle_rad') and abs(math.atan2(math.sin(transform.angle_rad-angle),math.cos(transform.angle_rad-angle)))>1e-9:
        raise ValueError('transform.angle_rad disagrees with transformed basis')
    pose=pose or {}
    g=leg_geometry(kind,**pose)
    points={n:tuple(transform(g[n])) for n in ('H','K','A','F','O1','A1','O2','O3')}
    planes={k:side*v for k,v in _PLANES.items()}
    a1,a2,a3=(g['lengths_mm'][n] for n in ('a1','a2','a3'))
    parts={
        'thigh':{'point_names':('H','O1','K'),'pivot_x_mm':(0,a1-6,a1),'width_mm':5,'thickness_mm':1.2,'length_mm':a1,'keyed_H':True,'key_flat_angle_rad':0.0},
        'shank':{'point_names':('O3','K','A'),'pivot_x_mm':(0,6,a2+6),'width_mm':5,'thickness_mm':1.2,'length_mm':a2+6},
        'return_rail':{'point_names':('O1','A1'),'pivot_x_mm':(0,a2),'width_mm':3.2,'boss_diameter_mm':5,'thickness_mm':1.2,'length_mm':a2},
        'foot':{'point_names':('A','A1'),'pivot_x_mm':(0,-6),'width_mm':5,'thickness_mm':1.2,'contact_x_mm':a3,'curve_sag_mm':3},
    }
    joints={name:_stack([planes[k] for k in layers],(planes['extension'],) if name in ('O2','O3') else ()) for name,layers in {
        'H':('motor_horn','hip_support','thigh'),'K':('thigh','shank'),
        'A':('shank','foot','compression'),'O1':('thigh','return_rail','compression'),
        'A1':('foot','return_rail'),'O2':('motor_horn','extension'),
        'O3':('shank','extension')}.items()}
    delta=math.radians(60)
    joints['H']['bearing_layers_y_mm']=(planes['hip_support'],)
    joints['H']['keyed_layers_y_mm']=(planes['thigh'],planes['motor_horn'])
    # Candidate output adapter begins at the manufacturer case exterior.
    # There is no inner clip/groove in the motor envelope: axial capture at
    # the output face depends on an unverified manufacturer-specific coupling.
    h=joints['H'];outer=side*max(abs(y) for y in h['shaft_bounds_y_mm'])
    lo,hi=sorted((side*42.0,outer))
    h.update(shaft_bounds_y_mm=(lo,hi),shaft_center_y_mm=(lo+hi)/2,
             shaft_length_mm=hi-lo,clip_centers_y_mm=(outer-side*.5,),
             case_face_coupling='PROVISIONAL manufacturer output adapter; no inner retainer')
    # O2 is a headed pin fixed to the horn, not a long through-stack journal.
    # Its 1.9mm shank stays between horn inner face and outer seat; a .4mm
    # head outside the horn supplies inner capture and one outer groove/clip.
    o=joints['O2']
    o.update(shaft_bounds_y_mm=tuple(sorted((side*50.8,side*55.6))),
             shaft_center_y_mm=side*53.2,shaft_length_mm=4.8,
             clip_centers_y_mm=(side*55.1,),headed_pin=True,
             head_center_y_mm=side*50.6,head_width_mm=.4)
    springs={}
    for name,free,anchors in (('extension',18 if kind=='hind' else 13,('O2','O3')),
                              ('compression',34 if kind=='hind' else 27,('O1','A'))):
        L=math.dist(points[anchors[0]],points[anchors[1]])
        springs[name]={'anchors':anchors,'length_mm':L,'free_length_mm':free,
                       'outer_diameter_mm':4,'wire_diameter_mm':.5,
                       'plane_y_mm':planes[name],'solid_length_mm':7 if name=='compression' else None,
                       'seat_offset_mm':3.6 if name=='compression' else 0,
                       'coil_length_mm':L-7.2 if name=='compression' else L,
                       'coil_free_length_mm':free-7.2 if name=='compression' else free,
                       'bind_margin_mm':1,'travel_ok':L-7.2>=8 if name=='compression' else None,
                       'provenance':'DESIGN_ASSUMPTION','capacity_verified':False}
    return {'leg_type':kind,'side':side,'geometry':g,'world_points':points,
            'torso_angle_rad':angle,'planes_y_mm':planes,'parts':parts,
            'joints':joints,'springs':springs,'cable_anchor':'A',
            'motor_thigh_deflection_rad':g['motor_proximal_angle_rad']-g['thigh_angle_rad'],
            'horn':{'fixed_bend_rad':delta,'key_flat_angle_rad':-delta,'shaft_angle_rad':g['thigh_angle_rad']},
            'primary_proximal_drive':'rigid keyed thigh and bent horn on one shaft'}


def _native_face(b,pn,face,thickness,material='PA12',process=None):
    import FreeCAD as App
    import cad_common as cc
    from refine_flexor import sketch_face
    if pn in b.sources:
        return b.sources[pn]
    # Resolve overlapping/coplanar 2D boolean faces as real 3D unions before
    # extracting the one section used by Sketcher. This avoids compound face
    # outlines introducing duplicate/internal sketch edges.
    solids=[f.extrude(App.Vector(0,0,thickness)) for f in face.Faces]
    if not solids:
        raise RuntimeError(pn+': empty native section')
    merged=solids[0]
    for piece in solids[1:]:
        merged=merged.fuse(piece)
    merged=merged.removeSplitter()
    if not merged.isValid() or len(merged.Solids)!=1:
        raise RuntimeError(pn+': contour extrusion must form one valid solid')
    bottoms=[f for f in merged.Faces if f.BoundBox.ZLength<1e-7 and abs(f.CenterOfMass.z)<1e-7]
    if len(bottoms)!=1:
        raise RuntimeError(pn+': expected one planar bottom face, got '+str(len(bottoms)))
    face=bottoms[0]
    body=b.doc.addObject('PartDesign::Body',pn)
    cc.metadata(body,pn,material,process or 'SLS PA12; native contour; finish bores; provisional fits')
    body.Revision='r02'
    sk=sketch_face(b.doc,body,pn+'_Profile',face)
    pad=body.newObject('PartDesign::Pad',pn+'_Pad');pad.Profile=sk;pad.Length=thickness
    b.doc.recompute();sk.Visibility=False
    b.library.addObject(body);b.sources[pn]=body
    return body


def _key_bore(body,b,x,y,angle,suffix):
    """Native rotated D profile: key flat normal follows angle in sketch XY."""
    import FreeCAD as App, Part, Sketcher
    V=App.Vector;r=1.025;flat=.85;a=math.acos(flat/r);h=math.sqrt(r*r-flat*flat)
    sk=b.doc.addObject('Sketcher::SketchObject',body.Name+'_'+suffix);body.addObject(sk);sk.Placement.Base.z=1.2
    c,s=math.cos(angle),math.sin(angle)
    def p(dx,dy):return V(x+c*dx-s*dy,y+s*dx+c*dy,0)
    geoms=[Part.ArcOfCircle(Part.Circle(V(x,y,0),V(0,0,1),r),angle+a,angle+math.tau-a),
           Part.LineSegment(p(flat,-h),p(flat,h))]
    for geom in geoms:
        j=sk.addGeometry(geom,False);sk.addConstraint(Sketcher.Constraint('Block',j))
    base=body.Tip;pk=body.newObject('PartDesign::Pocket',body.Name+'_'+suffix+'Pocket');pk.Profile=sk;pk.Length=1.2
    b.doc.recompute();sk.Visibility=False;base.Visibility=False
    return body


def _rod_source(b,pn,spec):
    import FreeCAD as App, Part
    import cad_common as cc
    from build_flexor import profile_part
    from refine_flexor import pill_face,disk
    if pn in b.sources:
        return b.sources[pn]
    W,T,L=spec['width_mm'],spec['thickness_mm'],spec['length_mm']
    xs=spec['pivot_x_mm']
    # Rail's 3.2mm web cannot contain a 4.05mm bearing seat; native bosses
    # restore a 5mm pivot section rather than cutting the thin rail apart.
    if 'boss_diameter_mm' in spec:
        face=pill_face((0,0),(L,0),W)
        for x in xs:
            face=face.fuse(disk(x,0,spec['boss_diameter_mm']/2))
        for x in xs:
            face=face.cut(disk(x,0,2.025))
        return _native_face(b,pn,face.removeSplitter(),T)
    # profile_part local origins have pivot centers at (W/2,W/2).
    bores=[(x+W/2,W/2,4.05) for x in xs if not (spec.get('keyed_H') and x==0)]
    body=profile_part(b,pn,L+W,W,T,bores)
    if spec.get('keyed_H'):
        _key_bore(body,b,W/2,W/2,0.0,'ThighKey')
    return body


def _foot_source(b,pn,spec):
    import FreeCAD as App, Part
    from refine_flexor import disk,pill_face
    V=App.Vector
    if pn in b.sources:
        return b.sources[pn]
    L=spec['contact_x_mm'];r=2.5;sag=spec['curve_sag_mm']
    # Two true circular arcs form a bowed foot contour; end caps are arcs.
    wire=Part.Wire([
        Part.Arc(V(0,-r,0),V(L/2,-sag-r,0),V(L,-r,0)).toShape(),
        Part.Arc(V(L,-r,0),V(L+r,0,0),V(L,r,0)).toShape(),
        Part.Arc(V(L,r,0),V(L/2,-sag+r,0),V(0,r,0)).toShape(),
        Part.Arc(V(0,r,0),V(-r,0,0),V(0,-r,0)).toShape()])
    face=Part.Face(wire)
    # A1 is BEHIND A in foot frame. A continuous native web joins both
    # bearing bosses; a disjoint disk would violate the one-solid contract.
    face=face.fuse(pill_face((-6,0),(0,0),5)).fuse(disk(-6,0,r))
    face=face.cut(disk(0,0,2.025)).cut(disk(-6,0,2.025)).removeSplitter()
    return _native_face(b,pn,face,spec['thickness_mm'])


def _journal_source(b,length,groove_z=None,key_z=None,headed=False):
    import FreeCAD as App, Sketcher
    import cad_common as cc
    pn=('LEG_r02_HEADED_PIN_D1p9_L' if headed else ('LEG_r03_DUAL_KEYED_H_JOURNAL_D1p9_L' if key_z is not None else 'LEG_r02_JOURNAL_D1p9_L'))+str(round(length,5)).replace('.','p')
    if pn in b.sources:
        return b.sources[pn]
    body=b.ring(pn,1.9,0,length)
    base=body.Tip
    # Every length gets a new definition; no shared source is resized.
    for i,z in enumerate(groove_z or (.8,length-.2)):
        sk=b.doc.addObject('Sketcher::SketchObject',pn+'_Groove'+str(i));body.addObject(sk)
        sk.Placement.Base.z=z;cc.circle(sk,0,0,1.05);cc.circle(sk,0,0,.85)
        pk=body.newObject('PartDesign::Pocket',pn+'_GroovePocket'+str(i));pk.Profile=sk;pk.Length=.6
        b.doc.recompute();sk.Visibility=False;base.Visibility=False;base=pk
    if headed:
        sk=b.doc.addObject('Sketcher::SketchObject',pn+'_Head');body.addObject(sk)
        sk.Placement.Base.z=length;cc.circle(sk,0,0,1.6)
        pad=body.newObject('PartDesign::Pad',pn+'_HeadPad');pad.Profile=sk;pad.Length=.4
        b.doc.recompute();sk.Visibility=False;base.Visibility=False;base=pad
    if key_z is not None:
        keys=key_z if isinstance(key_z,(list,tuple)) else (key_z,)
        for j,key in enumerate(keys):
            sk=b.doc.addObject('Sketcher::SketchObject',pn+'_DriveFlat'+str(j));body.addObject(sk)
            sk.Placement.Base.z=key+.6
            cc.rectangle(sk,.85,-1.1,1.2,2.2)
            pk=body.newObject('PartDesign::Pocket',pn+'_DriveKeyPocket'+str(j));pk.Profile=sk;pk.Length=1.2
            b.doc.recompute();sk.Visibility=False;base.Visibility=False;base=pk
    body.Process='turned 1.9 journal, two native annular grooves; clip standard/fatigue UNVERIFIED'
    body.Revision='r02'
    return body


def spring_shape(length,kind,free_length):
    """Actual .5mm circular wire, OD4, closed coils and helical centerline.

    Called inside FreeCAD. Raises if construction is invalid; no decorative
    cylinder/cone substitution. Returned purchased-spring wire is a BRep;
    native custom structural parts remain sketch/pad features.
    Compression has 12 active + 2 closed end coils, nominal solid 7mm.
    Extension has assumed free coil count and real closed eyelets. Auxiliary
    coaxial end tori are deliberately omitted on extension: their tangent
    contacts with tightly pitched helix wire produced invalid OCC unions.
    """
    import FreeCAD as App, Part
    if kind=='extension':
        from spring_wire_r03 import shape
        return shape(length,free_length)
    V=App.Vector
    if kind not in ('extension','compression') or length<=4:
        raise ValueError('Invalid spring type or installed eye/seat length')
    if kind=='compression' and length<8:
        raise ValueError('Compression spring violates assumed 7mm solid + 1mm margin')
    radius,wire=1.75,.5
    z0,z1=(2.0,length-2.0) if kind=='extension' else (.25,length-.25)
    turns=max(1,round((free_length-4)/wire)) if kind=='extension' else 12
    pitch=(z1-z0)/turns
    if pitch<wire-1e-9:
        raise ValueError('Assumed coil count causes intersecting wire; revise spring data')
    path=Part.Wire(Part.makeHelix(pitch,z1-z0,radius).Edges)
    # Helix tangent at its first point has a pitch component along the axis.
    tangent=V(0,radius,pitch/math.tau)
    section=Part.Wire([Part.makeCircle(wire/2,V(radius,0,0),tangent)])
    solid=path.makePipeShell([section],True,True)
    # Construct in the helix's local frame, then move the completed sweep.
    # Moving the path before re-wrapping its Edges loses its location context
    # in this OCC build and leaves the hooks disconnected from the coil.
    solid.translate(V(0,0,z0))
    if not solid.isValid() or len(solid.Solids)!=1:
        raise RuntimeError(kind+': helix sweep itself is invalid or disconnected')
    if kind=='compression':
        for z in (z0,z1):
            solid=solid.fuse(Part.makeTorus(radius,wire/2,V(0,0,z),V(0,0,1)))
    if kind=='extension':
        for z,end in ((0,z0),(length,z1)):
            # End eyelet planes contain the spring axis, permitting transverse
            # pivot studs through their centers; connectors are real round wire.
            eye=Part.makeTorus(1.25,wire/2,V(0,0,z),V(0,1,0))
            a=V(1.25,0,z);d=V(radius,0,end)-a
            # Join the bridge to the helix FIRST, with finite penetration past
            # both centerline endpoints. Do not fuse disconnected eyelets first
            # or rely on exact end-face/tangent contacts to repair a compound.
            unit=d/d.Length;overlap=.15
            bridge=Part.makeCylinder(wire/2,d.Length+2*overlap,a-unit*overlap,d)
            solid=solid.fuse(bridge).removeSplitter()
            if not solid.isValid() or len(solid.Solids)!=1:
                raise RuntimeError('extension: hook bridge union failed at eye '+str(z))
            solid=solid.fuse(eye).removeSplitter()
            if not solid.isValid() or len(solid.Solids)!=1:
                raise RuntimeError('extension: closed eye union failed at eye '+str(z))
    solid=solid.removeSplitter()
    if not solid.isValid() or len(solid.Solids)!=1:
        raise RuntimeError('Helical spring wire did not form one valid solid; inspect source')
    return solid


def _compression_seat_source(b):
    """Native pivot barrel/web with integral axial reaction disk (two pads)."""
    import FreeCAD as App, Part
    import cad_common as cc
    from refine_flexor import disk,pill_face
    pn='LEG_r02_COMPRESSION_PIVOT_SEAT_NATIVE'
    if pn in b.sources:
        return b.sources[pn]
    face=disk(0,0,2.6).fuse(pill_face((0,0),(2.8,0),1.6)).cut(disk(0,0,2.025)).removeSplitter()
    body=_native_face(b,pn,face,1.2,'steel','machined pivot seat/web and axial coil seat; exact seat retention UNVERIFIED')
    base=body.Tip
    sk=b.doc.addObject('Sketcher::SketchObject',pn+'_ReactionDisk');body.addObject(sk)
    sk.Placement=App.Placement(App.Vector(3,0,.6),App.Rotation(App.Vector(0,0,1),App.Vector(1,0,0)))
    cc.circle(sk,0,0,2.4);cc.circle(sk,0,0,.65)
    pad=body.newObject('PartDesign::Pad',pn+'_ReactionPad');pad.Profile=sk;pad.Length=.6
    b.doc.recompute();sk.Visibility=False;base.Visibility=False
    return body


def _axis_placement(A,B,y):
    import FreeCAD as App
    axis=App.Vector(B[0]-A[0],0,B[1]-A[1])
    return App.Placement(App.Vector(A[0],y,A[1]),App.Rotation(App.Vector(0,0,1),axis))


def _outer_axial_placement(point,outer_y,angle,side):
    """Local +Z points inward on either side, local +X keeps sagittal sign."""
    import FreeCAD as App
    V=App.Vector;c,s=math.cos(angle),math.sin(angle)
    normal=V(0,-side,0)
    rotation=App.Rotation(V(c,0,s),V(-side*s,0,side*c),normal,'ZXY')
    return App.Placement(V(point[0],outer_y,point[1]),rotation)


def build_leg(b,tag,kind,side,transform,pose=None,include_support=True):
    """Build one native leg into b; return contract and instance/motion names.

    No document creation, pose-controller mutation, file save or export occurs.
    The caller owns recompute/verification/save and whole-robot collision checks.
    Set include_support=False when the torso already provides H's OD7/ID4.05
    housing at Y=side*42.6. H bearing/journal remain; duplicate housing is omitted.
    """
    import FreeCAD as App, Part
    import cad_common as cc
    from refine_flexor import pill_face,disk
    from retain_flexor import clip_source
    from build_flexor import profile_part
    c=leg_contract(kind,side,transform,pose);P=c['world_points'];g=c['geometry']
    planes=c['planes_y_mm'];group='Hindlegs' if kind=='hind' else 'Forelegs'
    instances=[];sources=[];motion={}
    def add(source,suffix,placement,desc,grp=group):
        source.Revision='r02'
        d=dict(desc,tag=tag,leg_type=kind,side=side)
        o=b.add(source,tag+'_'+suffix,placement,grp,d)
        instances.append(o.Name);sources.append(source.Name);motion[o.Name]=d
        return o
    def plane_at(point,center,thickness,angle):
        return cc.plane_placement(point,center+thickness/2,angle)
    for name in ('thigh','shank','return_rail'):
        spec=c['parts'][name];pn='LEG_r03_DIRECT_'+kind.upper()+'_'+name.upper()
        src=_rod_source(b,pn,spec);a,z=spec['point_names'][0],spec['point_names'][-1]
        ang=math.atan2(P[z][1]-P[a][1],P[z][0]-P[a][0])
        if name=='return_rail':
            placement=plane_at(P[a],planes[name],1.2,ang)
            rule='origin_centered_profile'
        else:
            placement=cc.line_place(P[a],P[z],planes[name],spec['width_mm'],1.2)
            rule='capsule_pivot_offset'
        add(src,name,placement,{'kind':'leg_r02_segment','a':a,'b':z,'y':planes[name],
            'width':spec['width_mm'],'thickness':1.2,'placement_rule':rule})
    spec=c['parts']['foot'];src=_foot_source(b,'LEG_r03_'+kind.upper()+'_CURVED_FOOT_RETURN_TOWARD_HIP',spec)
    angle=c['torso_angle_rad']+g['distal_angle_rad']
    add(src,'Foot',plane_at(P['A'],planes['foot'],1.2,angle),
        {'kind':'leg_r02_body','point':'A','body':'foot','y':planes['foot'],'thickness':1.2})
    # Native dark curved contact cup around the foot tip. Its contact center is F.
    V=App.Vector
    face=Part.Face(Part.Wire([
        Part.Arc(V(0,-3,0),V(3,0,0),V(0,3,0)).toShape(),
        Part.makeLine(V(0,3,0),V(0,2.5,0)),
        Part.Arc(V(0,2.5,0),V(2.5,0,0),V(0,-2.5,0)).toShape(),
        Part.makeLine(V(0,-2.5,0),V(0,-3,0))]))
    pad=_native_face(b,'LEG_r02_CURVED_CONTACT_PAD',face,2.4,'rubber','molded rubber curved contact; grip/attachment UNVERIFIED')
    add(pad,'FootPad',plane_at(P['F'],planes['foot'],2.4,angle),
        {'kind':'leg_r02_body','point':'F','body':'foot','y':planes['foot'],'thickness':2.4})
    # Bent lever arm is rigidly fixed to the shaft; its D bore is rotated
    # back by delta so its world key normal follows the thigh/shaft angle.
    pn='LEG_r03_'+kind.upper()+'_BENT_INPUT_HORN_KEYED_SAME_DIRECTION_PROVISIONAL'
    if pn in b.sources:horn=b.sources[pn]
    else:
        horn=profile_part(b,pn,14,5,1.2,[(11.5,2.5,2.05)])
        _key_bore(horn,b,2.5,2.5,c['horn']['key_flat_angle_rad'],'HornKey')
        horn.Process='fixed bent native horn, assumed +60deg fixed bend / -60deg key offset; motor spline UNVERIFIED'
    add(horn,'InputHorn',cc.line_place(P['H'],P['O2'],planes['motor_horn'],5,1.2),
        {'kind':'leg_r02_segment','a':'H','b':'O2','y':planes['motor_horn'],'width':5,'thickness':1.2,'placement_rule':'capsule_pivot_offset'})
    # Separate fixed support boss at H, supplied to the lead for torso mounting.
    if include_support:
        support=b.ring('LEG_r02_HIP_SUPPORT_OD7_BR4p05_T1p2',7,4.05,1.2,'PA12')
        add(support,'HipSupport',cc.hardware_place(P['H'],planes['hip_support'],1.2),
            {'kind':'leg_r02_point','point':'H','y':planes['hip_support'],'length':1.2})
    clip=clip_source(b)
    for point,stack in c['joints'].items():
        if point=='H':
            outer=side*max(abs(y) for y in stack['shaft_bounds_y_mm'])
            grooves=tuple(abs(outer-y)+.3 for y in stack['clip_centers_y_mm'])
            journal=_journal_source(b,stack['shaft_length_mm'],grooves,tuple(abs(outer-y) for y in stack['keyed_layers_y_mm']))
            place=_outer_axial_placement(P[point],outer,c['torso_angle_rad']+g['thigh_angle_rad'],side)
            desc={'kind':'leg_r02_body_axial','body':'motor_shaft','shaft_angle_rad':g['thigh_angle_rad'],'point':point,'y':stack['shaft_center_y_mm'],'length':stack['shaft_length_mm'],'start_y':outer,'axial_direction':-side}
        elif point=='O2':
            journal=_journal_source(b,4.8,(.8,),headed=True)
            place=_outer_axial_placement(P[point],side*55.6,0,side)
            desc={'kind':'leg_r02_headed_pin','point':point,'outer_y':side*55.6,'length':4.8,'axial_direction':-side}
        else:
            journal=_journal_source(b,stack['shaft_length_mm'])
            place=cc.hardware_place(P[point],stack['shaft_center_y_mm'],stack['shaft_length_mm'])
            desc={'kind':'leg_r02_point','point':point,'y':stack['shaft_center_y_mm'],'length':stack['shaft_length_mm']}
        add(journal,point+'_Journal',place,desc)
        for j,y in enumerate(stack['layers_y_mm']):
            # Both H rotating parts are keyed; only the ground support bears.
            if point=='O2' or (point=='H' and y not in stack['bearing_layers_y_mm']) or (point in ('O2','O3') and abs(y-planes['extension'])<1e-8):
                continue
            bearing=b.ring('LEG_r02_BRG_2x4x1p2_PROVISIONAL',4,2,1.2)
            add(bearing,point+'_Bearing'+str(j),cc.hardware_place(P[point],y,1.2),
                {'kind':'leg_r02_point','point':point,'y':y,'length':1.2})
        for j,y in enumerate(stack['clip_centers_y_mm']):
            add(clip,point+'_Clip'+str(j),cc.hardware_place(P[point],y,.6),
                {'kind':'leg_r02_point','point':point,'y':y,'length':.6})
        for j,s in enumerate(stack['spacers']):
            L=s['length_mm'];y=s['center_y_mm'];pn='LEG_r02_SPACER_D3_ID2p05_L'+str(round(L,5)).replace('.','p')
            spacer=b.ring(pn,3,2.05,L)
            add(spacer,point+'_Spacer'+str(j),cc.hardware_place(P[point],y,L),
                {'kind':'leg_r02_point','point':point,'y':y,'length':L})
    # H's one-piece grooved/locally keyed shaft already extends to the case
    # output face 42.0; no duplicate adapter overlaps that rotating journal.
    # Coil solids and separately supported pivot/seat/guide hardware.
    for name,s in c['springs'].items():
        a,z=s['anchors'];A,B=P[a],P[z];L=s['length_mm'];y=s['plane_y_mm']
        pn='LEG_r02_'+tag+'_'+name.upper()+'_WIRE_L'+str(round(L,8)).replace('.','p')
        shape=spring_shape(s['coil_length_mm'],name,s['coil_free_length_mm'])
        source=cc.simple_shape(b.doc,pn,shape,'spring','actual assumed coil wire; rate/fatigue/catalog UNVERIFIED',role='SPRING')
        for key,val in [('FreeLength_mm',s['coil_free_length_mm']),('AnchorFreeLength_mm',s['free_length_mm']),('InstalledCoilLength_mm',s['coil_length_mm']),('SeatInset_mm',s['seat_offset_mm']),('WireDiameter_mm',.5),('OuterDiameter_mm',4)]:
            source.addProperty('App::PropertyLength',key,'SpringAssumptions');setattr(source,key,val)
        source.addProperty('App::PropertyString','Provenance');source.Provenance='DESIGN_ASSUMPTION'
        b.library.addObject(source);b.sources[pn]=source
        unit=((B[0]-A[0])/L,(B[1]-A[1])/L)
        spring_origin=(A[0]+unit[0]*s['seat_offset_mm'],A[1]+unit[1]*s['seat_offset_mm'])
        add(source,name+'_Spring',_axis_placement(spring_origin,B,y),
            {'kind':'leg_r02_spring','spring':name,'a':a,'b':z,'y':y,'free_length_mm':s['free_length_mm'],'seat_offset_mm':s['seat_offset_mm'],'rebuild_length_dependent_source':True},'ElasticElements')
        if name=='compression':
            seat=_compression_seat_source(b)
            for end,(point,toward) in enumerate(((a,z),(z,a))):
                ang=math.atan2(P[toward][1]-P[point][1],P[toward][0]-P[point][0])
                add(seat,name+'_SeatAssembly'+str(end),plane_at(P[point],y,1.2,ang),
                    {'kind':'leg_r02_compression_seat','a':point,'b':toward,'y':y,'thickness':1.2,'seat_face_offset_mm':3.6},'ElasticElements')
            # Fixed-length guide rod/tube. Opposing seat inner faces delimit
            # engagement; no part is scaled or resized in place during motion.
            end_origin=(B[0]-unit[0]*3.6,B[1]-unit[1]*3.6)
            rod=b.ring('LEG_r02_COMP_GUIDE_ROD_D1p2_L14',1.2,0,14)
            tube=b.ring('LEG_r02_COMP_GUIDE_TUBE_OD1p7_ID1p3_L14',1.7,1.3,14)
            add(rod,name+'_GuideRod',_axis_placement(spring_origin,B,y),
                {'kind':'leg_r02_spring_guide','a':a,'b':z,'y':y,'offset_mm':3.6,'length':14},'ElasticElements')
            add(tube,name+'_GuideTube',_axis_placement(end_origin,A,y),
                {'kind':'leg_r02_spring_guide','a':z,'b':a,'y':y,'offset_mm':3.6,'length':14},'ElasticElements')
    b.doc.recompute()
    return {'tag':tag,'contract':c,'sources':tuple(dict.fromkeys(sources)),
            'instances':tuple(instances),'motion':motion,
            'limitations':('CAD validity/clearances NOT_RUN by worker',
              'Case-face manufacturer output coupling/axial capture, spline and D extension torque capacity unresolved',
              'Compression seat free-length conversion 7.2mm and guide engagement require CAD verification',
              'Bonded curved contact pad attachment/grip unverified',
              'Spring wire is real helical BRep; catalog/rate/fatigue unverified',
              'Whole-robot spring/moving-journal clearances and loaded equilibrium unverified')}
