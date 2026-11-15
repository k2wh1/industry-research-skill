import csv,tempfile,unittest
from pathlib import Path
import importlib.util
spec=importlib.util.spec_from_file_location("substantive_stop_gate",Path(__file__).resolve().parents[1]/"scripts"/"substantive_stop_gate.py")
g=importlib.util.module_from_spec(spec);spec.loader.exec_module(g)
def w(dir,name,fields,rows):
 p=Path(dir)/name
 with p.open('w',encoding='utf-8',newline='') as f:
  out=csv.DictWriter(f,fieldnames=sorted(fields));out.writeheader();out.writerows(rows)
 return p
class Tests(unittest.TestCase):
 def go(self,rel='monotonic_increase',blockers=None):
  with tempfile.TemporaryDirectory() as d:
   a=w(d,'s.csv',g.SERIES,[{'series_id':'AWS','period':str(y),'value':str(v),'source_ref':'10K'} for y,v in [(2023,27.14),(2024,37.04),(2025,35.43)]])
   b=w(d,'c.csv',g.CLAIMS,[dict(claim_id='C1',report_location='p10',series_id='AWS',relation=rel,start_period='2023',end_period='2025',verification_ref='audit')])
   c=w(d,'b.csv',g.BLOCKERS,blockers or [])
   return g.check(a,b,c)
 def test_false_monotonic(self):self.assertEqual(self.go()['status'],'BLOCKED')
 def test_true_nonlinear(self):self.assertEqual(self.go('non_monotonic')['status'],'PASS_DOCUMENTARY')
 def test_feasible_alternative(self):
  b=[dict(issue_id='B1',module='cloud',status='EXTERNAL_BLOCKED',primary_attempt_ref='10K',claim_of_unavailability='ROIC unavailable',alternative_name=n,alternative_source_ref='official',alternative_status=st,alternative_reason='no asset denominator',work_done_ref='review') for n,st in [('TCO','FEASIBLE'),('proxy ROIC','INFEASIBLE')]]
  self.assertEqual(self.go('non_monotonic',b)['status'],'BLOCKED')
 def test_documented_blocker(self):
  b=[dict(issue_id='B1',module='cloud',status='EXTERNAL_BLOCKED',primary_attempt_ref='10K',claim_of_unavailability='ROIC unavailable',alternative_name=n,alternative_source_ref='official',alternative_status='INFEASIBLE',alternative_reason='no asset denominator',work_done_ref='review') for n in ('TCO','proxy ROIC')]
  self.assertEqual(self.go('non_monotonic',b)['status'],'STAGED')
 def test_insufficient_attempts(self):
  b=[dict(issue_id='B1',module='cloud',status='EXTERNAL_BLOCKED',primary_attempt_ref='10K',claim_of_unavailability='ROIC unavailable',alternative_name='TCO',alternative_source_ref='official',alternative_status='UNTESTED',alternative_reason='',work_done_ref='review')]
  self.assertEqual(self.go('non_monotonic',b)['status'],'BLOCKED')
if __name__=='__main__':unittest.main()
