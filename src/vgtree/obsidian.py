"""Safe Obsidian workspace audit, plan, and starter scaffolding."""

from __future__ import annotations

import hashlib
import os
import shutil
import subprocess
import tempfile
from importlib.resources import files
from pathlib import Path
from typing import Any

import yaml

from vgtree.models import GuardResult


CORE_MARKDOWN = ("HOME.md", "PROJECT_MAP.md", "STATUS.md", "TODO.md")
GOVERNED_MARKDOWN = (*CORE_MARKDOWN, "PROVENANCE.md", "TRANSACTIONS.md")
PROJECT_REGISTRY = Path("90_System/VGTREE/PROJECT_REGISTRY.yaml")
FILE_REGISTRY = Path("90_System/VGTREE/FILE_REGISTRY.yaml")
MAX_AUDIT_FILE_BYTES = 4 * 1024 * 1024
FILE_UIDS = {
    "HOME.md": "FILE-000001",
    "PROJECT_MAP.md": "FILE-000002",
    "STATUS.md": "FILE-000003",
    "TODO.md": "FILE-000004",
    "PROVENANCE.md": "FILE-000005",
    "TRANSACTIONS.md": "FILE-000006",
}


class ObsidianWorkspace:
    def __init__(self, *, cli_path: str | Path | None = None) -> None:
        self.cli_path = Path(cli_path) if cli_path is not None else _find_obsidian_cli()

    def audit(
        self, vault: str | Path, mode: str, *, live: bool = False
    ) -> GuardResult:
        mode_error = _validate_mode(mode)
        if mode_error:
            return mode_error
        vault_path = Path(vault)
        if not vault_path.is_dir():
            return GuardResult(
                "FAIL", "OBSIDIAN_VAULT_NOT_FOUND", f"Vault directory not found: {vault_path}"
            )

        findings = self._static_findings(vault_path, mode)
        static_status = "PASS" if not findings else "REVIEW_REQUIRED"
        static_code = "OBSIDIAN_AUDIT_PASS" if not findings else "OBSIDIAN_AUDIT_FINDINGS"
        data: dict[str, Any] = {
            "vault": str(vault_path),
            "mode": mode,
            "live_checked": False,
            "findings": findings,
        }
        if live:
            live_result = self._live_check(vault_path)
            if live_result.status != "PASS":
                return GuardResult(
                    live_result.status,
                    live_result.code,
                    live_result.message,
                    {**data, **live_result.data},
                )
            data["live_checked"] = True
            data["live"] = live_result.data

        return GuardResult(
            static_status,
            static_code,
            "Obsidian workspace audit passed."
            if not findings
            else "Obsidian workspace requires review.",
            data,
        )

    def plan(self, vault: str | Path, mode: str) -> GuardResult:
        mode_error = _validate_mode(mode)
        if mode_error:
            return mode_error
        vault_path = Path(vault)
        if not vault_path.is_dir():
            return GuardResult(
                "FAIL", "OBSIDIAN_VAULT_NOT_FOUND", f"Vault directory not found: {vault_path}"
            )
        findings = self._static_findings(vault_path, mode)
        operations = [
            {
                "action": "create" if item["code"] == "SURFACE_MISSING" else "review",
                "path": item["path"],
                "reason": item["message"],
            }
            for item in findings
        ]
        return GuardResult(
            "PASS",
            "OBSIDIAN_PLAN_READY",
            "Read-only workspace plan generated; no vault files were changed.",
            {
                "vault": str(vault_path),
                "mode": mode,
                "operations": operations,
                "findings": findings,
            },
        )

    def scaffold(self, destination: str | Path, mode: str) -> GuardResult:
        mode_error = _validate_mode(mode)
        if mode_error:
            return mode_error
        destination_path = Path(destination)
        if destination_path.exists():
            if not destination_path.is_dir():
                return GuardResult(
                    "BLOCKED",
                    "OBSIDIAN_DESTINATION_NOT_DIRECTORY",
                    "Scaffold destination exists and is not a directory.",
                )
            if any(destination_path.iterdir()):
                return GuardResult(
                    "BLOCKED",
                    "OBSIDIAN_DESTINATION_NOT_EMPTY",
                    "Scaffold writes only to a new or empty destination.",
                )

        destination_path.parent.mkdir(parents=True, exist_ok=True)
        temporary = Path(
            tempfile.mkdtemp(prefix=".vgtree-scaffold-", dir=destination_path.parent)
        )
        try:
            _render_scaffold(temporary, mode)
            audit = self.audit(temporary, mode)
            if audit.status != "PASS":
                return GuardResult(
                    "FAIL",
                    "OBSIDIAN_SCAFFOLD_INVALID",
                    "Generated starter failed its own audit.",
                    audit.data,
                )
            if destination_path.exists():
                destination_path.rmdir()
            os.replace(temporary, destination_path)
        except (OSError, UnicodeError, yaml.YAMLError) as exc:
            return GuardResult("FAIL", "OBSIDIAN_SCAFFOLD_FAILED", str(exc))
        finally:
            if temporary.exists():
                shutil.rmtree(temporary)

        return GuardResult(
            "PASS",
            "OBSIDIAN_SCAFFOLDED",
            "Obsidian starter workspace created.",
            {
                "destination": str(destination_path),
                "mode": mode,
                "files": [
                    str(path.relative_to(destination_path)).replace("\\", "/")
                    for path in sorted(destination_path.rglob("*"))
                    if path.is_file()
                ],
            },
        )

    def _static_findings(self, vault: Path, mode: str) -> list[dict[str, str]]:
        markdown = GOVERNED_MARKDOWN if mode == "governed" else CORE_MARKDOWN
        required = [*markdown, str(PROJECT_REGISTRY).replace("\\", "/")]
        if mode == "governed":
            required.append(str(FILE_REGISTRY).replace("\\", "/"))
        findings: list[dict[str, str]] = []
        vault_root = vault.resolve(strict=True)
        resolved_paths: dict[str, Path] = {}
        for relative in required:
            try:
                resolved = _resolve_audit_file(vault_root, relative)
            except _AuditPathError as exc:
                findings.append(_finding(exc.code, relative, exc.message))
                continue
            if resolved is None:
                findings.append(
                    _finding("SURFACE_MISSING", relative, "Required workspace surface is missing.")
                )
            else:
                resolved_paths[relative] = resolved

        project_uid: str | None = None
        project_registry_key = str(PROJECT_REGISTRY).replace("\\", "/")
        registry_path = resolved_paths.get(project_registry_key)
        if registry_path is not None:
            try:
                registry = yaml.safe_load(registry_path.read_text(encoding="utf-8"))
                projects = registry.get("projects", []) if isinstance(registry, dict) else []
                project_uid = projects[0].get("project_uid") if projects else None
                if not project_uid:
                    findings.append(
                        _finding(
                            "PROJECT_UID_MISSING",
                            str(PROJECT_REGISTRY).replace("\\", "/"),
                            "Project registry needs at least one project UID.",
                        )
                    )
            except (OSError, UnicodeError, yaml.YAMLError):
                findings.append(
                    _finding(
                        "YAML_INVALID",
                        project_registry_key,
                        "Project registry could not be read or parsed.",
                    )
                )

        frontmatter_by_path: dict[str, dict[str, Any]] = {}
        for relative in markdown:
            path = resolved_paths.get(relative)
            if path is None:
                continue
            try:
                metadata = _frontmatter(path)
                frontmatter_by_path[relative] = metadata
            except (OSError, UnicodeError, ValueError, yaml.YAMLError):
                findings.append(
                    _finding(
                        "FRONTMATTER_INVALID",
                        relative,
                        "Frontmatter could not be read or parsed.",
                    )
                )
                continue
            if project_uid and metadata.get("project_uid") != project_uid:
                findings.append(
                    _finding(
                        "PROJECT_UID_MISMATCH",
                        relative,
                        "Frontmatter project UID does not match the project registry.",
                    )
                )
            if mode == "governed" and not metadata.get("file_uid"):
                findings.append(
                    _finding("FILE_UID_MISSING", relative, "Governed mode requires a file UID.")
                )

        home_path = resolved_paths.get("HOME.md")
        if home_path is not None:
            home = home_path.read_text(encoding="utf-8")
            for link in ("[[PROJECT_MAP", "[[STATUS", "[[TODO"):
                if link not in home:
                    findings.append(
                        _finding(
                            "DISCOVERABILITY_LINK_MISSING",
                            "HOME.md",
                            f"Home is missing {link}.",
                        )
                    )

        file_registry_key = str(FILE_REGISTRY).replace("\\", "/")
        if mode == "governed" and file_registry_key in resolved_paths:
            findings.extend(
                _file_registry_findings(
                    resolved_paths, frontmatter_by_path, markdown
                )
            )
        return findings

    def _live_check(self, vault: Path) -> GuardResult:
        if self.cli_path is None or not self.cli_path.is_file():
            return GuardResult(
                "BLOCKED",
                "OBSIDIAN_LIVE_UNAVAILABLE",
                "Obsidian CLI is unavailable; no live validation was claimed.",
            )
        try:
            cli_resolved = self.cli_path.resolve(strict=True)
            vault_resolved = vault.resolve(strict=True)
            cwd_resolved = Path.cwd().resolve(strict=True)
        except OSError:
            return GuardResult(
                "BLOCKED",
                "OBSIDIAN_CLI_UNTRUSTED",
                "Obsidian CLI path could not be resolved safely.",
            )
        if _is_within(cli_resolved, vault_resolved) or _is_within(
            cli_resolved, cwd_resolved
        ):
            return GuardResult(
                "BLOCKED",
                "OBSIDIAN_CLI_UNTRUSTED",
                "Obsidian CLI must not be loaded from the audited vault or current workspace.",
            )
        try:
            completed = subprocess.run(
                [str(cli_resolved), "help"],
                cwd=vault,
                check=False,
                capture_output=True,
                text=True,
                timeout=10,
                shell=False,
            )
        except (OSError, subprocess.SubprocessError) as exc:
            return GuardResult(
                "BLOCKED", "OBSIDIAN_LIVE_UNAVAILABLE", str(exc)
            )
        if completed.returncode != 0:
            return GuardResult(
                "BLOCKED",
                "OBSIDIAN_LIVE_UNAVAILABLE",
                "Obsidian CLI did not confirm a live session.",
                {"returncode": completed.returncode},
            )
        return GuardResult(
            "PASS",
            "OBSIDIAN_LIVE_PASS",
            "Obsidian CLI responded successfully.",
            {"returncode": completed.returncode},
        )


def _render_scaffold(root: Path, mode: str) -> None:
    root.mkdir(parents=True, exist_ok=True)
    markdown = GOVERNED_MARKDOWN if mode == "governed" else CORE_MARKDOWN
    for relative in markdown:
        template = _template(relative)
        file_uid_line = (
            f"file_uid: {FILE_UIDS[relative]}" if mode == "governed" else ""
        )
        rendered = template.replace("{{file_uid_line}}", file_uid_line)
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(rendered, encoding="utf-8", newline="\n")

    registry_path = root / PROJECT_REGISTRY
    registry_path.parent.mkdir(parents=True, exist_ok=True)
    registry_path.write_text(
        'schema_version: "1.0"\nprojects:\n  - project_uid: PRJ-0001\n'
        "    title: VGTREE Starter Workspace\n    status: ACTIVE\n",
        encoding="utf-8",
        newline="\n",
    )
    if mode == "governed":
        entries = []
        for relative in markdown:
            digest = hashlib.sha256((root / relative).read_bytes()).hexdigest()
            entries.append(
                {
                    "path": relative,
                    "file_uid": FILE_UIDS[relative],
                    "sha256": digest,
                }
            )
        file_registry_path = root / FILE_REGISTRY
        file_registry_path.write_text(
            yaml.safe_dump(
                {"schema_version": "1.0", "files": entries},
                sort_keys=False,
                allow_unicode=True,
            ),
            encoding="utf-8",
            newline="\n",
        )


def _template(relative: str) -> str:
    resource = files("vgtree").joinpath("templates", "obsidian", relative)
    return resource.read_text(encoding="utf-8")


def _frontmatter(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    if not lines or lines[0] != "---":
        raise ValueError("Missing YAML frontmatter opening delimiter.")
    try:
        closing = lines.index("---", 1)
    except ValueError as exc:
        raise ValueError("Missing YAML frontmatter closing delimiter.") from exc
    metadata = yaml.safe_load("\n".join(lines[1:closing])) or {}
    if not isinstance(metadata, dict):
        raise ValueError("YAML frontmatter must be an object.")
    return metadata


def _file_registry_findings(
    resolved_paths: dict[str, Path],
    metadata: dict[str, dict[str, Any]],
    markdown: tuple[str, ...],
) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    file_registry_key = str(FILE_REGISTRY).replace("\\", "/")
    try:
        registry = yaml.safe_load(
            resolved_paths[file_registry_key].read_text(encoding="utf-8")
        )
        items = registry.get("files", []) if isinstance(registry, dict) else []
    except (KeyError, OSError, UnicodeError, yaml.YAMLError):
        return [
            _finding(
                "YAML_INVALID",
                file_registry_key,
                "File registry could not be read or parsed.",
            )
        ]
    entries = {
        item.get("path"): item
        for item in items
        if isinstance(item, dict) and isinstance(item.get("path"), str)
    }
    for relative in markdown:
        path = resolved_paths.get(relative)
        if path is None:
            continue
        entry = entries.get(relative)
        if entry is None:
            findings.append(
                _finding("FILE_REGISTRY_ENTRY_MISSING", relative, "File is absent from the file registry.")
            )
            continue
        if entry.get("file_uid") != metadata.get(relative, {}).get("file_uid"):
            findings.append(
                _finding("FILE_UID_MISMATCH", relative, "File UID and registry entry differ.")
            )
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        if entry.get("sha256") != digest:
            findings.append(
                _finding("HASH_MISMATCH", relative, "File content hash differs from the registry.")
            )
    return findings


def _finding(code: str, path: str, message: str) -> dict[str, str]:
    return {"code": code, "path": path, "message": message}


class _AuditPathError(ValueError):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


def _resolve_audit_file(vault_root: Path, relative: str) -> Path | None:
    candidate = vault_root / Path(relative)
    if candidate.is_symlink():
        raise _AuditPathError(
            "PATH_UNSAFE", "Required workspace surface must not be a filesystem link."
        )
    try:
        resolved = candidate.resolve(strict=True)
    except FileNotFoundError:
        return None
    except OSError as exc:
        raise _AuditPathError(
            "PATH_UNSAFE", "Required workspace surface could not be resolved safely."
        ) from exc
    if resolved != vault_root and vault_root not in resolved.parents:
        raise _AuditPathError(
            "PATH_UNSAFE", "Required workspace surface resolves outside the vault."
        )
    if not resolved.is_file():
        return None
    try:
        size = resolved.stat().st_size
    except OSError as exc:
        raise _AuditPathError(
            "PATH_UNSAFE", "Required workspace surface could not be inspected safely."
        ) from exc
    if size > MAX_AUDIT_FILE_BYTES:
        raise _AuditPathError(
            "FILE_TOO_LARGE",
            f"Required workspace surface exceeds {MAX_AUDIT_FILE_BYTES} bytes.",
        )
    return resolved


def _is_within(candidate: Path, root: Path) -> bool:
    return candidate == root or root in candidate.parents


def _validate_mode(mode: str) -> GuardResult | None:
    if mode in {"core", "governed"}:
        return None
    return GuardResult(
        "FAIL", "OBSIDIAN_MODE_INVALID", "Mode must be either core or governed."
    )


def _find_obsidian_cli() -> Path | None:
    windows_default = Path.home() / "AppData/Local/Programs/Obsidian/Obsidian.com"
    if windows_default.is_file():
        return windows_default
    located = shutil.which("obsidian") or shutil.which("Obsidian.com")
    if located:
        return Path(located)
    return None
