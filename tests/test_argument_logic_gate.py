"""Regression checks for thesis coherence; not a factual-audit suite."""
from __future__ import annotations
import csv
import importlib.util
import tempfile
import unittest
from pathlib import Path
root=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location("logic",root/"scripts"/"argument_logic_gate.py")
logic=importlib.util.module_from_spec(spec);spec.loader.exec_module(logic)

def put(folder,name,fields,values):
    path=Path(folder)/name
    with path.open("w",newline="",encoding="utf-8") as f:
        writer=csv.DictWriter(f,fieldnames=sorted(fields))
        writer.writeheader();writer.writerows(values)
    return path

class ArgumentLogicTests(unittest.TestCase):
    def run_case(self,model_fixed="GPU capital and ASIC tapeout",
                 missing_mechanism=False,bridge_status="CHECKED",sector_extra=False,model_claim="A01"):
        with tempfile.TemporaryDirectory() as d:
            scope=[
                dict(module=x,priority="HIGH",in_scope="YES",bridge_exemption_reason="") for x in ("MASTER","MEMORY","FOUNDRY")
            ]
            if sector_extra:scope.append(dict(module="RF",priority="HIGH",in_scope="YES",bridge_exemption_reason=""))
            p=put(d,"scope.csv",logic.SCOPE,scope)
            cl=[]
            for m in [r["module"] for r in scope]:
                cl.append(dict(claim_id={"MASTER":"A01","MEMORY":"A02","FOUNDRY":"A03","RF":"A04"}[m],
                    module=m,priority="HIGH",observation_refs="company-annual.pdf",
                    mechanism="" if missing_mechanism and m=="MEMORY" else "demand converts to contracted price",
                    financial_bridge="revenue less capex, working capital and interest",
                    counter_explanation="mix effect instead of unit pricing",
                    falsification_condition="gross margin diverges from output",
                    conclusion_scope="group-level only",status="CHECKED"))
            q=put(d,"claims.csv",logic.CLAIMS,cl)
            bridges=[
                dict(bridge_id="B01",source_module="MASTER",target_module="MEMORY",
                    driver="capacity increases",transmission_path="volume and price",
                    economic_effect="producer cash flow may increase subject to ASP",
                    competing_response="customer switches suppliers",evidence_ref="report.pdf#5",
                    falsifier="margin fails to rise",status=bridge_status),
                dict(bridge_id="B02",source_module="MEMORY",target_module="FOUNDRY",
                    driver="interposer shortage",transmission_path="output constrained",
                    economic_effect="different bargaining power",competing_response="add foundry capacity",
                    evidence_ref="report.pdf#6",falsifier="lead times shrink",status="CHECKED")
            ]
            b=put(d,"bridges.csv",logic.BRIDGES,bridges)
            mod=[dict(model_id="M01",related_claim=model_claim,
                      boundary_and_horizon="same four-year horizon",
                      fixed_cost_terms=model_fixed,variable_cost_terms="price per task",
                      units_check_ref="model-audit.md#units",formula_ref="model.py#cost",
                      counterexample_test_ref="negative-tests.md#1",status="CHECKED")]
            t=put(d,"models.csv",logic.MODELS,mod)
            return logic.evaluate(p,q,b,t)
    def test_complete_trace_is_documentary_ready(self):
        self.assertEqual(self.run_case()["status"],"ARGUMENT_DOCUMENTARY_READY")
    def test_missing_mechanism_blocks(self):
        self.assertEqual(self.run_case(missing_mechanism=True)["status"],"ARGUMENT_REVISION_REQUIRED")
    def test_missing_fixed_cost_accounting_blocks(self):
        self.assertEqual(self.run_case(model_fixed="")["status"],"ARGUMENT_REVISION_REQUIRED")
    def test_unchecked_cross_sector_link_blocks(self):
        self.assertEqual(self.run_case(bridge_status="OPEN")["status"],"ARGUMENT_REVISION_REQUIRED")
    def test_high_module_without_link_or_exemption_blocks(self):
        self.assertEqual(self.run_case(sector_extra=True)["status"],"ARGUMENT_REVISION_REQUIRED")
    def test_model_must_connect_to_specific_claim(self):
        self.assertEqual(self.run_case(model_claim="UNKNOWN")["status"],"ARGUMENT_REVISION_REQUIRED")
if __name__=="__main__":unittest.main()
