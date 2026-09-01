import pandas as pd
import pytest

from turbofan_anomaly.data.io import FD002_COLUMNS
from turbofan_anomaly.inference.pipeline import validate_cycle_input
from turbofan_anomaly.inference.visualization import DEMO_LABEL, render_timeline_svg


def _cycles(count=30):
    return pd.DataFrame([[1, cycle, 0.1, 0.2, 0.3, *range(21)] for cycle in range(1, count + 1)], columns=FD002_COLUMNS)


def test_cycle_input_rejects_aliases_unsorted_and_short_engines():
    with pytest.raises(ValueError, match="exact"):
        validate_cycle_input(_cycles().assign(alias=1))
    with pytest.raises(ValueError, match="sorted"):
        validate_cycle_input(_cycles().iloc[::-1].reset_index(drop=True))
    with pytest.raises(ValueError, match="at least"):
        validate_cycle_input(_cycles(29))


def test_svg_is_deterministic_and_labeled(tmp_path):
    timeline = pd.DataFrame({"end_cycle": [30, 31], "calibrated_score": [0.1, 0.2], "smoothed_score": [0.1, 0.15], "threshold": [0.18, 0.18], "alert": [False, True]})
    output = tmp_path / "timeline.svg"
    render_timeline_svg(timeline, output)
    content = output.read_text(encoding="utf-8")
    assert DEMO_LABEL in content and "#d62728" in content
