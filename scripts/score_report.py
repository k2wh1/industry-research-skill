#!/usr/bin/env python3
"""Validate human research ratings and quality gates; never auto-verifies facts."""
from __future__ import annotations

import argparse
import csv
import json
import math
from collections import defaultdict
from pathlib import Path

WEIGHTS = {
    "research_question": 10, "business_logic": 15, "evidence": 20,
    "modeling": 15, "competition": 10, "investment": 10,
    "falsification": 10, "structure": 10,
}
GATES = ("source_integrity", "data_audit", "model_integrity",
         "industry_coverage", "counterevidence", "visual_editorial")


def load_csv(path: Path, fields: set[str]) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        if not reader.fieldnames or not fields.issubset(reader.fieldnames):
            raise ValueError(f"{path}: required columns missing: {sorted(fields - set(reader.fieldnames or []))}")
        return list(reader)


def evaluate(scores: Path, gates: Path) -> dict:
    rows = load_csv(scores, {"round_id", "criterion_id", "score_0_5", "evidence_refs", "weakness", "next_action"})
    gate_rows = load_csv(gates, {"round_id", "gate", "status", "review_evidence"})
    rounds: dict[str, dict] = {}
    errors: list[str] = []
    for row in rows:
        rid, criterion = row["round_id"].strip(), row["criterion_id"].strip()
        if not rid or not criterion:
            errors.append("score row missing round_id/criterion_id")
            continue
        bucket = rounds.setdefault(rid, {"ratings": {}, "gates": {}})
        if criterion not in WEIGHTS:
            errors.append(f"{rid}: unknown criterion {criterion}")
            continue
        if criterion in bucket["ratings"]:
            errors.append(f"{rid}: duplicate criterion {criterion}")
            continue
        raw = row["score_0_5"].strip()
        try:
            score = float(raw)
        except ValueError:
            errors.append(f"{rid}/{criterion}: score missing or invalid")
            continue
        if not math.isfinite(score) or not 0 <= score <= 5 or abs(score * 10 - round(score * 10)) > 1e-8:
            errors.append(f"{rid}/{criterion}: score must be 0..5 with at most one decimal")
            continue
        if not row["evidence_refs"].strip() or not row["next_action"].strip():
            errors.append(f"{rid}/{criterion}: evidence_refs and next_action required")
        bucket["ratings"][criterion] = {
            "score": score, "weighted": round(score / 5 * WEIGHTS[criterion], 2),
            "evidence_refs": row["evidence_refs"].strip(),
            "weakness": row["weakness"].strip(),
            "next_action": row["next_action"].strip(),
        }
    for row in gate_rows:
        rid, gate, status = row["round_id"].strip(), row["gate"].strip(), row["status"].strip().upper()
        if not rid or not gate:
            errors.append("gate row missing round_id/gate")
            continue
        bucket = rounds.setdefault(rid, {"ratings": {}, "gates": {}})
        if gate not in GATES:
            errors.append(f"{rid}: unknown gate {gate}")
            continue
        if gate in bucket["gates"]:
            errors.append(f"{rid}: duplicate gate {gate}")
            continue
        if status not in {"PASS", "FAIL", "UNKNOWN"}:
            errors.append(f"{rid}/{gate}: status must be PASS/FAIL/UNKNOWN")
            continue
        if not row["review_evidence"].strip():
            errors.append(f"{rid}/{gate}: review_evidence required even for UNKNOWN")
        bucket["gates"][gate] = {"status": status, "evidence": row["review_evidence"].strip()}
    if not rounds:
        errors.append("no scoring rounds supplied")
    result_rounds = []
    previous = None
    for rid in sorted(rounds):
        data = rounds[rid]
        for criterion in WEIGHTS:
            if criterion not in data["ratings"]:
                errors.append(f"{rid}: missing score {criterion}")
        for gate in GATES:
            if gate not in data["gates"]:
                errors.append(f"{rid}: missing gate {gate}")
        if set(data["ratings"]) != set(WEIGHTS) or set(data["gates"]) != set(GATES):
            continue
        total = round(sum(x["weighted"] for x in data["ratings"].values()), 2)
        statuses = [x["status"] for x in data["gates"].values()]
        if "FAIL" in statuses:
            status = "BLOCKED"
        elif "UNKNOWN" in statuses:
            status = "STAGED"
        elif total >= 90 and all(x["score"] >= 4 for x in data["ratings"].values()):
            status = "HUMAN_RELEASE_REVIEW_REQUIRED"
        else:
            status = "REVISION_REQUIRED"
        grade = "A" if total >= 90 else "B" if total >= 80 else "C" if total >= 70 else "D" if total >= 60 else "E"
        queue = sorted(({
            "criterion_id": key, "potential_points": round(WEIGHTS[key] - value["weighted"], 2),
            "current_score": value["score"], "next_action": value["next_action"],
            "weakness": value["weakness"],
        } for key, value in data["ratings"].items()),
            key=lambda x: (-x["potential_points"], x["criterion_id"]))
        info = {
            "round_id": rid, "total": total, "grade": grade, "status": status,
            "delta_from_previous": None if previous is None else round(total - previous, 2),
            "criteria": data["ratings"], "gates": data["gates"],
            "revision_queue": queue,
        }
        result_rounds.append(info)
        previous = total
    return {"valid": not errors, "errors": errors, "rounds": result_rounds,
            "warning": "Scores and gate statuses are supplied by reviewers; calculations do not verify source authenticity."}


def render_review(result: dict) -> str:
    lines = ["# 研究质量迭代报告", "",
             "> 人工登记评分的算术汇总，不等于事实审计或独立终审。", ""]
    if result["errors"]:
        lines += ["## 输入问题", *("- " + e for e in result["errors"]), ""]
    for r in result["rounds"]:
        lines += [f"## {r['round_id']}｜{r['total']}/100 ({r['grade']})",
                  f"状态：{r['status']}", ""]
        if r["delta_from_previous"] is not None:
            lines += [f"较上一轮：{r['delta_from_previous']:+.2f} 分", ""]
        lines += ["| 维度 | 原始得分/5 | 加权得分 | 证据定位 |",
                  "|---|---:|---:|---|"]
        for key in WEIGHTS:
            v = r["criteria"][key]
            lines.append(f"| {key} | {v['score']:.1f} | {v['weighted']:.2f} | {v['evidence_refs'].replace('|', '/')} |")
        lines += ["", "### 修订优先级（按加权缺口）"]
        for item in r["revision_queue"][:3]:
            lines.append(f"- {item['criterion_id']}（潜在缺口 {item['potential_points']:.2f} 分）：{item['next_action']}")
        lines += ["", "### 硬门槛"]
        for gate, g in r["gates"].items():
            lines.append(f"- {gate}: {g['status']}；{g['evidence']}")
        lines.append("")
    return "\n".join(lines)


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--scores", required=True, type=Path)
    p.add_argument("--gates", required=True, type=Path)
    p.add_argument("--out-dir", type=Path)
    args = p.parse_args()
    try:
        result = evaluate(args.scores, args.gates)
    except (OSError, csv.Error, UnicodeError, ValueError) as exc:
        p.exit(2, f"Cannot evaluate quality inputs: {exc}\n")
    if args.out_dir:
        args.out_dir.mkdir(parents=True, exist_ok=True)
        (args.out_dir / "quality_history.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
        (args.out_dir / "quality_review.md").write_text(render_review(result), encoding="utf-8")
        with (args.out_dir / "revision_queue.csv").open("w", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(f, fieldnames=["round_id", "criterion_id", "potential_points", "current_score", "weakness", "next_action"])
            writer.writeheader()
            for r in result["rounds"]:
                for x in r["revision_queue"]:
                    writer.writerow({"round_id": r["round_id"], **x})
    for e in result["errors"]:
        print("[ERROR]", e)
    for r in result["rounds"]:
        print(f"{r['round_id']}: {r['total']:.2f}/100, grade {r['grade']}, status {r['status']}, delta {r['delta_from_previous']}")
    return 1 if result["errors"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
