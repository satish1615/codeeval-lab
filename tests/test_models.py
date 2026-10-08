import unittest
from codeeval.models import Benchmark, InputError


BASE = {"schema_version": 1, "name": "sample", "fail_to_pass": ["mod.test_fix"],
        "pass_to_pass": ["mod.test_existing"], "protected_paths": ["tests/**"]}


class BenchmarkTests(unittest.TestCase):
    def test_valid(self):
        b = Benchmark.from_dict(BASE)
        self.assertEqual(b.max_new_failures, 0)
        self.assertEqual(b.fail_to_pass, ("mod.test_fix",))

    def test_schema_required(self):
        for version in [None, 2, True]:
            with self.subTest(version=version), self.assertRaises(InputError):
                Benchmark.from_dict({**BASE, "schema_version": version})

    def test_f2p_required(self):
        with self.assertRaises(InputError):
            Benchmark.from_dict({**BASE, "fail_to_pass": []})

    def test_duplicate_ids(self):
        with self.assertRaises(InputError):
            Benchmark.from_dict({**BASE, "fail_to_pass": ["a", "a"]})

    def test_overlap(self):
        with self.assertRaises(InputError):
            Benchmark.from_dict({**BASE, "pass_to_pass": ["mod.test_fix"]})

    def test_max_new_failures_rejects_boolean(self):
        with self.assertRaises(InputError):
            Benchmark.from_dict({**BASE, "max_new_failures": True})

    def test_max_new_failures_rejects_negative(self):
        with self.assertRaises(InputError):
            Benchmark.from_dict({**BASE, "max_new_failures": -1})

    def test_unsafe_glob(self):
        with self.assertRaises(InputError):
            Benchmark.from_dict({**BASE, "protected_paths": ["../tests/**"]})
