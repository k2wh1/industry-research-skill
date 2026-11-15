#!/usr/bin/env python3
"""Check Execute -> Reflection -> Revision -> Verification trace consistency.

This validates documentary evidence of workflow only. It cannot verify research
facts, prove that an AI truly reflected, or authorize RELEASED status.
"""
from __future__ import annotations

import argparse
import csv
import json
from collections import defaultdict
from pathlib import Path

FIELDS = {
    "run_id", "module", "round_id", "draft_ref", "reflection_ref",
    "p0_open", "p1_open", "decision", "revision_ref",
    "verification_ref", "blocking_reason",
}
DECISIONS = {"REVISE", "PASS", "EXTERNAL_BLOCKED", "STOP_LIMIT"}


def evaluate(trace: Path) -> dict:
    with trace.open(encoding="utf-8-sig", newline="") as fh:
        reader = csv.DictReader(fh)
        if not reader.fieldnames or not FIELDS.issubset(reader.fieldnames):
            missing = sorted(FIELDS - set(reader.fieldnames or ()))
            raise ValueError(f"missing required fields: {missing}")
        rows = list(reader)

    errors: list[str] = []
    warnings: list[str] = []
    if not rows:
        errors.append("No execution rounds recorded")
    run_ids = {r["run_id"].strip() for r in rows}
    if len(run_ids) != 1 or not all(run_ids):
        errors.append("Trace must contain exactly one nonempty run_id")

    modules: dict[str, list[dict]] = defaultdict(list)
    for index, row in enumerate(rows, 1):
        module = row["module"].strip()
        if not module:
            errors.append(f"row {index}: module missing")
            continue
        modules[module].append({k: (v or "").strip() for k, v in row.items() if k})

    final_states: dict[str, str] = {}
    for module, history in modules.items():
        for idx, row in enumerate(history):
            marker = f"{module}/{row['round_id'] or idx + 1}"
            if row["round_id"] != f"R{idx + 1}":
                errors.append(f"{marker}: expected sequential round R{idx + 1}")
            if not row["draft_ref"] or not row["reflection_ref"]:
                errors.append(f"{marker}: draft_ref and reflection_ref required")
            decision = row["decision"].upper()
            if decision not in DECISIONS:
                errors.append(f"{marker}: invalid decision {decision}")
                continue
            try:
                p0, p1 = int(row["p0_open"]), int(row["p1_open"])
                if p0 < 0 or p1 < 0:
                    raise ValueError
            except ValueError:
                errors.append(f"{marker}: p0_open/p1_open must be nonnegative integers")
                continue

            is_last = idx == len(history) - 1
            if decision == "REVISE":
                if not row["revision_ref"] or not row["verification_ref"]:
                    errors.append(f"{marker}: REVISE needs revision_ref and verification_ref")
                if row["revision_ref"] == row["draft_ref"]:
                    errors.append(f"{marker}: revision must have a distinct version/ref")
                if is_last:
                    errors.append(f"{marker}: REVISE cannot be the last round; re-reflect on revision")
                elif history[idx + 1]["draft_ref"] != row["revision_ref"]:
                    errors.append(f"{marker}: next round draft_ref must equal this revision_ref")
            elif decision == "PASS":
                if p0 or p1:
                    errors.append(f"{marker}: PASS with unresolved P0/P1")
                if not row["verification_ref"]:
                    errors.append(f"{marker}: PASS requires final full-artifact verification")
                if not is_last:
                    errors.append(f"{marker}: PASS may only be the last round")
            else:
                if not row["blocking_reason"] or not row["verification_ref"]:
                    errors.append(f"{marker}: {decision} needs blocker and impact review evidence")
                if not is_last:
                    errors.append(f"{marker}: {decision} may only be the last round")
                warnings.append(f"{module}: ended as {decision}, staged output only")
            final_states[module] = decision

    ready = bool(modules) and all(s == "PASS" for s in final_states.values())
    status = "INCOMPLETE" if errors else ("READY_FOR_HUMAN_REVIEW" if ready else "STAGED_ONLY")
    return {
        "status": status,
        "run_id": next(iter(run_ids)) if len(run_ids) == 1 else None,
        "modules": {name: {"rounds": len(history), "decision": final_states.get(name)}
                    for name, history in modules.items()},
        "errors": errors,
        "warnings": warnings,
        "notice": (
            "Trace consistency check only. Independently verify evidence, "
            "run revision_gate.py and run_qa.py; no automatic RELEASED."
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--trace", required=True, type=Path)
    parser.add_argument("--require-ready", action="store_true",
                        help="Fail if not ready for independent final review")
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    try:
        result = evaluate(args.trace)
    except (OSError, UnicodeError, csv.Error, ValueError) as exc:
        parser.exit(2, f"Invalid trace: {exc}\n")
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 1 if result["status"] == "INCOMPLETE" or (
        args.require_ready and result["status"] != "READY_FOR_HUMAN_REVIEW") else 0


if __name__ == "__main__":
    raise SystemExit(main())
