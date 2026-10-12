"""Native moving-link graph audit against supplement Fig S9."""
import FreeCAD as App,Part,json,math
from collections import Counter
from pathlib import Path
from kinematics import spine

EXPECTED=[('O','G'),('G','B1'),('G','B2'),('A1','B1'),('A2','B2'),('B1','C1'),('B2','C2'),('C1','D1'),('C2','D2'),('E1','D1'),('E2','D2')]

def run(doc,p,root,revision='r03'):
    state=spine(doc.PoseController.SpinePhaseRad,p);motion=json.loads(doc.PoseController.MotionMap)
    rows=[];errors=[];axis_issues=[];torso_axes=[];missing={};extra={};observed={-1:[],1:[]}
    for n,m in motion.items():
        if m.get('kind')!='segment' or not n.startswith(('Link','DirectCrank')):continue
        o=doc.getObject(n)
        if o is None:continue
        edge=(m['a'],m['b']);side=1 if m['y']>0 else -1;observed[side].append(edge)
        bores=[]
        for sk in o.LinkedObject.Group:
            if sk.TypeId!='Sketcher::SketchObject':continue
            for g in sk.Geometry:
                if isinstance(g,Part.Circle):
                    P=o.LinkPlacement.multVec(sk.Placement.multVec(g.Center));bores.append((P.x,P.z))
        for key in edge:errors.append(min(math.dist(state[key],P) for P in bores))
        rows.append({'instance':n,'side':side,'edge':edge,'role':'moving source link'})
    for kind,i in [('hind',1),('fore',2)]:
        o=doc.getObject('Torso_'+kind)
        if o is None:continue
        edge=(f'E{i}',f'D{i}')
        # o.Shape already contains the AppLink world placement. Inspect the
        # physical cylindrical bore surfaces directly: transforming them again
        # through LinkPlacement would double-apply the torso motion. This works
        # for both old cages and r06's independently sketched E/D ears.
        candidates={-1:[],1:[]}
        for face in o.Shape.Faces:
            surface=face.Surface
            if not isinstance(surface,Part.Cylinder) or abs(surface.Radius-2.025)>1e-6:continue
            axis=surface.Axis
            if axis.Length<=1e-12 or abs(axis.y)/axis.Length<1-1e-8:continue
            cy=float(face.CenterOfMass.y)
            side=1 if cy>0 else -1
            if abs(cy-side*15.2)>1.0:continue
            center=surface.Center
            candidates[side].append({'axis_point_world_mm':(float(center.x),float(center.y),float(center.z)),
                'axis_direction_world':tuple(float(v)/axis.Length for v in axis),
                'face_center_y_mm':cy,'radius_mm':float(surface.Radius)})
        for side in (-1,1):
            for key in edge:
                available=candidates[side]
                if not available:
                    axis_issues.append({'instance':o.Name,'side':side,'pivot':key,
                        'error':'No native radius2.025 Y-axis cylindrical bore in side band centered at Y='+str(side*15.2)})
                    continue
                chosen=min(available,key=lambda q:math.dist(state[key],(q['axis_point_world_mm'][0],q['axis_point_world_mm'][2])))
                error=math.dist(state[key],(chosen['axis_point_world_mm'][0],chosen['axis_point_world_mm'][2]))
                errors.append(error)
                torso_axes.append(dict(chosen,instance=o.Name,side=side,pivot=key,axis_error_mm=error))
            observed[side].append(edge)
        rows.append({'instance':o.Name,'sides':[-1,1],'edge':edge,'role':'rigid torso frame replaces E-D output rocker'})
    for side in [-1,1]:
        missing[str(side)]=list((Counter(EXPECTED)-Counter(observed[side])).elements())
        extra[str(side)]=list((Counter(observed[side])-Counter(EXPECTED)).elements())
    maximum_error=max(errors,default=0.0)
    status='PASS' if not axis_issues and errors and not any(missing.values()) and not any(extra.values()) and maximum_error<1e-4 else 'FAIL'
    result={'status':status,'source':'Supplement PDF p30 Fig S9; translucent rods in panelA are alternate poses',
            'expected_projected_edges':EXPECTED,'physical_moving_members':rows,'missing_edges':missing,'extra_edges':extra,
            'actual_native_hole_axis_error_mm':maximum_error,'torso_native_bore_axes':torso_axes,'native_axis_issues':axis_issues,'projected_mobility':{'links_including_ground_and_two_slider_blocks':14,'one_DOF_joint_equivalents':19,'planar_gruebler':3*(14-1)-2*19},
            'fixed_structure':'LumbarIntegrated A/E backbone, motor cradle and C/A guide ears are one grounded frame; no independently moving frame bars',
            'bilateral_copies':'Two side planes share one phase and B synchronization shafts; they are not extra independent planar links',
            'limits':'Source topology and native axis audit, not complete spatial mobility, elastic equilibrium or fabrication validation'}
    Path(root,f'reports/verification/{revision}_s9_topology.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k!='physical_moving_members'}));return result
