"""Executable-workflow integration tests with fake sources; never factual research QA."""
import importlib.util,json,sys,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location("runner",ROOT/"scripts"/"research_runtime.py")
runner=importlib.util.module_from_spec(spec);spec.loader.exec_module(runner)
WORKER=ROOT/"tests"/"fixture_research_worker.py"
class ResearchRuntimeTests(unittest.TestCase):
 def start(self,dir):
  brief=Path(dir)/"brief.json"
  brief.write_text(json.dumps({"title":"Synthetic","as_of":"2026-11-15",
    "modules":[{"id":"S01","priority":"HIGH"},{"id":"S02","priority":"HIGH"}]}))
  root=Path(dir)/"work";runner.init(brief,root);return root
 def test_executes_all_stages_and_revises(self):
  with tempfile.TemporaryDirectory() as d:
   root=self.start(d);s=runner.run(root,[sys.executable,str(WORKER)],revisions=2)
   self.assertEqual(s["status"],"INTERNAL_RESEARCH_CANDIDATE")
   self.assertEqual(s["revisions"],1)
   self.assertTrue(any(i["phase"]=="revise" for i in s["history"]))
   self.assertTrue((root/"report.pdf").is_file())
 def test_revision_limit_blocks_and_can_resume(self):
  with tempfile.TemporaryDirectory() as d:
   root=self.start(d)
   s=runner.run(root,[sys.executable,str(WORKER)],revisions=0)
   self.assertEqual(s["status"],"NEEDS_MORE_RESEARCH")
   self.assertEqual(s["pending"],["revise","review","render"])
   later=runner.run(root,[sys.executable,str(WORKER)],revisions=1)
   self.assertEqual(later["status"],"INTERNAL_RESEARCH_CANDIDATE")
 def test_snapshot_tampering_blocks_resumption(self):
  with tempfile.TemporaryDirectory() as d:
   root=self.start(d);runner.run(root,[sys.executable,str(WORKER)],revisions=0)
   (root/"source_S01.txt").write_text("tampered")
   with self.assertRaisesRegex(runner.ResearchError,"Source snapshot"):
    runner.run(root,[sys.executable,str(WORKER)],revisions=1)
 def test_formula_error_is_rejected(self):
  with tempfile.TemporaryDirectory() as d:
   root=self.start(d);runner.run(root,[sys.executable,str(WORKER)],revisions=0)
   p=root/"models.json";content=json.loads(p.read_text());content["calculations"][0]["result"]=99
   p.write_text(json.dumps(content))
   with self.assertRaisesRegex(runner.ResearchError,"arithmetic conflict"):
    runner.verify(root,"analyze",["S01","S02"])
 def test_quote_fabrication_is_rejected(self):
  with tempfile.TemporaryDirectory() as d:
   root=self.start(d);runner.run(root,[sys.executable,str(WORKER)],revisions=0)
   p=root/"claims.json";content=json.loads(p.read_text());content["claims"][0]["verbatim_quote"]="fabricated words"
   p.write_text(json.dumps(content))
   with self.assertRaisesRegex(runner.ResearchError,"quote not found"):
    runner.verify(root,"research",["S01","S02"])
 def test_unsafe_code_not_executed(self):
  with self.assertRaises(runner.ResearchError):
   runner.expression("__import__('os').system('whoami')",{})
 def test_missing_worker_is_rejected(self):
  with tempfile.TemporaryDirectory() as d:
   root=self.start(d)
   with self.assertRaisesRegex(runner.ResearchError,"Trusted worker"):
    runner.run(root,[],revisions=0)
 def test_missing_high_module_in_report_is_rejected(self):
  with tempfile.TemporaryDirectory() as d:
   root=self.start(d);runner.run(root,[sys.executable,str(WORKER)],revisions=0)
   p=root/"report.md";p.write_text(p.read_text().replace("[C002]",""))
   with self.assertRaisesRegex(runner.ResearchError,"HIGH modules"):
    runner.verify(root,"draft",["S01","S02"])
if __name__=="__main__":unittest.main()
