#!/usr/bin/env python3
"""Foreground research workflow executor. Requires a trusted external AI worker.

A PASS means local artifact consistency, not factual truth or institutional approval.
"""
import argparse,ast,csv,hashlib,json,math,re,subprocess,sys,zipfile
from datetime import datetime,timezone
from pathlib import Path

PHASES=["plan","research","analyze","draft","review","render"]
class ResearchError(ValueError):pass
def read(p):return json.loads(Path(p).read_text(encoding="utf-8"))
def write(p,obj):
 p=Path(p);p.parent.mkdir(parents=True,exist_ok=True)
 t=p.with_suffix(p.suffix+".tmp");t.write_text(json.dumps(obj,indent=2,ensure_ascii=False),encoding="utf-8");t.replace(p)
def inside(root,p):
 f=(root/p).resolve()
 if not f.is_relative_to(root.resolve()) or f==root.resolve():raise ResearchError("Artifact path escapes workspace")
 if not f.is_file() or f.stat().st_size==0:raise ResearchError("Required file absent: "+str(p))
 return f
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def high_modules(brief):
 if not brief.get("title") or not re.fullmatch(r"20\d\d-\d\d-\d\d",brief.get("as_of","")):raise ResearchError("Title/as_of required")
 mods=brief.get("modules",[])
 ids=[x.get("id") for x in mods]
 if not ids or any(not x or not re.fullmatch(r"[A-Za-z]\w*",x) for x in ids) or len(set(ids))!=len(ids):
  raise ResearchError("Explicit unique module IDs required")
 return [x["id"] for x in mods if x.get("priority","HIGH")=="HIGH"]
def expression(exp,vars):
 ops={ast.Add:lambda a,b:a+b,ast.Sub:lambda a,b:a-b,ast.Mult:lambda a,b:a*b,ast.Div:lambda a,b:a/b}
 def value(n):
  if isinstance(n,ast.Expression):return value(n.body)
  if isinstance(n,ast.Name):
   v=vars.get(n.id)
   if isinstance(v,bool) or not isinstance(v,(int,float)):raise ResearchError("Invalid numeric model input")
   return float(v)
  if isinstance(n,ast.Constant) and type(n.value) in (int,float):return float(n.value)
  if isinstance(n,ast.UnaryOp) and isinstance(n.op,ast.USub):return -value(n.operand)
  if isinstance(n,ast.BinOp) and type(n.op) in ops:
   try:return ops[type(n.op)](value(n.left),value(n.right))
   except ZeroDivisionError as e:raise ResearchError("Zero denominator") from e
  raise ResearchError("Unsafe model expression")
 try:v=value(ast.parse(exp,mode="eval"))
 except SyntaxError as e:raise ResearchError("Invalid formula") from e
 if not math.isfinite(v):raise ResearchError("Non-finite model result")
 return v
def verify(root,phase,high):
 def load(f):return read(inside(root,f))
 if phase=="plan":
  plan=load("plan.json")
  if not plan.get("central_question") or set(high)-{x.get("module") for x in plan.get("tasks",[])}:
   raise ResearchError("Plan did not address all HIGH modules")
  return {"tasks":len(plan["tasks"])}
 if phase in ("research","revise"):
  sources=load("sources.json").get("sources",[]);claims=load("claims.json").get("claims",[])
  by={}
  for s in sources:
   sid=s.get("source_id")
   if not sid or sid in by:raise ResearchError("Source ID duplicated or blank")
   p=inside(root,s.get("snapshot_path",""))
   if p.suffix.lower() not in (".txt",".md",".html") or digest(p)!=s.get("sha256"):
    raise ResearchError("Source snapshot missing or hash mismatch: "+sid)
   if not s.get("url") or not s.get("retrieved_at"):raise ResearchError("Source capture metadata missing")
   by[sid]=(s,re.sub(r"\s+"," ",p.read_text(encoding="utf-8")))
  ids=set();evidenced=set()
  for c in claims:
   cid=c.get("claim_id")
   if not cid or cid in ids:raise ResearchError("Claim ID duplicated or blank")
   ids.add(cid);src=by.get(c.get("source_id"))
   if not src:raise ResearchError("Claim source unavailable: "+cid)
   s,text=src;quote=re.sub(r"\s+"," ",c.get("verbatim_quote","")).strip()
   if not quote or quote not in text:raise ResearchError("Claim quote not found in captured source: "+cid)
   if c.get("verification")!="VERIFIED" or not c.get("location") or not c.get("claim_text"):
    raise ResearchError("Claim lacks actual verification location: "+cid)
   if c.get("module")!=s.get("module"):raise ResearchError("Claim/source module mismatch")
   evidenced.add(c.get("module"))
  if not claims or set(high)-evidenced:raise ResearchError("HIGH modules missing source-backed claims")
  if phase=="research":return {"sources":len(sources),"claims":len(claims)}
 if phase in ("analyze","revise"):
  models=load("models.json").get("calculations",[])
  evidence={c["claim_id"] for c in load("claims.json")["claims"]}
  if not models:raise ResearchError("No reproducible model")
  for m in models:
   if not m.get("units") or not m.get("horizon") or not m.get("source_claim_ids") or not set(m["source_claim_ids"])<=evidence:
    raise ResearchError("Model missing units, horizon or evidence IDs")
   value=expression(m.get("formula",""),m.get("inputs",{}))
   if not isinstance(m.get("result"),(int,float)) or isinstance(m["result"],bool) or not math.isclose(value,m["result"],rel_tol=1e-7,abs_tol=1e-8):
    raise ResearchError("Model arithmetic conflict: "+m.get("calc_id","?"))
  if phase=="analyze":return {"models":len(models)}
 if phase in ("draft","revise"):
  report=inside(root,"report.md").read_text(encoding="utf-8")
  claims=load("claims.json")["claims"];ids={c["claim_id"] for c in claims}
  cited=set(re.findall(r"\[([A-Za-z]\d{3,5})\]",report))
  if len(report)<350 or not cited or not cited<=ids:raise ResearchError("Draft short, absent citations or unknown claim citations")
  if any(not any(c["claim_id"] in cited and c["module"]==m for c in claims) for m in high):
   raise ResearchError("Draft does not substantiate all HIGH modules")
  return {"report_chars":len(report),"cited_claims":len(cited)}
 if phase=="review":
  data=load("review.json")
  if set(high)-set(data.get("reviewed_modules",[])):raise ResearchError("Audit missed HIGH module")
  issues=data.get("issues",[]);major=[]
  for i in issues:
   if not i.get("id") or not i.get("finding") or i.get("severity") not in ("P0","P1","P2") or i.get("status") not in ("OPEN","FIXED"):
    raise ResearchError("Malformed audit defect")
   if i["severity"] in ("P0","P1") and i["status"]=="OPEN":major.append(i["id"])
  if data.get("decision") not in ("PASS","REVISE") or bool(major)!=(data["decision"]=="REVISE"):
   raise ResearchError("Audit decision inconsistent with unresolved major defects")
  inside(root,data.get("review_artifact",""))
  return {"decision":data["decision"],"major_open":major}
 if phase=="render":
  pdf=inside(root,"report.pdf");docx=inside(root,"report.docx")
  raw=pdf.read_bytes()
  if not raw.startswith(b"%PDF-") or b"%%EOF" not in raw[-4096:] or len(raw)<200:raise ResearchError("PDF structure invalid")
  try:
   with zipfile.ZipFile(docx) as z:
    if not {"[Content_Types].xml","_rels/.rels","word/document.xml"}<=set(z.namelist()):
     raise ResearchError("DOCX missing required files")
    if b"<w:document" not in z.read("word/document.xml"):raise ResearchError("DOCX invalid document root")
  except zipfile.BadZipFile as e:raise ResearchError("DOCX not ZIP") from e
  return {"pdf_bytes":len(raw),"docx_bytes":docx.stat().st_size}
 raise ResearchError("Unknown stage "+phase)
def init(brief_file,root):
 root.mkdir(parents=True,exist_ok=True)
 if (root/"state.json").exists():raise ResearchError("Workspace already initialized")
 brief=read(brief_file);high_modules(brief)
 write(root/"brief.json",brief)
 state={"status":"RUNNING","pending":PHASES[:],"completed":[],"revisions":0,"history":[],"brief_hash":digest(root/"brief.json")}
 write(root/"state.json",state);return state
def run(root,worker,revisions=3,timeout=1800):
 root=root.resolve()
 if not worker or timeout<=0:raise ResearchError("Trusted worker command and positive timeout required")
 brief=read(inside(root,"brief.json"));state=read(inside(root,"state.json"))
 if state["brief_hash"]!=digest(root/"brief.json"):raise ResearchError("Brief modified after initialization")
 if state["status"]=="INTERNAL_RESEARCH_CANDIDATE":return state
 high=high_modules(brief)
 for phase in ("plan","research","analyze"):
  if phase in state["completed"]:verify(root,phase,high)
 pending=state["pending"]
 def save(stage,result):
  state["history"].append({"phase":stage,"at":datetime.now(timezone.utc).isoformat(),"result":result})
  write(root/"state.json",state)
 while pending:
  phase=pending[0]
  job={"phase":phase,"workspace":str(root),"brief":brief,"revision":state["revisions"]}
  try:
   p=subprocess.run(worker,input=json.dumps(job,ensure_ascii=False),text=True,cwd=root,capture_output=True,timeout=timeout)
   if p.returncode:raise ResearchError("Worker error: "+p.stderr[-1000:])
   result=verify(root,phase,high)
  except (ResearchError,subprocess.TimeoutExpired,OSError) as e:
   state["status"]="BLOCKED_ARTIFACT_OR_WORKER";save(phase,{"error":str(e)});raise
  pending.pop(0)
  if phase=="review" and result["decision"]=="REVISE":
   pending[:]=["revise","review","render"]
   if state["revisions"]>=revisions:
    state["status"]="NEEDS_MORE_RESEARCH";save(phase,result);return state
   state["revisions"]+=1
  if phase not in state["completed"]:state["completed"].append(phase)
  state["status"]="RUNNING";save(phase,result)
 state["status"]="INTERNAL_RESEARCH_CANDIDATE"
 save("handoff",{"notice":"Not proof of independent fact verification or institutional approval"})
 return state
def main():
 p=argparse.ArgumentParser(description=__doc__);subs=p.add_subparsers(dest="cmd",required=True)
 a=subs.add_parser("init");a.add_argument("--brief",required=True,type=Path);a.add_argument("--workspace",required=True,type=Path)
 a=subs.add_parser("run");a.add_argument("--workspace",required=True,type=Path);a.add_argument("--max-revisions",type=int,default=3)
 a.add_argument("--timeout",type=int,default=1800);a.add_argument("--worker",nargs=argparse.REMAINDER,required=True)
 q=p.parse_args()
 try:res=init(q.brief,q.workspace) if q.cmd=="init" else run(q.workspace,q.worker,q.max_revisions,q.timeout)
 except (ValueError,OSError,subprocess.SubprocessError) as e:p.exit(2,f"Research stopped: {e}\n")
 print(json.dumps(res,indent=2,ensure_ascii=False))
 return 0 if res["status"] in ("RUNNING","INTERNAL_RESEARCH_CANDIDATE") else 1
if __name__=="__main__":raise SystemExit(main())
