#!/usr/bin/env python3
"""Documentary defect-remediation gate. Does not validate external facts."""
from __future__ import annotations
import argparse,csv,json
from pathlib import Path
FIELDS={'issue_id','module','priority','source_section','finding','evidence_ref','corrective_action','status','fix_ref','verification_ref','blocker_reason'}
SCORE_FIELDS={'round_id','criterion_id','score_0_5'}
HIGH={'P0','P1'}
VALID_STATUS={'OPEN','FIXED','EXTERNAL_BLOCKED'}

def load(path:Path,required:set[str])->list[dict]:
    with path.open(encoding='utf-8-sig',newline='') as f:
        r=csv.DictReader(f)
        if not r.fieldnames or not required.issubset(set(r.fieldnames)):
            raise ValueError(f'{path}: missing columns {sorted(required-set(r.fieldnames or []))}')
        return list(r)

def inspect(ledger:Path,rounds:Path,mode:str='handoff')->dict:
    issues=load(ledger,FIELDS);scores=load(rounds,SCORE_FIELDS)
    failures=[];warnings=[]
    if not issues:failures.append('no defect-review entries; record at least one audit finding or a NO_FINDING row')
    ids=set();important=0;open_count=0;external=0;fixed=0
    for row in issues:
        k=row['issue_id'].strip();pr=row['priority'].strip().upper();st=row['status'].strip().upper()
        if not k or k in ids:failures.append(f'duplicate/missing issue id {k}')
        ids.add(k)
        if pr not in {'P0','P1','P2','NO_FINDING'}:failures.append(f'{k}: invalid priority')
        if st not in VALID_STATUS:failures.append(f'{k}: invalid status {st}')
        if pr=='NO_FINDING':continue
        for field in ('module','source_section','finding','evidence_ref','corrective_action'):
            if not row[field].strip():failures.append(f'{k}: missing {field}')
        if pr in HIGH:
            important+=1
            if st=='OPEN':open_count+=1
            if st=='EXTERNAL_BLOCKED':external+=1
        if st=='FIXED':
            fixed+=1
            if not row['fix_ref'].strip() or not row['verification_ref'].strip():
                failures.append(f'{k}: FIXED requires fix_ref and verification_ref')
        elif st=='EXTERNAL_BLOCKED':
            if not row['blocker_reason'].strip():failures.append(f'{k}: external blocker not explained')
            if pr in HIGH and not row['verification_ref'].strip():
                failures.append(f'{k}: external blocker needs an impact/alternative review reference')
    seq=list(dict.fromkeys(r['round_id'].strip() for r in scores if r['round_id'].strip()))
    if important and len(seq)<2:failures.append('high-priority findings require at least two distinct scoring rounds')
    if important and not ('R1' in seq and 'R2' in seq):
        warnings.append('no canonical R1/R2 labels (accepted only if two distinct rounds)')
    if open_count:warnings.append(f'{open_count} high-priority findings remain OPEN')
    if external:warnings.append(f'{external} high-priority findings remain EXTERNAL_BLOCKED')
    if mode=='handoff' and (open_count or external):
        failures.append('P0/P1 defects remain unresolved or externally blocked; no module handoff')
    return {'status':'PASS_HANDOFF' if not failures and mode=='handoff' else ('STAGED_ONLY' if not failures else 'LOOP_INCOMPLETE'),
        'mode':mode,'issue_count':len(issues),'important':important,'fixed':fixed,
        'high_open':open_count,'high_external_blocked':external,'rounds':seq,'errors':failures,
        'warnings':warnings,'notice':'Documentary check only; independent fact review still required.'}

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--ledger',type=Path,required=True);p.add_argument('--rounds',type=Path,required=True)
    p.add_argument('--mode',choices=['handoff','staged'],default='handoff');p.add_argument('--out',type=Path)
    args=p.parse_args()
    try:r=inspect(args.ledger,args.rounds,args.mode)
    except (OSError,UnicodeError,ValueError,csv.Error) as exc:p.exit(2,f'Invalid gate input: {exc}\n')
    if args.out:
        args.out.parent.mkdir(parents=True,exist_ok=True)
        args.out.write_text(json.dumps(r,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(r,ensure_ascii=False,indent=2))
    return 1 if r['errors'] else 0
if __name__=='__main__':raise SystemExit(main())
