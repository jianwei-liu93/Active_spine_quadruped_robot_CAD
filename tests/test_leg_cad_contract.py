"""Check native-leg dimensions/retention contracts without a FreeCAD process."""
import math
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
try:
    from build_leg_r02 import leg_contract
except ImportError:
    leg_contract=None

class LegCADContractTests(unittest.TestCase):
    def setUp(self): self.assertIsNotNone(leg_contract,'native leg contract required')

    def test_separate_part_planes_have_bearing_width_and_axial_clearance(self):
        for side in (-1,1):
            c=leg_contract('hind',side)
            self.assertEqual(c['planes_y_mm']['foot'],side*48)
            self.assertEqual(c['planes_y_mm']['motor_horn'],side*51.4)
            self.assertGreater(abs(c['planes_y_mm']['motor_horn']),abs(c['planes_y_mm']['return_rail']))
            h=c['joints']['H']
            self.assertAlmostEqual(min(abs(y) for y in h['shaft_bounds_y_mm']),42.0)
            self.assertEqual(len(h['clip_centers_y_mm']),1)
            self.assertAlmostEqual(abs(h['clip_centers_y_mm'][0]),52.35)
            self.assertEqual(h['case_face_coupling'],'PROVISIONAL manufacturer output adapter; no inner retainer')
            self.assertGreater(min(abs(y) for y in c['joints']['O2']['shaft_bounds_y_mm']),50.0)
            for name,want in {'K':(44.4,46.2),'A':(46.2,48,53.2),'O1':(44.4,49.8,53.2),'A1':(48,49.8)}.items():
                stack=c['joints'][name]
                self.assertEqual(sorted(abs(y) for y in stack['layers_y_mm']),list(want))
                for gap in stack['spacers']:
                    self.assertGreater(gap['length_mm'],0)
                lo,hi=stack['shaft_bounds_y_mm']
                for y in stack['clip_centers_y_mm']:
                    self.assertGreater(y-.3,lo)
                    self.assertLess(y+.3,hi)
                    self.assertGreaterEqual(min(abs(y-z)-.9 for z in stack['layers_y_mm']),.049999)
                self.assertAlmostEqual(stack['groove_width_mm'],.6)
                self.assertEqual(stack['groove_root_diameter_mm'],1.7)

    def test_source_dimensions_include_real_named_pivots_and_lever(self):
        for kind,a1,a2,a3 in (('hind',29,30,31),('fore',22,24,34)):
            c=leg_contract(kind,1)
            self.assertEqual(c['parts']['thigh']['point_names'],('H','O1','K'))
            self.assertEqual(c['parts']['thigh']['pivot_x_mm'],(0,a1-6,a1))
            self.assertEqual(c['parts']['thigh']['length_mm'],a1)
            self.assertTrue(c['parts']['thigh']['keyed_H'])
            self.assertEqual(c['parts']['thigh']['key_flat_angle_rad'],0)
            self.assertEqual(c['parts']['shank']['pivot_x_mm'],(0,6,a2+6))
            self.assertEqual(c['parts']['shank']['point_names'],('O3','K','A'))
            self.assertEqual(c['parts']['return_rail']['pivot_x_mm'],(0,a2))
            self.assertEqual(c['parts']['foot']['pivot_x_mm'],(0,-6))
            self.assertEqual(c['parts']['foot']['contact_x_mm'],a3)
            self.assertEqual(c['springs']['compression']['anchors'],('O1','A'))
            self.assertEqual(c['springs']['extension']['anchors'],('O2','O3'))
            self.assertEqual(c['cable_anchor'],'A')

    def test_spring_preload_travel_and_geometry_are_separate_from_capacity(self):
        for kind,ef,cf in (('hind',18,34),('fore',13,27)):
            c=leg_contract(kind,1)
            e,k=c['springs']['extension'],c['springs']['compression']
            self.assertEqual((e['free_length_mm'],k['free_length_mm']),(ef,cf))
            self.assertGreater(e['length_mm'],ef)
            self.assertLess(k['length_mm'],cf)
            self.assertEqual(k['solid_length_mm'],7)
            self.assertTrue(k['travel_ok'])
            self.assertAlmostEqual(k['coil_length_mm'],k['length_mm']-7.2)
            self.assertAlmostEqual(k['coil_free_length_mm'],cf-7.2)
            self.assertGreater(28-k['coil_length_mm'],0)
            self.assertLess(28-k['coil_length_mm'],14)
            for spring in (e,k):
                self.assertEqual(spring['outer_diameter_mm'],4)
                self.assertEqual(spring['wire_diameter_mm'],.5)
                self.assertEqual(spring['provenance'],'DESIGN_ASSUMPTION')
                self.assertFalse(spring['capacity_verified'])

    def test_direct_hip_drive_and_fixed_bent_horn_key_align_in_world(self):
        def transform(point):
            x,z=point
            return (10-z,20+x)
        transform.angle_rad=math.pi/2
        for kind,delta in (('hind',math.pi/3),('fore',math.pi/3)):
            a=leg_contract(kind,-1,transform)
            self.assertEqual(a['motor_thigh_deflection_rad'],0)
            self.assertEqual(a['joints']['H']['bearing_layers_y_mm'],(-42.6,))
            self.assertEqual(a['joints']['H']['keyed_layers_y_mm'],(-44.4,-51.4))
            g=a['geometry']
            self.assertAlmostEqual(g['thigh_angle_rad'],math.radians(-40 if kind=='hind' else -50))
            P=a['world_points']
            self.assertAlmostEqual(math.dist(P['H'],P['O1']),a['parts']['thigh']['pivot_x_mm'][1])
            self.assertAlmostEqual(math.dist(P['O1'],P['K']),6)
            self.assertAlmostEqual(math.dist(P['A'],P['A1']),6)
            self.assertGreater(sum((P['K'][i]-P['H'][i])*(P['K'][i]-P['O1'][i]) for i in (0,1)),0)
            self.assertLess(sum((P['F'][i]-P['A'][i])*(P['A1'][i]-P['A'][i]) for i in (0,1)),0)
            arm=math.atan2(a['world_points']['O2'][1]-a['world_points']['H'][1],a['world_points']['O2'][0]-a['world_points']['H'][0])
            key_angle=a['horn']['key_flat_angle_rad']
            self.assertAlmostEqual(math.sin(arm+key_angle-(transform.angle_rad+g['thigh_angle_rad'])),0)
            self.assertAlmostEqual(key_angle,-delta)
            with self.assertRaises(ValueError): leg_contract(kind,-1,transform,{'motor_proximal_angle':.4})
        self.assertEqual(a['world_points']['H'],(10,44))

    def test_contract_rejects_degenerate_transform_and_invalid_side(self):
        with self.assertRaises(ValueError): leg_contract('hind',0)
        with self.assertRaises(ValueError): leg_contract('hind',1,lambda p:(p[0]*2,p[1]))
        with self.assertRaises(ValueError): leg_contract('hind',1,lambda p:(p[0],-p[1]))

if __name__=='__main__': unittest.main()
