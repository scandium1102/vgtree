from __future__ import annotations

import copy
import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from vgtree.models import GuardResult
from vgtree.receipts import (
    MAX_RECEIPT_BYTES,
    load_receipt,
    receipt_to_evidence,
    validate_receipt,
)
from vgtree.validation import validate_evidence


def valid_receipt() -> dict:
    return {
        "receipt_version": "1.0",
        "receipt_id": "receipt-build-001",
        "task_id": "release-example",
        "branch_id": "build",
        "tool": {"name": "unittest", "version": "3.11", "invocation_kind": "CLI"},
        "subject": "integrated source at commit abc1234",
        "evidence_type": "branch-validation",
        "evidence_method": "full test suite",
        "status": "PASS",
        "artifacts": [
            {
                "subject": "test report",
                "reference": "artifacts/test-report.json",
                "digest": "sha256:" + ("0" * 64),
            }
        ],
        "validations": [
            {
                "name": "full test suite",
                "method": "python -m unittest discover -s tests -v",
                "outcome": "PASS",
                "reference": "artifacts/test-report.json",
            }
        ],
        "started_at": "2026-08-20T10:00:00Z",
        "ended_at": "2026-08-20T10:02:00Z",
        "notes": "Fresh run against the exact integrated subject",
    }


class ReceiptValidationTests(unittest.TestCase):
    def test_valid_receipt_passes(self) -> None:
        report = validate_receipt(valid_receipt())
        self.assertTrue(report.valid, report.issues)

    def test_unknown_property_is_rejected(self) -> None:
        value = valid_receipt()
        value["trust_me"] = True
        self.assertFalse(validate_receipt(value).valid)

    def test_end_cannot_precede_start(self) -> None:
        value = valid_receipt()
        value["ended_at"] = "2026-08-20T09:59:59Z"
        codes = {item.code for item in validate_receipt(value).issues}
        self.assertIn("RECEIPT_TIME_REVERSED", codes)

    def test_pass_requires_bound_artifact_or_validation(self) -> None:
        value = valid_receipt()
        value["artifacts"] = []
        value["validations"] = []
        codes = {item.code for item in validate_receipt(value).issues}
        self.assertIn("RECEIPT_PASS_PROOF_REQUIRED", codes)

    def test_input_digest_must_be_sha256(self) -> None:
        value = valid_receipt()
        value["input_digest"] = "md5:unsafe"
        self.assertFalse(validate_receipt(value).valid)


class ReceiptFileTests(unittest.TestCase):
    def test_load_receipt_hashes_exact_bytes(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "receipts"
            root.mkdir()
            path = root / "receipt.json"
            raw = json.dumps(valid_receipt(), ensure_ascii=False).encode("utf-8")
            path.write_bytes(raw)
            loaded = load_receipt(root, path)
            self.assertIsInstance(loaded, tuple)
            value, digest, reference = loaded
            self.assertEqual(value["receipt_id"], "receipt-build-001")
            self.assertEqual(digest, "sha256:" + hashlib.sha256(raw).hexdigest())
            self.assertEqual(reference, str(path))

    def test_path_escape_is_blocked_without_reading_content(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            root = base / "receipts"
            root.mkdir()
            outside = base / "outside.json"
            outside.write_text("private bytes", encoding="utf-8")
            result = load_receipt(root, outside)
            self.assertIsInstance(result, GuardResult)
            self.assertEqual(result.code, "RECEIPT_PATH_UNSAFE")
            self.assertNotIn("private bytes", str(result.as_dict()))

    def test_direct_link_is_blocked(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "receipts"
            root.mkdir()
            candidate = root / "receipt.json"
            candidate.write_text("{}", encoding="utf-8")
            with patch("vgtree.receipts.Path.is_symlink", return_value=True):
                result = load_receipt(root, candidate)
            self.assertEqual(result.code, "RECEIPT_PATH_UNSAFE")

    def test_intermediate_link_is_blocked(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "receipts"
            nested = root / "nested"
            nested.mkdir(parents=True)
            candidate = nested / "receipt.json"
            candidate.write_text(json.dumps(valid_receipt()), encoding="utf-8")
            with patch("vgtree.receipts._path_has_links", return_value=True):
                result = load_receipt(root, candidate)
            self.assertEqual(result.code, "RECEIPT_PATH_UNSAFE")

    def test_oversized_receipt_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "receipts"
            root.mkdir()
            path = root / "receipt.json"
            path.write_bytes(b"x" * (MAX_RECEIPT_BYTES + 1))
            result = load_receipt(root, path)
            self.assertEqual(result.code, "RECEIPT_TOO_LARGE")


class ReceiptEvidenceTests(unittest.TestCase):
    def test_receipt_generates_existing_evidence_shape(self) -> None:
        digest = "sha256:" + ("4" * 64)
        result = receipt_to_evidence(
            valid_receipt(),
            reference=".vgtree/receipts/release-example/receipt-build-001.json",
            file_digest=digest,
        )
        self.assertEqual(result.status, "PASS", result)
        evidence = result.data["evidence"]
        self.assertEqual(evidence["id"], "receipt-build-001")
        self.assertEqual(evidence["type"], "branch-validation")
        self.assertEqual(evidence["method"], "full test suite")
        self.assertEqual(evidence["digest"], digest)
        self.assertTrue(validate_evidence(evidence).valid)

    def test_baseline_receipt_keeps_exact_method(self) -> None:
        value = copy.deepcopy(valid_receipt())
        value["evidence_type"] = "baseline"
        value["evidence_method"] = "Fresh skeleton inspection"
        value["subject"] = "branch:build:baseline"
        result = receipt_to_evidence(
            value,
            reference="release-example/baseline.json",
            file_digest="sha256:" + ("5" * 64),
        )
        self.assertEqual(result.data["evidence"]["method"], "Fresh skeleton inspection")

    def test_invalid_digest_is_rejected(self) -> None:
        result = receipt_to_evidence(
            valid_receipt(), reference="receipt.json", file_digest="bad"
        )
        self.assertEqual(result.code, "RECEIPT_DIGEST_INVALID")


if __name__ == "__main__":
    unittest.main()
