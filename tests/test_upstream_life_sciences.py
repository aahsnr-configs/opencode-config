"""Offline completeness checks against the pinned upstream plugin inventory."""
import ast
import hashlib
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
LOCK = json.loads((ROOT / 'life-sciences/upstream-lock.json').read_text())
ADAPTED = json.loads((ROOT / 'life-sciences/opencode-adaptations.json').read_text())

class UpstreamInventory(unittest.TestCase):
    def test_every_upstream_file_matches_its_recorded_provenance(self):
        self.assertEqual(ADAPTED['upstream_commit'], LOCK['commit'])
        adaptations = {e['path']: e for e in ADAPTED['files']}
        self.assertEqual(len(adaptations), len(ADAPTED['files']))
        originals = {e['path']: e['git_blob_sha1'] for e in LOCK['files']}
        self.assertTrue(set(adaptations) <= set(originals))
        for entry in LOCK['files']:
            with self.subTest(path=entry['path']):
                data = (ROOT / entry['path']).read_bytes()
                digest = hashlib.sha1(b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest()
                adaptation = adaptations.get(entry['path'])
                if adaptation:
                    self.assertEqual(adaptation['upstream_git_blob_sha1'], entry['git_blob_sha1'])
                    self.assertTrue(adaptation['reason'].strip())
                    self.assertNotEqual(adaptation['installed_git_blob_sha1'], entry['git_blob_sha1'])
                    self.assertEqual(digest, adaptation['installed_git_blob_sha1'])
                else:
                    self.assertEqual(digest, entry['git_blob_sha1'])

    def test_all_skills_and_python_sources(self):
        names = [e['path'] for e in LOCK['files'] if e['path'].endswith('/SKILL.md')]
        self.assertEqual(len(names), LOCK['skill_count'])
        self.assertEqual(len(names), len(set(names)))
        for entry in LOCK['files']:
            if entry['path'].endswith('.py'):
                ast.parse((ROOT / entry['path']).read_text(), filename=entry['path'])
