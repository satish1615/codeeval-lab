"""Human-readable output formats for benchmark results."""
from __future__ import annotations
import json
from .evaluate import Report


def render(report: Report, output_format: str) -> str:
    if output_format == "json":
        return json.dumps(report.as_dict(), indent=2, sort_keys=True) + "\n"
    status = "PASS" if report.passed else "FAIL"
    if output_format == "text":
        gates = "\n".join(f"  {key}: {'PASS' if ok else 'FAIL'}"
                          for key, ok in report.gate_results.items())
        reasons = "\n".join("  - " + reason for reason in report.reasons)
        return (f"{report.benchmark}: {status}\nGates:\n{gates}\n"
                f"Fail-to-pass fixed: {len(report.fail_to_pass_fixed)}\n"
                f"Fail-to-pass unfixed: {len(report.fail_to_pass_unfixed)}\n"
                f"New regressions: {len(report.new_failures)}\n"
                + ("Reasons:\n" + reasons + "\n" if reasons else ""))
    if output_format == "markdown":
        rows = "\n".join(f"| {key} | {'PASS' if ok else 'FAIL'} |"
                         for key, ok in report.gate_results.items())
        reasons = "\n".join(f"- {reason}" for reason in report.reasons)
        return (f"# {report.benchmark}: {status}\n\n| Gate | Result |\n"
                f"| --- | --- |\n{rows}\n\n"
                f"Fixed: {len(report.fail_to_pass_fixed)}; regressions: {len(report.new_failures)}\n"
                + ("\n## Reasons\n" + reasons + "\n" if reasons else ""))
    raise ValueError(f"unknown report format: {output_format}")
