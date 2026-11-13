#!/usr/bin/env python3
"""Offline structure & citation-ID checks; NOT factual or source authenticity review."""

from __future__ import annotations

import argparse
import csv
import re
from collections import Counter
from pathlib import Path

EVIDENCE_PATTERN = re.compile(r"\[(E\d{3,})\]")
VALID_TYPES = {"FACT", "GUIDANCE", "ASSUMPTION", "INFERENCE"}


def style_warnings(content: str) -> list[tuple[str, str]]:
    """Heuristic presentation warnings, not AI-origin detection or factual review."""
    result: list[tuple[str, str]] = []
    lines = content.splitlines()
    wide_tables = []
    for idx, line in enumerate(lines, 1):
        if line.startswith("|") and line.endswith("|") and "---" not in line:
            num_cols = len(line.strip("|").split("|"))
            if num_cols > 4:
                wide_tables.append((idx, num_cols))
    if wide_tables:
        result.append(("WARN", "Wide Markdown tables (>4 columns), e.g. line "
                       + ", ".join(f"{n}: {c} cols" for n, c in wide_tables[:3])
                       + "; split these for report reading and Word export."))
    if content.count("**") >= 30:
        result.append(("WARN", "Frequent bold markers: consider removing paragraph-level emphasis."))
    if content.count("→") >= 8:
        result.append(("WARN", "Frequent arrow chains: explain economic mechanisms in prose."))
    methodological_headings = [h for h in lines if h.startswith("## ") and any(
        phrase in h for phrase in ("核心观点（先结论", "最强反方", "跟踪看板", "证伪矩阵"))]
    if methodological_headings:
        result.append(("WARN", "Report contains process/checklist headings; move research matrices to appendices."))
    return result


def check_report(report_path: Path, ledger_path: Path | None = None,
                 mode: str = "industry") -> list[tuple[str, str]]:
    findings: list[tuple[str, str]] = []
    content = report_path.read_text(encoding="utf-8-sig")
    findings.extend(style_warnings(content))
    report_ids = set(EVIDENCE_PATTERN.findall(content))
    if not report_ids:
        findings.append(("WARN", "Report contains no evidence references of the form [E001]."))
    headings = [line.lstrip("# ").strip() for line in content.splitlines()
                if re.match(r"^#{1,6}\s+", line)]
    if len(headings) < 4:
        findings.append(("WARN", "Few Markdown headings: consider checking document structure."))
    if "研究基准日" not in content:
        findings.append(("WARN", "Research as-of date (研究基准日) not found."))
    if "资料截止" not in content and "数据截止" not in content:
        findings.append(("WARN", "Evidence/data cutoff (资料截止/数据截止) not found."))
    if not any(term in content for term in ("反证", "反方", "证伪")):
        findings.append(("WARN", "No counter-evidence/falsification discussion found."))
    if not any(term in content for term in ("风险", "下行")):
        findings.append(("WARN", "No apparent risk discussion found."))
    if mode == "company" and not any(term in content.upper() for term in ("ROIC", "FCFF", "FCF")):
        findings.append(("WARN", "Company report lacks obvious capital-return/FCF discussion."))
    if mode == "company" and not any(term in content for term in ("估值", "价值区间", "不能估值")):
        findings.append(("WARN", "Company report lacks apparent valuation discussion or explanation."))
    if ledger_path is None:
        findings.append(("WARN", "No evidence ledger provided; citation linkage was not checked."))
        return findings
    with ledger_path.open(encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        if not reader.fieldnames or "claim_id" not in reader.fieldnames:
            findings.append(("ERROR", "Evidence ledger must have a claim_id column."))
            return findings
        rows = list(reader)
    ids = [row.get("claim_id", "").strip() for row in rows]
    duplicates = sorted(cid for cid, count in Counter(ids).items() if cid and count > 1)
    if duplicates:
        findings.append(("ERROR", "Duplicate evidence IDs: " + ", ".join(duplicates)))
    ledger_ids = set(ids) - {""}
    for cid in sorted(report_ids - ledger_ids):
        findings.append(("ERROR", f"{cid} is cited in report but absent in ledger."))
    for cid in sorted(ledger_ids - report_ids):
        findings.append(("WARN", f"{cid} is in ledger but not cited in report."))
    for n, row in enumerate(rows, start=2):
        cid = row.get("claim_id", "").strip()
        if not EVIDENCE_PATTERN.fullmatch(f"[{cid}]"):
            findings.append(("ERROR", f"Ledger row {n}: invalid claim_id: {cid!r}."))
        kind = row.get("evidence_type", "").strip()
        if kind not in VALID_TYPES:
            findings.append(("WARN", f"Ledger row {n} ({cid}): unknown evidence_type {kind!r}."))
        if not row.get("statement", "").strip():
            findings.append(("WARN", f"Ledger row {n} ({cid}): missing statement."))
        if kind in {"FACT", "GUIDANCE"}:
            for field in ("source_org", "period", "url_or_file"):
                if field in row and not row.get(field, "").strip():
                    findings.append(("WARN", f"Ledger row {n} ({cid}): missing {field}."))
    if not findings:
        findings.append(("PASS", "No structural/citation-ID issues detected; manual fact verification still required."))
    return findings


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("report", type=Path)
    parser.add_argument("--ledger", type=Path)
    parser.add_argument("--mode", choices=["industry", "company", "thematic", "update"], default="industry")
    args = parser.parse_args()
    try:
        findings = check_report(args.report, args.ledger, args.mode)
    except (OSError, UnicodeDecodeError, csv.Error) as exc:
        parser.exit(2, f"Cannot read report/ledger: {exc}\n")
    for level, msg in findings:
        print(f"[{level}] {msg}")
    return 1 if any(level == "ERROR" for level, _ in findings) else 0


if __name__ == "__main__":
    raise SystemExit(main())
