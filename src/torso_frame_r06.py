"""Native transverse output frames; lead-only r06 candidate construction.

Movie S1 attachment morphology: reports/source_review/
movie_s1_frame_attachment_r06.md. All dimensions/slots/case capture are frozen
DESIGN_ASSUMPTION in assembly_r06.json. No vendor hole pattern is inferred.
Preserves existing torso AppLink placement/motion and all separate hardware.
Old integral knee/guide supports are deliberately replaced with the old body;
the lead must regenerate them on these compact orthogonal mounts.
"""
import json
import math
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]


def apply(b, remove_old=True):
    """Create two connected native frames and swap only Torso_fore/hind sources.

    Existing source mapping is torsoXYZ -> source(x,z,16-y). No save, live
    tool call, shaft/motor/link-placement change or motion-map edit occurs.
    Repeated apply rejects before adding features. Final runtime BRep checks
    are lead execution checks, not source-worker validation evidence.
    """
    import FreeCAD as App,Part
    import cad_common as cc
    from refine_flexor import rect,disk,pill_face,sketch_face
    from kinematics import spine
    from leg_geometry_r02 import leg_geometry
    cfg=json.loads((ROOT/'parameters/assembly_r06.json').read_text())['attachment_frame']
    doc=b.doc;s=spine(0,b.p);V=App.Vector
    names={k:'TORSO_'+k.upper()+'_TRANSVERSE_FRAME_r06' for k in ('fore','hind')}
    if any(doc.getObject(n) for n in names.values()):raise ValueError('r06 transverse frames already exist; repeated application rejected')
    links={k:doc.getObject('Torso_'+k) for k in names}
    if any(o is None or o.TypeId!='App::Link' for o in links.values()):raise ValueError('Existing Torso_fore/hind AppLinks required')
    xyz=lambda p:V(p[0],p[2],16-p[1])
    vec=lambda p:V(p[0],p[2],-p[1])
    def rounded(x,y,w,h,r):
        pts=[(x+r,y),(x+w-r,y),(x+w,y+r),(x+w,y+h-r),(x+w-r,y+h),(x+r,y+h),(x,y+h-r),(x,y+r)]
        # Quarter-circle midpoints preserve exact arc/line profiles.
        d=r/math.sqrt(2)
        mids=[(x+w-r+d,y+r-d),(x+w-r+d,y+h-r+d),(x+r-d,y+h-r+d),(x+r-d,y+r-d)]
        p=lambda q:V(q[0],q[1],0)
        edges=[]
        for j in range(4):
            i=2*j;edges.append(Part.makeLine(p(pts[i]),p(pts[(i+1)%8])))
            edges.append(Part.Arc(p(pts[(i+1)%8]),p(mids[j]),p(pts[(i+2)%8])).toShape())
        return Part.Face(Part.Wire(edges))
    def pad(body,label,face,origin,u,v,normal,length):
        old=body.Tip;sk=sketch_face(doc,body,body.Name+'_'+label+'Profile',face)
        sk.Placement=App.Placement(xyz(origin),App.Rotation(vec(u),vec(v),vec(normal),'ZXY'))
        feature=body.newObject('PartDesign::Pad',body.Name+'_'+label);feature.Profile=sk;feature.Length=length
        doc.recompute();sk.Visibility=False
        if old:old.Visibility=False
        if not feature.Shape.isValid() or len(feature.Shape.Solids)!=1:
            raise RuntimeError(body.Name+' '+label+': native feature must remain one connected valid solid')
        return feature
    def sagittal(body,label,face,y,thickness):
        return pad(body,label,face,(0,y,0),(1,0,0),(0,0,1),(0,-1,0),thickness)
    def horizontal(body,label,x0,x1,y0,y1,z,thickness):
        return pad(body,label,rect(x0,y0,x1-x0,y1-y0),(0,0,z),(1,0,0),(0,1,0),(0,0,1),thickness)
    result={};axisframes={};features={}
    for kind in ('fore','hind'):
        body=doc.addObject('PartDesign::Body',names[kind]);cc.metadata(body,body.Name,'PA12','DESIGN_ASSUMPTION Movie-S1 transverse frame; generic slots; supplier pattern/capture/load UNVERIFIED');body.Revision='r06'
        sign=cfg['plate_normal_x'][kind];px=cfg['plate_inner_x_mm'][kind];T=cfg['plate_thickness_mm']
        ymin,ymax=cfg['plate_y_bounds_mm'];zmin,zmax=cfg['plate_z_bounds_mm'];width=cfg['slot_width_mm']
        plate=rounded(ymin,zmin,ymax-ymin,zmax-zmin,cfg['plate_corner_radius_mm'])
        # Plate sketch X is sign*torsoY; symmetric Y bounds/pattern preserve
        # the prescribed YZ coordinates for either outward X normal.
        slots=[(0,0,cfg['center_slot_z_length_mm'])]+[(sign*y,z,cfg['corner_slot_z_length_mm']) for y,z in cfg['corner_slot_centers_yz_mm']]
        for y,z,L in slots:plate=plate.cut(pill_face((y,z-(L-width)/2),(y,z+(L-width)/2),width))
        pad(body,'TransverseSlottedPlate',plate,(px,0,0),(0,sign,0),(0,0,1),(sign,0,0),T)
        i=1 if kind=='hind' else 2;E=s['E'+str(i)];D=tuple(s['D'+str(i)][j]-E[j] for j in (0,1));H=leg_geometry(kind)['H']
        # Independent short bearing ears; no E-D/E-H/D-H triangle/bar.
        for side,y in enumerate(cfg['ear_y_centers_mm']):
            for label,P in (('E',(0,0)),('D',D)):
                face=pill_face(P,(px,P[1]),cfg['ear_width_mm']).cut(disk(*P,cfg['bearing_bore_mm']/2))
                sagittal(body,'Ear'+label+str(side),face,y+cfg['ear_thickness_mm']/2,cfg['ear_thickness_mm'])
        x0,x1=cfg['case_x_bounds_mm'][kind];cz0,cz1=cfg['case_z_bounds_mm'][kind];pt=cfg['pan_thickness_mm']
        case_end=x0 if sign==1 else x1
        if abs(case_end-(px+sign*T))>1e-9:
            raise ValueError('Pan case end must meet transverse plate outer face exactly')
        y0,y1=cfg['pan_y_bounds_positive_mm'];outer=cfg[kind+'_panel_xz_outer_mm'];window=cfg[kind+'_panel_xz_window_mm']
        for side in (-1,1):
            label='L' if side==1 else 'R';lo,hi=sorted((side*y0,side*y1))
            # Pan first touches transverse plate at its case-end face; panel
            # then intersects pan over its complete outboard axial thickness.
            horizontal(body,'BottomPan'+label,x0,x1,lo,hi,cz0-pt,pt)
            panel=rect(*outer).cut(rect(*window)).fuse(disk(*H,cfg['outer_hip_boss_od_mm']/2)).cut(disk(*H,cfg['bearing_bore_mm']/2)).removeSplitter()
            sagittal(body,'OuterHPanel'+label,panel,side*abs(cfg['outer_hip_support_y_mm'][1])+cfg['outer_hip_panel_thickness_mm']/2,cfg['outer_hip_panel_thickness_mm'])
            sw=cfg['top_strap_x_width_mm']
            for j,x in enumerate((x0,x1-sw)):horizontal(body,'TopStrap'+label+str(j),x,x+sw,lo,hi,cz1,pt)
            band=cfg['inner_case_band_width_mm'];by0,by1=sorted((side*y0,side*cfg['case_y_bounds_positive_mm'][0]))
            sagittal(body,'InnerCaseCapture'+label,rect(H[0]-band/2,cz0,band,cz1-cz0),by1,by1-by0)
        if kind=='hind':
            a,c=cfg['hind_knee_connector_x_bounds_mm'];ya,yb=cfg['hind_knee_connector_y_bounds_positive_mm'];za,zb=cfg['hind_knee_connector_z_bounds_mm']
            for side in (-1,1):
                lo,hi=sorted((side*ya,side*yb));horizontal(body,'KneeConnector'+('L' if side==1 else 'R'),a,c,lo,hi,za,zb-za)
        body.addProperty('App::PropertyString','AttachmentProvenance','Source');body.AttachmentProvenance=cfg['supplier_mounting_pattern']
        doc.recompute();b.library.addObject(body);b.sources[body.Name]=body;result[kind]=body
        features[kind]=tuple(o.Name for o in body.Group if o.TypeId=='PartDesign::Pad')
        axisframes[kind]={'E_xz':(0,0),'D_xz':D,'H_xz':H,'bearing_axis_torso':(0,1,0),'plate_normal_torso':(sign,0,0),'plate_inner_x_mm':px}
    old={k:links[k].LinkedObject for k in links};placements={k:links[k].LinkPlacement for k in links}
    for kind in links:links[kind].setLink(result[kind]);links[kind].LinkPlacement=placements[kind]
    doc.recompute();removed=[];retained=[]
    for source in {o.Name:o for o in old.values()}.values():
        if not remove_old:
            retained.append(source.Name);continue
        owned={o.Name for o in [source]+list(getattr(source,'Group',[]))}
        external=[q for o in [source]+list(getattr(source,'Group',[])) for q in o.InList if q.Name not in owned and q!=b.library]
        if external or any(o.TypeId=='App::Link' and o.LinkedObject==source for o in doc.Objects):retained.append(source.Name);continue
        name=source.Name
        for key,val in list(b.sources.items()):
            if val.Name==name:del b.sources[key]
        children=[o.Name for o in source.Group]
        doc.getObject('PartsLibrary').removeObject(source)
        doc.removeObject(name)
        for childname in reversed(children):
            if doc.getObject(childname) is not None:doc.removeObject(childname)
        removed.append(name)
    doc.recompute()
    return {'bodies':{k:o.Name for k,o in result.items()},'instances':{k:o.Name for k,o in links.items()},'axisframes':axisframes,'native_features':features,'removed_unused_sources':removed,'retained_referenced_sources':retained,
            'worker_validation':'CAD validity/interference NOT_RUN','assumptions':('Generic slots are not verified supplier mounting holes','Dimensions/case contact/load capacity provisional','Existing seven motors, leg/cable datums and separate hardware preserved','Old integral hind knee/guide mounts removed with old torso; lead must regenerate')}
