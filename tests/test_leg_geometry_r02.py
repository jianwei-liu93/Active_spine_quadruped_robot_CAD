"""Independent checks of the frozen r02 leg reconstruction assumptions."""
import math
from pathlib import Path
import sys
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
try:
    from leg_geometry_r02 import leg_geometry
except ImportError:
    leg_geometry = None


class CorrectedLegGeometryTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(leg_geometry,'r02 leg geometry implementation required')

    def test_hand_checked_hind_right_angle_pose_and_named_spring_seats(self):
        g=leg_geometry('hind',0,math.pi/2,0)
        expected={'H':(-13,0),'K':(16,0),'A':(16,30),'F':(47,30),
                  'O1':(22,0),'A1':(22,30),'O2':(-4,0),'O3':(16,-6)}
        for name,point in expected.items():
            self.assertIsInstance(g[name],tuple)
            for got,want in zip(g[name],point): self.assertAlmostEqual(got,want)
        self.assertEqual(g['cable_anchor'],g['A'])
        self.assertAlmostEqual(g['spring_lengths_mm']['extension'],math.sqrt(436))
        self.assertAlmostEqual(g['spring_lengths_mm']['compression'],math.sqrt(936))
        self.assertEqual(g['spring_attachments']['compression'],('O1','A'))
        self.assertEqual(g['spring_attachments']['extension'],('O2','O3'))

    def test_fore_has_its_own_lengths_and_closed_return_rail(self):
        g=leg_geometry('fore',0,math.pi/2,0)
        for name,want in {'H':(13,0),'K':(37,0),'A':(37,24),'F':(67,24),'O1':(43,0),'A1':(43,24)}.items():
            for got,target in zip(g[name],want): self.assertAlmostEqual(got,target)
        self.assertAlmostEqual(math.dist(g['O1'],g['A1']),24)

    def test_physical_pose_grids_preserve_all_rigid_lengths_and_loop(self):
        for kind,neutral,lengths in (('hind',(-40,-100),(29,30,31)),('fore',(-130,90),(24,24,30))):
            for dh in (-.25,0,.25):
                for dk in (-.30,0,.30):
                    qh=math.radians(neutral[0])+dh
                    qk=math.radians(neutral[1])+dk
                    g=leg_geometry(kind,qh,qk)
                    for start,end,length in zip(('H','K','A'),('K','A','F'),lengths):
                        self.assertAlmostEqual(math.dist(g[start],g[end]),length)
                    self.assertAlmostEqual(math.dist(g['O1'],g['A1']),lengths[1])
                    self.assertAlmostEqual(math.dist(g['K'],g['O1']),6)
                    self.assertAlmostEqual(math.dist(g['A'],g['A1']),6)
                    for i in (0,1):
                        self.assertAlmostEqual(g['O1'][i]-g['K'][i],g['A1'][i]-g['A'][i])
                        self.assertAlmostEqual(g['A'][i]-g['K'][i],g['A1'][i]-g['O1'][i])
                    self.assertAlmostEqual(g['qa_rad'],-qk)
                    self.assertAlmostEqual(g['distal_angle_rad'],qh)
                    self.assertLess(max(g['loop_residuals_mm'].values()),1e-12)

    def test_motor_angle_only_moves_motor_owned_attachment(self):
        a=leg_geometry('hind',-.7,-1.6,-.7)
        b=leg_geometry('hind',-.7,-1.6,.3)
        for key in ('H','K','A','F','O1','A1','O3','cable_anchor'):
            self.assertEqual(a[key],b[key])
        self.assertNotEqual(a['O2'],b['O2'])
        self.assertEqual(a['spring_lengths_mm']['compression'],b['spring_lengths_mm']['compression'])
        self.assertNotEqual(a['spring_lengths_mm']['extension'],b['spring_lengths_mm']['extension'])
        self.assertEqual(b['thigh_angle_rad'],-.7)
        self.assertEqual(b['motor_proximal_angle_rad'],.3)

    def test_asymmetric_passive_knees_remain_independent(self):
        left=leg_geometry('hind',-.7,-1.4,-.7)
        right=leg_geometry('hind',-.7,-1.8,-.7)
        self.assertEqual(left['K'],right['K'])
        self.assertEqual(left['O2'],right['O2'])
        self.assertNotEqual(left['A'],right['A'])
        self.assertNotEqual(left['F'],right['F'])
        self.assertNotEqual(left['spring_lengths_mm']['compression'],right['spring_lengths_mm']['compression'])

    def test_attachment_offsets_are_invariant_in_their_owning_body(self):
        fixtures={'O1':('thigh',(35,0)),'A1':('foot',(6,0)),
                  'O2':('motor_horn',(9,0)),'O3':('shank',(-6,0))}
        for qh,qk,motor in ((-.7,-1.6,.3),(-1.0,-1.3,-.9),(.2,.5,-.1)):
            g=leg_geometry('hind',qh,qk,motor)
            for name,(body,want) in fixtures.items():
                self.assertEqual(g['owning_body'][name],body)
                frame=g['body_frames'][body]
                dx,dz=(g[name][i]-frame['origin'][i] for i in (0,1))
                c,s=math.cos(frame['angle_rad']),math.sin(frame['angle_rad'])
                local=(c*dx+s*dz,-s*dx+c*dz)
                for got,target in zip(local,want): self.assertAlmostEqual(got,target)

    def test_defaults_and_invalid_inputs(self):
        for kind,qh,qk in (('hind',-40,-100),('fore',-130,90)):
            g=leg_geometry(kind)
            self.assertAlmostEqual(g['thigh_angle_rad'],math.radians(qh))
            self.assertAlmostEqual(g['passive_knee_rad'],math.radians(qk))
            self.assertEqual(g['motor_proximal_angle_rad'],g['thigh_angle_rad'])
        with self.assertRaises(ValueError): leg_geometry('unknown')
        for args in ((float('nan'),0,0),(0,float('inf'),0),(0,0,float('nan'))):
            with self.assertRaises(ValueError): leg_geometry('fore',*args)

if __name__=='__main__': unittest.main()
