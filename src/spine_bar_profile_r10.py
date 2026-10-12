"""Lead-run native long-link relief refinement; no axes, saves or GUI calls."""
import json,math
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def rounded_rectangle_geometry(x,y,w,h,r):
    import FreeCAD as App,Part
    if not 0 < r < min(w,h)/2:raise ValueError('Invalid relief corner radius')
    V=lambda xx,yy:App.Vector(xx,yy,0)
    # A single explicit boundary, not every edge of a planar Boolean result:
    # the latter can retain internal seams and leave a stale failed Pocket.
    line=lambda a,b:Part.LineSegment(V(*a),V(*b))
    arc=lambda cx,cy,a,b:Part.ArcOfCircle(Part.Circle(V(cx,cy),App.Vector(0,0,1),r),a,b)
    return [line((x+r,y),(x+w-r,y)),arc(x+w-r,y+r,-math.pi/2,0),
            line((x+w,y+r),(x+w,y+h-r)),arc(x+w-r,y+h-r,0,math.pi/2),
            line((x+w-r,y+h),(x+r,y+h)),arc(x+r,y+h-r,math.pi/2,math.pi),
            line((x,y+h-r),(x,y+r)),arc(x+r,y+r,math.pi,3*math.pi/2)]

def rebuild_profile(doc):
    import Sketcher
    import cad_common as cc
    from kinematics import load_parameters
    cfg=json.loads((ROOT/'parameters/assembly_r10.json').read_text())['bar_profile_r10']
    source=doc.getObject(cfg['long_source_name']);sketch=doc.getObject(source.Name+'_Cuts')
    length=load_parameters(ROOT/'parameters/candidate_r02.json')['L4_mm'];width=6.0
    for j in range(sketch.GeometryCount-1,-1,-1):sketch.delGeometry(j)
    for x in (width/2,length+width/2):cc.circle(sketch,x,width/2,cfg['bore_diameter_mm']/2)
    inset=cfg['relief_end_inset_from_bore_mm'];rw=cfg['relief_width_mm']
    for g in rounded_rectangle_geometry(width/2+inset,(width-rw)/2,length-2*inset,rw,cfg['relief_corner_radius_mm']):
        j=sketch.addGeometry(g,False);sketch.addConstraint(Sketcher.Constraint('Block',j))
    sketch.solve();doc.recompute()
    if sketch.GeometryCount!=10 or not sketch.FullyConstrained or any('Invalid' in o.State for o in source.Group):
        raise RuntimeError('Long-link native feature recomputation failed')
    if not source.Shape.isValid() or len(source.Shape.Solids)!=1:raise RuntimeError('Long-link solid invalid')
    sketch.Visibility=False
    return source

def apply(b):
    import Part,Sketcher
    import cad_common as cc
    cfg=json.loads((ROOT/'parameters/assembly_r10.json').read_text())['bar_profile_r10']
    source=b.doc.getObject(cfg['long_source_name'])
    if source is None or source.TypeId!='PartDesign::Body':raise ValueError('Expected actual long-link Body')
    if source.Revision=='r10':raise ValueError('Long-link r10 profile already applied')
    instances=[o for o in b.doc.Objects if o.TypeId=='App::Link' and o.LinkedObject==source]
    if len(instances)!=4:raise ValueError('Expected four B-C link instances')
    descriptors=[b.motion[o.Name] for o in instances]
    if any(m['kind']!='segment' or m['width']!=6 or m['thickness']!=cfg['thickness_mm'] for m in descriptors):
        raise ValueError('Unexpected link frame/thickness')
    sketch=b.doc.getObject(source.Name+'_Cuts')
    if sketch is None:raise ValueError('Long-link bore/relief sketch missing')
    # Both bores remain exact in the same source-local frame. Recreate only the
    # cut profile so all four instances retain their placements and MotionMap.
    length=b.p['L4_mm'];width=6.0;r=cfg['bore_diameter_mm']/2
    before={o.Name:str(o.LinkPlacement) for o in instances}
    rebuild_profile(b.doc)
    rw=cfg['relief_width_mm']
    if not sketch.FullyConstrained or not source.Shape.isValid() or len(source.Shape.Solids)!=1:
        raise RuntimeError('Long-link native profile invalid')
    if before!={o.Name:str(o.LinkPlacement) for o in instances}:raise RuntimeError('Link placement changed')
    source.PartNumber='SPN_LONG_BC_RELIEVED_r10';source.Revision='r10'
    source.Process+='; r10 rounded-rectangular through relief; Movie S1 morphology, metric profile/strength DESIGN_ASSUMPTION'
    sketch.Visibility=False
    return {'source':source.Name,'part_number':source.PartNumber,'instances':[o.Name for o in instances],
            'bores_local_xy_mm':[[width/2,width/2],[length+width/2,width/2]],
            'bore_diameter_mm':2*r,'center_distance_mm':length,'thickness_mm':cfg['thickness_mm'],
            'side_rail_width_mm':(width-rw)/2,'profile_fully_constrained':True,
            'source_frame_and_placements_preserved':True,'short_bar_profiles':'unchanged; source supports plain bars',
            'limits':'No fork/chamfer assigned without identified source layering; strength and fits unverified'}
