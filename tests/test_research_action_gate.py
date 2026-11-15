"""Documentary gate regression tests."""
import csv, tempfile, unittest
from pathlib import Path
import importlib.util
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location("research_action_gate",ROOT/"scripts"/"research_action_gate.py")
mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
def write(p,fields,rows):
    with open(p,"w",encoding="utf-8",newline="") as f:
        w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(rows)
class TestResearchActionGate(unittest.TestCase):
    def evaluate(self,action="DONE",placeholder=False,distinct=True,source="VERIFIED"):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);paths=[root/x for x in ("report.md","evidence.csv","source.csv","actions.csv","coverage.csv","defects.csv","score.csv","gates.csv")]
            paths[0].write_text("Evidence [E001] "+("原始资料X" if placeholder else "published."),encoding="utf-8")
            write(paths[1],["evidence_id","source_url"],[{"evidence_id":"E001","source_url":"https://example.com"}])
            write(paths[2],["evidence_id","status","verification_ref","finding"],[{"evidence_id":"E001","status":source,"verification_ref":"page#1","finding":"checked"}])
            write(paths[3],["action_id","severity","finding","next_action","status","output_ref","verification_ref","blocker_reason"],
                [{"action_id":"A1","severity":"P1","finding":"missing bridge","next_action":"build bridge","status":action,"output_ref":"revision.md","verification_ref":"review.md","blocker_reason":""}])
            write(paths[4],["sub_industry","priority","analytical_depth_0_3","evidence_ids","status"],
                [{"sub_industry":"Cloud","priority":"HIGH","analytical_depth_0_3":"3","evidence_ids":"E001","status":"pass"}])
            write(paths[5],["issue_id","priority","status","fix_ref","verification_ref","blocker_reason"],[])
            criteria=("research_question","business_logic","evidence","modeling","competition","investment","falsification","structure")
            write(paths[6],["round_id","criterion_id","next_action","evidence_refs","score_0_5"],[
                {"round_id":"R1","criterion_id":k,"next_action":(f"improve-{k}" if distinct else "improve"),"evidence_refs":"section#1","score_0_5":"4"} for k in criteria])
            write(paths[7],["round_id","gate","status","review_evidence"],[
                {"round_id":"R1","gate":k,"status":"PASS","review_evidence":"full-review"} for k in
                ("source_integrity","data_audit","model_integrity","industry_coverage","counterevidence","visual_editorial")])
            return mod.check(*paths)
    def test_clean_documentary_review(self):self.assertEqual(self.evaluate()["status"],"READY_FOR_INDEPENDENT_REVIEW")
    def test_open_action_blocks(self):self.assertEqual(self.evaluate(action="OPEN")["status"],"BLOCKED_ACTIONABLE")
    def test_placeholders_block(self):self.assertEqual(self.evaluate(placeholder=True)["status"],"BLOCKED_ACTIONABLE")
    def test_copy_paste_scoring_blocks(self):self.assertEqual(self.evaluate(distinct=False)["status"],"BLOCKED_ACTIONABLE")
    def test_unverified_source_stages(self):self.assertEqual(self.evaluate(source="UNVERIFIED")["status"],"STAGED_REVIEW")
if __name__=="__main__":unittest.main()
