"""Validate VGTREE's no-install SKILL_ONLY fallback in an engine-free process."""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path


EXPECTED_SKILLS = {
    "building-obsidian-workspaces",
    "executing-tree-work",
    "governing-knowledge-architecture",
    "planning-tree-work",
    "using-vgtree",
    "verifying-tree-work",
}
REQUIRED_SHARED = {
    "references/obsidian-audit-checklist.md",
    "references/runtime-modes.md",
    "schemas/capability-map.schema.json",
    "schemas/receipt.schema.json",
    "schemas/state.schema.json",
    "schemas/task.schema.json",
    "templates/capability-map.json",
    "templates/receipt.json",
    "templates/skill-only-work-record.json",
}


def validate(plugin_root: Path, require_engine_absent: bool) -> dict[str, object]:
    root = plugin_root.resolve(strict=True)
    issues: list[str] = []
    for path in root.rglob("*"):
        if path.is_symlink():
            issues.append(f"bundle cannot contain symlinks: {path.relative_to(root).as_posix()}")

    manifest_path = root / ".codex-plugin" / "plugin.json"
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        manifest = {}
        issues.append(f"invalid plugin manifest: {exc}")
    if manifest.get("skills") != "./skills/":
        issues.append("manifest must expose ./skills/")
    if "mcpServers" in manifest or "apps" in manifest:
        issues.append("SKILL_ONLY bundle cannot declare MCP servers or apps")

    skill_files = sorted((root / "skills").glob("*/SKILL.md"))
    skill_names = {path.parent.name for path in skill_files}
    if skill_names != EXPECTED_SKILLS:
        issues.append("bundle does not contain the exact six VGTREE Skills")
    for path in skill_files:
        body = path.read_text(encoding="utf-8")
        for phrase in (
            "SKILL_ONLY",
            "Do not install",
            "engine_validation=NOT_RUN",
            "REVIEW_REQUIRED",
        ):
            if phrase not in body:
                issues.append(f"{path.parent.name} is missing {phrase}")

    shared = root / "shared"
    for relative in sorted(REQUIRED_SHARED):
        if not (shared / relative).is_file():
            issues.append(f"missing shared resource: {relative}")
    try:
        record = json.loads(
            (shared / "templates" / "skill-only-work-record.json").read_text(
                encoding="utf-8"
            )
        )
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        record = {}
        issues.append(f"invalid SKILL_ONLY work record: {exc}")
    expected_record = {
        "runtime_mode": "SKILL_ONLY",
        "engine_validation": "NOT_RUN",
        "overall_status": "REVIEW_REQUIRED",
    }
    for field, expected in expected_record.items():
        if record.get(field) != expected:
            issues.append(f"work record {field} must equal {expected}")

    engine_present = shutil.which("vgtree") is not None
    if require_engine_absent and engine_present:
        issues.append("vgtree executable unexpectedly exists in the clean PATH")

    return {
        "validation_status": "PASS" if not issues else "FAIL",
        "issues": issues,
        "runtime_mode": "SKILL_ONLY",
        "engine_validation": "NOT_RUN",
        "overall_status": "REVIEW_REQUIRED",
        "engine_present": engine_present,
        "installed_software": False,
        "skills": len(skill_files),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plugin-root", type=Path, required=True)
    parser.add_argument("--require-engine-absent", action="store_true")
    args = parser.parse_args()
    try:
        result = validate(args.plugin_root, args.require_engine_absent)
    except (OSError, ValueError) as exc:
        result = {
            "validation_status": "FAIL",
            "issues": [f"{type(exc).__name__}: {exc}"],
            "runtime_mode": "SKILL_ONLY",
            "engine_validation": "NOT_RUN",
            "overall_status": "REVIEW_REQUIRED",
            "engine_present": False,
            "installed_software": False,
            "skills": 0,
        }
    json.dump(result, sys.stdout, ensure_ascii=False, sort_keys=True)
    sys.stdout.write("\n")
    return 0 if result["validation_status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
