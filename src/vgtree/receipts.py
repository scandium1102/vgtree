"""Tool Receipt validation, contained loading, and compact evidence binding."""

from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime
from importlib.resources import files
from pathlib import Path
from typing import Any, Iterable

from jsonschema import Draft202012Validator

from vgtree.models import GuardResult, ValidationIssue, ValidationReport
from vgtree.validation import FORMAT_CHECKER, validate_evidence


MAX_RECEIPT_BYTES = 4 * 1024 * 1024
SHA256_PATTERN = re.compile(r"sha256:[0-9a-f]{64}")
RECEIPT_SCHEMA = json.loads(
    files("vgtree").joinpath("schemas", "receipt.schema.json").read_text(encoding="utf-8")
)
RECEIPT_VALIDATOR = Draft202012Validator(
    RECEIPT_SCHEMA, format_checker=FORMAT_CHECKER
)


def _json_path(parts: Iterable[Any]) -> str:
    rendered = "$"
    for part in parts:
        rendered += f"[{part}]" if isinstance(part, int) else f".{part}"
    return rendered


def validate_receipt(value: object) -> ValidationReport:
    """Validate receipt structure and time/proof semantics."""

    issues = [
        ValidationIssue("SCHEMA_INVALID", _json_path(error.absolute_path), error.message)
        for error in sorted(
            RECEIPT_VALIDATOR.iter_errors(value),
            key=lambda item: list(item.absolute_path),
        )
    ]
    if isinstance(value, dict) and not issues:
        started = _parse_time(value["started_at"])
        ended = _parse_time(value["ended_at"])
        if ended < started:
            issues.append(
                ValidationIssue(
                    "RECEIPT_TIME_REVERSED",
                    "$.ended_at",
                    "ended_at cannot precede started_at.",
                )
            )
        if value["status"] == "PASS" and not _has_bound_proof(value):
            issues.append(
                ValidationIssue(
                    "RECEIPT_PASS_PROOF_REQUIRED",
                    "$",
                    "A passing receipt requires a bound artifact or validation.",
                )
            )
    return ValidationReport("PASS" if not issues else "FAIL", tuple(issues))


def _parse_time(value: str) -> datetime:
    return datetime.fromisoformat(value[:-1] + "+00:00" if value.endswith("Z") else value)


def _has_bound_proof(receipt: dict[str, Any]) -> bool:
    for field in ("artifacts", "validations"):
        for item in receipt[field]:
            if isinstance(item, dict) and (
                isinstance(item.get("reference"), str)
                and bool(item["reference"].strip())
                or isinstance(item.get("digest"), str)
                and SHA256_PATTERN.fullmatch(item["digest"]) is not None
            ):
                return True
    return False


def load_receipt(
    root: str | Path,
    receipt: str | Path,
    *,
    max_bytes: int = MAX_RECEIPT_BYTES,
) -> tuple[dict[str, Any], str, str] | GuardResult:
    """Load one validated regular file contained below an explicit root."""

    root_path = Path(root)
    try:
        root_resolved = root_path.resolve(strict=True)
    except FileNotFoundError:
        return GuardResult("FAIL", "RECEIPT_ROOT_NOT_FOUND", "Receipt root was not found.")
    except OSError:
        return GuardResult("FAIL", "RECEIPT_PATH_UNSAFE", "Receipt root is unsafe.")
    if not root_resolved.is_dir():
        return GuardResult("FAIL", "RECEIPT_PATH_UNSAFE", "Receipt root must be a directory.")

    receipt_path = Path(receipt)
    reference = str(receipt_path)
    candidate = receipt_path if receipt_path.is_absolute() else root_resolved / receipt_path
    try:
        lexical = candidate.absolute()
        if lexical.is_symlink() or _path_has_links(lexical, root_resolved):
            return GuardResult("FAIL", "RECEIPT_PATH_UNSAFE", "Receipt links are not allowed.")
        resolved = lexical.resolve(strict=True)
    except FileNotFoundError:
        return GuardResult("FAIL", "RECEIPT_NOT_FOUND", "Receipt file was not found.")
    except OSError:
        return GuardResult("FAIL", "RECEIPT_PATH_UNSAFE", "Receipt path is unsafe.")
    if not _is_within(resolved, root_resolved) or not resolved.is_file():
        return GuardResult(
            "FAIL", "RECEIPT_PATH_UNSAFE", "Receipt must be a regular file inside its root."
        )
    try:
        if resolved.stat().st_size > max_bytes:
            return GuardResult("FAIL", "RECEIPT_TOO_LARGE", "Receipt exceeds 4 MiB.")
        raw = resolved.read_bytes()
    except OSError:
        return GuardResult("FAIL", "RECEIPT_READ_FAILED", "Receipt could not be read.")
    if len(raw) > max_bytes:
        return GuardResult("FAIL", "RECEIPT_TOO_LARGE", "Receipt exceeds 4 MiB.")
    digest = "sha256:" + hashlib.sha256(raw).hexdigest()
    try:
        decoded = raw.decode("utf-8")
    except UnicodeDecodeError:
        return GuardResult("FAIL", "RECEIPT_ENCODING_INVALID", "Receipt must be UTF-8.")
    try:
        value = json.loads(decoded)
    except json.JSONDecodeError:
        return GuardResult("FAIL", "RECEIPT_JSON_INVALID", "Receipt is not valid JSON.")
    report = validate_receipt(value)
    if not report.valid:
        return GuardResult(
            "FAIL",
            "RECEIPT_INVALID",
            "Receipt failed validation.",
            {"validation": report.as_dict()},
        )
    assert isinstance(value, dict)
    return value, digest, reference


def _path_has_links(candidate: Path, root: Path) -> bool:
    try:
        relative = candidate.relative_to(root)
    except ValueError:
        return False
    current = root
    for part in relative.parts:
        current = current / part
        if current.is_symlink():
            return True
    return False


def _is_within(candidate: Path, root: Path) -> bool:
    return candidate == root or root in candidate.parents


def receipt_to_evidence(
    receipt: dict[str, Any], reference: str, file_digest: str
) -> GuardResult:
    """Bind validated receipt bytes into the existing compact evidence shape."""

    report = validate_receipt(receipt)
    if not report.valid:
        return GuardResult(
            "FAIL",
            "RECEIPT_INVALID",
            "Receipt failed validation.",
            {"validation": report.as_dict()},
        )
    if not SHA256_PATTERN.fullmatch(file_digest):
        return GuardResult("FAIL", "RECEIPT_DIGEST_INVALID", "Receipt digest is invalid.")
    if not reference.strip():
        return GuardResult(
            "FAIL", "RECEIPT_REFERENCE_REQUIRED", "Receipt reference is required."
        )
    evidence = {
        "id": receipt["receipt_id"],
        "type": receipt["evidence_type"],
        "subject": receipt["subject"],
        "method": receipt["evidence_method"],
        "timestamp": receipt["ended_at"],
        "outcome": receipt["status"],
        "digest": file_digest,
        "reference": reference,
    }
    evidence_report = validate_evidence(evidence)
    if not evidence_report.valid:
        return GuardResult(
            "FAIL",
            "RECEIPT_EVIDENCE_INVALID",
            "Receipt could not produce valid compact evidence.",
            {"validation": evidence_report.as_dict()},
        )
    return GuardResult(
        "PASS",
        "RECEIPT_EVIDENCE_CREATED",
        "Receipt was bound to compact evidence.",
        {"evidence": evidence},
    )
