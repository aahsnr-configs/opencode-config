"""Offline completeness checks against the pinned upstream plugin inventory."""
import ast
import hashlib
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
LOCK = json.loads((ROOT / 'life-sciences/upstream-lock.json').read_text())

class UpstreamInventory(unittest.TestCase):
    def test_every_upstream_file_is_present_and_unmodified(self):
        for entry in LOCK['files']:
            with self.subTest(path=entry['path']):
                data = (ROOT / entry['path']).read_bytes()
                digest = hashlib.sha1(b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest()
                self.assertEqual(digest, entry['git_blob_sha1'])

    def test_all_skills_and_python_sources(self):
        names = [e['path'] for e in LOCK['files'] if e['path'].endswith('/SKILL.md')]
        self.assertEqual(len(names), LOCK['skill_count'])
        self.assertEqual(len(names), len(set(names)))
        for entry in LOCK['files']:
            if entry['path'].endswith('.py'):
                ast.parse((ROOT / entry['path']).read_text(), filename=entry['path'])
