#!/usr/bin/env python3
"""Tests for schema download failures, cache, offline, and strict validation."""
import contextlib
import importlib.util
import io
import json
import pathlib
import tempfile
import unittest
from unittest import mock
from urllib.error import HTTPError

SCRIPT = pathlib.Path(__file__).resolve().parents[1] / 'scripts' / 'validate_against_live_schema.py'
spec = importlib.util.spec_from_file_location('schema_check', SCRIPT)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

# Deliberately small V2 schema for exercising validator behavior, not presented as official schema.
SCHEMA = {
    '$schema': 'https://json-schema.org/draft/2020-12/schema',
    'type': 'object',
    'properties': {
        'permissions': {'type': 'array'},
        'agents': {'type': 'object'},
        'mcp': {'type': 'object', 'properties': {'servers': {'type': 'object'}}},
        'compaction': {'type': 'object', 'properties': {'keep': {'type': 'object'}}},
        'default_agent': {'type': 'string'},
    },
    'additionalProperties': True,
}

class TestSchemaValidator(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        root = pathlib.Path(self.temp.name)
        self.path = root / 'opencode.jsonc'
        self.path.write_text(json.dumps({'permissions': [], 'mcp': {'servers': {}}, 'compaction': {'keep': {}}, 'default_agent': 'chat'}))
        self.cache = root / 'cache' / 'config-schema.json'
        self.base = ['--config', str(self.path), '--cache', str(self.cache)]

    def run_case(self, args):
        stdout = io.StringIO()
        stderr = io.StringIO()
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            rc = module.main(self.base + args)
        return rc, stdout.getvalue() + stderr.getvalue()

    def test_403_fallback_success_is_partial(self):
        error = HTTPError('https://opencode.ai/config.json', 403, 'Forbidden', {}, None)
        with mock.patch.object(module, 'fetch_schema', side_effect=error), mock.patch.object(module, 'cli_fallback', return_value=True):
            rc, msg = self.run_case([])
        self.assertEqual(rc, 0)
        self.assertIn('PARTIAL:', msg)
        self.assertIn('403', msg)
        self.assertNotIn('PASS: FULL', msg)

    def test_403_strict_mode_nonzero(self):
        error = HTTPError('https://opencode.ai/config.json', 403, 'Forbidden', {}, None)
        with mock.patch.object(module, 'fetch_schema', side_effect=error):
            rc, msg = self.run_case(['--require-schema'])
        self.assertEqual(rc, 2)
        self.assertIn('--require-schema', msg)

    def test_403_without_cli_is_explicitly_unverified(self):
        error = HTTPError('https://opencode.ai/config.json', 403, 'Forbidden', {}, None)
        with mock.patch.object(module, 'fetch_schema', side_effect=error), mock.patch.object(module, 'cli_fallback', return_value=False):
            rc, msg = self.run_case([])
        self.assertEqual(rc, 2)
        self.assertIn('UNVERIFIED', msg)

    def test_offline_with_explicit_schema(self):
        path = pathlib.Path(self.temp.name) / 'schema.json'
        path.write_text(json.dumps(SCHEMA))
        rc, msg = self.run_case(['--offline', '--schema-file', str(path)])
        self.assertEqual(rc, 0)
        self.assertIn('PASS: FULL', msg)

    def test_cached_schema_used_if_download_fails(self):
        module.atomic_store(self.cache, SCHEMA)
        with mock.patch.object(module, 'fetch_schema', side_effect=HTTPError('x',403,'Forbidden',{},None)):
            rc, msg = self.run_case([])
        self.assertEqual(rc, 0)
        self.assertIn('PASS: FULL', msg)
        self.assertIn('cache:', msg)

    def test_download_success_populates_cache(self):
        with mock.patch.object(module, 'fetch_schema', return_value=SCHEMA):
            rc, msg = self.run_case([])
        self.assertEqual(rc, 0)
        self.assertTrue(self.cache.exists())
        self.assertIn('PASS: FULL', msg)

    def test_schema_rejects_invalid_config(self):
        self.path.write_text(json.dumps({'permissions': 'incorrect', 'mcp': {'servers': {}}, 'compaction': {'keep': {}}}))
        path = pathlib.Path(self.temp.name) / 'schema.json'
        path.write_text(json.dumps(SCHEMA))
        rc, msg = self.run_case(['--schema-file', str(path)])
        self.assertEqual(rc, 1)
        self.assertIn('permissions', msg)

    def test_stale_schema_is_rejected(self):
        path = pathlib.Path(self.temp.name) / 'old-schema.json'
        path.write_text(json.dumps({'type': 'object', 'properties': {'permission': {'type': 'object'}}}))
        rc, msg = self.run_case(['--schema-file', str(path)])
        self.assertEqual(rc, 1)
        self.assertIn('stale or incompatible', msg)

    def test_invalid_config_json_fails_early(self):
        self.path.write_text('{"mcp":')
        rc, msg = self.run_case(['--offline'])
        self.assertEqual(rc, 1)
        self.assertIn('Could not parse configuration', msg)

    def test_jsonc_accepted_when_json5_available(self):
        self.path.write_text('{ // comment\n "permissions": [], "mcp": { "servers": {} }, "compaction": {"keep": {}}, }')
        path = pathlib.Path(self.temp.name) / 'schema.json'
        path.write_text(json.dumps(SCHEMA))
        rc, msg = self.run_case(['--schema-file', str(path)])
        self.assertEqual(rc, 0)
        self.assertIn('PASS: FULL', msg)

if __name__=='__main__': unittest.main()
