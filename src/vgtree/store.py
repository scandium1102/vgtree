"""Atomic local state persistence with explicit writer locks."""

from __future__ import annotations

import json
import os
import uuid
from pathlib import Path
from typing import Any

from vgtree.models import GuardResult
from vgtree.validation import validate_state


class StateStore:
    def load(self, path: str | Path) -> GuardResult:
        state_path = Path(path)
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

    def save(self, path: str | Path, state: Any) -> GuardResult:
        report = validate_state(state)
        if not report.valid:
            return GuardResult(
                "FAIL",
                "STATE_INVALID",
                "State was not written because validation failed.",
                {"validation": report.as_dict()},
            )

        state_path = Path(path)
        lock_path = state_path.with_name(f"{state_path.name}.lock")
        temporary_path = state_path.with_name(
            f".{state_path.name}.tmp-{uuid.uuid4().hex}"
        )
        try:
            state_path.parent.mkdir(parents=True, exist_ok=True)
            lock_descriptor = os.open(
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
            with os.fdopen(lock_descriptor, "w", encoding="utf-8") as lock_file:
                lock_file.write(f"pid={os.getpid()}\n")
                lock_file.flush()
                os.fsync(lock_file.fileno())
            with temporary_path.open("w", encoding="utf-8", newline="\n") as handle:
                json.dump(state, handle, ensure_ascii=False, indent=2, sort_keys=True)
                handle.write("\n")
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temporary_path, state_path)
        except (OSError, TypeError, ValueError) as exc:
            if temporary_path.exists():
                temporary_path.unlink()
            return GuardResult("FAIL", "STATE_WRITE_FAILED", str(exc))
        finally:
            try:
                lock_path.unlink()
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

