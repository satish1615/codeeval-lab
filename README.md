# CodeEval Lab

A **deterministic evaluation tool for code-repair benchmarks**. It reads a baseline and candidate JUnit XML report, checks whether required failures were repaired, ensures earlier passing tests remain green, and flags changes to protected files. Designed as a reproducible engineering exercise in correctness evaluation, not as a production sandbox or a substitute for running tests.

**Status:** Early-stage personal engineering project. It has no claimed external adoption, peer-reviewed publications, or research validation. Do not represent it as an upstream open-source contribution.

## Why build it?

Coding-agent benchmark evaluations need checks beyond "the requested tests pass." A solution might repair the target failure and quietly break unrelated behavior or modify a verifier. CodeEval Lab explicitly checks:

1. **Fail-to-pass (F2P):** Tests known to fail in the baseline must pass in the candidate.
2. **Pass-to-pass (P2P):** Tests identified as passing in the baseline must stay passing.
3. **Regression gate:** All other baseline passes must remain green, and newly introduced failing tests count as regressions.
4. **Protected-path gate:** Detect patches touching configured test, benchmark, or CI paths.
5. **Audit-ready output:** Text, Markdown, or JSON gate reports suitable for CI artifacts.

Inputs are the **actual test reports** and a **unified diff**. This tool does not execute arbitrary candidate code.

## Run in 60 seconds

Python 3.10+ required. No runtime dependencies outside the Python standard library.

```bash
python -m pip install -e .
python -m unittest discover -s tests -v

codeeval evaluate \
  --manifest examples/benchmark.json \
  --baseline examples/baseline.xml \
  --candidate examples/candidate.xml \
  --diff examples/change.patch \
  --format text
```

Expected output:

```text
Cache invalidation regression benchmark: PASS
Gates:
  fail_to_pass: PASS
  pass_to_pass: PASS
  regressions: PASS
  protected_paths: PASS
Fail-to-pass fixed: 2
Fail-to-pass unfixed: 0
New regressions: 0
```

Write an evaluation artifact with `--format json --out report.json`. The process returns status `0` when gates pass, `1` when a gate fails, and `2` for invalid inputs.

## Benchmark configuration

See [`examples/benchmark.json`](examples/benchmark.json):

```json
{
  "schema_version": 1,
  "name": "Cache invalidation regression benchmark",
  "fail_to_pass": ["tests.test_cache.test_stale_entry", "tests.test_cache.test_parallel_refresh"],
  "pass_to_pass": ["tests.test_cache.test_cache_hit", "tests.test_api.test_get_item"],
  "protected_paths": ["tests/**", "benchmark/**", ".github/workflows/**"],
  "max_new_failures": 0
}
```

Case IDs follow the JUnit `classname.name` convention. Use exactly matching IDs in the baseline, candidate, and benchmark configuration. Required F2P tests **must have failed in the baseline**; required P2P tests **must have passed in the baseline**. Invalid labels are errors rather than silently accepted. Missing candidate tests count as failures for required tests, and regressions for baseline passes.

## Repository structure

```text
src/codeeval/       Validation, JUnit parsing, patch inspection, gates, reports, CLI
examples/           Fully runnable benchmark and example JUnit artifacts
tests/              Unit and CLI regression tests
docs/METHODOLOGY.md Design decisions, limitations, and research directions
.github/workflows/  CI against Python 3.10–3.13
```

## Scope and limitations

- **Not a sandbox:** Test suites must run in a separate trusted/isolated environment. JUnit input may be falsified by whoever generated it. Use independent execution and secured artifacts for real evaluations.
- **Heuristic diff inspection:** Protected path checks match parsed unified diff paths against glob patterns. They do not detect every conceivable malicious change or runtime exploit.
- **No AI grading:** The verdict is rule-based and reproducible; it does not judge natural-language reasoning quality or task difficulty.
- **Candidate reports:** This tool cannot infer whether a missing or skipped test was intentionally suppressed. It conservatively fails gates where necessary.

See the [methodology](docs/METHODOLOGY.md) for details and potential improvements.

## Contributing

Run the test suite before submitting changes. Please include a small regression test when fixing parser or evaluator behavior. This repository is intended to document real, inspectable source-level engineering work.

## License

MIT. See `LICENSE`.
