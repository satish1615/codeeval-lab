"""Command-line entry point. Exit 0=pass, 1=failed gates, 2=input error."""
from __future__ import annotations
import argparse
import json
import sys
from pathlib import Path
from .diff import read_changed_paths
from .evaluate import evaluate
from .junit import parse_junit
from .models import Benchmark, InputError
from .report import render


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="codeeval", description="Evaluate repair benchmarks from JUnit reports")
    sub = parser.add_subparsers(dest="command", required=True)
    cmd = sub.add_parser("evaluate", help="Evaluate benchmark gates")
    for arg in ("manifest", "baseline", "candidate", "diff"):
        cmd.add_argument(f"--{arg}", required=True, type=Path)
    cmd.add_argument("--format", choices=("text", "json", "markdown"), default="text")
    cmd.add_argument("--out", type=Path, help="Write report instead of printing")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        try:
            raw = json.loads(args.manifest.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            raise InputError(f"cannot read benchmark manifest: {exc}") from exc
        benchmark = Benchmark.from_dict(raw)
        report = evaluate(benchmark, parse_junit(args.baseline),
                          parse_junit(args.candidate), read_changed_paths(args.diff))
        output = render(report, args.format)
        if args.out:
            try:
                args.out.write_text(output, encoding="utf-8")
            except OSError as exc:
                raise InputError(f"cannot write report: {exc}") from exc
        else:
            print(output, end="")
        return 0 if report.passed else 1
    except InputError as exc:
        print(f"input error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
