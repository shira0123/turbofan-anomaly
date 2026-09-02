from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = ROOT / "configs/research/fd002-core-literature-extraction-protocol-v1.json"


def test_core_literature_protocol_is_preregistered_and_bounded():
    protocol = json.loads(PROTOCOL.read_text(encoding="utf-8"))
    selected = protocol["selected_core"]
    reserves = protocol["ordered_reserve"]
    assert protocol["status"] == "registered_before_new_full_text_numerical_extraction"
    assert 15 <= len(selected) <= 25
    assert len(selected) == 20
    assert [row["order"] for row in selected] == list(range(1, 21))
    assert [row["order"] for row in reserves] == list(range(1, len(reserves) + 1))
    selected_ids = {row["paper_id"] for row in selected}
    reserve_ids = {row["paper_id"] for row in reserves}
    assert len(selected_ids) == len(selected)
    assert selected_ids.isdisjoint(reserve_ids)
    assert protocol["scientific_boundary"]["official_nasa_test_access"] is False
    assert protocol["scientific_boundary"]["held_out_internal_test_access"] is False
    assert protocol["scientific_boundary"]["pdf_commit_permitted"] is False


def test_preregistered_literature_authorities_are_unchanged():
    protocol = json.loads(PROTOCOL.read_text(encoding="utf-8"))
    for reference in protocol["preserved_authorities"]:
        observed = hashlib.sha256((ROOT / reference["path"]).read_bytes()).hexdigest()
        assert observed == reference["sha256"]
