"""Behavior checks for three-segment FK, tangent geometry and unilateral laws."""
import math
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from kinematics import load_parameters
try:
    import leg_mechanics as m
except ImportError:
    m = None


class LegMechanicsTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(m, 'leg mechanics implementation required')
        self.p = load_parameters()

    def test_full_fore_fk_keeps_independent_distal_segment(self):
        p = dict(self.p, leg_a1_mm=3, leg_a2_mm=4, leg_a3_mm=5)
        s = m.leg_pose(0, math.pi/2, -math.pi/2, p)
        self.assertAlmostEqual(s['K'][0], 3)
        self.assertAlmostEqual(s['A'][1], 4)
        self.assertAlmostEqual(s['F'][0], 8)
        self.assertAlmostEqual(s['F'][1], 4)
        t = m.leg_pose(0, math.pi/2, 0, p)
        self.assertAlmostEqual(t['F'][0], 3)
        self.assertAlmostEqual(t['F'][1], 9)

    def test_hind_parallelogram_closes_over_declared_pose_grid(self):
        for dh in (-.25, 0, .25):
            for dk in (-.30, 0, .30):
                qh, qk = self.p['leg_qh_rad']+dh, self.p['leg_qk_rad']+dk
                s = m.leg_pose(qh, qk, None, self.p)
                self.assertAlmostEqual(s['qa_rad'], -qk)
                self.assertAlmostEqual(s['alpha3_rad'], qh)
                for u, v, w, x in (('P1','P0','P2','P3'), ('P3','P0','P2','P1')):
                    for i in (0, 1):
                        self.assertAlmostEqual(s[u][i]-s[v][i], s[w][i]-s[x][i])
                self.assertAlmostEqual(math.dist(s['A'],s['F']), 31)
                self.assertAlmostEqual(math.dist(s['K'],s['A']), 30)

    def test_tangent_route_contacts_arc_and_hand_checked_length(self):
        for sign in (-1,1):
            route = m.tangent_route((-5,0),(0,0),3,(5,0),sign)
            self.assertAlmostEqual(route['wrap_angle_rad'], math.pi-2*math.acos(.6))
            self.assertAlmostEqual(route['length_mm'], 8+3*(math.pi-2*math.acos(.6)))
            for anchor, contact in zip(((-5,0),(5,0)), route['contacts']):
                self.assertAlmostEqual(math.hypot(*contact),3)
                self.assertAlmostEqual(sum((anchor[i]-contact[i])*contact[i] for i in (0,1)),0)
            self.assertEqual(route['points'][1:3], route['contacts'])
            self.assertGreater(route['wrap_angle_rad'],0)
            self.assertAlmostEqual(sign*(route['arc_end_rad']-route['arc_start_rad']),route['wrap_angle_rad'])

    def test_route_is_continuous_when_anchor_crosses_polar_cut(self):
        lengths = [m.tangent_route((-5,z),(0,0),3,(5,0),1)['length_mm'] for z in (-1e-6,0,1e-6)]
        self.assertLess(max(lengths)-min(lengths), 1e-5)

    def test_tangent_rejects_inside_boundary_and_invalid_radius(self):
        for point,radius in (((1,0),3),((3,0),3),((5,0),0)):
            with self.assertRaises(ValueError): m.tangent_route(point,(0,0),radius,(5,0),1)
        with self.assertRaises(ValueError): m.tangent_route((-5,0),(0,0),3,(5,0),0)

    def test_extension_force_energy_and_travel_are_unilateral(self):
        s = m.spring_state(18,'extension',self.p)
        self.assertEqual(s['force_N'],1)
        self.assertEqual(s['energy_Nmm'],2)
        self.assertTrue(s['travel_ok'])
        self.assertEqual(s['initial_tension_N'],0)
        for length in (10,14):
            self.assertEqual(m.spring_state(length,'extension',self.p)['force_N'],0)
        self.assertFalse(m.spring_state(27,'extension',self.p)['travel_ok'])
        p = dict(self.p, extension_initial_tension_N=2)
        self.assertEqual(m.spring_state(18,'extension',p)['energy_Nmm'],10)

    def test_compression_force_energy_bind_and_no_tension(self):
        s = m.spring_state(13,'compression',self.p)
        self.assertEqual(s['force_N'],2)
        self.assertEqual(s['energy_Nmm'],5)
        self.assertTrue(s['travel_ok'])
        self.assertTrue(m.spring_state(7,'compression',self.p)['travel_ok'])
        self.assertFalse(m.spring_state(6.9,'compression',self.p)['travel_ok'])
        self.assertEqual(m.spring_state(20,'compression',self.p)['force_N'],0)

    def test_spring_energy_derivative_has_correct_force_sign(self):
        for kind,length,sign in (('extension',18,1),('compression',13,-1)):
            h=1e-5
            dU=(m.spring_state(length+h,kind,self.p)['energy_Nmm']-m.spring_state(length-h,kind,self.p)['energy_Nmm'])/(2*h)
            self.assertAlmostEqual(dU,sign*m.spring_state(length,kind,self.p)['force_N'])

    def test_independently_secured_asymmetric_elastic_cables(self):
        left = m.cable_state(99,100,self.p)
        right = m.cable_state(102,100,self.p)
        self.assertEqual((left['state'],left['slack_mm'],left['tension_N'],left['energy_Nmm']),('slack',1,0,0))
        self.assertEqual((right['state'],right['slack_mm'],right['tension_N'],right['energy_Nmm']),('stretched',0,4,4))
        self.assertEqual(m.cable_state(100,100,self.p)['state'],'taut_unloaded')
        h=1e-5
        dU=(m.cable_state(102+h,100,self.p)['energy_Nmm']-m.cable_state(102-h,100,self.p)['energy_Nmm'])/(2*h)
        self.assertAlmostEqual(dU,right['tension_N'])

    def test_rejects_nonphysical_lengths_and_rates(self):
        with self.assertRaises(ValueError): m.spring_state(-1,'extension',self.p)
        with self.assertRaises(ValueError): m.spring_state(12,'wrong',self.p)
        with self.assertRaises(ValueError): m.cable_state(100,100,dict(self.p,cable_stiffness_N_per_mm=-2))
        with self.assertRaises(ValueError): m.cable_state(float('nan'),100,self.p)

if __name__ == '__main__':
    unittest.main()
