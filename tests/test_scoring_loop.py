"""Tests for the reviewer-supplied 100-point loop. No live evidence asserted."""
import csv
import importlib.util
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("score_report", ROOT / "scripts/score_report.py")
scoring = importlib.util.module_from_spec(spec)
spec.loader.exec_module(scoring)


def write_rows(path, fields, rows):
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def sample(tmp, *, score=4.5, gate="PASS", rounds=("R1",)):
    scores = Path(tmp) / "scores.csv"
    gates = Path(tmp) / "gates.csv"
    srows, grows = [], []
    for rnd in rounds:
        for key in scoring.WEIGHTS:
            srows.append(dict(round_id=rnd, criterion_id=key, score_0_5=score if rnd == "R1" else 5,
                              evidence_refs="chapter/E001", weakness="tracked", next_action="verify source"))
        for key in scoring.GATES:
            grows.append(dict(round_id=rnd, gate=key, status=gate, review_evidence="reviewer checked"))
    write_rows(scores, ["round_id", "criterion_id", "score_0_5", "evidence_refs", "weakness", "next_action"], srows)
    write_rows(gates, ["round_id", "gate", "status", "review_evidence"], grows)
    return scores, gates


class ScoreLoopSuite(unittest.TestCase):
    def test_weighted_total_and_human_gate(self):
        with tempfile.TemporaryDirectory() as tmp:
            s, g = sample(tmp)
            result = scoring.evaluate(s, g)
            self.assertTrue(result["valid"])
            self.assertEqual(result["rounds"][0]["total"], 90)
            self.assertEqual(result["rounds"][0]["status"], "HUMAN_RELEASE_REVIEW_REQUIRED")
            self.assertEqual(result["rounds"][0]["grade"], "A")

    def test_failed_gate_blocks_high_score(self):
        with tempfile.TemporaryDirectory() as tmp:
            s, g = sample(tmp, score=5, gate="FAIL")
            result = scoring.evaluate(s, g)
            self.assertEqual(result["rounds"][0]["total"], 100)
            self.assertEqual(result["rounds"][0]["status"], "BLOCKED")

    def test_unknown_gate_preserves_staged(self):
        with tempfile.TemporaryDirectory() as tmp:
            s, g = sample(tmp, gate="UNKNOWN")
            self.assertEqual(scoring.evaluate(s, g)["rounds"][0]["status"], "STAGED")

    def test_missing_criterion_is_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            s, g = sample(tmp)
            rows = list(csv.DictReader(s.open(encoding="utf-8")))
            write_rows(s, list(rows[0]), rows[:-1])
            result = scoring.evaluate(s, g)
            self.assertFalse(result["valid"])
            self.assertTrue(any("missing score" in x for x in result["errors"]))

    def test_duplicate_criterion_is_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            s, g = sample(tmp)
            rows = list(csv.DictReader(s.open(encoding="utf-8")))
            write_rows(s, list(rows[0]), rows + [rows[0]])
            self.assertTrue(any("duplicate criterion" in x for x in scoring.evaluate(s,g)["errors"]))

    def test_round_delta_and_revision_queue(self):
        with tempfile.TemporaryDirectory() as tmp:
            s, g = sample(tmp, score=4, rounds=("R1", "R2"))
            result = scoring.evaluate(s, g)
            self.assertEqual([r["total"] for r in result["rounds"]], [80, 100])
            self.assertEqual(result["rounds"][1]["delta_from_previous"], 20)
            self.assertEqual(result["rounds"][0]["revision_queue"][0]["criterion_id"], "evidence")

    def test_invalid_score_is_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            s, g = sample(tmp, score=6)
            self.assertFalse(scoring.evaluate(s, g)["valid"])

    def test_ratings_cannot_replace_fact_review(self):
        with tempfile.TemporaryDirectory() as tmp:
            s, g = sample(tmp)
            result = scoring.evaluate(s, g)
            self.assertIn("do not verify source authenticity", result["warning"])

if __name__ == "__main__":
    unittest.main()
