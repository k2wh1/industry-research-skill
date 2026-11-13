#!/usr/bin/env python3
"""Check an industry coverage CSV for structural research gaps.

This script cannot verify facts, evidence quality, causal analysis, or whether the
industry taxonomy is exhaustive. A 'ready' result is a *structural* checkpoint.
"""
from __future__ import annotations

import argparse
import csv
import re
from collections import Counter
from pathlib import Path

REQUIRED = (
    "id", "section", "subsection", "priority", "required_depth", "status",
    "evidence_ids", "quantitative_artifact", "gap", "next_action",
)
STATUSES = {"complete", "partial", "missing", "not_applicable"}
PRIORITIES = {"high": 3, "medium": 2, "low": 1}
DEFAULT_MIN_ITEMS = 10
DEFAULT_MIN_SECTIONS = 4
QUANTITATIVE_TERMS = ("模型", "测算", "财务", "量化", "预测", "历史数据", "敏感性", "market model", "forecast")


def check_coverage(path: Path, min_items: int = DEFAULT_MIN_ITEMS,
                   min_sections: int = DEFAULT_MIN_SECTIONS):
    """Return findings and summary for a human-authored coverage register."""
    if min_items < 1 or min_sections < 1:
        raise ValueError("min_items and min_sections must be >= 1")
    findings: list[tuple[str, str]] = []
    with path.open(encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)
        fields = set(reader.fieldnames or ())
        missing_fields = sorted(set(REQUIRED) - fields)
        if missing_fields:
            return [("ERROR", "Missing required columns: " + ", ".join(missing_fields))], {}
        rows = list(reader)
    if not rows:
        return [("ERROR", "Coverage register is empty")], {}

    def cell(row: dict, key: str) -> str:
        return str(row.get(key) or "").strip()

    ids = [cell(row, "id") for row in rows]
    if any(not item for item in ids):
        findings.append(("ERROR", "Empty coverage ID found"))
    duplicates = sorted(key for key, count in Counter(ids).items() if key and count > 1)
    if duplicates:
        findings.append(("ERROR", "Duplicate coverage IDs: " + ", ".join(duplicates)))
    if len(rows) < min_items:
        findings.append(("WARN", f"Only {len(rows)} scope items; full-industry register requires >= {min_items} "
                          "items as an initial structural safeguard (adjust --min-items for unusual scopes)."))

    total_weight = complete_weight = partial_weight = 0
    high_not_complete = []
    counts = Counter()
    section_names = set()
    complete_without_evidence = []
    unresolved_without_action = []
    not_applicable_without_reason = []
    quant_missing = []
    invalid_rows = 0

    for line_num, row in enumerate(rows, 2):
        rid = cell(row, "id") or f"row {line_num}"
        status = cell(row, "status").lower()
        priority = cell(row, "priority").lower()
        section = cell(row, "section")
        subsection = cell(row, "subsection")
        depth = cell(row, "required_depth")
        evidence = cell(row, "evidence_ids")
        quant = cell(row, "quantitative_artifact")
        gap = cell(row, "gap")
        action = cell(row, "next_action")
        if priority not in PRIORITIES:
            findings.append(("ERROR", f"{rid}: invalid priority {priority!r}"))
            invalid_rows += 1
            continue
        if status not in STATUSES:
            findings.append(("ERROR", f"{rid}: invalid status {status!r}"))
            invalid_rows += 1
            continue
        if not section or not subsection or not depth:
            findings.append(("ERROR", f"{rid}: incomplete research scope definition"))
            invalid_rows += 1
            continue
        section_names.add(section)
        counts[status] += 1
        if status == "not_applicable":
            if not gap:
                not_applicable_without_reason.append(rid)
                findings.append(("WARN", f"{rid}: not_applicable requires written justification in gap"))
            continue
        weight = PRIORITIES[priority]
        total_weight += weight
        if status == "complete":
            complete_weight += weight
            if not evidence:
                complete_without_evidence.append(rid)
                findings.append(("WARN", f"{rid}: marked complete but has no evidence references"))
            if any(term in depth.lower() for term in QUANTITATIVE_TERMS) and not quant:
                quant_missing.append(rid)
                findings.append(("WARN", f"{rid}: quantitative depth promised but quantitative_artifact missing"))
        elif status == "partial":
            partial_weight += weight
        if status in {"missing", "partial"}:
            if priority == "high":
                high_not_complete.append(rid)
            if not gap or not action:
                unresolved_without_action.append(rid)
                findings.append(("WARN", f"{rid}: unfinished item needs gap and next_action"))
        if evidence and any(not re.fullmatch(r"E\d{3,}", token.strip().strip("[]"))
                            for token in re.split(r"[;,，；\s]+", evidence) if token.strip()):
            findings.append(("ERROR", f"{rid}: evidence_ids must contain E001-style IDs separated by semicolons"))

    if len(section_names) < min_sections:
        findings.append(("WARN", f"Only {len(section_names)} distinct research sections; "
                          f"full-industry register requires >= {min_sections} as a structural safeguard."))
    if high_not_complete:
        findings.append(("WARN", "High-priority incomplete items: " + ", ".join(high_not_complete)))

    blockers = []
    if len(rows) < min_items:
        blockers.append("insufficient scope items")
    if len(section_names) < min_sections:
        blockers.append("insufficient research sections")
    if total_weight == 0:
        blockers.append("no applicable scope")
    if invalid_rows or any(level == "ERROR" for level, _ in findings):
        blockers.append("invalid coverage data")
    if counts["partial"] or counts["missing"]:
        blockers.append("unfinished applicable items")
    if complete_without_evidence:
        blockers.append("completed items without evidence IDs")
    if quant_missing:
        blockers.append("promised quantitative artifacts missing")
    if not_applicable_without_reason:
        blockers.append("unjustified exclusions")
    if unresolved_without_action:
        blockers.append("unfinished items without an action plan")

    summary = {
        "items": len(rows),
        "sections": len(section_names),
        "complete": counts["complete"],
        "partial": counts["partial"],
        "missing": counts["missing"],
        "not_applicable": counts["not_applicable"],
        "weighted_complete": (complete_weight / total_weight) if total_weight else None,
        "weighted_partial_or_complete": ((complete_weight + partial_weight) / total_weight) if total_weight else None,
        "high_priority_incomplete": high_not_complete,
        "blockers": blockers,
        "full_label_ready": not blockers,
    }
    if blockers:
        findings.append(("WARN", "Not structurally ready for 'completed full industry research': "
                         + "; ".join(blockers) + "."))
    if not findings:
        findings.append(("PASS", "Coverage register passes structural checks only; research and "
                          "sources still need substantive review."))
    return findings, summary


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("coverage", type=Path)
    parser.add_argument("--strict", action="store_true", help="Fail when structural readiness check fails")
    parser.add_argument("--min-items", type=int, default=DEFAULT_MIN_ITEMS)
    parser.add_argument("--min-sections", type=int, default=DEFAULT_MIN_SECTIONS)
    args = parser.parse_args()
    try:
        findings, summary = check_coverage(args.coverage, args.min_items, args.min_sections)
    except (OSError, csv.Error, UnicodeDecodeError, ValueError) as err:
        parser.exit(2, f"Unable to check coverage register: {err}\n")
    for level, message in findings:
        print(f"[{level}] {message}")
    if summary:
        ratio = "N/A" if summary["weighted_complete"] is None else f"{summary['weighted_complete']:.1%}"
        print(f"Coverage: {summary['items']} items / {summary['sections']} sections; "
              f"complete {summary['complete']}, partial {summary['partial']}, "
              f"missing {summary['missing']}, N/A {summary['not_applicable']}; "
              f"weighted complete {ratio}")
        print("Structurally ready:", "yes (NOT a fact/quality audit)" if summary["full_label_ready"] else "NO")
    has_error = any(level == "ERROR" for level, _ in findings)
    return 1 if has_error or (args.strict and not summary.get("full_label_ready", False)) else 0


if __name__ == "__main__":
    raise SystemExit(main())
