"""Recover affected paths from ordinary unified git patches without applying them."""
from __future__ import annotations
from pathlib import Path
import fnmatch
import shlex
from .models import InputError


def _normalize_path(raw: str) -> str | None:
    raw = raw.strip()
    if not raw:
        return None
    if raw.startswith('"'):
        try:
            parts = shlex.split(raw)
        except ValueError as exc:
            raise InputError(f"invalid quoted patch path: {raw}") from exc
        if len(parts) != 1:
            raise InputError(f"ambiguous patch path: {raw}")
        raw = parts[0]
    else:
        raw = raw.split("\t", 1)[0]
    if raw == "/dev/null":
        return None
    if raw.startswith(("a/", "b/")):
        raw = raw[2:]
    if raw.startswith("/") or ".." in raw.split("/") or not raw:
        raise InputError(f"unsafe patch path: {raw}")
    return raw


def changed_paths(patch: str) -> tuple[str, ...]:
    paths: set[str] = set()
    for line in patch.splitlines():
        if line.startswith("diff --git "):
            # Include file names even for mode-only changes and binary patches
            # that don't have ordinary ---/+++ content headers.
            try:
                parts = shlex.split(line)
            except ValueError as exc:
                raise InputError("invalid diff --git header") from exc
            if len(parts) != 4:
                raise InputError("unsupported diff --git path encoding")
            for entry in parts[2:]:
                path = _normalize_path(entry)
                if path is not None:
                    paths.add(path)
            continue
        for prefix in ("+++ ", "--- ", "rename from ", "rename to ", "copy from ", "copy to "):
            if line.startswith(prefix):
                path = _normalize_path(line[len(prefix):])
                if path is not None:
                    paths.add(path)
                break
    # A patch without recognized paths must not silently pass as clean.
    if patch.strip() and not paths:
        raise InputError("nonempty patch has no recognizable file paths")
    return tuple(sorted(paths))


def read_changed_paths(path: str | Path) -> tuple[str, ...]:
    try:
        return changed_paths(Path(path).read_text(encoding="utf-8"))
    except (OSError, UnicodeError) as exc:
        raise InputError(f"cannot read patch {path}: {exc}") from exc


def protected_changes(paths: tuple[str, ...], patterns: tuple[str, ...]) -> list[str]:
    return sorted({path for path in paths for pattern in patterns
                   if fnmatch.fnmatchcase(path, pattern)})
