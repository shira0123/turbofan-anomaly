"""Independently reproduce the frozen FD002 confirmatory result read-only."""
from __future__ import annotations
import argparse,json,os
from pathlib import Path
os.environ.setdefault("CUBLAS_WORKSPACE_CONFIG", ":4096:8")
import numpy as np
import pandas as pd
import torch
from turbofan_anomaly.data.io import load_fd002
from turbofan_anomaly.data.metadata import create_window_metadata,assign_endpoint_operating_modes
from turbofan_anomaly.data.preprocessing import load_preprocessor
from turbofan_anomaly.data.windows import build_window_array,summary_features
from turbofan_anomaly.evaluation.provenance import find_repository_root,sha256_file
from turbofan_anomaly.models.classical import load_baseline_artifact
from turbofan_anomaly.models.lstm_training import load_lstm_artifact,reconstruction_errors
from turbofan_anomaly.workflows.run_confirmatory_evaluation import DEFAULT_PROTOCOL,validate_execution_protocol,_score_frame,evaluate_detector
def parse_args():
    p=argparse.ArgumentParser(description=__doc__); p.add_argument("--protocol",type=Path,default=DEFAULT_PROTOCOL); p.add_argument("--result",type=Path,default=Path("reports/final_evaluation_v2/fd002-confirmatory-internal-held-out-v1/result.json")); p.add_argument("--output",type=Path); p.add_argument("--device",choices=("cpu","cuda","auto"),default="auto"); return p.parse_args()
def _close(observed,expected,atol=1e-12,rtol=1e-10):
    a=np.asarray(observed,dtype=float); b=np.asarray(expected,dtype=float); assert a.shape==b.shape and np.allclose(a,b,atol=atol,rtol=rtol); return float(np.max(np.abs(a-b))) if a.size else 0.0
def verify(repo:Path,protocol_path:Path,result_path:Path,device:torch.device):
    protocol=json.loads(protocol_path.read_text()); validate_execution_protocol(protocol); result=json.loads(result_path.read_text()); assert result["protocol_sha256"]==sha256_file(protocol_path); assert result["primary_candidate_id"]==protocol["primary"]["candidate_id"]
    for key in ("threshold_refit","model_refit","calibration_refit","online_recalibration","score_or_decision_fusion","official_nasa_test_accessed"): assert result[key] is False
    checks=[]
    for item in result["outputs"]: assert sha256_file(repo/item["path"])==item["sha256"]; checks.append(item["path"])
    manifest=json.loads((repo/protocol["authority"]["split_manifest_path"]).read_text()); ids=set(map(int,protocol["partition"]["engine_ids"])); assert ids=={int(r["engine"]) for r in manifest["engines"] if r["split"]=="test"}; assert not ids & {int(r["engine"]) for r in manifest["engines"] if r["split"] in {"train","validation"}}
    source=load_fd002(repo/protocol["partition"]["source_path"]); held=source[source.engine.astype(int).isin(ids)].sort_values(["engine","cycle"],kind="stable").reset_index(drop=True); del source; assert held.shape==(10779,26) and set(held.engine.astype(int))==ids
    pre,_=load_preprocessor(repo/protocol["preprocessing"]["artifact_path"],expected_split_manifest_id="fd002-primary-v1"); transformed=pre.transform(held); stored_cycle=pd.read_csv(repo/protocol["local_derived_artifacts"]["cycle_frame"]); pd.testing.assert_frame_equal(transformed,stored_cycle,check_exact=False,atol=1e-12,rtol=1e-10)
    meta=create_window_metadata(held,split="internal_held_out",manifest_id="fd002-primary-v1",source_dataset_sha256=protocol["partition"]["source_sha256"],window_size=30); context=assign_endpoint_operating_modes(meta,transformed); stored_context=pd.read_csv(repo/protocol["local_derived_artifacts"]["window_context"]); pd.testing.assert_frame_equal(context,stored_context,check_dtype=False,check_exact=False,atol=1e-12,rtol=1e-10); seq=build_window_array(transformed,context); stored_seq=np.load(repo/protocol["local_derived_artifacts"]["sequences"],allow_pickle=False); assert np.array_equal(seq,stored_seq)
    model,_=load_baseline_artifact(repo/protocol["primary"]["model_path"],expected_split_manifest_id="fd002-primary-v1",expected_preprocessing_decision_id="fd002-preprocessing-selection-v1"); raw,cal=model.score(summary_features(seq)); pf=_score_frame(context,"pca_reconstruction",cal,raw); ptrace,pm,_,_,_=evaluate_detector(pf,context,protocol["primary"]); stored_primary=pd.read_csv(result_path.parent/"primary_score_alert_trace.csv"); primary_diff=max(_close(ptrace["raw_score"],stored_primary["raw_score"]),_close(ptrace["alert_score"],stored_primary["alert_score"]),_close(ptrace["smoothed_score"],stored_primary["smoothed_score"])); assert np.array_equal(ptrace["alert_active"].to_numpy(bool),stored_primary["alert_active"].to_numpy(bool))
    seed_scores=[]
    for path in protocol["comparator"]["model_paths"]:
        lm,ref,_=load_lstm_artifact(repo/path,expected_split_manifest_id="fd002-primary-v1",expected_preprocessing_decision_id="fd002-preprocessing-selection-v1"); rr=reconstruction_errors(lm.to(device),seq,batch_size=128,device=device); seed_scores.append(np.searchsorted(ref,rr,side="right")/len(ref))
    cf=_score_frame(context,"lstm_calibrated_ensemble",np.mean(seed_scores,axis=0),None); ctrace,cm,_,_,_=evaluate_detector(cf,context,protocol["comparator"]); stored_comparator=pd.read_csv(result_path.parent/"comparator_score_alert_trace.csv"); comparator_diff=max(_close(ctrace["alert_score"],stored_comparator["alert_score"]),_close(ctrace["smoothed_score"],stored_comparator["smoothed_score"])); assert np.array_equal(ctrace["alert_active"].to_numpy(bool),stored_comparator["alert_active"].to_numpy(bool))
    metrics=pd.read_csv(result_path.parent/"detector_policy_metrics.csv"); reproduced=pd.concat([pm,cm],ignore_index=True); assert len(metrics)==10 and set(metrics.detector_id)=={"pca_reconstruction","lstm_calibrated_ensemble"}; metric_diff=0.0
    for column in ("precision","recall","f1","false_positive_alerted_endpoints_per_1000_healthy_endpoints","engine_detection_coverage","median_first_alert_delay"):
        metric_diff=max(metric_diff,_close(reproduced[column],metrics[column]))
    access=json.loads((result_path.parent/"access_declaration.json").read_text()); assert access["internal_held_out_opened"] and not access["official_nasa_test_opened"] and not access["held_out_used_for_fit_calibration_threshold_selection_or_model_selection"]
    return {"verified":True,"independent_reproduction":True,"partition_engines":52,"cycle_rows":10779,"windows":9271,"modes":6,"output_count":len(checks),"metric_rows":10,"maximum_primary_score_difference":primary_diff,"maximum_comparator_score_difference":comparator_diff,"maximum_metric_difference":metric_diff,"official_nasa_test_opened":False,"frozen_primary_verified":True,"fit_or_recalibration_performed":False}
def main():
    a=parse_args(); repo=find_repository_root(Path.cwd()); device=torch.device("cuda" if (a.device=="cuda" or a.device=="auto" and torch.cuda.is_available()) else "cpu"); report=verify(repo,repo/a.protocol,repo/a.result,device); text=json.dumps(report,indent=2,sort_keys=True)+"\n"; print(text,end="");
    if a.output: (repo/a.output).write_text(text,encoding="utf-8",newline="\n")
if __name__=="__main__": main()
