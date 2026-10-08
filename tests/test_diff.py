import unittest
from codeeval.diff import changed_paths, protected_changes
from codeeval.models import InputError


class DiffTests(unittest.TestCase):
    def test_standard_patch(self):
        data = 'diff --git a/src/a.py b/src/a.py\n--- a/src/a.py\n+++ b/src/a.py\n@@ -1 +1 @@\n-x\n+y\n'
        self.assertEqual(changed_paths(data), ('src/a.py',))

    def test_added_file(self):
        data = '--- /dev/null\n+++ b/src/new.py\n'
        self.assertEqual(changed_paths(data), ('src/new.py',))

    def test_deleted_file(self):
        data = '--- a/tests/test_x.py\n+++ /dev/null\n'
        self.assertEqual(changed_paths(data), ('tests/test_x.py',))

    def test_rename(self):
        data = 'rename from src/old.py\nrename to src/new.py\n'
        self.assertEqual(changed_paths(data), ('src/new.py', 'src/old.py'))

    def test_quoted_path(self):
        data = '+++ "b/src/my file.py"\n'
        self.assertEqual(changed_paths(data), ('src/my file.py',))

    def test_protected_globs(self):
        self.assertEqual(protected_changes(('src/a.py', 'tests/x.py'), ('tests/**',)), ['tests/x.py'])

    def test_unsafe_patch_path(self):
        with self.assertRaises(InputError):
            changed_paths('+++ b/../tests/test.py')

    def test_binary_patch_header(self):
        data = 'diff --git a/tests/data.bin b/tests/data.bin\nGIT binary patch\n'
        self.assertEqual(changed_paths(data), ('tests/data.bin',))

    def test_quoted_git_header(self):
        data = 'diff --git "a/tests/a b.bin" "b/tests/a b.bin"\n'
        self.assertEqual(changed_paths(data), ('tests/a b.bin',))

    def test_invalid_git_header(self):
        with self.assertRaises(InputError):
            changed_paths('diff --git a/x\n')

    def test_empty_patch(self):
        self.assertEqual(changed_paths(''), ())

    def test_unrecognized_patch(self):
        with self.assertRaises(InputError):
            changed_paths('nonsense diff')
