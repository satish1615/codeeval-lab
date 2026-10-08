import unittest
from codeeval.evaluate import evaluate
from codeeval.junit import TestCase
from codeeval.models import Benchmark, InputError


B = Benchmark('cache', ('test.fix',), ('test.stable',), ('tests/**',), 0)
BASELINE = {'test.fix': TestCase('test.fix', 'failed'),
            'test.stable': TestCase('test.stable', 'passed'),
            'test.unlisted': TestCase('test.unlisted', 'passed')}
CANDIDATE = {'test.fix': TestCase('test.fix', 'passed'),
             'test.stable': TestCase('test.stable', 'passed'),
             'test.unlisted': TestCase('test.unlisted', 'passed')}


class EvaluatorTests(unittest.TestCase):
    def test_pass_all_gates(self):
        result = evaluate(B, BASELINE, CANDIDATE, ('src/fix.py',))
        self.assertTrue(result.passed)
        self.assertEqual(result.as_dict()['summary']['fail_to_pass_rate'], 1)

    def test_unfixed_f2p_fails(self):
        candidate = {**CANDIDATE, 'test.fix': TestCase('test.fix', 'failed')}
        result = evaluate(B, BASELINE, candidate, ())
        self.assertFalse(result.gate_results['fail_to_pass'])

    def test_missing_f2p_fails(self):
        candidate = {k: v for k, v in CANDIDATE.items() if k != 'test.fix'}
        self.assertFalse(evaluate(B, BASELINE, candidate, ()).passed)

    def test_p2p_regression_fails(self):
        candidate = {**CANDIDATE, 'test.stable': TestCase('test.stable', 'skipped')}
        result = evaluate(B, BASELINE, candidate, ())
        self.assertFalse(result.gate_results['pass_to_pass'])
        self.assertIn('test.stable', result.new_failures)

    def test_unlisted_regression_caught(self):
        candidate = {k: v for k, v in CANDIDATE.items() if k != 'test.unlisted'}
        result = evaluate(B, BASELINE, candidate, ())
        self.assertFalse(result.gate_results['regressions'])

    def test_candidate_only_failure_counted(self):
        candidate = {**CANDIDATE, 'new': TestCase('new', 'errored')}
        self.assertIn('new', evaluate(B, BASELINE, candidate, ()).new_failures)

    def test_allow_one_unlisted_regression(self):
        candidate = {**CANDIDATE, 'test.unlisted': TestCase('test.unlisted', 'failed')}
        relaxed = Benchmark('cache', ('test.fix',), ('test.stable',), (), 1)
        self.assertTrue(evaluate(relaxed, BASELINE, candidate, ()).passed)

    def test_protected_test_modification(self):
        result = evaluate(B, BASELINE, CANDIDATE, ('tests/test_stable.py',))
        self.assertFalse(result.gate_results['protected_paths'])

    def test_baseline_must_confirm_initial_failure(self):
        bad = {**BASELINE, 'test.fix': TestCase('test.fix', 'passed')}
        with self.assertRaises(InputError):
            evaluate(B, bad, CANDIDATE, ())

    def test_baseline_must_confirm_existing_pass(self):
        bad = {**BASELINE, 'test.stable': TestCase('test.stable', 'errored')}
        with self.assertRaises(InputError):
            evaluate(B, bad, CANDIDATE, ())
