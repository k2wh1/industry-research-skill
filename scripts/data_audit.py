#!/usr/bin/env python3
"""Offline numeric/units/period consistency audit for a research data table.

Does not verify whether a number matches its cited source. Numbers must be
transcribed from sources and checked manually. Exit 1 for detected ERRORs.
"""
from __future__ import annotations

import argparse
import csv
import re
from collections import defaultdict
from datetime import date
from decimal import Decimal, InvalidOperation
from pathlib import Path

METRIC_COLUMNS = ("metric_id", "entity", "metric", "period", "period_type", "currency",
                  "unit", "basis", "value", "evidence_id", "observation_kind", "publish_date")
RULE_COLUMNS = ("check_id", "op", "target_id", "input_ids", "tolerance_abs", "tolerance_rel", "notes")
MULTIPLIERS = {
    "ones": Decimal(1), "个": Decimal(1), "元": Decimal(1), "千": Decimal("1e3"),
    "万": Decimal("1e4"), "万元": Decimal("1e4"), "million": Decimal("1e6"),
    "百万": Decimal("1e6"), "百万美元": Decimal("1e6"), "亿": Decimal("1e8"),
    "亿元": Decimal("1e8"), "亿美元": Decimal("1e8"), "亿日元": Decimal("1e8"),
    "billion": Decimal("1e9"), "十亿": Decimal("1e9"), "万亿": Decimal("1e12"),
    "万亿元": Decimal("1e12"), "万亿美元": Decimal("1e12"),
    "万亿日元": Decimal("1e12"), "trillion": Decimal("1e12"),
    "pct": Decimal(1), "%": Decimal(1), "bp": Decimal(1),
}
PERCENT_UNITS = {"pct", "%"}
KINDS = {"actual", "forecast", "guidance", "assumption", "estimate"}
PERIOD_TYPES = {"FY", "CY", "FQ", "CQ", "TTM", "POINT", "OTHER"}
OPS = {"sum", "difference", "ratio_pct", "yoy_pct"}


def read_csv(path: Path, required: tuple[str, ...]):
    with path.open(newline="", encoding="utf-8-sig") as fh:
        reader = csv.DictReader(fh)
        missing = sorted(set(required) - set(reader.fieldnames or []))
        if missing:
            raise ValueError(f"{path.name}: missing columns {', '.join(missing)}")
        return list(reader)


def dec(value: str) -> Decimal:
    n = Decimal(str(value).strip().replace(",", ""))
    if not n.is_finite():
        raise InvalidOperation("non-finite value")
    return n


def audit(metrics_path: Path, rules_path: Path | None = None, as_of: str | None = None):
    findings: list[tuple[str, str]] = []
    rows = read_csv(metrics_path, METRIC_COLUMNS)
    lookup = {}
    comparable = defaultdict(list)
    cutoff = date.fromisoformat(as_of) if as_of else None
    for line, row in enumerate(rows, start=2):
        mid = row["metric_id"].strip()
        if not mid or mid in lookup:
            findings.append(("ERROR", f"metrics line {line}: blank/duplicate metric_id {mid!r}"))
            continue
        if any(not row.get(col, "").strip() for col in METRIC_COLUMNS if col not in ("evidence_id",)):
            findings.append(("ERROR", f"{mid}: required metadata blank; record entity/period/unit/basis/source"))
            continue
        unit = row["unit"].strip()
        if unit not in MULTIPLIERS:
            findings.append(("ERROR", f"{mid}: unrecognized unit {unit!r}; add explicit conversion"))
            continue
        if row["observation_kind"].strip() not in KINDS:
            findings.append(("ERROR", f"{mid}: unknown observation_kind"))
            continue
        if row["period_type"].strip() not in PERIOD_TYPES:
            findings.append(("ERROR", f"{mid}: unknown period_type"))
            continue
        try:
            value = dec(row["value"])
            published = date.fromisoformat(row["publish_date"].strip())
        except (InvalidOperation, ValueError):
            findings.append(("ERROR", f"{mid}: value/date invalid"))
            continue
        if cutoff and published > cutoff:
            findings.append(("ERROR", f"{mid}: source publish_date {published} after as-of {cutoff}"))
        if not re.fullmatch(r"E\d{3,}", row["evidence_id"].strip()):
            findings.append(("WARN", f"{mid}: missing/invalid evidence_id; cited fact not linked"))
        kind = "percent" if unit in PERCENT_UNITS else "bp" if unit == "bp" else "quantity"
        normalized = value * MULTIPLIERS[unit]
        lookup[mid] = {**row, "value_d": value, "value_norm": normalized, "kind": kind}
        key = (row["entity"], row["metric"], row["period"], row["period_type"],
               row["currency"], row["basis"], row["observation_kind"], kind)
        comparable[key].append((mid, normalized))

    for same, values in comparable.items():
        if len(values) < 2:
            continue
        numbers = [v for _, v in values]
        if max(numbers) - min(numbers) > max(Decimal("0.000001"), abs(max(numbers)) * Decimal("0.000001")):
            findings.append(("ERROR", f"same-period/basis conflicting metrics: {', '.join(i for i, _ in values)}; reconcile source versions"))

    if rules_path:
        rules = read_csv(rules_path, RULE_COLUMNS)
        rule_ids = set()
        for line, rule in enumerate(rules, 2):
            rid = rule["check_id"].strip()
            if not rid or rid in rule_ids:
                findings.append(("ERROR", f"rules line {line}: missing/duplicate check_id"))
                continue
            rule_ids.add(rid)
            op = rule["op"].strip()
            if op not in OPS:
                findings.append(("ERROR", f"{rid}: unknown operation {op}"))
                continue
            ids = [x.strip() for x in rule["input_ids"].split(";") if x.strip()]
            target = rule["target_id"].strip()
            if target not in lookup or any(i not in lookup for i in ids):
                findings.append(("ERROR", f"{rid}: target/input metric ID not found"))
                continue
            expected_inputs = 1 if op == "sum" else 2
            if (op == "sum" and not ids) or (op != "sum" and len(ids) != expected_inputs):
                findings.append(("ERROR", f"{rid}: wrong number of input IDs"))
                continue
            allrows = [lookup[target]] + [lookup[i] for i in ids]
            currency_rows = allrows if op in ("sum", "difference") else allrows[1:]
            if len({r["currency"] for r in currency_rows}) != 1:
                findings.append(("ERROR", f"{rid}: cross-currency arithmetic without FX conversion"))
                continue
            if any(r["kind"] != "quantity" for r in allrows[1:]):
                findings.append(("ERROR", f"{rid}: operands must be numeric quantities, not percent/bp"))
                continue
            if op in ("sum", "difference"):
                if lookup[target]["kind"] != "quantity":
                    findings.append(("ERROR", f"{rid}: target must be a quantity"))
                    continue
                if len({(r["period"], r["period_type"]) for r in allrows}) != 1:
                    findings.append(("ERROR", f"{rid}: incompatible comparison periods"))
                    continue
            else:
                if lookup[target]["kind"] != "percent":
                    findings.append(("ERROR", f"{rid}: ratio/growth target must be percentage points (unit pct)"))
                    continue
                if op == "ratio_pct" and len({(r["period"], r["period_type"]) for r in allrows[1:]}) != 1:
                    findings.append(("ERROR", f"{rid}: ratio inputs must be in same period"))
                    continue
                if op == "yoy_pct" and (allrows[1]["period"] == allrows[2]["period"] or allrows[1]["period_type"] != allrows[2]["period_type"]):
                    findings.append(("ERROR", f"{rid}: YoY inputs need different periods"))
                    continue
            values = [lookup[i]["value_norm"] for i in ids]
            try:
                if op == "sum":
                    computed = sum(values, Decimal(0))
                elif op == "difference":
                    computed = values[0] - values[1]
                else:
                    computed = (values[0] / values[1] - (1 if op == "yoy_pct" else 0)) * Decimal(100)
                atol = dec(rule["tolerance_abs"] or "0")
                rtol = dec(rule["tolerance_rel"] or "0")
                if atol < 0 or rtol < 0:
                    raise InvalidOperation("negative tolerance")
            except (InvalidOperation, ZeroDivisionError):
                findings.append(("ERROR", f"{rid}: invalid tolerance or denominator"))
                continue
            recorded = lookup[target]["value_norm"]
            diff = abs(computed - recorded)
            tol = max(atol * MULTIPLIERS[lookup[target]["unit"]], abs(recorded) * rtol)
            if diff > tol:
                factor = MULTIPLIERS[lookup[target]["unit"]]
                findings.append(("ERROR", f"{rid}: reported {recorded/factor:g}, calculated {computed/factor:g} {lookup[target]['unit']} (difference {diff/factor:g})"))
    if not rows:
        findings.append(("WARN", "metrics table empty; no numeric audit performed"))
    if not rules_path:
        findings.append(("WARN", "no reconciliation rules: cannot check arithmetic identities"))
    if not findings:
        findings.append(("PASS", "recorded values are internally consistent under supplied rules; external facts NOT verified"))
    return findings


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("metrics", type=Path)
    p.add_argument("--rules", type=Path)
    p.add_argument("--as-of")
    args = p.parse_args()
    try:
        findings = audit(args.metrics, args.rules, args.as_of)
    except (OSError, csv.Error, ValueError) as exc:
        p.exit(2, f"Could not audit input: {exc}\n")
    for kind, msg in findings:
        print(f"[{kind}] {msg}")
    return 1 if any(kind == "ERROR" for kind, _ in findings) else 0


if __name__ == "__main__":
    raise SystemExit(main())
