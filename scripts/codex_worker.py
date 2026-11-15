#!/usr/bin/env python3
"""Bridge research_runtime phase requests to installed/authenticated Codex CLI."""
import json,os,shutil,subprocess,sys
PHASES={
"plan":"Write plan.json containing central_question and tasks for EVERY HIGH module, with module, research question, likely original sources, evidence and work plan.",
"research":"Actively find and open actual PRIMARY source documents. Save source text snapshots and compute SHA256. Write sources.json {sources:[{source_id,module,url,retrieved_at,snapshot_path,sha256}]} and claims.json {claims:[{claim_id,module,source_id,verbatim_quote,location,claim_text,verification:'VERIFIED'}]}. Every HIGH module must have real evidence. Verbatim quotes must appear in captured text. Never invent evidence.",
"analyze":"Read captured primary sources and claims. Produce models.json {calculations:[{calc_id,formula,inputs,result,units,horizon,source_claim_ids}]}. Formula uses +,-,*,/ and numeric named inputs. Explicitly distinguish fact, assumption and inference. Compute independently; never fake a source or metric.",
"draft":"Write comprehensive report.md with central industry thesis, each HIGH module, sector profit transfer, financial mechanism, risks, falsification and conditional investment implications. Cite exact claim IDs like [C001] for major facts, cover every HIGH module, avoid summary-only output. Do not invent facts.",
"review":"Actually read report.md, source snapshots, claims.json and models.json. Write audit_review.md and review.json with reviewed_modules all HIGH module IDs, review_artifact:'audit_review.md', decision:'PASS' or 'REVISE', issues:[{id,severity:'P0/P1/P2',status:'OPEN/FIXED',finding,verification_ref if FIXED}]. Identify real factual, causal, modeling, missing-coverage and presentation problems. If substantive review impossible, produce OPEN P1, never false PASS.",
"revise":"Read audit_review.md, review.json, source extracts and report. Actually repair OPEN major defects in report.md and if needed sources.json, claims.json, models.json. Retain a revision_log.md of old issue and actual changes. Do not merely relabel audit issues as fixed. Controller will RE-REVIEW.",
"render":"Produce genuinely readable report.docx and report.pdf from report.md. Check Chinese fonts, tables, captions, heading hierarchy, page numbers and chart legibility. Do not create blank/dummy files. If conversion impossible, exit unsuccessfully."
}
def main():
    job=json.load(sys.stdin);phase=job["phase"];workspace=job["workspace"];brief=job["brief"]
    if phase not in PHASES:raise SystemExit(f"Unsupported phase {phase}")
    cli=os.environ.get("RESEARCH_CODEX_BIN","codex");exe=shutil.which(cli)
    if not exe:raise SystemExit(f"Codex CLI not found: {cli}. Install and authenticate first.")
    prompt=(f"You are an industry research agent executing a real stage, not describing an ideal plan.\n"
        f"Title: {brief['title']}\nAs-of: {brief['as_of']}\n"
        f"FULL BRIEF: {json.dumps(brief,ensure_ascii=False)}\n"
        f"WORKSPACE: {workspace}\nSTAGE: {phase}\n"
        f"STAGE OUTPUT CONTRACT: {PHASES[phase]}\n"
        "Use real research tools and write actual files to WORKSPACE. "
        "Do not invent sources, profits, citations, pages, or test outcomes. "
        "If blocked, fail clearly, leave actual blocker notes, and do not claim research completion. "
        "Do not recursively run research_runtime.py.")
    return subprocess.run([exe,"exec","-"],input=prompt,text=True,cwd=workspace).returncode
if __name__=="__main__":raise SystemExit(main())
