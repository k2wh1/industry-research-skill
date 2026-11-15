import csv,importlib.util,tempfile,unittest
from pathlib import Path
spec=importlib.util.spec_from_file_location("gate",Path(__file__).resolve().parents[1]/"scripts"/"formal_final_gate.py")
gate=importlib.util.module_from_spec(spec);spec.loader.exec_module(gate)
def save(d,name,fields,items):
 p=Path(d)/name
 with p.open("w",encoding="utf-8",newline="") as f:
  w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(items)
 return p
class TestFormalFinal(unittest.TestCase):
 def case(self,materiality="NONCRITICAL",gapstatus="DISCLOSED",defectstatus="FIXED",sourcestatus="VERIFIED",highstatus="PASS",missingacceptance=False):
  with tempfile.TemporaryDirectory() as d:
   report=Path(d)/"report.md";report.write_text("Investment thesis: E001",encoding="utf-8")
   acc=[dict(criterion=k,status="PASS",evidence_ref="audit.md#"+k,review_note="checked") for k in gate.REQUIRED]
   if missingacceptance:acc.pop()
   a=save(d,"a.csv",["criterion","status","evidence_ref","review_note"],acc)
   b=save(d,"b.csv",["gap_id","module","materiality","status","impact_on_conclusion","mitigation_ref","disclosure_ref"],[
    dict(gap_id="G1",module="HBM",materiality=materiality,status=gapstatus,impact_on_conclusion="no SKU ROIC inference",mitigation_ref="proxy.md",disclosure_ref="report.md#limits")])
   c=save(d,"c.csv",["issue_id","priority","status","fix_ref","verification_ref"],[
    dict(issue_id="D1",priority="P1",status=defectstatus,fix_ref="R2.md",verification_ref="QA.md")])
   e=save(d,"e.csv",["priority","status","evidence_ids"],[dict(priority="HIGH",status=highstatus,evidence_ids="E001")])
   f=save(d,"f.csv",["evidence_id","status","verification_ref"],[
    dict(evidence_id="E001",status=sourcestatus,verification_ref="10K-page-4")])
   return gate.evaluate(report,a,b,c,e,f)
 def test_noncritical_gap_can_be_final(self):self.assertEqual(self.case()["status"],"FINAL_RESEARCH_READY")
 def test_critical_gap_not_final(self):self.assertEqual(self.case(materiality="CRITICAL")["status"],"REVISION_REQUIRED")
 def test_open_gap_not_final(self):self.assertEqual(self.case(gapstatus="OPEN")["status"],"REVISION_REQUIRED")
 def test_p1_open_not_final(self):self.assertEqual(self.case(defectstatus="OPEN")["status"],"REVISION_REQUIRED")
 def test_source_unverified_not_final(self):self.assertEqual(self.case(sourcestatus="UNVERIFIED")["status"],"REVISION_REQUIRED")
 def test_high_partial_not_final(self):self.assertEqual(self.case(highstatus="PARTIAL")["status"],"REVISION_REQUIRED")
 def test_missing_acceptance_not_final(self):self.assertEqual(self.case(missingacceptance=True)["status"],"REVISION_REQUIRED")
 def test_resolved_critical_gap_can_be_final(self):self.assertEqual(self.case(materiality="CRITICAL",gapstatus="RESOLVED")["status"],"FINAL_RESEARCH_READY")
if __name__=="__main__":unittest.main()
