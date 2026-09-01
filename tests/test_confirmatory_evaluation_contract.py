import json
from pathlib import Path
import pandas as pd
import pytest
from turbofan_anomaly.data.metadata import create_window_metadata,assign_endpoint_operating_modes
from turbofan_anomaly.workflows.run_confirmatory_evaluation import validate_execution_protocol

ROOT=Path(__file__).resolve().parents[1]
def test_registered_contract_is_frozen(): validate_execution_protocol(json.loads((ROOT/'configs/evaluation/fd002-confirmatory-execution-protocol-v1.json').read_text()))
def test_endpoint_context_uses_final_cycle_mode():
    f=pd.DataFrame({'engine':[1]*31,'cycle':range(1,32),'op_mode':[0]*30+[5]}); m=create_window_metadata(f,split='internal_held_out',manifest_id='fd002-primary-v1',source_dataset_sha256='a'*64,window_size=30); c=assign_endpoint_operating_modes(m,f); assert c.op_mode.tolist()==[0,5]
def test_protocol_rejects_engine_membership_drift():
    p=json.loads((ROOT/'configs/evaluation/fd002-confirmatory-execution-protocol-v1.json').read_text()); p['partition']['engine_ids']=p['partition']['engine_ids'][:-1]
    with pytest.raises(RuntimeError): validate_execution_protocol(p)
def test_protocol_forbids_official_and_fusion():
    p=json.loads((ROOT/'configs/evaluation/fd002-confirmatory-execution-protocol-v1.json').read_text()); assert p['access_boundary']['official_nasa_test_access_authorized'] is False; assert p['comparator']['fusion_allowed'] is False
