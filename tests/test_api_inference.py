import pandas as pd
from fastapi.testclient import TestClient

from src.api.main import AnomalyService, app


def test_predict_window_returns_alert_payload():
    sample_df = pd.read_csv("data/splits/train.csv")
    window = sample_df.head(30).to_dict(orient="records")

    service = AnomalyService()
    result = service.predict_window(window)

    assert set(result.keys()) >= {"alert", "score", "threshold", "op_mode", "reconstruction_error", "explanation"}
    assert isinstance(result["alert"], bool)
    assert isinstance(result["op_mode"], int)
    assert result["score"] >= 0.0
    assert result["threshold"] >= 0.0
    assert isinstance(result["explanation"], dict)
    assert result["explanation"]["shap_top3"]
    assert result["explanation"]["sensor_top3"]


def test_predict_accepts_single_row_payload():
    sample_df = pd.read_csv("data/splits/train.csv")
    client = TestClient(app)
    response = client.post("/predict", json={"row": sample_df.iloc[0].to_dict()})

    assert response.status_code == 200
    payload = response.json()
    assert payload["alert"] in {True, False}
    assert payload["explanation"]["shap_top3"]
