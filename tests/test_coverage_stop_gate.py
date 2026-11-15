import csv
import importlib.util
import tempfile
import unittest
from pathlib import Path

spec=importlib.util.spec_from_file_location("gate",Path(__file__).resolve().parents[1]/"scripts"/"coverage_stop_gate.py")
gate=importlib.util.module_from_spec(spec)
spec.loader.exec_module(gate)

def write(root,name,fields,records):
    path=Path(root)/name
    with path.open("w",encoding="utf-8",newline="") as f:
        w=csv.DictWriter(f,fieldnames=sorted(fields));w.writeheader()
        w.writerows(records)
    return path

class GateTests(unittest.TestCase):
    def setup_rows(self,root,cover_status="partial",queue_status="IN_PROGRESS",module="GPUaaS",stop="NONE"):
        c=write(root,"coverage.csv",gate.COVERAGE,[dict(sub_industry="GPUaaS",priority="HIGH",analytical_depth_0_3="2",evidence_ids="E001",status=cover_status)])
        q=write(root,"queue.csv",gate.QUEUE,[dict(sub_industry="GPUaaS",priority="HIGH",research_question="Capital return?",next_action="Investigate cohort",status=queue_status,attempt_ref="research.md#3",blocker_reason="Customer data not published")])
        d=write(root,"defects.csv",gate.DEFECTS,[dict(module=module,priority="P1",status="EXTERNAL_BLOCKED",blocker_reason="Customer data not published",verification_ref="review.md")])
        return gate.review(c,q,d,stop)
    def test_partial_high_blocks_handoff(self):
        with tempfile.TemporaryDirectory() as t:
            self.assertEqual(self.setup_rows(t)["status"],"BLOCK_PREMATURE_STOP")
    def test_external_block_only_specific_module(self):
        with tempfile.TemporaryDirectory() as t:
            self.assertEqual(self.setup_rows(t,queue_status="EXTERNAL_BLOCKED",module="Storage",stop="EXTERNAL_DATA")["status"],"BLOCK_PREMATURE_STOP")
    def test_valid_external_block_remains_staged(self):
        with tempfile.TemporaryDirectory() as t:
            self.assertEqual(self.setup_rows(t,queue_status="EXTERNAL_BLOCKED",stop="EXTERNAL_DATA")["status"],"STAGED_EXTERNAL_DATA")
    def test_resource_limit_requires_evidence(self):
        with tempfile.TemporaryDirectory() as t:
            self.assertEqual(self.setup_rows(t,queue_status="STOP_LIMIT",stop="RESOURCE_LIMIT")["status"],"STAGED_RESOURCE_LIMIT")
    def test_pass_requires_depth_and_source(self):
        with tempfile.TemporaryDirectory() as t:
            self.assertEqual(self.setup_rows(t,cover_status="pass",queue_status="DONE")["status"],"COVERAGE_HANDOFF_CANDIDATE")
    def test_false_done_rejected(self):
        with tempfile.TemporaryDirectory() as t:
            self.assertEqual(self.setup_rows(t,queue_status="DONE")["status"],"BLOCK_PREMATURE_STOP")
if __name__=="__main__":unittest.main()
