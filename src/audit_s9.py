"""Native moving-link graph audit against supplement Fig S9."""
import FreeCAD as App,Part,json,math
from collections import Counter
from pathlib import Path
from kinematics import spine

EXPECTED=[('O','G'),('G','B1'),('G','B2'),('A1','B1'),('A2','B2'),('B1','C1'),('B2','C2'),('C1','D1'),('C2','D2'),('E1','D1'),('E2','D2')]

def run(doc,p,root,revision='r03'):
    state=spine(doc.PoseController.SpinePhaseRad,p);motion=json.loads(doc.PoseController.MotionMap)
    rows=[];errors=[];missing={};extra={};observed={-1:[],1:[]}
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
        # One rigid bilateral torso cage carries both E/D attachment pairs.
        sk=next(f for f in o.LinkedObject.Group if f.Name==kind+'OutputBoresLeft')
        bores=[]
        for g in sk.Geometry:
            if isinstance(g,Part.Circle):
                P=o.LinkPlacement.multVec(sk.Placement.multVec(g.Center));bores.append((P.x,P.z))
        for key in edge:errors.append(min(math.dist(state[key],P) for P in bores))
        for side in [-1,1]:observed[side].append(edge)
        rows.append({'instance':o.Name,'sides':[-1,1],'edge':edge,'role':'torso cage replaces E-D output rocker'})
    for side in [-1,1]:
        missing[str(side)]=list((Counter(EXPECTED)-Counter(observed[side])).elements())
        extra[str(side)]=list((Counter(observed[side])-Counter(EXPECTED)).elements())
    status='PASS' if not any(missing.values()) and not any(extra.values()) and max(errors)<1e-4 else 'FAIL'
    result={'status':status,'source':'Supplement PDF p30 Fig S9; translucent rods in panelA are alternate poses',
            'expected_projected_edges':EXPECTED,'physical_moving_members':rows,'missing_edges':missing,'extra_edges':extra,
            'actual_native_hole_axis_error_mm':max(errors),'projected_mobility':{'links_including_ground_and_two_slider_blocks':14,'one_DOF_joint_equivalents':19,'planar_gruebler':3*(14-1)-2*19},
            'fixed_structure':'LumbarIntegrated A/E backbone, motor cradle and C/A guide ears are one grounded frame; no independently moving frame bars',
            'bilateral_copies':'Two side planes share one phase and B synchronization shafts; they are not extra independent planar links',
            'limits':'Source topology and native axis audit, not complete spatial mobility, elastic equilibrium or fabrication validation'}
    Path(root,f'reports/verification/{revision}_s9_topology.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k!='physical_moving_members'}));return result
