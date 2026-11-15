#!/usr/bin/env python3
"""Validate registered numeric narrative and external-blocker alternatives; does not verify sources."""
import argparse,csv,json,math
from collections import defaultdict
from pathlib import Path

SERIES={'series_id','period','value','source_ref'}
CLAIMS={'claim_id','report_location','series_id','relation','start_period','end_period','verification_ref'}
BLOCKERS={'issue_id','module','status','claim_of_unavailability','primary_attempt_ref','alternative_name','alternative_source_ref','alternative_status','alternative_reason','work_done_ref'}
RELATIONS={'monotonic_increase','monotonic_decrease','start_to_end_increase','start_to_end_decrease','non_monotonic','equal'}
ALTERNATIVES={'FEASIBLE','INFEASIBLE','UNTESTED'}

def read(path,required):
    with Path(path).open(encoding='utf-8-sig',newline='') as f:
        rd=csv.DictReader(f)
        if not rd.fieldnames or not required.issubset(rd.fieldnames):
            raise ValueError(f'{path}: missing {sorted(required-set(rd.fieldnames or []))}')
        return [{k:(v or '').strip() for k,v in r.items() if k} for r in rd]

def check(series_path,claims_path,blockers_path):
    series=read(series_path,SERIES);claims=read(claims_path,CLAIMS);blockers=read(blockers_path,BLOCKERS)
    errors=[];warnings=[];data=defaultdict(dict)
    for r in series:
        try:v=float(r['value'])
        except ValueError: errors.append(f"{r['series_id']}: nonnumeric");continue
        if not math.isfinite(v):errors.append(f"{r['series_id']}: nonfinite");continue
        if not r['source_ref']:errors.append(f"{r['series_id']}: missing source_ref")
        if r['period'] in data[r['series_id']]:errors.append(f"{r['series_id']}: duplicate period")
        data[r['series_id']][r['period']]=v
    if not claims:errors.append('no claims registered')
    for r in claims:
        tag=r['claim_id'];rel=r['relation']
        if not tag or not r['report_location'] or not r['verification_ref']:errors.append(f'{tag}: lacks location or review')
        if rel not in RELATIONS:errors.append(f'{tag}: invalid relation');continue
        d=data.get(r['series_id'],{});ps=sorted(k for k in d if r['start_period']<=k<=r['end_period'])
        if len(ps)<2 or r['start_period'] not in ps or r['end_period'] not in ps:
            errors.append(f'{tag}: missing data endpoints');continue
        v=[d[p] for p in ps];diff=[b-a for a,b in zip(v,v[1:])];e=1e-9
        verdict={'monotonic_increase':all(x>e for x in diff),
                 'monotonic_decrease':all(x<-e for x in diff),
                 'start_to_end_increase':v[-1]>v[0]+e,'start_to_end_decrease':v[-1]<v[0]-e,
                 'non_monotonic':not(all(x>=-e for x in diff) or all(x<=e for x in diff)),
                 'equal':abs(v[-1]-v[0])<=e}[rel]
        if not verdict:errors.append(f"{tag}: text conflicts with {r['series_id']} {list(zip(ps,v))}: {rel}")
    grouped=defaultdict(list)
    for r in blockers:grouped[(r['issue_id'],r['module'])].append(r)
    for (issue,module),items in grouped.items():
        if not issue or not module:errors.append('blocker missing id or module');continue
        if 'EXTERNAL_BLOCKED' not in {r['status'] for r in items}:continue
        if any(not r['primary_attempt_ref'] for r in items):errors.append(f'{issue}: no original source attempt')
        if any(r['alternative_status']=='FEASIBLE' for r in items):
            errors.append(f'{issue}: feasible alternative found; execute before external block')
        valid=[r for r in items if r['alternative_status']=='INFEASIBLE' and r['alternative_source_ref'] and r['alternative_reason']]
        if len({r['alternative_name'] for r in valid})<2:errors.append(f'{issue}: fewer than two assessed alternatives')
        if any(r['alternative_status'] not in ALTERNATIVES for r in items):errors.append(f'{issue}: invalid alternative status')
        if any(not r['work_done_ref'] for r in items):errors.append(f'{issue}: missing work/impact report')
        warnings.append(f'{issue}: local external blocker, does not imply entire report stop')
    return {'status':'BLOCKED' if errors else 'STAGED' if warnings else 'PASS_DOCUMENTARY',
            'claim_count':len(claims),'errors':errors,'warnings':warnings,
            'disclaimer':'Only registered claims/attempts checked; sources and omitted statements are not authenticated.'}

def main():
    p=argparse.ArgumentParser(description=__doc__)
    for key in ('series','claims','blockers'):p.add_argument('--'+key,required=True,type=Path)
    p.add_argument('--out',type=Path);a=p.parse_args()
    try:r=check(a.series,a.claims,a.blockers)
    except (ValueError,OSError,csv.Error) as exc:p.exit(2,f'bad input: {exc}\n')
    if a.out:
        a.out.parent.mkdir(parents=True,exist_ok=True)
        a.out.write_text(json.dumps(r,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(r,ensure_ascii=False,indent=2));return 1 if r['errors'] else 0
if __name__=='__main__':raise SystemExit(main())
