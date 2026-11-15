#!/usr/bin/env python3
"""Check internal finalization records; NOT an independent factual audit or release approval."""
import argparse, csv, json, re
from pathlib import Path

REQUIRED=("source_integrity","research_depth","judgment_and_falsification",
          "editorial_integrity","final_integrated_review")
def rows(path,fields):
    with Path(path).open(encoding="utf-8-sig",newline="") as f:
        rd=csv.DictReader(f)
        missing=set(fields)-set(rd.fieldnames or [])
        if missing:raise ValueError(f"{path}: missing fields {sorted(missing)}")
        return [{k:(v or "").strip() for k,v in r.items() if k} for r in rd]
def evaluate(report,acceptance,gaps,defects,coverage,sources):
    report_text=Path(report).read_text(encoding="utf-8")
    acc=rows(acceptance,["criterion","status","evidence_ref","review_note"])
    gap=rows(gaps,["gap_id","module","materiality","status","impact_on_conclusion","mitigation_ref","disclosure_ref"])
    defect=rows(defects,["issue_id","priority","status","fix_ref","verification_ref"])
    cov=rows(coverage,["priority","status","evidence_ids"])
    src=rows(sources,["evidence_id","status","verification_ref"])
    errors=[];warnings=[]
    by={}
    for a in acc:
        if a["criterion"] in by:errors.append("duplicate criterion: "+a["criterion"])
        by[a["criterion"]]=a
    for key in REQUIRED:
        a=by.get(key)
        if not a:errors.append("missing criterion: "+key);continue
        if a["status"].upper()!="PASS":errors.append("failed criterion: "+key)
        if not a["evidence_ref"] or not a["review_note"]:errors.append("missing review evidence: "+key)
    seen=set()
    for g in gap:
        ident=g["gap_id"]; mat=g["materiality"].upper();state=g["status"].upper()
        if not ident or ident in seen:errors.append("duplicate/missing gap ID: "+ident)
        seen.add(ident)
        if mat not in ("CRITICAL","NONCRITICAL"):errors.append("invalid materiality: "+ident)
        if state not in ("OPEN","RESOLVED","DISCLOSED"):errors.append("invalid gap state: "+ident)
        if state=="OPEN" or (mat=="CRITICAL" and state!="RESOLVED"):
            errors.append("unresolved critical or open gap: "+ident)
        if state=="DISCLOSED":
            if mat!="NONCRITICAL" or not all(g[k] for k in ("impact_on_conclusion","mitigation_ref","disclosure_ref")):
                errors.append("unbounded or unsupported disclosure: "+ident)
            else:warnings.append("disclosed noncritical gap: "+ident)
        if state=="RESOLVED" and not g["mitigation_ref"]:errors.append("resolved gap missing fix: "+ident)
    for d in defect:
        if d["priority"].upper() in ("P0","P1"):
            if d["status"].upper()!="FIXED" or not d["fix_ref"] or not d["verification_ref"]:
                errors.append("unfixed material defect: "+d["issue_id"])
    if not cov:errors.append("empty research coverage")
    for i,c in enumerate(cov,1):
        if c["priority"].lower()=="high":
            if c["status"].upper() not in ("PASS","COMPLETE") or not c["evidence_ids"]:
                errors.append(f"HIGH coverage incomplete: row {i}")
    index={}
    for s in src:
        if s["evidence_id"] in index:errors.append("duplicate source review: "+s["evidence_id"])
        index[s["evidence_id"]]=s
    cited=sorted(set(re.findall(r"\bE\d{3}\b",report_text)))
    if not cited:errors.append("report has no E### references for source audit")
    for ref in cited:
        s=index.get(ref)
        if not s or s["status"].upper()!="VERIFIED" or not s["verification_ref"]:
            errors.append("source citation not independently located: "+ref)
    if re.search(r"原始资料X|SOURCE_PLACEHOLDER|20\d\d[-/]xx|未填写来源",report_text,re.I):
        errors.append("report contains placeholder")
    return {"status":"REVISION_REQUIRED" if errors else "FINAL_RESEARCH_READY",
            "accepted_criteria":sum(by.get(k,{}).get("status","").upper()=="PASS" for k in REQUIRED),
            "used_citations":len(cited),"errors":errors,"warnings":warnings,
            "notice":"Documentary checks only: no source authentication or independent institutional release."}
def main():
    p=argparse.ArgumentParser(description=__doc__)
    for k in ("report","acceptance","gaps","defects","coverage","sources"):
        p.add_argument("--"+k,required=True,type=Path)
    p.add_argument("--out",type=Path);a=p.parse_args()
    try:r=evaluate(a.report,a.acceptance,a.gaps,a.defects,a.coverage,a.sources)
    except (OSError,ValueError,csv.Error,UnicodeError) as e:p.exit(2,f"bad input: {e}\n")
    if a.out:
        a.out.parent.mkdir(parents=True,exist_ok=True)
        a.out.write_text(json.dumps(r,ensure_ascii=False,indent=2),encoding="utf-8")
    print(json.dumps(r,ensure_ascii=False,indent=2))
    return 1 if r["status"]=="REVISION_REQUIRED" else 0
if __name__=="__main__":raise SystemExit(main())
