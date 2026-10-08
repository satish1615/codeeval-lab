# Evaluation methodology

## Objective

A code-repair agent is evaluated for *correctness* and *non-regression*. Given an immutable benchmark manifest, independent baseline/candidate JUnit XML results, and a candidate unified patch, evaluate four deterministic gates. This project intentionally does not run agent code or assign subjective language-model scores.

## Gate definitions

Let **F** be a manifest-declared set of baseline failing/erroring tests; **P** be a manifest-declared set of baseline passing tests. Both are verified against the baseline report first, so benchmark labels cannot be accepted without evidence.

- **F2P** passes iff all F have status `passed` in candidate results.
- **P2P** passes iff all P retain status `passed`.
- **Regression gate** compares every baseline passing test, not only P. Missing, skipped, failed, and errored candidate outcomes are regressions. Tests absent from baseline but failing/erroring in the candidate are regressions too. The total must be at most `max_new_failures`.
- **Protected paths** passes iff no changed file path matches configured `fnmatch` glob patterns. The tool checks both old and new patch paths for delete/rename detection.

Overall = conjunction of all four gate results. Input validation errors return exit status 2 and are never treated as benchmark success.

## Repeatability and test provenance

Deterministic verdicts require stable test IDs and an unchanged baseline definition. For real usage, store the baseline and candidate results as immutable CI artifacts, verify artifact provenance, and run tests from clean checkouts under controlled dependency versions. This repository does **not** implement artifact signing or trusted execution.

## Threat model (limited)

A coding agent might modify tests to force a pass, delete failing tests, introduce a regression, or alter the expected test-set labels. This tool checks changed paths, missing tests, unchanged pass-to-pass tests, and baseline test status. It does not stop attackers with write access to both the manifest and the reported test artifacts, and it does not fully parse every possible Git binary patch variant.

## Future work

- Support schema-validated SARIF/Checkstyle-style reports and Git rename/binary edge cases.
- Add provenance checks for CI-generated artifacts and commit SHA matching.
- Compare benchmark verdicts to independently reviewed code fixes; measure precision/recall and uncertainty of heuristic gates.
- Add mutation testing to quantify whether test sets distinguish sound fixes from plausible incorrect patches.
- Test robustness against deliberately adversarial agents and patch transformations.

Research directions are proposals, not claimed completed studies.
