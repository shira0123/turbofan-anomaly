import pandas as pd

from src.api.main import AnomalyService


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
