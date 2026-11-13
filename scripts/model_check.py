#!/usr/bin/env python3
"""Check whether model 'validation' reuses calibration targets (self-validation).

This is a transparent structural guard, not a test of predictive power.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path


def check_manifest(path: Path):
    findings = []
    payload = json.loads(path.read_text(encoding="utf-8-sig"))
    models = payload.get("models", [])
    if not isinstance(models, list) or not models:
        return [("ERROR", "No models defined; cannot claim independent modeling")]
    seen = set()
    for item in models:
        mid = item.get("model_id")
        if not mid or mid in seen:
            findings.append(("ERROR", f"Missing/duplicate model_id: {mid}"))
            continue
        seen.add(mid)
        for field in ("research_question", "formula", "output_metric", "model_file"):
            if not item.get(field):
                findings.append(("ERROR", f"{mid}: missing {field}"))
        model_file = item.get("model_file")
        if model_file and not (path.parent / model_file).is_file():
            findings.append(("ERROR", f"{mid}: declared model file not found relative to manifest: {model_file}"))
        inputs = item.get("inputs", [])
        if not inputs or not isinstance(inputs, list):
            findings.append(("ERROR", f"{mid}: no traceable model inputs"))
        else:
            for datum in inputs:
                if not datum.get("variable") or not datum.get("unit") or not datum.get("origin"):
                    findings.append(("ERROR", f"{mid}: input lacks variable/unit/origin"))
                if datum.get("origin") not in ("source", "assumption", "calibration"):
                    findings.append(("ERROR", f"{mid}: origin must be source/assumption/calibration"))
                if datum.get("origin") == "source" and not datum.get("evidence_id"):
                    findings.append(("ERROR", f"{mid}: sourced input has no evidence_id"))
        calibration = set(item.get("calibration_targets", []))
        validation = set(item.get("validation_targets", []))
        if calibration & validation:
            findings.append(("ERROR", f"{mid}: circular validation: {', '.join(sorted(calibration & validation))}"))
        if item.get("claims_independent_validation"):
            if not validation:
                findings.append(("ERROR", f"{mid}: independent validation claimed with no targets"))
            if set(item.get("input_target_ids", [])) & validation:
                findings.append(("ERROR", f"{mid}: validation target was also an input; not independent"))
            if not item.get("validation_period"):
                findings.append(("ERROR", f"{mid}: no validation period"))
        if not item.get("units_and_scope"):
            findings.append(("WARN", f"{mid}: units/denominator, segment and time scope not described"))
        if not item.get("reconciliation_notes"):
            findings.append(("WARN", f"{mid}: missing difference/reconciliation analysis"))
    if not findings:
        findings.append(("PASS", "No declared calibration/validation circularity detected; analyst must inspect the model and independent evidence"))
    return findings


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("manifest", type=Path)
    args = p.parse_args()
    try:
        results = check_manifest(args.manifest)
    except (OSError, ValueError, TypeError, AttributeError) as exc:
        p.exit(2, f"Cannot check model manifest: {exc}\n")
    for level, message in results:
        print(f"[{level}] {message}")
    return 1 if any(level == "ERROR" for level, _ in results) else 0


if __name__ == "__main__":
    raise SystemExit(main())
