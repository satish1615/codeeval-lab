"""Deterministic benchmark gates. No execution of candidate source code."""
from __future__ import annotations
from dataclasses import asdict, dataclass
from .models import Benchmark, InputError
from .junit import TestCase
from .diff import protected_changes


@dataclass(frozen=True)
class Report:
    benchmark: str
    passed: bool
    fail_to_pass_fixed: list[str]
    fail_to_pass_unfixed: list[str]
    pass_to_pass_maintained: list[str]
    pass_to_pass_broken: list[str]
    new_failures: list[str]
    protected_path_changes: list[str]
    changed_paths: list[str]
    gate_results: dict[str, bool]
    reasons: list[str]

    def as_dict(self) -> dict:
        result = asdict(self)
        result["summary"] = {
            "fail_to_pass_rate": len(self.fail_to_pass_fixed) / (
                len(self.fail_to_pass_fixed) + len(self.fail_to_pass_unfixed)),
            "pass_to_pass_rate": len(self.pass_to_pass_maintained) / (
                len(self.pass_to_pass_maintained) + len(self.pass_to_pass_broken))
                if self.pass_to_pass_maintained or self.pass_to_pass_broken else None,
            "new_failure_count": len(self.new_failures),
        }
        return result


def evaluate(benchmark: Benchmark, baseline: dict[str, TestCase],
             candidate: dict[str, TestCase], changed: tuple[str, ...]) -> Report:
    # Validate benchmark metadata against the *baseline*, not candidate outputs.
    for case in benchmark.fail_to_pass:
        if case not in baseline or baseline[case].status not in {"failed", "errored"}:
            raise InputError(f"fail-to-pass case was not failing in baseline: {case}")
    for case in benchmark.pass_to_pass:
        if case not in baseline or baseline[case].status != "passed":
            raise InputError(f"pass-to-pass case was not passing in baseline: {case}")

    f2p_fixed = sorted(c for c in benchmark.fail_to_pass if
                       c in candidate and candidate[c].status == "passed")
    f2p_unfixed = sorted(set(benchmark.fail_to_pass) - set(f2p_fixed))
    p2p_ok = sorted(c for c in benchmark.pass_to_pass if
                    c in candidate and candidate[c].status == "passed")
    p2p_bad = sorted(set(benchmark.pass_to_pass) - set(p2p_ok))

    # All baseline passes must remain green, even if omitted from declared P2P.
    regressions = {c for c, result in baseline.items() if result.status == "passed"
                   and (c not in candidate or candidate[c].status != "passed")}
    # New candidate-only failing tests also count as regressions.
    regressions |= {c for c, result in candidate.items() if c not in baseline and
                    result.status in {"failed", "errored"}}
    protected = protected_changes(changed, benchmark.protected_paths)
    gates = {
        "fail_to_pass": not f2p_unfixed,
        "pass_to_pass": not p2p_bad,
        "regressions": len(regressions) <= benchmark.max_new_failures,
        "protected_paths": not protected,
    }
    reasons = []
    if f2p_unfixed:
        reasons.append(f"{len(f2p_unfixed)} required failing tests not repaired")
    if p2p_bad:
        reasons.append(f"{len(p2p_bad)} required passing tests did not stay passing")
    if not gates["regressions"]:
        reasons.append(f"{len(regressions)} regressions exceed limit {benchmark.max_new_failures}")
    if protected:
        reasons.append(f"protected paths modified: {', '.join(protected)}")
    return Report(benchmark.name, all(gates.values()), f2p_fixed, f2p_unfixed,
                  p2p_ok, p2p_bad, sorted(regressions), protected, list(changed), gates, reasons)
