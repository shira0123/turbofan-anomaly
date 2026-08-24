"""Portable repository paths and evidence-preserving SHA-256 verification.

Registered historical JSON files contain both POSIX separators and Windows
backslashes.  Callers normalize those separators only while resolving a path;
the registered file bytes themselves are never rewritten.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
from pathlib import Path, PurePosixPath
import re


_SHA256_PATTERN = re.compile(r"[0-9a-fA-F]{64}\Z")
_WINDOWS_DRIVE_PATTERN = re.compile(r"^[A-Za-z]:")


class RegisteredHashMismatch(ValueError):
    """Raised when no permitted byte representation matches a registered hash."""


@dataclass(frozen=True)
class HashVerification:
    """Successful registered-hash verification and the representation matched."""

    path: Path
    expected_sha256: str
    observed_raw_sha256: str
    match_form: str


def sha256_file(path: Path) -> str:
    """Return the SHA-256 digest of the exact on-disk bytes at ``path``."""
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def canonical_repo_relative(path_value: str | Path) -> str:
    """Return a canonical POSIX repository-relative path.

    Historical backslashes are accepted as separators. Absolute paths, drive
    paths, UNC paths, and any parent traversal are rejected.
    """
    value = str(path_value)
    if not value or "\x00" in value:
        raise ValueError("Repository-relative path may not be empty or contain NUL")
    normalized = value.replace("\\", "/")
    if normalized.startswith("/") or _WINDOWS_DRIVE_PATTERN.match(normalized):
        raise ValueError(f"Absolute paths are not permitted: {path_value!s}")
    pure = PurePosixPath(normalized)
    if pure.is_absolute() or ".." in pure.parts:
        raise ValueError(f"Parent traversal is not permitted: {path_value!s}")
    parts = tuple(part for part in pure.parts if part not in {"", "."})
    if not parts:
        raise ValueError("Repository-relative path must name an artifact")
    return PurePosixPath(*parts).as_posix()


def resolve_repo_path(path_value: str | Path, repo_root: Path) -> Path:
    """Resolve a serialized repository path without allowing root escape."""
    root = Path(repo_root).resolve()
    canonical = canonical_repo_relative(path_value)
    candidate = (root / Path(*PurePosixPath(canonical).parts)).resolve()
    try:
        candidate.relative_to(root)
    except ValueError as error:
        raise ValueError(f"Resolved path escapes repository root: {path_value!s}") from error
    return candidate


def repo_relative_posix(path: Path, repo_root: Path) -> str:
    """Serialize an existing or planned repository path with POSIX separators."""
    root = Path(repo_root).resolve()
    candidate = Path(path)
    if not candidate.is_absolute():
        candidate = root / candidate
    candidate = candidate.resolve()
    try:
        relative = candidate.relative_to(root)
    except ValueError as error:
        raise ValueError(f"Path lies outside repository root: {path}") from error
    return canonical_repo_relative(relative.as_posix())


def find_repository_root(start: Path | None = None) -> Path:
    """Find the nearest parent containing this project's ``pyproject.toml``."""
    candidate = Path.cwd() if start is None else Path(start)
    candidate = candidate.resolve()
    if candidate.is_file():
        candidate = candidate.parent
    for parent in (candidate, *candidate.parents):
        if (parent / "pyproject.toml").is_file():
            return parent
    raise FileNotFoundError(f"Could not locate repository root from {candidate}")


def _permitted_hash_forms(raw: bytes) -> dict[str, str]:
    forms = {"raw": hashlib.sha256(raw).hexdigest()}
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        return forms
    if "\x00" in text:
        return forms
    without_crlf = text.replace("\r\n", "")
    if "\r" in without_crlf:
        return forms
    lf_text = text.replace("\r\n", "\n")
    crlf_text = lf_text.replace("\n", "\r\n")
    forms["lf"] = hashlib.sha256(lf_text.encode("utf-8")).hexdigest()
    forms["crlf"] = hashlib.sha256(crlf_text.encode("utf-8")).hexdigest()
    return forms


def verify_registered_hash(path: Path, expected_sha256: str) -> HashVerification:
    """Verify exact bytes or their LF/CRLF-only text equivalent.

    No whitespace, encoding, JSON, CSV, or Unicode canonicalization is allowed.
    The returned ``match_form`` is ``raw``, ``lf``, or ``crlf``.
    """
    expected = str(expected_sha256).lower()
    if not _SHA256_PATTERN.fullmatch(expected):
        raise ValueError("expected_sha256 must be a 64-character hexadecimal digest")
    artifact = Path(path)
    raw = artifact.read_bytes()
    forms = _permitted_hash_forms(raw)
    for match_form in ("raw", "lf", "crlf"):
        if forms.get(match_form) == expected:
            return HashVerification(
                path=artifact,
                expected_sha256=expected,
                observed_raw_sha256=forms["raw"],
                match_form=match_form,
            )
    candidates = ", ".join(f"{name}={digest}" for name, digest in forms.items())
    raise RegisteredHashMismatch(
        f"Registered SHA-256 mismatch for {artifact}: expected={expected}; {candidates}"
    )
