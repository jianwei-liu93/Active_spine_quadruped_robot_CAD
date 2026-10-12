"""Lead-executed native Movie-S1 fixed-frame candidate; no automatic CAD calls.

Movie52/54 bare frame and shaft58 motivate horizontal E1--E2 rail, short
E1--A2/E2--A1 ears and broad shelves. See source_review/movie_s1_exploded_spine.md.
Dimensions remain frozen reconstruction assumptions, not recovered tooling.
Slot formulas, S9 pivots, case30deg and existing physical tie hardware stay
unchanged. Case collars/bands and tie recesses copy r02 native feature logic;
no shim, tie, screw, shaft, liner or other assembly instance is added here.
Native validation and interference were NOT_RUN by this source worker.
"""
import math


def apply(b):
    """Replace only the two lumbar source bodies, preserving AppLinks/placements.

    Construct both new sources before swapping. Remove an old source only if
    no AppLink still uses it. Never save the document or mutate shaft sources.
    """
    import FreeCAD as App, Part
    import cad_common as cc
    from refine_flexor import rect,disk,pill_face,sketch_face
    from kinematics import spine
    from spine_attachments_r02 import provisional_parameters,rotate_plane
    doc=b.doc;p=b.p;s=spine(0,p);V=App.Vector
    angle=p['spine_case_angle_rad'];cfg=provisional_parameters()
    if abs(angle-math.pi/6)>1e-9:raise ValueError('r04 frozen case angle requires 30deg')
    links={side:doc.getObject('LumbarIntegrated1' if side==1 else 'LumbarIntegrated_1') for side in (1,-1)}
    if any(o is None or o.TypeId!='App::Link' for o in links.values()):
        raise ValueError('Both existing LumbarIntegrated AppLinks are required')
    def rotate(face):
        face=face.copy();face.rotate(V(),V(0,0,1),math.degrees(angle));return face
    def section(face):
        # Resolve 2D boolean compounds in 3D, then retain ALL section wires.
        pieces=[f.extrude(V(0,0,1)) for f in face.Faces]
        if not pieces:raise RuntimeError('empty frame section')
        solid=pieces[0]
        for q in pieces[1:]:solid=solid.fuse(q)
        solid=solid.removeSplitter()
        if not solid.isValid() or len(solid.Solids)!=1:raise RuntimeError('frame section must be connected')
        bottoms=[f for f in solid.Faces if f.BoundBox.ZLength<1e-7 and abs(f.CenterOfMass.z)<1e-7]
        if len(bottoms)!=1:raise RuntimeError('frame section must have one complete bottom face')
        return bottoms[0]
    def pad(body,label,face,z,length,reverse=False):
        old=body.Tip;sk=sketch_face(doc,body,body.Name+'_'+label+'Sketch',section(face),z)
        feature=body.newObject('PartDesign::Pad',body.Name+'_'+label);feature.Profile=sk;feature.Length=length;feature.Reversed=reverse
        doc.recompute();sk.Visibility=False
        if old:old.Visibility=False
        return feature
    def pocket(body,label,holes,z,depth,reverse=False):
        sk=doc.addObject('Sketcher::SketchObject',body.Name+'_'+label+'Sketch');body.addObject(sk);sk.Placement.Base.z=z
        for x,y,r in holes:cc.circle(sk,x,y,r)
        old=body.Tip;feature=body.newObject('PartDesign::Pocket',body.Name+'_'+label);feature.Profile=sk;feature.Length=depth;feature.Reversed=reverse
        doc.recompute();sk.Visibility=False;old.Visibility=False
        return feature
    annulus=rotate(rect(-12,-9,24,38).cut(rect(-10.4,-7.4,20.8,34.8)))
    collar=rotate(rect(-12,-9,24,38).cut(rect(-10,-7,20,34)))
    bands=[rotate(rect(-12,-7,24,1.5)),rotate(rect(-12,24,24,3))]
    corners=[rotate_plane(P,angle) for P in cfg['tie_corners_case_local_mm']]
    guides=[];slot_report=[]
    for i,sign in ((1,1),(2,-1)):
        xs=[spine(j*math.tau/720,p)['C'+str(i)][0] for j in range(721)]
        xc=(min(xs)+max(xs))/2;zc=sign*p['guide_z_mm']
        ax,az=s['A2' if i==1 else 'A1'];r=p['guide_pivot_radius_mm']
        pts=[V(xc-6.5,zc,0),V(xc+6.5,zc,0),V(ax+r,az,0),V(ax-r,az,0)]
        web=Part.Face(Part.makePolygon(pts+[pts[0]]))
        face=pill_face((xc-6.5,zc),(xc+6.5,zc),8.2).fuse(web).fuse(disk(ax,az,r))
        face=face.cut(pill_face((xc-6.5,zc),(xc+6.5,zc),5.2)).cut(disk(ax,az,2.025)).removeSplitter()
        guides.append(face)
        slot_report.append({'slider':'C'+str(i),'pivot':'A2' if i==1 else 'A1','center_xz_mm':(xc,zc),'travel_bounds_x_mm':(min(xs),max(xs))})
    new={};features={}
    for side in (1,-1):
        suffix='L' if side==1 else 'R';pn='FRM_LUMBAR_HORIZONTAL_SHELF_'+suffix+'_r04'
        if doc.getObject(pn):raise ValueError(pn+' exists; rebuild in fresh document to avoid mutating cached source')
        body=doc.addObject('PartDesign::Body',pn)
        cc.metadata(body,pn,'PA12','ASSUMED Movie-S1 horizontal rail/case cradle; native shelf/slot/clamp; fits and preload UNVERIFIED')
        body.Revision='r04'
        pad(body,'CaseWindowBase',annulus,0,1.6)
        for label,A,B in (('HorizontalPlatform','E1','E2'),('ShortEarE1A2','E1','A2'),('ShortEarE2A1','E2','A1')):
            pad(body,label,pill_face(s[A],s[B],5),0,1.6)
        for j,face in enumerate((rect(-35.5,-2.5,19.5,5),rect(16,-2.5,19.5,5))):
            pad(body,'BroadShelf'+str(j),face,0 if side==1 else 1.6,11,side==1)
        for j,face in enumerate(guides):
            pad(body,'OuterGuide'+str(j),face,-11 if side==1 else 12.6,1.6,side==1)
        # Brace bosses added individually rather than a disconnected 2D fusion.
        for j,P in enumerate(corners):pad(body,'BraceBoss'+str(j),disk(*P,cfg['tie_boss_radius_mm']),0,1.6)
        pad(body,'CaseEdgeCollar',collar,1.6 if side==1 else 0,1.4,side==-1)
        for j,band in enumerate(bands):pad(body,'CaseFaceBand'+str(j),band,1.6 if side==1 else 0,.4,side==-1)
        pocket(body,'TieClearances',[(P[0],P[1],cfg['screw_clearance_mm']/2) for P in corners],1.6,1.6)
        pocket(body,'TieCollarRecesses',[(P[0],P[1],cfg['tie_collar_recess_mm']/2) for P in corners],3 if side==1 else -1.4,1.4,side==-1)
        # OD7 bosses leave 1.475mm radial wall around selected OD4.05 seats.
        for key in ('A1','A2'):pad(body,'InnerJournalBoss'+key,disk(*s[key],3.5),0,1.6)
        for key in ('E1','E2'):pad(body,'ShelfJournalBoss'+key,disk(*s[key],3.5),1.6 if side==1 else 0,14.2,side==1)
        # Final cuts clear every base/shelf/collar feature across the whole stack.
        pocket(body,'WholeStackJournalClearances',[(0,0,6.5)]+[(s[n][0],s[n][1],2.025) for n in ('A1','A2','E1','E2')],14.2,26.8)
        doc.recompute()
        if not body.Shape.isValid() or len(body.Shape.Solids)!=1:
            raise RuntimeError(pn+' requires one valid native solid before replacement')
        b.library.addObject(body);b.sources[body.Name]=body;new[side]=body
        features[side]=tuple(o.Name for o in body.Group if o.TypeId in ('PartDesign::Pad','PartDesign::Pocket'))
    old={side:links[side].LinkedObject for side in links}
    placements={side:links[side].LinkPlacement for side in links}
    for side in links:
        links[side].setLink(new[side]);links[side].LinkPlacement=placements[side]
    doc.recompute();removed=[];retained=[]
    for source in {o.Name:o for o in old.values()}.values():
        owned={o.Name for o in [source]+list(getattr(source,'Group',[]))}
        external=[q for o in [source]+list(getattr(source,'Group',[])) for q in o.InList
                  if q.Name not in owned and q!=b.library]
        if external or any(o.TypeId=='App::Link' and o.LinkedObject==source for o in doc.Objects):
            retained.append(source.Name);continue
        # Only the exact replaced source is eligible for deletion; other cached
        # definitions and hardware remain untouched.
        oldname=source.Name
        for key,val in list(b.sources.items()):
            if val.Name==oldname:del b.sources[key]
        for child in reversed(list(getattr(source,'Group',[]))):doc.removeObject(child.Name)
        doc.removeObject(oldname);removed.append(oldname)
    doc.recompute()
    return {'instances':tuple(o.Name for o in links.values()),'sources':tuple(o.Name for o in new.values()),
            'features':features,'guide_slots':slot_report,'removed_unused_sources':tuple(removed),'retained_used_sources':tuple(retained),
            'worker_validation':'CAD validity/collision NOT_RUN','execution_native_validity':True,
            'limitations':('Whole-spine collision and motion sweep require lead validation','Shelf, clamp fit/preload and fabrication dimensions remain assumptions','Existing shaft/liner/tie/shim hardware preserved; no new attachment hardware added')}
