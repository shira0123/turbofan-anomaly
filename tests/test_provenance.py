from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

from turbofan_anomaly.evaluation.provenance import (
    RegisteredHashMismatch,
    canonical_repo_relative,
    repo_relative_posix,
    resolve_repo_path,
    verify_registered_hash,
)


def _digest(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def test_historical_backslashes_resolve_to_repo_relative_path(tmp_path: Path) -> None:
    expected = tmp_path / "reports" / "lstm_v2" / "run_summary.csv"
    assert resolve_repo_path(
        r"reports\lstm_v2\run_summary.csv", tmp_path
    ) == expected
    assert repo_relative_posix(expected, tmp_path) == (
        "reports/lstm_v2/run_summary.csv"
    )


@pytest.mark.parametrize(
    "unsafe",
    [
        "../secret.txt",
        "reports/../../secret.txt",
        "/absolute/file.txt",
        r"\server\share\file.txt",
        "C:/absolute/file.txt",
        r"C:\absolute\file.txt",
        "C:drive-relative.txt",
    ],
)
def test_path_policy_rejects_absolute_and_traversal(unsafe: str) -> None:
    with pytest.raises(ValueError):
        canonical_repo_relative(unsafe)


def test_registered_hash_reports_raw_lf_and_crlf_match_forms(tmp_path: Path) -> None:
    artifact = tmp_path / "evidence.csv"

    raw = b"a,b\n1,2\n"
    artifact.write_bytes(raw)
    assert verify_registered_hash(artifact, _digest(raw)).match_form == "raw"

    artifact.write_bytes(b"a,b\r\n1,2\r\n")
    assert verify_registered_hash(artifact, _digest(raw)).match_form == "lf"

    artifact.write_bytes(raw)
    crlf = b"a,b\r\n1,2\r\n"
    assert verify_registered_hash(artifact, _digest(crlf)).match_form == "crlf"


def test_registered_hash_permits_no_other_canonicalization(tmp_path: Path) -> None:
    artifact = tmp_path / "evidence.txt"
    artifact.write_bytes(b"value: 1 \n")
    with pytest.raises(RegisteredHashMismatch):
        verify_registered_hash(artifact, _digest(b"value: 1\n"))

    artifact.write_bytes(b"a\rb\n")
    with pytest.raises(RegisteredHashMismatch):
        verify_registered_hash(artifact, _digest(b"a\nb\n"))
