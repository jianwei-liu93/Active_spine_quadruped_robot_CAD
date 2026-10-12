"""Synthetic fixtures test validation logic, never constitute CAD evidence."""
import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from sweep_robot_r03 import _phases,_sample_phases,_group,PLANAR_KINDS
from aggregate_spine_sweep import aggregate

class SweepCoverageTests(unittest.TestCase):
    def test_explicit_partitions_prepend_neutral_and_validate_values(self):
        self.assertEqual(_sample_phases(5,[90,45,45]),([0,45,90],[45,90]))
        self.assertEqual(_sample_phases(5,[0,45]),([0,45],[0,45]))
        self.assertEqual(_sample_phases(5,None)[0],_phases(5))
        self.assertEqual(len(_phases(1)),361)
        for values in ([float('nan')],[-1],[361]):
            with self.assertRaises(ValueError):_sample_phases(5,values)
        for kind in ('tendon_r03_wheel','tendon_r03_guide','tendon_r03_cable','torso_r03_offset','torso_r04_rigid'):
            self.assertEqual(_group({'kind':kind,'torso':'hind'}),('torso','hind'))
            self.assertIn(kind,PLANAR_KINDS)
        self.assertIsNone(_group({'kind':'future_unknown'}))
    def reports(self):
        def row(phases):
            return {'revision':'r05','status':'PASS','document_sha256':'a'*64,'motion_map_sha256':'b'*64,
              'volume_tolerance_mm3':1e-5,'bbox_overlap_tolerance_mm':1e-6,'reprojection_tolerance_mm':1e-6,
              'leg_angles_rad':{'hindL':[-.7,-1.7]},'motion_kinds':{'point':2},'instances':2,
              'parts':[{'instance':'A','source':'nativeA','valid':True,'solids':1,'volume_mm3':1},{'instance':'B','source':'nativeB','valid':True,'solids':1,'volume_mm3':2}],
              'native_shapes_valid_one_solid':True,'errors':[],'raw_overlaps':[],'raw_overlap_pairs':0,
              'neutral':{'phase_deg':0,'raw_overlaps':[]},
              'neutral_reprojection':{'status':'PASS','saved_phase_rad':0,'identity_world_copy_max_bound_error_mm':0,'saved_phase_descriptor_max_bound_error_mm':0},
              'pair_coverage':{'all_pairs':1,'neutral_all_pairs_once':True,'pair_samples_covered_including_cache':len(phases),'pair_samples_expected':len(phases)},
              'sample_degrees':phases,'actual_sample_degrees':phases,'samples_total':len(phases),'samples_completed':len(phases)}
        return [row(list(range(181))),row([0]+list(range(181,361)))]
    def run_fixture(self,rows,**kwargs):
        with tempfile.TemporaryDirectory() as directory:
            paths=[]
            for i,r in enumerate(rows):
                p=Path(directory)/('part'+str(i)+'.json');p.write_text(json.dumps(r));paths.append(p)
            return aggregate(paths,**kwargs)
    def test_complete_actual_fixture_coverage_and_duplicate_neutral_count(self):
        result=self.run_fixture(self.reports())
        self.assertEqual(result['samples_completed'],361)
        self.assertEqual(result['actual_partition_sample_count'],362)
        self.assertEqual(result['duplicate_phase_samples'],1)
    def test_coarse_coverage_cannot_claim_full_degree_pass(self):
        rows=self.reports()
        for r in rows:
            phases=[v for v in r['sample_degrees'] if v%15==0]
            r['revision']='r06'
            r['sample_degrees']=r['actual_sample_degrees']=phases
            r['samples_total']=r['samples_completed']=len(phases)
            r['pair_coverage']['pair_samples_covered_including_cache']=len(phases)
            r['pair_coverage']['pair_samples_expected']=len(phases)
        with self.assertRaisesRegex(ValueError,'Missing actual phase'):self.run_fixture(rows)
        result=self.run_fixture(rows,expected_phase_values_deg=range(0,361,15))
        self.assertEqual(result['coverage_kind'],'explicit_samples')
        self.assertEqual(result['revision'],'r06')
        self.assertEqual(result['samples_completed'],25)

    def test_missing_hash_inventory_failed_or_incomplete_partition_rejected(self):
        mutations=[lambda r:r[1].update(document_sha256='c'*64),
                   lambda r:r[1].update(status='FAIL'),
                   lambda r:r[1].update(samples_completed=1),
                   lambda r:r[1]['parts'][0].update(volume_mm3=4),
                   lambda r:r[1].update(errors=[{'error':'Boolean failure'}]),
                   lambda r:r[1].update(raw_overlap_pairs=1),
                   lambda r:r[1].update(volume_tolerance_mm3=.01)]
        for mutate in mutations:
            rows=self.reports();mutate(rows)
            with self.assertRaises(ValueError):self.run_fixture(rows)
        rows=self.reports();r=rows[1]
        r['sample_degrees'].remove(360);r['actual_sample_degrees']=r['sample_degrees']
        r['samples_total']=r['samples_completed']=len(r['sample_degrees'])
        r['pair_coverage']['pair_samples_covered_including_cache']=r['pair_coverage']['pair_samples_expected']=len(r['sample_degrees'])
        with self.assertRaisesRegex(ValueError,'Missing actual phase'):self.run_fixture(rows)

if __name__=='__main__':unittest.main()
