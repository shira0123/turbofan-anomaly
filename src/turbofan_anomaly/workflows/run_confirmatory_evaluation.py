"""Execute the frozen FD002 internal held-out confirmatory evaluation once."""
from __future__ import annotations

import argparse, hashlib, json, os, platform, subprocess
from pathlib import Path
from typing import Any

os.environ.setdefault("CUBLAS_WORKSPACE_CONFIG", ":4096:8")
import joblib
import numpy as np
import pandas as pd
import torch
from sklearn.metrics import average_precision_score, roc_auc_score

from turbofan_anomaly.alerting.persistence import apply_alert_policy
from turbofan_anomaly.alerting.thresholds import FittedThresholds
from turbofan_anomaly.data.io import FD002_COLUMNS, load_fd002, validate_fd002_frame
from turbofan_anomaly.data.metadata import create_window_metadata, assign_endpoint_operating_modes
from turbofan_anomaly.data.preprocessing import load_preprocessor
from turbofan_anomaly.data.windows import build_window_array, summary_features
from turbofan_anomaly.evaluation.alerts import evaluate_alert_policy
from turbofan_anomaly.evaluation.provenance import find_repository_root, sha256_file
from turbofan_anomaly.evaluation.proxies import registered_validation_policies
from turbofan_anomaly.models.classical import load_baseline_artifact
from turbofan_anomaly.models.lstm_training import load_lstm_artifact, reconstruction_errors

DEFAULT_PROTOCOL=Path("configs/evaluation/fd002-confirmatory-execution-protocol-v1.json")

def parse_args()->argparse.Namespace:
    p=argparse.ArgumentParser(description=__doc__); p.add_argument("--protocol",type=Path,default=DEFAULT_PROTOCOL); p.add_argument("--device",choices=("auto","cpu","cuda"),default="auto"); return p.parse_args()

def _json(path:Path)->dict[str,Any]: return json.loads(path.read_text(encoding="utf-8"))
def _hash(path:Path)->str: return sha256_file(path)
def _write_json(path:Path,value:Any)->None: path.parent.mkdir(parents=True,exist_ok=True); path.write_text(json.dumps(value,indent=2,sort_keys=True,allow_nan=False)+"\n",encoding="utf-8",newline="\n")
def _write_csv(path:Path,frame:pd.DataFrame)->None: path.parent.mkdir(parents=True,exist_ok=True); frame.to_csv(path,index=False,lineterminator="\n")
def _require(x:bool,msg:str)->None:
    if not x: raise RuntimeError(msg)
def _device(name:str)->torch.device:
    if name=="cuda" and not torch.cuda.is_available(): raise RuntimeError("CUDA requested but unavailable")
    return torch.device("cuda" if (name=="cuda" or name=="auto" and torch.cuda.is_available()) else "cpu")
def validate_execution_protocol(p:dict[str,Any])->None:
    _require(p["status"]=="registered_before_internal_held_out_access","protocol lifecycle changed")
    q=p["partition"]; _require(len(q["engine_ids"])==52==len(set(q["engine_ids"])),"52 unique engines required"); _require(q["expected_cycle_rows"]==10779 and q["expected_windows"]==9271,"registered counts changed")
    _require(p["primary"]["candidate_id"]=="pca_reconstruction__per_mode__quantile_0.995__ewma_alpha_0.20__persistence_8","primary changed")
    _require(p["comparator"]["fusion_allowed"] is False and p["access_boundary"]["official_nasa_test_access_authorized"] is False,"boundary changed")
def _thresholds(spec:dict[str,Any])->FittedThresholds:
    vals={int(k):float(v) for k,v in spec["thresholds"].items()}; return FittedThresholds("per_mode","quantile_0.995",vals,{k:1 for k in vals})
def _score_frame(meta:pd.DataFrame,detector:str,scores:np.ndarray,raw:np.ndarray|None)->pd.DataFrame:
    f=meta[["window_id","engine","start_cycle","end_cycle","max_cycle","op_mode"]].copy(); f["raw_score"]=np.nan if raw is None else raw; f["alert_score"]=scores; f["detector_id"]=detector; f["pipeline_id"]="p1_k6"; f["split"]="internal_held_out"; return f
def evaluate_detector(frame:pd.DataFrame,meta:pd.DataFrame,spec:dict[str,Any])->tuple[pd.DataFrame,pd.DataFrame,pd.DataFrame,pd.DataFrame]:
    trace=apply_alert_policy(frame,_thresholds(spec),ewma_alpha=float(spec["ewma_alpha"]),persistence=int(spec["persistence"])); metrics=[]; engines=[]; events=[]; ranks=[]
    for policy in registered_validation_policies():
        pf=policy.apply(meta); m,e,v=evaluate_alert_policy(trace,pf); m["detector_id"]=frame["detector_id"].iloc[0]; m["endpoint_false_alert_rate_percent"]=m["false_positive_alerted_endpoints_per_1000_healthy_endpoints"]/10.0; metrics.append(m); e.insert(0,"detector_id",m["detector_id"]); engines.append(e)
        if not v.empty: v.insert(0,"detector_id",m["detector_id"]); events.append(v)
        inc=pf["proxy_label"].notna(); y=pf.loc[inc,"proxy_label"].astype(int); s=frame.set_index("window_id").loc[pf.loc[inc,"window_id"],"alert_score"]; ranks.append({"detector_id":m["detector_id"],"policy_id":policy.policy_id,"pr_auc":float(average_precision_score(y,s)),"roc_auc":float(roc_auc_score(y,s)),"evaluated_endpoints":int(inc.sum())})
    return trace,pd.DataFrame(metrics),pd.concat(engines,ignore_index=True),pd.concat(events,ignore_index=True) if events else pd.DataFrame(),pd.DataFrame(ranks)
def run(repo:Path,protocol_path:Path,device:torch.device)->dict[str,Any]:
    p=_json(protocol_path); validate_execution_protocol(p)
    for section,pathkey,hashkey in ((p["authority"],"final_evaluation_protocol_path","final_evaluation_protocol_sha256"),(p["authority"],"readiness_path","readiness_sha256"),(p["authority"],"split_manifest_path","split_manifest_sha256"),(p["partition"],"source_path","source_sha256"),(p["preprocessing"],"artifact_path","artifact_sha256"),(p["primary"],"model_path","model_sha256"),(p["comparator"],"bundle_path","bundle_sha256")):
        _require(_hash(repo/section[pathkey])==section[hashkey],f"hash mismatch: {section[pathkey]}")
    for path,h in zip(p["comparator"]["model_paths"],p["comparator"]["model_sha256"]): _require(_hash(repo/path)==h,f"hash mismatch: {path}")
    manifest=_json(repo/p["authority"]["split_manifest_path"]); ids=set(map(int,p["partition"]["engine_ids"])); trainval={int(x["engine"]) for x in manifest["engines"] if x["split"] in {"train","validation"}}; _require(not ids&trainval,"partition overlap")
    source=load_fd002(repo/p["partition"]["source_path"]); held=source[source.engine.astype(int).isin(ids)].sort_values(["engine","cycle"],kind="stable").reset_index(drop=True); del source
    _require(list(held.columns)==FD002_COLUMNS and held.shape==(10779,26),"held-out schema/count mismatch"); _require(set(held.engine.astype(int))==ids,"membership mismatch"); validate_fd002_frame(held); _require(np.isfinite(held.to_numpy(float)).all(),"non-finite input")
    pre_path=repo/p["preprocessing"]["artifact_path"]; pre_before=_hash(pre_path); pre,pre_meta=load_preprocessor(pre_path,expected_split_manifest_id="fd002-primary-v1"); transformed=pre.transform(held); _require(_hash(pre_path)==pre_before,"preprocessor changed"); _require(set(transformed.op_mode.astype(int))==set(range(6)),"six modes required")
    meta=create_window_metadata(held,split="internal_held_out",manifest_id="fd002-primary-v1",source_dataset_sha256=p["partition"]["source_sha256"],window_size=30); context=assign_endpoint_operating_modes(meta,transformed); seq=build_window_array(transformed,context); _require(seq.shape==(9271,30,21),"sequence shape mismatch")
    local=repo/p["local_derived_artifacts"]["directory"]; local.mkdir(parents=True,exist_ok=True); _write_csv(repo/p["local_derived_artifacts"]["cycle_frame"],transformed); _write_csv(repo/p["local_derived_artifacts"]["window_metadata"],meta); _write_csv(repo/p["local_derived_artifacts"]["window_context"],context); np.save(repo/p["local_derived_artifacts"]["sequences"],seq,allow_pickle=False)
    model,_=load_baseline_artifact(repo/p["primary"]["model_path"],expected_split_manifest_id="fd002-primary-v1",expected_preprocessing_decision_id="fd002-preprocessing-selection-v1"); raw,cal=model.score(summary_features(seq)); primary=_score_frame(context,"pca_reconstruction",cal,raw)
    seed_scores=[]
    for path in p["comparator"]["model_paths"]:
        lm,ref,_=load_lstm_artifact(repo/path,expected_split_manifest_id="fd002-primary-v1",expected_preprocessing_decision_id="fd002-preprocessing-selection-v1"); rr=reconstruction_errors(lm.to(device),seq,batch_size=128,device=device); seed_scores.append(np.searchsorted(ref,rr,side="right")/len(ref))
    comparator=_score_frame(context,"lstm_calibrated_ensemble",np.mean(seed_scores,axis=0),None)
    pt,pm,pe,pv,pr=evaluate_detector(primary,context,p["primary"]); ct,cm,ce,cv,cr=evaluate_detector(comparator,context,p["comparator"]); report=repo/p["reports"]["directory"]; report.mkdir(parents=True,exist_ok=True)
    outputs={"primary_score_alert_trace.csv":pt,"comparator_score_alert_trace.csv":ct,"detector_policy_metrics.csv":pd.concat([pm,cm],ignore_index=True),"per_engine_metrics.csv":pd.concat([pe,ce],ignore_index=True),"alert_events.csv":pd.concat([pv,cv],ignore_index=True),"ranking_metrics.csv":pd.concat([pr,cr],ignore_index=True)}
    _write_csv(report/"partition_summary.csv",pd.DataFrame([{"engines":52,"cycle_rows":10779,"columns":26,"windows":9271,"modes":6}]))
    for name,frame in outputs.items(): _write_csv(report/name,frame)
    targets=outputs["detector_policy_metrics.csv"].copy(); targets["endpoint_far_target_met"]=targets.endpoint_false_alert_rate_percent<6.0; targets["delay_aspiration_met"]=targets.median_first_alert_delay<=12; _write_csv(report/"target_attainment.csv",targets)
    access={"raw_source_opened_for_confirmatory_partitioning":True,"internal_held_out_opened":True,"official_nasa_test_opened":False,"held_out_used_for_fit_calibration_threshold_selection_or_model_selection":False,"confirmatory_evaluation_executed":True}; _write_json(report/"access_declaration.json",access)
    authority={"protocol_sha256":_hash(protocol_path),"preprocessor_sha256":pre_before,"raw_source_sha256":p["partition"]["source_sha256"],"pca_sha256":p["primary"]["model_sha256"],"held_out_cycle_frame_sha256":_hash(repo/p["local_derived_artifacts"]["cycle_frame"]),"sequences_sha256":_hash(repo/p["local_derived_artifacts"]["sequences"]),"window_context_sha256":_hash(repo/p["local_derived_artifacts"]["window_context"])}; _write_json(report/"authority_input_manifest.json",authority)
    _write_json(report/"runtime_provenance.json",{"python":platform.python_version(),"numpy":np.__version__,"pandas":pd.__version__,"torch":torch.__version__,"device":str(device),"cuda_available":torch.cuda.is_available(),"git_head":subprocess.check_output(["git","rev-parse","HEAD"],cwd=repo,text=True).strip(),"new_research_experiment":False})
    summary={"status":"complete_first_valid_run","primary_candidate_id":p["primary"]["candidate_id"],"comparator_role":p["comparator"]["role"],"partition":{ "engines":52,"rows":10779,"windows":9271},"access":access}; _write_json(report/"summary.json",summary)
    names=["partition_summary.csv",*outputs.keys(),"target_attainment.csv","authority_input_manifest.json","runtime_provenance.json","access_declaration.json","summary.json"]; manifest_rows=[{"path":str((report/n).relative_to(repo)).replace('\\','/'),"sha256":_hash(report/n),"size_bytes":(report/n).stat().st_size} for n in names]; _write_csv(report/"artifact_manifest.csv",pd.DataFrame(manifest_rows)); names.append("artifact_manifest.csv")
    result={"schema_version":"1.0.0","protocol_id":p["protocol_id"],"protocol_sha256":_hash(protocol_path),"status":"complete_first_valid_run","primary_candidate_id":p["primary"]["candidate_id"],"threshold_refit":False,"model_refit":False,"calibration_refit":False,"online_recalibration":False,"score_or_decision_fusion":False,"official_nasa_test_accessed":False,"outputs":[{"path":str((report/n).relative_to(repo)).replace('\\','/'),"sha256":_hash(report/n)} for n in names]}; _write_json(report/"result.json",result); print(json.dumps(summary,indent=2)); return result
def main()->None:
    a=parse_args(); repo=find_repository_root(Path.cwd()); run(repo,repo/a.protocol,_device(a.device))
if __name__=="__main__": main()
