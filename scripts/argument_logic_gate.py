#!/usr/bin/env python3
"""Documentary argument architecture gate: checks declared reasoning structure, not factual truth.

A passing result is not evidence of causality, correct math, or external source validation.
"""
from __future__ import annotations
import argparse
import csv
import json
from collections import defaultdict
from pathlib import Path

SCOPE = {"module","priority","in_scope","bridge_exemption_reason"}
CLAIMS = {"claim_id","module","priority","observation_refs","mechanism",
          "financial_bridge","counter_explanation","falsification_condition",
          "conclusion_scope","status"}
BRIDGES = {"bridge_id","source_module","target_module","driver",
           "transmission_path","economic_effect","competing_response",
           "evidence_ref","falsifier","status"}
MODELS = {"model_id","related_claim","boundary_and_horizon","fixed_cost_terms",
          "variable_cost_terms","units_check_ref","formula_ref",
          "counterexample_test_ref","status"}
ACCEPTED = {"CHECKED","REVISED"}
MISSING = {"", "N/A", "NA", "NONE", "TODO", "TBD", "待补", "待定", "无"}
def read(path, columns):
    with Path(path).open(encoding="utf-8-sig",newline="") as fh:
        reader=csv.DictReader(fh)
        found=set(reader.fieldnames or [])
        if not columns.issubset(found):
            raise ValueError(f"{path}: missing fields {sorted(columns - found)}")
        return [{k:(v or "").strip() for k,v in row.items() if k} for row in reader]

def substantive(value):
    return (value or "").strip().upper() not in MISSING

def evaluate(scope_path, claim_path, bridge_path, model_path, report_type="industry_full"):
    if report_type not in ("industry_full","thematic","company"):
        raise ValueError(f"unknown report_type: {report_type}")
    scope=read(scope_path,SCOPE)
    claims=read(claim_path,CLAIMS)
    bridges=read(bridge_path,BRIDGES)
    models=read(model_path,MODELS)
    errors=[];warnings=[]
    modules={}
    for row in scope:
        m=row["module"]
        if not m or m in modules:errors.append(f"scope duplicate/blank module: {m}");continue
        if row["in_scope"].upper() not in ("YES","NO"):
            errors.append(f"{m}: in_scope must be YES or NO")
        modules[m]=row
    wanted={m for m,r in modules.items() if r["in_scope"].upper()=="YES" and r["priority"].upper()=="HIGH"}
    seen=set(); per_module=defaultdict(list)
    for row in claims:
        cid=row["claim_id"];module=row["module"]
        if not cid or cid in seen:errors.append(f"duplicate/blank claim id: {cid}")
        seen.add(cid)
        if module not in modules or modules[module]["in_scope"].upper()!="YES":
            errors.append(f"{cid}: claim references module outside research scope: {module}")
        per_module[module].append(row)
        if row["priority"].upper()=="HIGH":
            fields=("observation_refs","mechanism","financial_bridge",
                    "counter_explanation","falsification_condition","conclusion_scope")
            missing=[k for k in fields if not substantive(row[k])]
            if missing:errors.append(f"{cid}: missing thesis logic {missing}")
            if row["status"].upper() not in ACCEPTED:
                errors.append(f"{cid}: high-priority argument not actually re-reviewed ({row['status']})")
    if not claims:errors.append("no argument chain registered")
    for m in wanted:
        if not any(r["priority"].upper()=="HIGH" and r["status"].upper() in ACCEPTED for r in per_module[m]):
            errors.append(f"{m}: missing checked high-priority argument")
    used=set();touched=set()
    for b in bridges:
        key=b["bridge_id"]
        if not key or key in used:errors.append(f"duplicate/blank bridge id: {key}")
        used.add(key)
        x=b["source_module"];y=b["target_module"]
        if x==y or x not in modules or y not in modules:
            errors.append(f"{key}: invalid distinct cross-sector modules: {x} / {y}")
        else:touched.update([x,y])
        fields=("driver","transmission_path","economic_effect",
                "competing_response","evidence_ref","falsifier")
        missing=[k for k in fields if not substantive(b[k])]
        if missing:errors.append(f"{key}: missing economic bridge {missing}")
        if b["status"].upper() not in ACCEPTED:
            errors.append(f"{key}: unchecked sector bridge")
    if report_type=="industry_full":
        if len(bridges)<2:errors.append("industry_full needs at least two substantive cross-sector bridges")
        for module in wanted:
            if module not in touched and not substantive(modules[module]["bridge_exemption_reason"]):
                errors.append(f"{module}: no cross-sector link or reasoned exemption")
    model_ids=set()
    for row in models:
        mid=row["model_id"]
        if not mid or mid in model_ids:errors.append(f"duplicate/blank model ID: {mid}")
        model_ids.add(mid)
        if row["related_claim"] not in seen:
            errors.append(f"{mid}: model does not support registered claim")
        fields=("boundary_and_horizon","fixed_cost_terms","variable_cost_terms",
                "units_check_ref","formula_ref","counterexample_test_ref")
        missing=[k for k in fields if not substantive(row[k])]
        if missing:errors.append(f"{mid}: missing model consistency evidence {missing}")
        if row["status"].upper() not in ACCEPTED:
            errors.append(f"{mid}: model not checked")
    if report_type=="industry_full" and not models:
        errors.append("industry_full requires at least one auditable operating/financial model")
    if not modules:errors.append("empty research scope")
    return {
        "status":"ARGUMENT_REVISION_REQUIRED" if errors else "ARGUMENT_DOCUMENTARY_READY",
        "report_type":report_type,
        "high_scope_modules":len(wanted),"claims":len(claims),
        "cross_sector_bridges":len(bridges),"models":len(models),
        "errors":errors,"warnings":warnings,
        "disclaimer":"Checks registered text fields and review status only. Does not verify source truth, mathematical correctness, causal identification, inference quality or prose not registered.",
    }

def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ("scope","claims","bridges","models"):
        p.add_argument("--"+name,type=Path,required=True)
    p.add_argument("--report-type",choices=("industry_full","thematic","company"),default="industry_full")
    p.add_argument("--out",type=Path)
    args=p.parse_args()
    try:r=evaluate(args.scope,args.claims,args.bridges,args.models,args.report_type)
    except (OSError,ValueError,csv.Error,UnicodeError) as exc:p.exit(2,f"Invalid inputs: {exc}\n")
    if args.out:
        args.out.parent.mkdir(parents=True,exist_ok=True)
        args.out.write_text(json.dumps(r,indent=2,ensure_ascii=False),encoding="utf-8")
    print(json.dumps(r,indent=2,ensure_ascii=False))
    return int(r["status"]=="ARGUMENT_REVISION_REQUIRED")

if __name__=="__main__":
    raise SystemExit(main())
