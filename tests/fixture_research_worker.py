"""Synthetic OFFLINE CI fixture. NOT an industry report or factual source."""
import hashlib,json,sys,zipfile
from pathlib import Path
job=json.load(sys.stdin);root=Path(job["workspace"]);stage=job["phase"]
mods=[x["id"] for x in job["brief"]["modules"] if x.get("priority","HIGH")=="HIGH"]
if stage=="plan":
 (root/"plan.json").write_text(json.dumps({"central_question":"Synthetic research task","tasks":[{"module":m,"plan":"Test"} for m in mods]}))
elif stage=="research":
 sources=[];claims=[]
 for i,m in enumerate(mods,1):
  p=root/f"source_{m}.txt"
  q="Synthetic revenue was 100 and is now 120."
  p.write_text(q+" This is a fictional source used only by a software test.",encoding="utf-8")
  sources.append({"source_id":f"S{i:03d}","module":m,"url":"https://example.invalid/fixture","retrieved_at":"2026-11-15","snapshot_path":p.name,"sha256":hashlib.sha256(p.read_bytes()).hexdigest()})
  claims.append({"claim_id":f"C{i:03d}","source_id":f"S{i:03d}","module":m,"verbatim_quote":q,"location":"fixture text","claim_text":"Synthetic revenue increased","verification":"VERIFIED"})
 (root/"sources.json").write_text(json.dumps({"sources":sources}))
 (root/"claims.json").write_text(json.dumps({"claims":claims}))
elif stage=="analyze":
 (root/"models.json").write_text(json.dumps({"calculations":[{"calc_id":"M01","formula":"(a-b)/b*100","inputs":{"a":120,"b":100},"result":20,"units":"percent","horizon":"synthetic annual","source_claim_ids":["C001"]}]}))
elif stage in ("draft","revise"):
 citations=" ".join(f"[C{i:03d}]" for i in range(1,len(mods)+1))
 report="# Test-only research\n"+citations+"\n"+"Synthetic mechanism paragraph; no real-world investment conclusion is asserted. "*10
 (root/"report.md").write_text(report)
 if stage=="revise":(root/"was_revised.flag").write_text("true")
elif stage=="review":
 need=not (root/"was_revised.flag").exists()
 (root/"review.md").write_text("Synthetic review evidence: initial defect injected, then revised.")
 (root/"review.json").write_text(json.dumps({"reviewed_modules":mods,"review_artifact":"review.md","decision":"REVISE" if need else "PASS","issues":[{"id":"D01","severity":"P1","status":"OPEN" if need else "FIXED","finding":"synthetic issue"}]}))
elif stage=="render":
 (root/"report.pdf").write_bytes(b"%PDF-1.4\n"+b"% Synthetic test content ONLY\n"*12+b"%%EOF\n")
 with zipfile.ZipFile(root/"report.docx","w") as z:
  z.writestr("[Content_Types].xml","<Types/>")
  z.writestr("_rels/.rels","<Relationships/>")
  z.writestr("word/document.xml","<w:document xmlns:w='http://schemas.openxmlformats.org/wordprocessingml/2006/main'><w:body/></w:document>")
else:sys.exit(1)
