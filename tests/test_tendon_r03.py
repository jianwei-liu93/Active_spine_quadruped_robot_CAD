"""Finite routing, branch transition and unilateral secured-cable checks."""
import math
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
try:
    from tendon_r03 import tendon_route, bilateral_states
except ImportError:
    tendon_route=bilateral_states=None

class TendonR03Tests(unittest.TestCase):
    def setUp(self): self.assertIsNotNone(tendon_route,'r03 routing required')

    def test_neutral_and_positive_wrap_contacts_have_correct_radii_and_tangencies(self):
        for side in (-1,1):
            for u in (0,.2,.8):
                r=tendon_route(side,u)
                self.assertEqual(r['wheel_regime'],'neutral_tangent' if u==0 else 'CW_wrap')
                self.assertLess(max(r['tangency_errors'].values()),1e-10)
                w=r['wheel'];T=w['contact']
                self.assertAlmostEqual(math.dist(T,w['center']),5.5)
                self.assertAlmostEqual(T[0],-27+side*.6)
                self.assertEqual(r['hip_guide']['axis'],(0,1,0))
                self.assertGreater(r['length_mm'],0)
                for a,b in zip(r['primitives'],r['primitives'][1:]):
                    self.assertLess(math.dist(a['end'],b['start']),1e-10)
                self.assertAlmostEqual(sum(p['length_mm'] for p in r['primitives']),r['length_mm'])

    def test_source_frame_references_and_fixed_shell_guide_over_assembled_interval(self):
        from leg_geometry_r02 import leg_geometry
        for side in (-1,1):
            neutral=tendon_route(side,0)
            self.assertEqual(neutral['wheel']['axle_center'],(-27,0,0))
            self.assertEqual(neutral['hip_guide']['center'],(leg_geometry('hind')['H'][0],side*53.2,0))
            for i in range(17):
                u=i*math.pi/32
                route=tendon_route(side,u)
                self.assertTrue(route['assembly_compatible'])
                self.assertEqual(route['assembled_operating_interval_rad'],(0,math.pi/2))
                self.assertLess(math.dist(route['shell_guide']['center'],neutral['shell_guide']['center']),1e-12)
                self.assertLess(math.dist(route['shell_guide']['axis'],neutral['shell_guide']['axis']),1e-12)
                self.assertLess(max(route['tangency_errors'].values()),1e-10)
            diagnostic=tendon_route(side,-.4)
            self.assertFalse(diagnostic['assembly_compatible'])
            self.assertGreater(math.dist(diagnostic['shell_guide']['center'],neutral['shell_guide']['center']),1e-6)
        with self.assertRaises(ValueError): bilateral_states(-.1)
        with self.assertRaises(ValueError): bilateral_states(math.pi/2+.01)

    def test_negative_rotation_uses_clear_chord_and_changes_shell_entry(self):
        a=tendon_route(1,0);b=tendon_route(1,-.3)
        self.assertEqual(b['wheel_regime'],'clear_chord')
        self.assertGreaterEqual(b['wheel']['chord_min_radius_mm'],5.5-1e-10)
        self.assertNotEqual(a['shell_guide']['entry'],b['shell_guide']['entry'])
        self.assertFalse(any(p['name']=='wheel_wrap' for p in b['primitives']))
        self.assertAlmostEqual(math.dist(b['wheel']['hole'],b['wheel']['center']),5.5)
        self.assertLess(b['length_mm'],a['length_mm'])

    def test_chord_wrap_transition_is_continuous_with_correct_take_up_derivative(self):
        h=1e-6
        for side in (-1,1):
            left=tendon_route(side,-h)['length_mm'];right=tendon_route(side,h)['length_mm']
            self.assertLess(abs(left-right),2e-5)
            u=.4
            derivative=(tendon_route(side,u+h)['length_mm']-tendon_route(side,u-h)['length_mm'])/(2*h)
            self.assertAlmostEqual(derivative,5.5,places=6)
            u=-.4
            derivative=(tendon_route(side,u+h)['length_mm']-tendon_route(side,u-h)['length_mm'])/(2*h)
            self.assertGreater(derivative,0)
            self.assertLess(derivative,5.5)

    def test_reverse_blocked_chord_transitions_to_other_tangent_without_penetration(self):
        neutral=tendon_route(1,0)
        boundary=neutral['wheel']['reverse_chord_limit_rad']
        h=1e-6
        a=tendon_route(1,boundary+h);b=tendon_route(1,boundary-h)
        self.assertEqual(a['wheel_regime'],'clear_chord')
        self.assertEqual(b['wheel_regime'],'reverse_CCW_wrap')
        self.assertLess(abs(a['length_mm']-b['length_mm']),2e-5)
        self.assertLess(max(b['tangency_errors'].values()),1e-10)

    def test_transform_applied_once_preserves_lengths_and_y(self):
        def t(p): return (10-p[1],20+p[0])
        t.angle_rad=math.pi/2
        a=tendon_route(1,.3);b=tendon_route(1,.3,transform=t)
        self.assertAlmostEqual(a['length_mm'],b['length_mm'])
        for pa,pb in zip(a['primitives'],b['primitives']):
            for key in ('start','end'):
                x,y,z=pa[key]
                self.assertAlmostEqual(pb[key][0],10-z)
                self.assertAlmostEqual(pb[key][1],y)
                self.assertAlmostEqual(pb[key][2],20+x)

    def test_secured_branches_use_constant_available_and_asymmetric_knees(self):
        a=bilateral_states(0)
        for side in (-1,1):
            self.assertAlmostEqual(a['branches'][side]['state']['slack_mm'],.5)
            self.assertEqual(a['branches'][side]['state']['tension_N'],0)
        b=bilateral_states(.3,left_knee=-1.1,right_knee=-2.0)
        self.assertNotEqual(b['branches'][1]['path_mm'],b['branches'][-1]['path_mm'])
        for side in (-1,1):
            self.assertEqual(a['branches'][side]['available_mm'],b['branches'][side]['available_mm'])
            self.assertGreaterEqual(b['branches'][side]['state']['energy_Nmm'],0)
        c=bilateral_states(.3)
        for side in (-1,1):
            # .3*5.5=1.65mm wound path, minus .5mm installed slack.
            self.assertAlmostEqual(c['branches'][side]['state']['tension_N'],2.3)
            self.assertAlmostEqual(c['branches'][side]['state']['energy_Nmm'],1.3225)

    def test_r04_offset_datums_preserve_tangency_and_installed_available_lengths(self):
        cfg={'cable_plane_mm':57,'wheel_x_mm':-37}
        states=bilateral_states(.4,**cfg)
        for side in (-1,1):
            neutral=tendon_route(side,**cfg)
            self.assertEqual(neutral['wheel']['axle_center'],(-37,0,0))
            self.assertEqual(neutral['ankle_anchor'][1],side*57)
            self.assertAlmostEqual(states['branches'][side]['available_mm'],neutral['length_mm']+.5)
            for i in range(17):
                u=i*math.pi/32;r=tendon_route(side,u,**cfg)
                self.assertLess(max(r['tangency_errors'].values()),1e-10)
                self.assertLess(math.dist(r['shell_guide']['center'],neutral['shell_guide']['center']),1e-12)
                self.assertAlmostEqual(r['length_mm']-neutral['length_mm'],5.5*u)
                # Independent centerline integral: Euclidean lines + radius*angle.
                integral=sum(math.dist(p['start'],p['end']) if p['type']=='line' else p['radius_mm']*p['sweep_rad'] for p in r['primitives'])
                self.assertAlmostEqual(integral,r['length_mm'])
            self.assertAlmostEqual(states['branches'][side]['state']['tension_N'],3.4)
        for cfg in ({'cable_plane_mm':0},{'cable_plane_mm':-1},{'cable_plane_mm':float('nan')},{'wheel_x_mm':float('inf')}):
            with self.assertRaises(ValueError):tendon_route(1,**cfg)
            with self.assertRaises(ValueError):bilateral_states(**cfg)

    def test_invalid_state_and_transform_rejected(self):
        with self.assertRaises(ValueError): tendon_route(0,0)
        with self.assertRaises(ValueError): tendon_route(1,float('nan'))
        with self.assertRaises(ValueError): tendon_route(1,0,transform=lambda p:(p[0]*2,p[1]))

if __name__=='__main__': unittest.main()
