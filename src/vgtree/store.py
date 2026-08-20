"""Transactional local state persistence with explicit writer locks."""

from __future__ import annotations

import json
import os
import uuid
from pathlib import Path
from typing import Any, Callable

from vgtree.models import GuardResult
from vgtree.validation import validate_state


class StateStore:
    def load(self, path: str | Path) -> GuardResult:
        return self._load_unlocked(Path(path))

    def save(
        self, path: str | Path, state: Any, *, create_only: bool = False
    ) -> GuardResult:
        report = validate_state(state)
        if not report.valid:
            return GuardResult(
                "FAIL",
                "STATE_INVALID",
                "State was not written because validation failed.",
                {"validation": report.as_dict()},
            )

        state_path = Path(path)
        acquired = self._acquire_lock(state_path)
        if isinstance(acquired, GuardResult):
            return acquired
        lock_path, lock_token = acquired
        try:
            return self._commit_unlocked(
                state_path, state, create_only=create_only
            )
        finally:
            self._release_lock(lock_path, lock_token)

    def update(
        self,
        path: str | Path,
        operation: Callable[[dict[str, Any]], GuardResult],
    ) -> GuardResult:
        """Serialize load, mutation, validation, and commit as one transaction."""

        state_path = Path(path)
        acquired = self._acquire_lock(state_path)
        if isinstance(acquired, GuardResult):
            return acquired
        lock_path, lock_token = acquired
        try:
            loaded = self._load_unlocked(state_path)
            if loaded.status != "PASS":
                return loaded
            result = operation(loaded.data["state"])
            if result.status != "PASS" or "state" not in result.data:
                return result
            saved = self._commit_unlocked(
                state_path, result.data["state"], create_only=False
            )
            return result if saved.status == "PASS" else saved
        finally:
            self._release_lock(lock_path, lock_token)

    def _load_unlocked(self, state_path: Path) -> GuardResult:
        if not state_path.is_file():
            return GuardResult(
                "FAIL", "STATE_NOT_FOUND", f"State file does not exist: {state_path}"
            )
        try:
            state = json.loads(state_path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError) as exc:
            return GuardResult("FAIL", "STATE_READ_FAILED", str(exc))
        except json.JSONDecodeError as exc:
            return GuardResult(
                "FAIL",
                "STATE_JSON_INVALID",
                f"Invalid JSON at line {exc.lineno}, column {exc.colno}.",
            )

        report = validate_state(state)
        if not report.valid:
            return GuardResult(
                "FAIL",
                "STATE_INVALID",
                "Stored state failed validation.",
                {"validation": report.as_dict()},
            )
        return GuardResult("PASS", "STATE_LOADED", "State loaded.", {"state": state})

    def _acquire_lock(
        self, state_path: Path
    ) -> tuple[Path, str] | GuardResult:
        lock_path = state_path.with_name(f"{state_path.name}.lock")
        token = f"pid={os.getpid()} nonce={uuid.uuid4().hex}\n"
        try:
            state_path.parent.mkdir(parents=True, exist_ok=True)
            descriptor = os.open(
                lock_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY
            )
        except FileExistsError:
            return GuardResult(
                "BLOCKED",
                "STATE_LOCKED",
                f"Another writer holds the state lock: {lock_path}",
                {"lock_path": str(lock_path)},
            )
        except OSError as exc:
            return GuardResult("FAIL", "STATE_LOCK_FAILED", str(exc))

        try:
            with os.fdopen(descriptor, "w", encoding="utf-8") as lock_file:
                lock_file.write(token)
                lock_file.flush()
                os.fsync(lock_file.fileno())
        except OSError as exc:
            try:
                lock_path.unlink()
            except OSError:
                pass
            return GuardResult("FAIL", "STATE_LOCK_FAILED", str(exc))
        return lock_path, token

    def _release_lock(self, lock_path: Path, token: str) -> None:
        try:
            if lock_path.read_text(encoding="utf-8") == token:
                lock_path.unlink()
        except (FileNotFoundError, OSError, UnicodeError):
            pass

    def _commit_unlocked(
        self, state_path: Path, state: Any, *, create_only: bool
    ) -> GuardResult:
        report = validate_state(state)
        if not report.valid:
            return GuardResult(
                "FAIL",
                "STATE_INVALID",
                "State was not written because validation failed.",
                {"validation": report.as_dict()},
            )

        temporary_path = state_path.with_name(
            f".{state_path.name}.tmp-{uuid.uuid4().hex}"
        )
        try:
            with temporary_path.open("x", encoding="utf-8", newline="\n") as handle:
                json.dump(state, handle, ensure_ascii=False, indent=2, sort_keys=True)
                handle.write("\n")
                handle.flush()
                os.fsync(handle.fileno())
            if create_only:
                os.link(temporary_path, state_path)
                temporary_path.unlink()
            else:
                os.replace(temporary_path, state_path)
        except FileExistsError:
            return GuardResult(
                "BLOCKED",
                "STATE_OUTPUT_EXISTS",
                "Create-only state output already exists.",
                {"path": str(state_path)},
            )
        except (OSError, TypeError, ValueError) as exc:
            return GuardResult("FAIL", "STATE_WRITE_FAILED", str(exc))
        finally:
            try:
                temporary_path.unlink()
            except FileNotFoundError:
                pass
            except OSError:
                pass

        return GuardResult(
            "PASS",
            "STATE_SAVED",
            "State was atomically saved.",
            {"path": str(state_path), "state": state},
        )
