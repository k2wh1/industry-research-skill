import csv
import importlib.util
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load_module(name, relative_path):
    spec = importlib.util.spec_from_file_location(name, ROOT / relative_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


dcf = load_module("dcf", "scripts/dcf.py")
quality = load_module("quality_check", "scripts/quality_check.py")


class DCFSuite(unittest.TestCase):
    def test_manual_value(self):
        # FCFF=110 next year with g=0%, WACC=10%; no debt; 10 million shares
        result = dcf.compute_dcf([110], 0.10, 0.0, 0, 10)
        # 110/1.1 + (110/0.1)/1.1 = 1100
        self.assertAlmostEqual(result["enterprise_value"], 1100)
        self.assertAlmostEqual(result["per_share_value"], 110)

    def test_net_cash_positive_adjustments(self):
        result = dcf.compute_dcf([100], 0.1, 0, -10, 10, 5)
        self.assertAlmostEqual(result["equity_value"], result["enterprise_value"] + 15)

    def test_invalid_growth(self):
        with self.assertRaises(ValueError):
            dcf.compute_dcf([100], .05, .05, 0, 1)

    def test_invalid_shares(self):
        with self.assertRaises(ValueError):
            dcf.compute_dcf([100], .10, .02, 0, 0)

    def test_boolean_rejected(self):
        with self.assertRaises(ValueError):
            dcf.compute_dcf([True], .10, .02, 0, 1)

    def test_sensitivity(self):
        data = {
            "forecast_fcff": [100, 110], "wacc": .1, "terminal_growth": .02,
            "net_debt": 100, "diluted_shares": 10,
            "sensitivity": {"wacc_delta": [-.01, 0, .01], "growth_delta": [-.005, 0, .005]},
        }
        result = dcf.calculate_from_payload(data)
        self.assertEqual(len(result["sensitivity"]["rows"]), 3)
        middle = result["sensitivity"]["rows"][1]["values"][1]["per_share_value"]
        self.assertAlmostEqual(middle, result["result"]["per_share_value"])


class QualitySuite(unittest.TestCase):
    def test_style_checks_detect_wide_table_and_arrows(self):
        sample = "| A | B | C | D | E |\n|---|---|---|---|---|\n| 1 | 2 | 3 | 4 | 5 |\n" + "A → B → C → D → E → F → G → H → I"
        warnings = quality.style_warnings(sample)
        self.assertTrue(any("Wide" in msg for _, msg in warnings))
        self.assertTrue(any("arrow" in msg for _, msg in warnings))

    def test_style_checks_clean_prose(self):
        self.assertFalse(quality.style_warnings("## 行业需求变化\n正文围绕供需与经营机制展开。"))

    def test_unknown_citation_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            report = Path(tmp) / "report.md"
            ledger = Path(tmp) / "ledger.csv"
            report.write_text("# Title\n研究基准日 2026-11-09 资料截止 2026-11-09\n## 风险反证\nText [E001]", encoding="utf-8")
            with ledger.open("w", newline="", encoding="utf-8") as f:
                w = csv.writer(f)
                w.writerow(["claim_id", "statement", "evidence_type", "source_org", "period", "url_or_file"])
                w.writerow(["E002", "sample", "FACT", "source", "2026", "link"])
            findings = quality.check_report(report, ledger)
            self.assertTrue(any(lvl == "ERROR" and "E001" in message for lvl, message in findings))

    def test_valid_citation_link(self):
        with tempfile.TemporaryDirectory() as tmp:
            report = Path(tmp) / "report.md"
            ledger = Path(tmp) / "ledger.csv"
            report.write_text("# Title\n研究基准日 2026-11-09 资料截止 2026-11-09\n## 风险反证\n## 结论\nClaim [E001]", encoding="utf-8")
            with ledger.open("w", newline="", encoding="utf-8") as f:
                w = csv.writer(f)
                w.writerow(["claim_id", "statement", "evidence_type", "source_org", "period", "url_or_file"])
                w.writerow(["E001", "sample", "FACT", "source", "2026", "link"])
            findings = quality.check_report(report, ledger)
            self.assertFalse(any(level == "ERROR" for level, _ in findings))


if __name__ == "__main__":
    unittest.main()

coverage = load_module("completeness_check", "scripts/completeness_check.py")


class CompletenessSuite(unittest.TestCase):
    def _write(self, tmp, items):
        p = Path(tmp) / "coverage.csv"
        with p.open("w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(coverage.REQUIRED)
            w.writerows(items)
        return p

    def test_missing_high_priority_not_full(self):
        with tempfile.TemporaryDirectory() as d:
            p = self._write(d, [
                ["A1", "行业", "规模", "high", "模型", "missing", "", "", "暂无数据", "去核验"],
                ["A2", "行业", "产品", "medium", "分类", "complete", "E001", "", "", ""],
            ])
            notes, result = coverage.check_coverage(p)
            self.assertFalse(result["full_label_ready"])
            self.assertEqual(result["missing"], 1)
            self.assertTrue(any("A1" in m for _, m in notes))

    def test_not_applicable_requires_justification(self):
        with tempfile.TemporaryDirectory() as d:
            p = self._write(d, [["A1", "行业", "金融监管", "low", "适用说明", "not_applicable", "", "", "", ""]])
            notes, result = coverage.check_coverage(p)
            self.assertTrue(any("justification" in m for _, m in notes))
            self.assertTrue(result["full_label_ready"] is False)  # no applicable items

    def test_complete_with_evidence(self):
        with tempfile.TemporaryDirectory() as d:
            p = self._write(d, [["A1", "行业", "规模", "high", "同口径模型", "complete", "E001;E002", "model.csv", "", ""]])
            notes, result = coverage.check_coverage(p)
            self.assertFalse(result["full_label_ready"])  # One item cannot certify a whole industry
            self.assertAlmostEqual(result["weighted_complete"], 1.0)
            self.assertFalse(any(lvl == "ERROR" for lvl, _ in notes))

    def test_duplicate_ids(self):
        with tempfile.TemporaryDirectory() as d:
            p = self._write(d, [
                ["A1", "行业", "规模", "high", "模型", "complete", "E001", "", "", ""],
                ["A1", "行业", "竞争", "high", "数据", "complete", "E002", "", "", ""],
            ])
            notes, _ = coverage.check_coverage(p)
            self.assertTrue(any(lvl == "ERROR" and "Duplicate" in msg for lvl, msg in notes))


class CoverageIntegritySuite(unittest.TestCase):
    def test_complete_rows_in_four_sections_pass_structural_gate(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "coverage.csv"
            with path.open("w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(coverage.REQUIRED)
                for n in range(12):
                    writer.writerow([f"A{n:02d}", f"section-{n % 4}", f"subject-{n}",
                                     "high", "qualitative comparison", "complete", "E001", "", "", ""])
            notes, result = coverage.check_coverage(path)
            self.assertTrue(result["full_label_ready"])
            self.assertEqual(result["sections"], 4)

    def test_medium_partial_blocks_full_label(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "coverage.csv"
            with path.open("w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(coverage.REQUIRED)
                for n in range(12):
                    status = "partial" if n == 1 else "complete"
                    writer.writerow([f"A{n:02d}", f"section-{n % 4}", f"subject-{n}",
                                     "medium", "research", status, "E001", "",
                                     "unverified data" if status == "partial" else "",
                                     "verify data" if status == "partial" else ""])
            _, result = coverage.check_coverage(path)
            self.assertFalse(result["full_label_ready"])
            self.assertIn("unfinished applicable items", result["blockers"])

    def test_numeric_artifact_missing_blocks_full_label(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "coverage.csv"
            with path.open("w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(coverage.REQUIRED)
                for n in range(12):
                    writer.writerow([f"A{n:02d}", f"section-{n % 4}", f"subject-{n}",
                                     "high", "量化模型", "complete", "E001", "", "", ""])
            _, result = coverage.check_coverage(path)
            self.assertFalse(result["full_label_ready"])
            self.assertIn("promised quantitative artifacts missing", result["blockers"])

# v2.3 research-quality checks: deterministic fixtures, not actual company data.
data_audit = load_module("data_audit", "scripts/data_audit.py")
model_check = load_module("model_check", "scripts/model_check.py")
figure_check = load_module("figure_check", "scripts/figure_check.py")


class DataAuditSuite(unittest.TestCase):
    COLUMNS = data_audit.METRIC_COLUMNS

    def write_metrics(self, base, records):
        path = Path(base) / "metrics.csv"
        with path.open("w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(self.COLUMNS)
            writer.writerows(records)
        return path

    def write_rules(self, base, records):
        path = Path(base) / "rules.csv"
        with path.open("w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(data_audit.RULE_COLUMNS)
            writer.writerows(records)
        return path

    @staticmethod
    def metric(mid, value, unit="亿元", period="CY2025", metric="sales", kind="estimate", pub="2026-01-01"):
        return [mid, "fictional sector", metric, period, "CY", "USD", unit, "comparison", value, "E001", kind, pub]

    def test_component_sum_error_detected(self):
        with tempfile.TemporaryDirectory() as tmp:
            values = [285, 250, 220, 150, 85, 55, 55, 45, 40]
            rows = [self.metric(f"s{i}", v, metric=f"category{i}") for i, v in enumerate(values)]
            rows += [self.metric("total", 1165, metric="total")]
            rules = self.write_rules(tmp, [["R1", "sum", "total", ";".join(f"s{i}" for i in range(len(values))), "0", "0", "reconcile"]])
            findings = data_audit.audit(self.write_metrics(tmp, rows), rules)
            self.assertTrue(any(level == "ERROR" and "1185" in note and "1165" in note for level, note in findings))

    def test_conflicting_same_period_number_in_different_units(self):
        with tempfile.TemporaryDirectory() as tmp:
            rows = [self.metric("a", "1.13", unit="万亿", metric="annual revenue", kind="actual"),
                    self.metric("b", "11.3", unit="万亿", metric="annual revenue", kind="actual")]
            findings = data_audit.audit(self.write_metrics(tmp, rows))
            self.assertTrue(any(level == "ERROR" and "conflicting" in message for level, message in findings))

    def test_equivalent_units_not_conflict(self):
        with tempfile.TemporaryDirectory() as tmp:
            rows = [self.metric("a", "1", unit="billion", metric="annual revenue"),
                    self.metric("b", "10", unit="亿元", metric="annual revenue")]
            findings = data_audit.audit(self.write_metrics(tmp, rows))
            self.assertFalse(any(level == "ERROR" for level, _ in findings))

    def test_source_date_after_asof_is_blocked(self):
        with tempfile.TemporaryDirectory() as tmp:
            rows = [self.metric("a", 10, pub="2027-01-01")]
            findings = data_audit.audit(self.write_metrics(tmp, rows), as_of="2026-11-09")
            self.assertTrue(any(level == "ERROR" and "after as-of" in msg for level, msg in findings))

    def test_cross_currency_ratio_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            rows = [self.metric("n", 30), self.metric("d", 100), self.metric("p", 30, unit="pct")]
            rows[1][5] = "CNY"
            rules = self.write_rules(tmp, [["R1", "ratio_pct", "p", "n;d", "0.01", "0", "currency error"]])
            findings = data_audit.audit(self.write_metrics(tmp, rows), rules)
            self.assertTrue(any(level == "ERROR" and "cross-currency" in msg for level, msg in findings))

    def test_correct_sum_and_pct_rule(self):
        with tempfile.TemporaryDirectory() as tmp:
            rows = [self.metric("a", 20, metric="part_a"), self.metric("b", 30, metric="part_b"), self.metric("t", 50, metric="total"),
                    self.metric("pct", 40, unit="pct", metric="share")]
            rules = self.write_rules(tmp, [["R1", "sum", "t", "a;b", 0, 0, ""],
                                           ["R2", "ratio_pct", "pct", "a;t", 0, 0, ""]])
            findings = data_audit.audit(self.write_metrics(tmp, rows), rules)
            self.assertFalse(any(level == "ERROR" for level, _ in findings))


class ModelAuditSuite(unittest.TestCase):
    def test_self_validation_blocked(self):
        import json
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "model.json"
            (Path(d) / "model.csv").write_text("metric,value\nx,1\n", encoding="utf-8")
            path.write_text(json.dumps({"models": [{
                "model_id": "M1", "research_question": "why?", "formula": "x", "output_metric": "market", "model_file": "model.csv",
                "inputs": [{"variable": "x", "unit": "units", "origin": "source", "evidence_id": "E001"}],
                "calibration_targets": ["market_2025"], "validation_targets": ["market_2025"],
                "claims_independent_validation": True, "input_target_ids": ["market_2025"],
                "validation_period": "CY2025", "units_and_scope": "USD", "reconciliation_notes": "unresolved"
            }]}), encoding="utf-8")
            findings = model_check.check_manifest(path)
            self.assertTrue(any(lvl == "ERROR" and "circular" in msg for lvl, msg in findings))
            self.assertTrue(any(lvl == "ERROR" and "also an input" in msg for lvl, msg in findings))

    def test_no_false_claim_of_independence(self):
        import json
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "model.json"
            (Path(d) / "model.csv").write_text("metric,value\nx,1\n", encoding="utf-8")
            path.write_text(json.dumps({"models": [{
                "model_id": "M1", "research_question": "why?", "formula": "x", "output_metric": "market", "model_file": "model.csv",
                "inputs": [{"variable": "x", "unit": "units", "origin": "assumption"}],
                "calibration_targets": ["market_2025"], "validation_targets": [],
                "claims_independent_validation": False, "input_target_ids": [],
                "units_and_scope": "USD", "reconciliation_notes": "calibration only"
            }]}), encoding="utf-8")
            findings = model_check.check_manifest(path)
            self.assertFalse(any(level == "ERROR" for level, _ in findings))


class FigureAuditSuite(unittest.TestCase):
    def test_figure_path_missing(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "figure_manifest.csv"
            with p.open("w", encoding="utf-8", newline="") as f:
                w = csv.writer(f)
                w.writerow(figure_check.REQUIRED)
                w.writerow(["F01", "charts/fig1.png", "Trend", "2021-2025", "USD bn", "E001", "What drives growth?", "Trend", "estimate"])
            findings = figure_check.check_figures(p)
            self.assertTrue(any(lvl == "ERROR" and "not found" in msg for lvl, msg in findings))

class ReleaseGateSuite(unittest.TestCase):
    def test_full_report_missing_artifacts_blocks(self):
        import subprocess
        import sys
        with tempfile.TemporaryDirectory() as d:
            report = Path(d) / "report.md"
            report.write_text("# draft\n研究基准日 2026-11-09 资料截止 2026-11-09\n## 风险和反证\n", encoding="utf-8")
            result = subprocess.run([sys.executable, str(ROOT / "scripts/run_qa.py"),
                                     "--mode", "industry_full", "--report", str(report)],
                                     capture_output=True, text=True, encoding="utf-8")
            self.assertEqual(result.returncode, 1)
            self.assertIn("Release status: BLOCKED", result.stdout)
            self.assertIn("metrics: required QA artifact", result.stdout)
