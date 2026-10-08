import tempfile
from pathlib import Path
import unittest
from codeeval.junit import parse_junit
from codeeval.models import InputError


class JUnitTests(unittest.TestCase):
    def parse(self, data):
        with tempfile.TemporaryDirectory() as d:
            f = Path(d) / 'out.xml'
            f.write_text(data)
            return parse_junit(f)

    def test_suites(self):
        cases = self.parse('<testsuites><testsuite><testcase classname="a" name="one"/>'
                           '<testcase classname="a" name="two"><failure message="bad"/></testcase>'
                           '</testsuite></testsuites>')
        self.assertEqual(cases['a.one'].status, 'passed')
        self.assertEqual(cases['a.two'].status, 'failed')
        self.assertEqual(cases['a.two'].detail, 'bad')

    def test_error_and_skip(self):
        cases = self.parse('<testsuite><testcase name="one"><error/></testcase>'
                           '<testcase name="two"><skipped/></testcase></testsuite>')
        self.assertEqual(cases['one'].status, 'errored')
        self.assertEqual(cases['two'].status, 'skipped')

    def test_duplicate_rejected(self):
        with self.assertRaisesRegex(InputError, 'duplicate'):
            self.parse('<testsuite><testcase name="one"/><testcase name="one"/></testsuite>')

    def test_multi_status_rejected(self):
        with self.assertRaises(InputError):
            self.parse('<testsuite><testcase name="one"><error/><failure/></testcase></testsuite>')

    def test_empty_rejected(self):
        with self.assertRaises(InputError):
            self.parse('<testsuite/>')

    def test_malformed_rejected(self):
        with self.assertRaises(InputError):
            self.parse('<testsuite><testcase>')

    def test_wrong_root(self):
        with self.assertRaises(InputError):
            self.parse('<root><testcase name="x"/></root>')

    def test_xml_namespace(self):
        cases = self.parse('<testsuite xmlns="urn:example"><testcase name="x"/></testsuite>')
        self.assertIn('x', cases)
