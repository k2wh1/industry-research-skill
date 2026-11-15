#!/usr/bin/env python3
"""Research-action release gate v2.8. Documentary consistency only, never fact authentication."""
from __future__ import annotations
import argparse,csv,json,re
from pathlib import Path
from collections import Counter

STATES={"OPEN","DONE","EXTERNAL_BLOCKED","STOP_LIMIT"}
def load(path, fields):
    with open(path,encoding="utf-8-sig",newline="") as f:
        reader=csv.DictReader(f)
        if not reader.fieldnames or not set(fields).issubset(reader.fieldnames):
            raise ValueError(f"{path}: missing columns {set(fields)-set(reader.fieldnames or [])}")
        return [{k:(v or "").strip() for k,v in row.items() if k} for row in reader]

def check(report, evidence, source_review, actions, coverage, defects, scorecard, gates):
    txt=Path(report).read_text(encoding="utf-8")
    ev=load(evidence,["evidence_id","source_url"])
    sr=load(source_review,["evidence_id","status","verification_ref","finding"])
    acts=load(actions,["action_id","severity","finding","next_action","status","output_ref","verification_ref","blocker_reason"])
    cov=load(coverage,["sub_industry","priority","analytical_depth_0_3","evidence_ids","status"])
    defects=load(defects,["issue_id","priority","status","fix_ref","verification_ref","blocker_reason"])
    scores=load(scorecard,["round_id","criterion_id","next_action","evidence_refs","score_0_5"])
    gate_rows=load(gates,["round_id","gate","status","review_evidence"])
    errors=[]; warnings=[]
    used=set(re.findall(r"\bE\d{3}\b",txt))
    ev_ids={e["evidence_id"] for e in ev}
    sr_lookup={s["evidence_id"]:s for s in sr}
    if len(ev_ids)!=len(ev):errors.append("duplicate evidence_id")
    if len(sr_lookup)!=len(sr):errors.append("duplicate source review id")
    for e in sorted(used):
        if e not in ev_ids:errors.append(f"{e}: cited without evidence ledger entry")
        item=sr_lookup.get(e)
        if not item:errors.append(f"{e}: no source verification record");continue
        if item["status"] not in {"VERIFIED","UNVERIFIED","CONFLICT"}:
            errors.append(f"{e}: invalid source status")
        if item["status"]=="VERIFIED" and not item["verification_ref"]:
            errors.append(f"{e}: VERIFIED without exact document/page evidence")
        if item["status"]!="VERIFIED":warnings.append(f"{e}: {item['status']} not independently verified")
    for e in ev:
        if e["evidence_id"] in used and (not e["source_url"].startswith(("https://","http://"))):
            errors.append(f"{e['evidence_id']}: missing URL")
    if re.search(r"原始资料X|(?:202[0-9])[-/]xx|(?:待核验日期)|(?:SOURCE_PLACEHOLDER)",txt,re.I):
        errors.append("publication-blocking placeholder in report")
    for item in acts:
        key=item["action_id"];state=item["status"]
        if state not in STATES:errors.append(f"{key}: invalid action state")
        if not (item["finding"] and item["next_action"]):errors.append(f"{key}: finding/action required")
        if state=="OPEN":
            errors.append(f"{key}: actionable research still OPEN")
        if state=="DONE" and not (item["output_ref"] and item["verification_ref"]):
            errors.append(f"{key}: DONE without output and re-review evidence")
        if state in {"EXTERNAL_BLOCKED","STOP_LIMIT"}:
            if not (item["blocker_reason"] and item["verification_ref"]):
                errors.append(f"{key}: blocker requires concrete cause and impact review")
            warnings.append(f"{key}: {state} requires staged delivery")
    action_severities={a["severity"].upper() for a in acts}
    if not acts:errors.append("reflection yielded no action or NO_FINDING review")
    for r in defects:
        if r["priority"].upper() in {"P0","P1"}:
            st=r["status"].upper()
            if st=="OPEN":errors.append(f"{r['issue_id']}: high-priority defect OPEN")
            if st=="FIXED" and not (r["fix_ref"] and r["verification_ref"]):
                errors.append(f"{r['issue_id']}: FIXED lacks fix and verification")
            if st=="EXTERNAL_BLOCKED":
                warnings.append(f"{r['issue_id']}: external data blocker")
                if not (r["blocker_reason"] and r["verification_ref"]):
                    errors.append(f"{r['issue_id']}: blocker lacks impact evidence")
    for r in cov:
        if r["priority"].upper()!="HIGH":continue
        try:depth=int(r["analytical_depth_0_3"])
        except ValueError:depth=-1
        if depth<3 and r["status"].lower() in {"pass","complete"}:
            warnings.append(f"{r['sub_industry']}: research depth {depth}<3 yet marked pass")
        if depth<2 or not r["evidence_ids"]:
            errors.append(f"{r['sub_industry']}: HIGH depth/evidence incomplete")
    final_round=sorted(set(s["round_id"] for s in scores))[-1] if scores else ""
    latest=[s for s in scores if s["round_id"]==final_round]
    if len(latest)!=8:errors.append("last quality round must cover eight dimensions")
    nonempty=[s["next_action"] for s in latest if s["next_action"]]
    if nonempty and Counter(nonempty).most_common(1)[0][1]>=5:
        errors.append("five or more quality dimensions have identical next_action (non-specific reflection)")
    if any(not s["evidence_refs"] for s in latest):
        errors.append("scorecard missing evidence localization")
    final_gates=[g for g in gate_rows if g["round_id"]==final_round]
    if len(final_gates)!=6:errors.append("last round must have six hard gates")
    if any(g["status"]!="PASS" for g in final_gates):
        warnings.append("hard quality gates not all PASS: stage only")
    if any(s["status"]!="VERIFIED" for s in (sr_lookup.get(e) or {"status":"UNVERIFIED"} for e in used)):
        warnings.append("source verification coverage incomplete")
    status="BLOCKED_ACTIONABLE" if errors else ("STAGED_REVIEW" if warnings else "READY_FOR_INDEPENDENT_REVIEW")
    return {"status":status,"evidence_used":len(used),"source_verified":sum(sr_lookup.get(e,{}).get("status")=="VERIFIED" for e in used),
            "actions":len(acts),"errors":errors,"warnings":warnings,
            "notice":"Only checks supplied research logs. It does NOT authenticate facts or authorize RELEASED."}

def main():
    p=argparse.ArgumentParser(description=__doc__)
    for n in ("report","evidence","source-review","actions","coverage","defects","scorecard","gates"):
        p.add_argument("--"+n,required=True,type=Path)
    p.add_argument("--out",type=Path)
    a=p.parse_args()
    args=[getattr(a,n.replace("-","_")) for n in ("report","evidence","source-review","actions","coverage","defects","scorecard","gates")]
    try:r=check(*args)
    except (OSError,ValueError,csv.Error,UnicodeError) as exc:p.exit(2,f"Invalid input: {exc}\n")
    if a.out:
        a.out.parent.mkdir(parents=True,exist_ok=True)
        a.out.write_text(json.dumps(r,ensure_ascii=False,indent=2),encoding="utf-8")
    print(json.dumps(r,ensure_ascii=False,indent=2))
    return 1 if r["status"]=="BLOCKED_ACTIONABLE" else 0
if __name__=="__main__":raise SystemExit(main())
