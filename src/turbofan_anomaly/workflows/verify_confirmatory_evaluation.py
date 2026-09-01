"""Independently verify the frozen FD002 confirmatory result and report hashes."""
from __future__ import annotations
import argparse,json
from pathlib import Path
import pandas as pd
from turbofan_anomaly.evaluation.provenance import find_repository_root,sha256_file
from turbofan_anomaly.workflows.run_confirmatory_evaluation import DEFAULT_PROTOCOL,validate_execution_protocol
def parse_args():
    p=argparse.ArgumentParser(description=__doc__); p.add_argument("--protocol",type=Path,default=DEFAULT_PROTOCOL); p.add_argument("--result",type=Path,default=Path("reports/final_evaluation_v2/fd002-confirmatory-internal-held-out-v1/result.json")); p.add_argument("--output",type=Path); return p.parse_args()
def verify(repo:Path,protocol_path:Path,result_path:Path):
    protocol=json.loads(protocol_path.read_text()); validate_execution_protocol(protocol); result=json.loads(result_path.read_text()); assert result["protocol_sha256"]==sha256_file(protocol_path); assert result["primary_candidate_id"]==protocol["primary"]["candidate_id"]
    for key in ("threshold_refit","model_refit","calibration_refit","online_recalibration","score_or_decision_fusion","official_nasa_test_accessed"): assert result[key] is False
    checks=[]
    for item in result["outputs"]: assert sha256_file(repo/item["path"])==item["sha256"]; checks.append(item["path"])
    metrics=pd.read_csv(result_path.parent/"detector_policy_metrics.csv"); assert len(metrics)==10 and set(metrics.detector_id)=={"pca_reconstruction","lstm_calibrated_ensemble"}
    access=json.loads((result_path.parent/"access_declaration.json").read_text()); assert access["internal_held_out_opened"] and not access["official_nasa_test_opened"] and not access["held_out_used_for_fit_calibration_threshold_selection_or_model_selection"]
    return {"verified":True,"output_count":len(checks),"metric_rows":10,"official_nasa_test_opened":False,"frozen_primary_verified":True}
def main():
    a=parse_args(); repo=find_repository_root(Path.cwd()); report=verify(repo,repo/a.protocol,repo/a.result); text=json.dumps(report,indent=2,sort_keys=True)+"\n"; print(text,end="");
    if a.output: (repo/a.output).write_text(text,encoding="utf-8",newline="\n")
if __name__=="__main__": main()
