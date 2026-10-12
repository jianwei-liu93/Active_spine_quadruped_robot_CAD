"""Pure rigid-matrix checks; no FreeCAD imports or native BRep claims."""
import json
import math
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from robot_pose_r03 import _tendon_placement,_guard_installed_tendons,KINDS
from tendon_r03 import tendon_route


def dot(a,b):return sum(x*y for x,y in zip(a,b))
def cross(a,b):return (a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0])
def unit(a):return tuple(x/math.sqrt(dot(a,a)) for x in a)
class Rotation:
    def __init__(self,*args):
        if not args:self.M=((1,0,0),(0,1,0),(0,0,1));return
        if len(args)==4 and args[3]=='ZXY':
            self.M=tuple(zip(*args[:3]));return
        if len(args)==4:
            x,y,z,w=args
            self.M=((1-2*(y*y+z*z),2*(x*y-z*w),2*(x*z+y*w)),(2*(x*y+z*w),1-2*(x*x+z*z),2*(y*z-x*w)),(2*(x*z-y*w),2*(y*z+x*w),1-2*(x*x+y*y)));return
        axis,angle=args
        if isinstance(angle,(tuple,list)):
            v,w=unit(axis),unit(angle);c=max(-1,min(1,dot(v,w)))
            axis=cross(v,w)
            if dot(axis,axis)<1e-20:axis=(1,0,0)
            angle=math.degrees(math.acos(c))
        x,y,z=unit(axis);a=math.radians(angle);c,s=math.cos(a),math.sin(a);t=1-c
        self.M=((t*x*x+c,t*x*y-s*z,t*x*z+s*y),(t*x*y+s*z,t*y*y+c,t*y*z-s*x),(t*x*z-s*y,t*y*z+s*x,t*z*z+c))
    def multVec(self,p):return tuple(dot(row,p) for row in self.M)
    def multiply(self,other):
        result=Rotation();result.M=tuple(tuple(dot(row,col) for col in zip(*other.M)) for row in self.M);return result
class Placement:
    def __init__(self,base,rotation):self.Base=base;self.Rotation=rotation
    def multVec(self,p):return tuple(a+b for a,b in zip(self.Base,self.Rotation.multVec(p)))
class App:
    Vector=staticmethod(lambda *p:tuple(p));Rotation=Rotation;Placement=Placement

class TendonPoseTests(unittest.TestCase):
    def assertPoint(self,got,want):
        for a,b in zip(got,want):self.assertAlmostEqual(a,b)
    def test_cable_source_transforms_once_and_keeps_axial_y(self):
        p=_tendon_placement(App,{'kind':'tendon_r03_cable'},(10,20),math.pi/2)
        self.assertPoint(p.multVec((-37,57,8)),(2,57,-17))
        self.assertPoint(p.multVec((0,0,0)),(10,0,20))
    def test_wheel_guide_stack_and_motor_alias_use_native_source_frames(self):
        E=(10,20);a=math.pi/2
        wheel=_tendon_placement(App,{'kind':'tendon_r03_wheel','center':(-37,0,0),'source_start_x':-38.2,'angle_rad':0},E,a)
        self.assertPoint(wheel.multVec((0,0,1.2)),(10,0,-17))
        self.assertPoint(wheel.multVec((5.5,0,1.2)),(10,5.5,-17))
        for side in (-1,1):
            for component,L,offset in ((None,1.2,0),('journal',3.6,0),('washer',.2,.8),('outer_clip',.6,1.35)):
                m={'kind':'tendon_r03_guide','center':(-30,side*57,8),'axis':(0,side,0),'component':component,'axial_offset_mm':offset}
                p=_tendon_placement(App,m,E,a)
                self.assertPoint(p.multVec((0,0,L/2)),(2,side*(57+offset),-10))
        motor=_tendon_placement(App,{'kind':'torso_r03_offset','point':(-22.6,0,0),'rotation_local_axis':(0,0,1),'rotation_deg':90},E,a)
        self.assertPoint(motor.multVec((0,13,0)),(10,0,-15.6))
    def test_captured_coupling_placement_composes_parent_rotation(self):
        q=(0,0,math.sqrt(.5),math.sqrt(.5))
        m={'kind':'torso_r04_rigid','local_placement_json':json.dumps({'base_xyz_mm':(-35.6,0,0),'rotation_xyzw':q})}
        p=_tendon_placement(App,m,(10,20),math.pi/2)
        self.assertPoint(p.multVec((1,0,0)),(10,1,-15.6))
    def test_stale_hind_leg_or_wheel_state_is_rejected_before_pose_mutation(self):
        route=tendon_route(1,cable_plane_mm=57,wheel_x_mm=-37)
        cable={'kind':'tendon_r03_cable','side':1,'wheel_angle_rad':0,'route_local':route}
        tags={'hindL':('hind',1),'foreL':('fore',1)}
        angles={'hindL':(math.radians(-40),math.radians(-100)),'foreL':(0,0)}
        _guard_installed_tendons({'cable':cable},tags,angles)
        changed=dict(angles,hindL=(math.radians(-40),math.radians(-99)))
        with self.assertRaisesRegex(ValueError,'fixed hind leg angles'):_guard_installed_tendons({'cable':cable},tags,changed)
        with self.assertRaisesRegex(ValueError,'fixed u=0'):_guard_installed_tendons({'cable':cable,'wheel':{'kind':'tendon_r03_wheel','angle_rad':.1}},tags,angles)
        self.assertTrue({'torso_r03_offset','torso_r04_rigid','tendon_r03_cable','tendon_r03_wheel','tendon_r03_guide'}<=KINDS)

if __name__=='__main__':unittest.main()
