import unittest, sys, math
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
try:
    import kinematics as k
except ImportError:
    k=None

class GeometryTests(unittest.TestCase):
    def test_intersections_and_infeasible(self):
        self.assertIsNotNone(k,'kinematics module required')
        points=k.circles((0,0),(6,0),5,5)
        self.assertAlmostEqual(points[0][0],3)
        self.assertAlmostEqual(abs(points[0][1]),4)
        with self.assertRaises(ValueError): k.circles((0,0),(20,0),5,5)
        with self.assertRaises(ValueError): k.circles((0,0),(0,0),5,5)
    def test_full_cycle_rigid_lengths_and_branch(self):
        self.assertIsNotNone(k,'kinematics module required')
        p=k.load_parameters()
        poses=[k.spine(i*math.tau/720,p) for i in range(721)]
        for s in poses:
            self.assertLess(max(abs(x) for x in k.residuals(s,p)),4.6e-7)
            self.assertGreater(min(s['margins_mm']),0.05)
        for a,b in zip(poses,poses[1:]):
            for n in ('B1','B2','C1','C2','D1','D2'):
                self.assertLess(math.dist(a[n],b[n]),0.5)
        for n in ('B1','B2','C1','C2','D1','D2'):
            self.assertLess(math.dist(poses[0][n],poses[-1][n]),1e-9)

if __name__=='__main__': unittest.main()
