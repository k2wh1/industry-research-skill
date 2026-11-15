"""Tests for the same-task execution/reflection/revision trace gate."""
from __future__ import annotations
import csv
import importlib.util
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("autonomous_loop_gate", ROOT / "scripts" / "autonomous_loop_gate.py")
gate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gate)


def make_trace(directory, rows):
    path = Path(directory) / "execution_cycle.csv"
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=sorted(gate.FIELDS))
        writer.writeheader()
        for row in rows:
            writer.writerow({
                "run_id": "task-001", "module": "M00", "round_id": "R1",
                "draft_ref": "report-v1.md", "reflection_ref": "review-R1.md",
                "p0_open": 0, "p1_open": 0, "decision": "PASS",
                "revision_ref": "", "verification_ref": "verify-R1.md",
                "blocking_reason": "", **row,
            })
    return path


class AutonomousLoopGateTests(unittest.TestCase):
    def test_first_pass_clean_can_reach_review(self):
        with tempfile.TemporaryDirectory() as d:
            result = gate.evaluate(make_trace(d, [{}]))
            self.assertEqual(result["status"], "READY_FOR_HUMAN_REVIEW")

    def test_unresolved_issue_cannot_pass(self):
        with tempfile.TemporaryDirectory() as d:
            result = gate.evaluate(make_trace(d, [{"p1_open": 1}]))
            self.assertEqual(result["status"], "INCOMPLETE")

    def test_revision_requires_new_reflection(self):
        with tempfile.TemporaryDirectory() as d:
            result = gate.evaluate(make_trace(d, [{
                "p1_open": 1, "decision": "REVISE",
                "revision_ref": "report-v2.md", "verification_ref": "diff-R1.md",
            }]))
            self.assertEqual(result["status"], "INCOMPLETE")

    def test_valid_revision_then_second_reflection(self):
        with tempfile.TemporaryDirectory() as d:
            rows = [
                {"p0_open": 1, "decision": "REVISE",
                 "revision_ref": "report-v2.md", "verification_ref": "verify-R1.md"},
                {"round_id": "R2", "draft_ref": "report-v2.md",
                 "reflection_ref": "review-R2.md", "verification_ref": "verify-R2.md"},
            ]
            self.assertEqual(gate.evaluate(make_trace(d, rows))["status"],
                             "READY_FOR_HUMAN_REVIEW")

    def test_revision_without_new_version_fails(self):
        with tempfile.TemporaryDirectory() as d:
            rows = [
                {"decision": "REVISE", "revision_ref": "report-v1.md"},
                {"round_id": "R2", "draft_ref": "report-v1.md"},
            ]
            self.assertEqual(gate.evaluate(make_trace(d, rows))["status"], "INCOMPLETE")

    def test_external_blocker_is_staged_only(self):
        with tempfile.TemporaryDirectory() as d:
            rows = [{"p1_open": 1, "decision": "EXTERNAL_BLOCKED",
                     "blocking_reason": "Customer-level ASP unavailable"}]
            self.assertEqual(gate.evaluate(make_trace(d, rows))["status"], "STAGED_ONLY")

    def test_multiple_modules_all_need_pass(self):
        with tempfile.TemporaryDirectory() as d:
            rows = [{}, {"module": "S01", "decision": "STOP_LIMIT",
                         "blocking_reason": "Tool limit reached"}]
            self.assertEqual(gate.evaluate(make_trace(d, rows))["status"], "STAGED_ONLY")


if __name__ == "__main__":
    unittest.main()
