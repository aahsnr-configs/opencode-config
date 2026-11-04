"""Offline execution checks for the pinned life-science skill installation."""
import ast
import importlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
LOCK = json.loads((ROOT / 'life-sciences/upstream-lock.json').read_text())


def has_entrypoint(path):
    """Find executable guards without importing helpers or executing their code."""
    for node in ast.parse(path.read_text()).body:
        if not isinstance(node, ast.If):
            continue
        test = node.test
        if (isinstance(test, ast.Compare)
                and isinstance(test.left, ast.Name)
                and test.left.id == '__name__'
                and len(test.ops) == 1 and isinstance(test.ops[0], ast.Eq)
                and len(test.comparators) == 1
                and isinstance(test.comparators[0], ast.Constant)
                and test.comparators[0].value == '__main__'):
            return True
    return False


class TestLifeSciencesRuntime(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Missing runtime dependencies are failures, rather than skipped checks.
        importlib.import_module('requests')
        cls.temp = tempfile.TemporaryDirectory(prefix='opencode-life-runtime-')
        cls.addClassCleanup(cls.temp.cleanup)
        base = Path(cls.temp.name)
        cls.workspace = base / 'research'
        cls.workspace.mkdir()
        cls.env = {**os.environ, 'XDG_CONFIG_HOME': str(base / 'xdg'),
                   'PYTHONDONTWRITEBYTECODE': '1'}
        cls.installed = base / 'xdg/opencode'
        result = subprocess.run(
            ['bash', str(ROOT / 'install.sh'), '--apply'],
            cwd=cls.workspace, env=cls.env, capture_output=True, text=True,
            timeout=60,
        )
        if result.returncode:
            raise AssertionError(f'Isolated installation failed: {result.stderr}')

    def execute(self, script, *args, input=None):
        return subprocess.run(
            [sys.executable, str(script), *args], input=input,
            cwd=self.workspace, env=self.env, capture_output=True, text=True,
            timeout=60,
        )

    def test_installed_pinned_files_match_checkout_bytes(self):
        for entry in LOCK['files']:
            with self.subTest(path=entry['path']):
                relative = Path(entry['path'])
                self.assertEqual(relative.parts[0], 'skills')
                self.assertEqual(
                    (self.installed / relative).read_bytes(),
                    (ROOT / relative).read_bytes(),
                )

    def test_bundled_upstream_suites(self):
        suites = [entry['path'] for entry in LOCK['files']
                  if Path(entry['path']).name.startswith('test_')
                  and entry['path'].endswith('.py')]
        self.assertEqual(len(suites), 3)
        for path in suites:
            with self.subTest(path=path):
                result = self.execute(self.installed / path)
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                self.assertRegex(result.stderr, r'Ran [1-9][0-9]* tests?')
                self.assertNotIn('skipped=', result.stderr)

    def test_installed_entrypoints_from_research_workspace(self):
        scripts = [entry['path'] for entry in LOCK['files']
                   if entry['path'].endswith('.py')
                   and not Path(entry['path']).name.startswith('test_')
                   and has_entrypoint(ROOT / entry['path'])]
        self.assertTrue(scripts)
        for path in scripts:
            with self.subTest(path=path):
                installed = self.installed / path
                if installed.name == 'map_locus_to_gene.py':
                    # The mapper has an argparse interface, not JSON stdin.
                    result = self.execute(installed, '--help')
                    self.assertEqual(result.returncode, 0, result.stderr)
                    self.assertIn('--input-json', result.stdout)
                    self.assertIn('--trait-query', result.stdout)
                else:
                    # Parsing fails before any provider request can occur.
                    result = self.execute(installed, input='{invalid json')
                    self.assertNotEqual(result.returncode, 0, result.stdout)
                    output = json.loads(result.stdout)
                    self.assertIs(output.get('ok'), False)
                    self.assertEqual(output['error']['code'], 'invalid_json')
                self.assertNotIn('Traceback', result.stdout + result.stderr)
        self.assertEqual(list(self.workspace.iterdir()), [])


if __name__ == '__main__':
    unittest.main()
