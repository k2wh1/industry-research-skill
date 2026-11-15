#!/usr/bin/env python3
"""Fail premature research termination when high-priority coverage remains actionable.

Documentary consistency check only: it cannot validate external data quality,
assert actual effort, or authorize RELEASED status.
"""
from __future__ import annotations
import argparse
import csv
import json
from pathlib import Path

COVERAGE = {"sub_industry","priority","analytical_depth_0_3","evidence_ids","status"}
QUEUE = {"sub_industry","priority","research_question","next_action","status","attempt_ref","blocker_reason"}
DEFECTS = {"module","priority","status","blocker_reason","verification_ref"}
DONE = {"PASS","COMPLETE"}
WAIT = {"PARTIAL","MISSING","OPEN"}
BLOCKED = {"EXTERNAL_BLOCKED","STOP_LIMIT"}
QUEUE_STATES = {"DONE","IN_PROGRESS","EXTERNAL_BLOCKED","STOP_LIMIT"}

def rows(path: Path, required: set[str]) -> list[dict[str,str]]:
    with path.open(encoding="utf-8-sig",newline="") as fh:
        reader=csv.DictReader(fh)
        if not reader.fieldnames or not required.issubset(reader.fieldnames):
            raise ValueError(f"{path}: missing {sorted(required-set(reader.fieldnames or []))}")
        return [{k:(v or "").strip() for k,v in row.items() if k} for row in reader]

def review(coverage:Path,queue:Path,defects:Path,stop_reason:str="NONE")->dict:
    cov=rows(coverage,COVERAGE); task=rows(queue,QUEUE); defects_rows=rows(defects,DEFECTS)
    errors=[];actionable=[];externally_blocked=[];stopped=[];finished=[]
    if not cov:errors.append("coverage register empty")
    q_by={};seen=set()
    for item in task:
        name=item["sub_industry"]
        if name in q_by:errors.append(f"{name}: duplicate queue row")
        q_by[name]=item
        if item["status"].upper() not in QUEUE_STATES:
            errors.append(f"{name}: invalid queue status")
    if stop_reason not in {"NONE","EXTERNAL_DATA","RESOURCE_LIMIT"}:
        errors.append("invalid stop reason")
    for item in cov:
        name=item["sub_industry"]; priority=item["priority"].upper();status=item["status"].upper()
        if name in seen:errors.append(f"{name}: duplicate coverage row")
        seen.add(name)
        try:depth=int(item["analytical_depth_0_3"])
        except ValueError:depth=-1
        if depth not in (0,1,2,3): errors.append(f"{name}: invalid depth")
        if priority!="HIGH":continue
        complete=(status in DONE and depth>=2 and bool(item["evidence_ids"]))
        if complete:
            finished.append(name);continue
        queue_row=q_by.get(name)
        if not queue_row:
            actionable.append(name);errors.append(f"{name}: HIGH unfinished and no research queue row");continue
        if not queue_row["research_question"] or not queue_row["next_action"]:
            errors.append(f"{name}: explicit research question/action required")
        qstatus=queue_row["status"].upper()
        if qstatus=="DONE":
            errors.append(f"{name}: queue DONE conflicts with unfinished coverage")
            actionable.append(name)
        elif qstatus=="EXTERNAL_BLOCKED":
            matching=[d for d in defects_rows if d["module"]==name and d["priority"].upper() in ("P0","P1")
                      and d["status"].upper()=="EXTERNAL_BLOCKED" and d["blocker_reason"] and d["verification_ref"]]
            if not matching or not queue_row["attempt_ref"] or not queue_row["blocker_reason"]:
                errors.append(f"{name}: external block must link exact module, defect, attempts and impact")
                actionable.append(name)
            else:externally_blocked.append(name)
        elif qstatus=="STOP_LIMIT":
            if stop_reason!="RESOURCE_LIMIT" or not queue_row["attempt_ref"] or not queue_row["blocker_reason"]:
                errors.append(f"{name}: STOP_LIMIT needs actual RESOURCE_LIMIT and specific attempt evidence")
                actionable.append(name)
            else:stopped.append(name)
        else:
            actionable.append(name)
            # Work in progress cannot be silently closed as reviewed.
    if actionable and stop_reason!="RESOURCE_LIMIT":
        errors.append(f"{len(actionable)} HIGH priorities remain actionable: research must continue")
    if actionable and stop_reason=="RESOURCE_LIMIT":
        errors.append("RESOURCE_LIMIT requires each unresolved HIGH to be explicitly queued STOP_LIMIT")
    if stop_reason=="EXTERNAL_DATA" and (actionable or stopped):
        errors.append("EXTERNAL_DATA cannot terminate unrelated actionable research")
    state="BLOCK_PREMATURE_STOP" if errors else (
        "STAGED_RESOURCE_LIMIT" if stopped else (
        "STAGED_EXTERNAL_DATA" if externally_blocked else "COVERAGE_HANDOFF_CANDIDATE"))
    return {"status":state,"high_complete":finished,"high_external_blocked":externally_blocked,
            "high_stop_limit":stopped,"high_actionable":actionable,"errors":errors,
            "notice":"Structure-only validation: humans must review factual support; never automatic RELEASED."}

def main()->int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--coverage",required=True,type=Path)
    p.add_argument("--queue",required=True,type=Path)
    p.add_argument("--defects",required=True,type=Path)
    p.add_argument("--stop-reason",choices=["NONE","EXTERNAL_DATA","RESOURCE_LIMIT"],default="NONE")
    p.add_argument("--out",type=Path)
    a=p.parse_args()
    try:result=review(a.coverage,a.queue,a.defects,a.stop_reason)
    except (OSError,UnicodeError,csv.Error,ValueError) as e:p.exit(2,f"invalid input: {e}\n")
    if a.out:
        a.out.parent.mkdir(parents=True,exist_ok=True)
        a.out.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding="utf-8")
    print(json.dumps(result,ensure_ascii=False,indent=2))
    return 1 if result["errors"] else 0

if __name__=="__main__":raise SystemExit(main())
