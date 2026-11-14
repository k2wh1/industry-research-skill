"""Regression tests for the documentary revision gate."""
import csv,importlib.util,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('revision_gate',ROOT/'scripts/revision_gate.py')
g=importlib.util.module_from_spec(spec);spec.loader.exec_module(g)
class RevisionGateTests(unittest.TestCase):
    def sample(self,d,status,fix='new.md#1',verify='review.md#2',blocker=''):
        l=Path(d)/'issues.csv';s=Path(d)/'scores.csv'
        with l.open('w',newline='') as f:
            w=csv.DictWriter(f,fieldnames=sorted(g.FIELDS));w.writeheader()
            w.writerow(dict(issue_id='P01',module='S05',priority='P1',source_section='2',
              finding='no margin bridge',evidence_ref='S05-E01',corrective_action='add bridge',
              status=status,fix_ref=fix,verification_ref=verify,blocker_reason=blocker))
        with s.open('w',newline='') as f:
            w=csv.DictWriter(f,fieldnames=sorted(g.SCORE_FIELDS));w.writeheader()
            for r in ('R1','R2'):w.writerow(dict(round_id=r,criterion_id='modeling',score_0_5='3.0'))
        return l,s
    def test_open_blocks_handoff(self):
        with tempfile.TemporaryDirectory() as d:
            l,s=self.sample(d,'OPEN',fix='',verify='')
            self.assertEqual(g.inspect(l,s,'handoff')['status'],'LOOP_INCOMPLETE')
    def test_fixed_requires_verification(self):
        with tempfile.TemporaryDirectory() as d:
            l,s=self.sample(d,'FIXED',verify='')
            self.assertEqual(g.inspect(l,s,'handoff')['status'],'LOOP_INCOMPLETE')
    def test_fixed_can_handoff_with_documentary_check(self):
        with tempfile.TemporaryDirectory() as d:
            l,s=self.sample(d,'FIXED')
            self.assertEqual(g.inspect(l,s,'handoff')['status'],'PASS_HANDOFF')
    def test_external_blocker_is_staged_only(self):
        with tempfile.TemporaryDirectory() as d:
            l,s=self.sample(d,'EXTERNAL_BLOCKED',fix='',blocker='customer product price private')
            self.assertEqual(g.inspect(l,s,'handoff')['status'],'LOOP_INCOMPLETE')
            self.assertEqual(g.inspect(l,s,'staged')['status'],'STAGED_ONLY')
if __name__=='__main__':unittest.main()
