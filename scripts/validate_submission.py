"""Validate the reproducible VGTREE OpenAI submission source package."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SUBMISSION = ROOT / "submission"
PLUGIN = ROOT / "plugins" / "vgtree"


def load_object(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path.name} must contain a JSON object")
    return value


def nonempty(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


def validate() -> dict[str, Any]:
    listing = load_object(SUBMISSION / "openai-listing-v1.1.0.json")
    tests = load_object(SUBMISSION / "openai-test-cases-v1.1.0.json")
    manifest = load_object(PLUGIN / ".codex-plugin" / "plugin.json")
    issues: list[str] = []

    expected_listing = {
        "submission_type": "skills-only",
        "name": "VGTREE",
        "category": "Productivity",
        "short_description": "Branch complex work into verifiable outcomes.",
        "website": "https://scandium1102.github.io/vgtree/",
        "support": "https://github.com/scandium1102/vgtree/issues",
        "privacy": "https://scandium1102.github.io/vgtree/privacy/",
        "terms": "https://scandium1102.github.io/vgtree/terms/",
        "availability": "ALL_PORTAL_AVAILABLE",
        "has_mcp": False,
        "has_ui": False,
        "requires_account": False,
        "has_telemetry": False,
        "screenshots": [],
    }
    for field, expected in expected_listing.items():
        if listing.get(field) != expected:
            issues.append(f"listing.{field} must equal {expected!r}")
    identity = listing.get("developer_identity")
    if not isinstance(identity, dict) or identity.get("mode") != "individual":
        issues.append("listing.developer_identity must use individual mode")
    if not isinstance(identity, dict) or identity.get("status") != "PENDING_USER_VERIFICATION":
        issues.append("identity status must remain PENDING_USER_VERIFICATION until live readback")
    if not nonempty(listing.get("long_description")):
        issues.append("listing.long_description is required")
    if not nonempty(listing.get("release_notes")):
        issues.append("listing.release_notes is required")

    prompts = listing.get("starter_prompts")
    expected_prompt_ids = {
        "capability-map",
        "wide-pass-execution",
        "receipt-verification",
        "obsidian-read-only-audit",
        "uid-first-knowledge-architecture",
    }
    if not isinstance(prompts, list) or len(prompts) != 5:
        issues.append("exactly five starter prompts are required")
    else:
        prompt_ids = {item.get("id") for item in prompts if isinstance(item, dict)}
        if prompt_ids != expected_prompt_ids:
            issues.append("starter prompt ids do not match the approved set")
        if not all(isinstance(item, dict) and nonempty(item.get("prompt")) for item in prompts):
            issues.append("every starter prompt needs prompt text")

    cases = tests.get("cases")
    positives: list[dict[str, Any]] = []
    negatives: list[dict[str, Any]] = []
    if not isinstance(cases, list):
        issues.append("test cases must be an array")
    else:
        positives = [item for item in cases if isinstance(item, dict) and item.get("polarity") == "positive"]
        negatives = [item for item in cases if isinstance(item, dict) and item.get("polarity") == "negative"]
        ids = [item.get("id") for item in cases if isinstance(item, dict)]
        if len(ids) != len(set(ids)):
            issues.append("test case ids must be unique")
    if len(positives) != 5:
        issues.append("exactly five positive test cases are required")
    if len(negatives) != 3:
        issues.append("exactly three negative test cases are required")
    for case in positives:
        for field in ("id", "user_prompt", "expected_behavior", "expected_result_shape", "fixture"):
            if not case.get(field):
                issues.append(f"positive case {case.get('id')!r} needs {field}")
    for case in negatives:
        for field in ("id", "user_prompt", "expected_safe_fallback", "why_not_complete", "fixture"):
            if not case.get(field):
                issues.append(f"negative case {case.get('id')!r} needs {field}")

    skill_files = sorted((PLUGIN / "skills").glob("*/SKILL.md"))
    if len(skill_files) != 6:
        issues.append("plugin must contain exactly six Skills")
    for skill_file in skill_files:
        text = skill_file.read_text(encoding="utf-8")
        for phrase in ("ENGINE", "SKILL_ONLY", "engine_validation=NOT_RUN", "REVIEW_REQUIRED"):
            if phrase not in text:
                issues.append(f"{skill_file.parent.name} is missing {phrase}")
    if "mcpServers" in manifest or "apps" in manifest:
        issues.append("Skills-only manifest cannot declare MCP servers or apps")
    if manifest.get("version") != listing.get("product_version"):
        issues.append("manifest and listing versions must match")
    interface = manifest.get("interface")
    if not isinstance(interface, dict):
        issues.append("manifest.interface must be an object")
    else:
        if interface.get("shortDescription") != listing.get("short_description"):
            issues.append("manifest and listing short descriptions must match")
        if interface.get("longDescription") != listing.get("long_description"):
            issues.append("manifest and listing long descriptions must match")
        expected_prompts = (
            [item.get("prompt") for item in prompts if isinstance(item, dict)]
            if isinstance(prompts, list)
            else []
        )
        if interface.get("defaultPrompt") != expected_prompts:
            issues.append("manifest default prompts must match the approved starter prompts")
    bundle = listing.get("bundle")
    if not isinstance(bundle, dict) or bundle.get("filename") != "vgtree-plugin-1.1.0.zip":
        issues.append("listing must name the exact plugin bundle")
    if not isinstance(bundle, dict) or bundle.get("digest_source") != "SHA256SUMS":
        issues.append("listing must bind the upload to SHA256SUMS")

    return {
        "status": "PASS" if not issues else "FAIL",
        "issues": issues,
        "starter_prompts": len(prompts) if isinstance(prompts, list) else 0,
        "positive_cases": len(positives),
        "negative_cases": len(negatives),
        "skills": len(skill_files),
        "identity_status": identity.get("status") if isinstance(identity, dict) else None,
    }


def main() -> int:
    try:
        result = validate()
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as exc:
        result = {"status": "FAIL", "issues": [f"{type(exc).__name__}: {exc}"]}
    json.dump(result, sys.stdout, ensure_ascii=False, sort_keys=True)
    sys.stdout.write("\n")
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
