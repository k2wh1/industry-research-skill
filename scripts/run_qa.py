#!/usr/bin/env python3
"""Run available research QA checks together; never claims factual verification.

For full industry research, missing critical artifacts are blockers rather than a
misleading green '36/36' result. Manual independent review is still mandatory.
"""
from __future__ import annotations

import argparse
import csv
from pathlib import Path

from completeness_check import check_coverage
from data_audit import audit
from figure_check import check_figures
from model_check import check_manifest
from quality_check import check_report
from score_report import evaluate


def run_checks(*, report: Path, ledger: Path | None = None,
               coverage: Path | None = None, metrics: Path | None = None,
               rules: Path | None = None, models: Path | None = None,
               figures: Path | None = None, review: Path | None = None,
               figure_plan: Path | None = None, scores: Path | None = None,
               gates: Path | None = None, as_of: str | None = None,
               mode: str = "industry_full"):
    out = []
    required = {"ledger": ledger}
    if mode in {"industry_full", "company"}:
        required.update({"metrics": metrics, "rules": rules, "models": models})
    if mode == "industry_full":
        required.update({"coverage": coverage, "figures": figures, "review": review, "figure_plan": figure_plan, "scores": scores, "gates": gates})
    for label, file in required.items():
        if file is None:
            out.append(("ERROR", f"{label}: required QA artifact not supplied"))
        elif not file.is_file():
            out.append(("ERROR", f"{label}: file does not exist: {file}"))
    if not report.is_file():
        out.append(("ERROR", f"report file missing: {report}"))
        return out
    if ledger and ledger.is_file():
        out.extend(check_report(report, ledger, "company" if mode == "company" else "industry"))
    else:
        out.extend(check_report(report))
    if coverage and coverage.is_file():
        findings, summary = check_coverage(coverage)
        out.extend(findings)
        if mode == "industry_full" and not summary.get("full_label_ready", False):
            out.append(("ERROR", "coverage structurally incomplete; full report label blocked"))
    if metrics and metrics.is_file():
        out.extend(audit(metrics, rules if rules and rules.is_file() else None, as_of))
        if mode in {"industry_full", "company"}:
            with metrics.open(encoding="utf-8-sig", newline="") as f:
                if not list(csv.DictReader(f)):
                    out.append(("ERROR", "metrics.csv contains no data; numerical QA not performed"))
    if rules and rules.is_file() and mode in {"industry_full", "company"}:
        with rules.open(encoding="utf-8-sig", newline="") as f:
            if not list(csv.DictReader(f)):
                out.append(("ERROR", "audit_rules.csv contains no rules; arithmetic QA not performed"))
    if models and models.is_file():
        out.extend(check_manifest(models))
    if figures and figures.is_file():
        out.extend(check_figures(figures, report))
    if mode == "industry_full" and not (figures and figures.is_file()):
        out.append(("ERROR", "no figure plan/manifest: core evidence visualization not evaluated"))
    if scores and scores.is_file() and gates and gates.is_file():
        rating = evaluate(scores, gates)
        for err in rating["errors"]:
            out.append(("ERROR", "quality loop: " + err))
        if rating["rounds"]:
            last = rating["rounds"][-1]
            out.append(("INFO", f"quality round {last['round_id']}: {last['total']}/100, {last['status']}"))
            if mode == "industry_full" and last["status"] != "HUMAN_RELEASE_REVIEW_REQUIRED":
                out.append(("ERROR", "quality gate not ready for human release review: " + last["status"]))
        elif mode == "industry_full":
            out.append(("ERROR", "quality loop has no completed valid review round"))
    return out


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--report", type=Path, required=True)
    for key in ("ledger", "coverage", "metrics", "rules", "models", "figures", "review"):
        p.add_argument(f"--{key}", type=Path)
    p.add_argument("--figure-plan", type=Path)
    p.add_argument("--scores", type=Path)
    p.add_argument("--gates", type=Path)
    p.add_argument("--as-of")
    p.add_argument("--mode", choices=["industry_full", "industry_brief", "thematic", "company", "update"], default="industry_full")
    args = p.parse_args()
    try:
        res = run_checks(**vars(args))
    except (OSError, ValueError, TypeError, csv.Error) as exc:
        p.exit(2, f"QA inputs cannot be read: {exc}\n")
    for level, msg in res:
        print(f"[{level}] {msg}")
    status = "BLOCKED" if any(lvl == "ERROR" for lvl, _ in res) else "STRUCTURAL QA PASSED — EXTERNAL FACTS NOT VERIFIED"
    print(f"Release status: {status}")
    return 1 if status == "BLOCKED" else 0


if __name__ == "__main__":
    raise SystemExit(main())
