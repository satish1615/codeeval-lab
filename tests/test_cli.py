import json
import subprocess
import sys
import tempfile
from pathlib import Path
import unittest


REPO = Path(__file__).resolve().parents[1]
EX = REPO / 'examples'


class CLITests(unittest.TestCase):
    def run_cli(self, *args):
        return subprocess.run([sys.executable, '-m', 'codeeval', 'evaluate',
             '--manifest', str(EX/'benchmark.json'), '--baseline', str(EX/'baseline.xml'),
             '--candidate', str(EX/'candidate.xml'), '--diff', str(EX/'change.patch'),
             *args], text=True, capture_output=True, check=False)

    def test_example_passes(self):
        p = self.run_cli()
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertIn('PASS', p.stdout)

    def test_json_report(self):
        p = self.run_cli('--format', 'json')
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertTrue(json.loads(p.stdout)['passed'])

    def test_markdown_report(self):
        p = self.run_cli('--format', 'markdown')
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertIn('| protected_paths | PASS |', p.stdout)

    def test_writes_report(self):
        with tempfile.TemporaryDirectory() as d:
            output = Path(d) / 'result.json'
            p = self.run_cli('--format', 'json', '--out', str(output))
            self.assertEqual(p.returncode, 0, p.stderr)
            self.assertTrue(json.loads(output.read_text())['passed'])
            self.assertFalse(p.stdout)

    def test_missing_input_exit_two(self):
        p = self.run_cli('--candidate', 'nonexistent.xml')
        self.assertEqual(p.returncode, 2)
        self.assertIn('input error', p.stderr)
