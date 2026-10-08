"""Validated benchmark definitions and normalized test observations."""
from __future__ import annotations
from dataclasses import dataclass
from typing import Any


class InputError(ValueError):
    """Raised when inputs are malformed or internally inconsistent."""


def _string_list(data: dict[str, Any], key: str) -> tuple[str, ...]:
    value = data.get(key, [])
    if not isinstance(value, list) or any(not isinstance(x, str) or not x.strip() for x in value):
        raise InputError(f"{key} must be a list of nonempty strings")
    if len(value) != len(set(value)):
        raise InputError(f"{key} contains duplicate entries")
    return tuple(value)


@dataclass(frozen=True)
class Benchmark:
    name: str
    fail_to_pass: tuple[str, ...]
    pass_to_pass: tuple[str, ...]
    protected_paths: tuple[str, ...]
    max_new_failures: int = 0

    @classmethod
    def from_dict(cls, raw: Any) -> Benchmark:
        if not isinstance(raw, dict):
            raise InputError("benchmark must be a JSON object")
        if raw.get("schema_version") != 1 or isinstance(raw.get("schema_version"), bool):
            raise InputError("schema_version must be 1")
        name = raw.get("name")
        if not isinstance(name, str) or not name.strip():
            raise InputError("name must be a nonempty string")
        f2p = _string_list(raw, "fail_to_pass")
        p2p = _string_list(raw, "pass_to_pass")
        if not f2p:
            raise InputError("fail_to_pass must specify at least one case")
        overlap = set(f2p) & set(p2p)
        if overlap:
            raise InputError(f"test IDs in both sets: {', '.join(sorted(overlap))}")
        protected = _string_list(raw, "protected_paths")
        for pattern in protected:
            if pattern.startswith("/") or ".." in pattern.split("/"):
                raise InputError(f"protected path pattern is not repository-relative: {pattern}")
        allowed = raw.get("max_new_failures", 0)
        if type(allowed) is not int or allowed < 0:
            raise InputError("max_new_failures must be a nonnegative integer")
        return cls(name=name, fail_to_pass=f2p, pass_to_pass=p2p,
                   protected_paths=protected, max_new_failures=allowed)
