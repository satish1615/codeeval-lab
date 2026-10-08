"""Read test-case outcomes from pytest/JUnit-compatible XML, fail closed on duplicates."""
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
import xml.etree.ElementTree as ET
from .models import InputError


@dataclass(frozen=True)
class TestCase:
    id: str
    status: str  # passed, failed, errored, skipped
    detail: str = ""


def _tag(elem: ET.Element) -> str:
    return elem.tag.rsplit("}", 1)[-1]


def parse_junit(path: str | Path) -> dict[str, TestCase]:
    try:
        root = ET.parse(path).getroot()
    except (ET.ParseError, OSError) as exc:
        raise InputError(f"cannot parse JUnit XML {path}: {exc}") from exc
    if _tag(root) not in {"testsuite", "testsuites"}:
        raise InputError(f"expected testsuite(s) root in {path}")
    found: dict[str, TestCase] = {}
    for elem in root.iter():
        if _tag(elem) != "testcase":
            continue
        name = elem.get("name", "").strip()
        group = elem.get("classname", "").strip()
        if not name:
            raise InputError("testcase is missing name")
        case_id = f"{group}.{name}" if group else name
        if case_id in found:
            raise InputError(f"duplicate test case ID: {case_id}")
        status, detail = "passed", ""
        for child in elem:
            kind = _tag(child)
            if kind in {"failure", "error", "skipped"}:
                new = {"failure": "failed", "error": "errored", "skipped": "skipped"}[kind]
                if status != "passed":
                    raise InputError(f"multiple result statuses for {case_id}")
                status, detail = new, (child.get("message") or child.text or "").strip()
        found[case_id] = TestCase(case_id, status, detail)
    if not found:
        raise InputError(f"no test cases in {path}")
    return found
