"""Behavioral tests: real SQLite persistence, controlled providers, real stdio MCP."""
import asyncio
import contextlib
import importlib.util
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'integrations/research-tools/src'))
from opencode_research_tools import zotero, openai_research
from opencode_research_tools.http import IntegrationError
from opencode_research_tools.state import Store
from opencode_research_tools.scispace import import_table


class TestResearchState(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.store = Store(self.tmp.name)
        self.r = self.store.create('research', 'What is the evidence?', {'providers': ['test']})

    def update(self, action, payload):
        self.r = self.store.update(self.r['id'], self.r['revision'], action, payload)

    def test_persistence_and_stale_revision(self):
        self.update('transition', {'state': 'running'})
        self.assertEqual(Store(self.tmp.name).get(self.r['id'])['state'], 'running')
        with self.assertRaisesRegex(IntegrationError, 'Revision conflict'):
            self.store.update(self.r['id'], 0, 'transition', {'state': 'paused'})
        self.assertEqual(self.store.get(self.r['id'])['revision'], 1)

    def test_transition_constraints_and_completeness(self):
        with self.assertRaises(IntegrationError):
            self.update('transition', {'state': 'completed'})
        self.update('transition', {'state': 'running'})
        with self.assertRaises(IntegrationError):
            self.update('transition', {'state': 'completed'})
        self.update('evidence', {'title': 'Paper', 'provider': 'test', 'url': 'https://example.org/paper', 'doi': '10.1000/test', 'access': 'abstract'})
        eid = self.r['evidence'][0]['id']
        with self.assertRaises(IntegrationError):
            self.update('report', {'text': 'Text', 'evidence_ids': ['invented']})
        self.update('report', {'text': 'Only abstract evidence is available.', 'evidence_ids': [eid]})
        self.update('transition', {'state': 'completed'})
        with self.assertRaises(IntegrationError):
            self.update('query', {'provider': 'test', 'query': 'more'})
        result = self.store.export(self.r['id'])
        self.assertIn('Only abstract evidence', result['markdown'])
        self.assertIn('https://example.org/paper', result['evidence_csv'])

    def test_duplicate_evidence_is_not_counted_twice(self):
        self.update('evidence', {'title': 'Paper', 'provider': 'test', 'url': 'https://example.org/a', 'doi': 'https://doi.org/10.1000/TEST'})
        with self.assertRaisesRegex(IntegrationError, 'Duplicate'):
            self.update('evidence', {'title': 'Same paper', 'provider': 'other', 'url': 'https://other.org/b', 'doi': '10.1000/test'})
        self.assertEqual(len(self.store.get(self.r['id'])['evidence']), 1)

    def test_screening_and_jobs(self):
        with self.assertRaises(IntegrationError):
            self.update('screen', {'evidence_id': 'missing', 'decision': 'include', 'reason': 'relevant'})
        self.update('job', {'provider': 'exa', 'job_id': 'same-run', 'status': 'running'})
        self.update('job', {'provider': 'exa', 'job_id': 'same-run', 'status': 'completed'})
        self.assertEqual(len(self.r['jobs']), 1)
        self.assertEqual(self.r['jobs']['exa:same-run']['status'], 'completed')

    def test_invalid_source_and_run_id(self):
        for url in ['file:///secret', 'https://user:password@example.org']:
            with self.assertRaises(IntegrationError):
                self.update('evidence', {'title': 'Bad', 'provider': 'test', 'url': url})
        with self.assertRaises(IntegrationError):
            self.store.get("' OR 1=1 --")

    def test_learning_objective_vs_qualitative_feedback(self):
        r = self.store.create('learning', 'Learn biology')
        r = self.store.update(r['id'], 0, 'attempt', {'question': 'Choose A or B', 'response': ' a ', 'correct_answer': 'A'})
        self.assertTrue(r['attempts'][0]['correct'])
        r = self.store.update(r['id'], 1, 'attempt', {'question': 'Explain why', 'response': 'My explanation', 'feedback': 'Review mechanism'})
        self.assertNotIn('correct', r['attempts'][1])
        self.assertEqual(r['attempts'][1]['grading'], 'qualitative-unverified')

    def test_schema_accepts_real_record(self):
        import jsonschema
        schema = json.loads((ROOT / 'schemas/research-run.schema.json').read_text())
        jsonschema.validate(self.r, schema)


class TestZotero(unittest.TestCase):
    @patch.object(zotero, 'request')
    def test_reads_use_fixed_api_and_bounded_parameters(self, req):
        req.return_value = ([], {})
        c = zotero.Zotero('local')
        c.search('TP53 & cancer', 5, 100)
        self.assertIn('q=TP53+%26+cancer', req.call_args.args[0])
        self.assertIn('start=100', req.call_args.args[0])
        self.assertNotIn('Zotero-API-Key', req.call_args.kwargs['headers'])
        for key in ['../../private', 'https://attacker.org', 'x']:
            with self.assertRaises(IntegrationError):
                c.get(key)
        with self.assertRaises(IntegrationError):
            c.export(['ABCDEFGH'], 'unsupported')

    @patch.object(zotero, 'request')
    def test_import_digest_gate_has_no_network_effect(self, req):
        items = [{'itemType': 'journalArticle', 'title': 'Title'}]
        c = zotero.Zotero('local')
        p = c.preview_import(items)
        self.assertTrue(p['digest'])
        with self.assertRaises(IntegrationError):
            c.import_items(items, 'wrong')
        req.assert_not_called()

    @patch.object(zotero, 'request')
    def test_duplicate_import_has_no_writes(self, req):
        req.return_value = ([{'data': {'DOI': '10.1000/test'}}], {})
        c = zotero.Zotero('local')
        items = [{'itemType': 'journalArticle', 'title': 'Title', 'DOI': '10.1000/test'}]
        with self.assertRaisesRegex(IntegrationError, 'Existing DOI'):
            c.import_items(items, c.preview_import(items)['digest'])
        self.assertEqual(req.call_count, 1)
        self.assertEqual(len(req.call_args.args), 1)

    @patch.object(zotero, 'request')
    def test_local_authorization_and_one_submission(self, req):
        req.side_effect = [('', {'Zotero-Server-ID': 'server-1'}), ({'key': 'not-a-real-key'}, {}), ({'successful': {'0': {'key': 'ABCDEFGH'}}}, {})]
        c = zotero.Zotero('local')
        items = [{'itemType': 'journalArticle', 'title': 'Reviewed title'}]
        result = c.import_items(items, c.preview_import(items)['digest'])
        self.assertIn('successful', result['result'])
        self.assertEqual(req.call_count, 3)
        last = req.call_args.args
        self.assertEqual(last[1], 'POST')
        self.assertEqual(last[3]['Zotero-Server-ID'], 'server-1')
        self.assertEqual(last[3]['Zotero-API-Key'], 'not-a-real-key')

    @patch.object(zotero, 'request')
    def test_older_local_api_cannot_import(self, req):
        req.return_value = ('', {})
        c = zotero.Zotero('local')
        items = [{'itemType': 'journalArticle', 'title': 'Title'}]
        with self.assertRaisesRegex(IntegrationError, '10'):
            c.import_items(items, c.preview_import(items)['digest'])
        self.assertEqual(req.call_count, 1)

    @patch.object(zotero, 'request')
    def test_bbt_mutations_are_not_exposed(self, req):
        with self.assertRaises(IntegrationError):
            zotero.better_bibtex('item.regenerate_key', [])
        req.assert_not_called()


class TestProvidersAndSetup(unittest.TestCase):
    def test_scispace_exports_preserve_analytical_columns(self):
        result = import_table('Title,DOI,Methods\nPaper,10.1000/a,Observational\n')
        self.assertEqual(result['rows'][0]['Methods'], 'Observational')
        self.assertEqual(result['origin'], 'user-supplied-export')
        with self.assertRaises(IntegrationError):
            import_table('{}', 'json')

    @patch.object(openai_research, 'request')
    def test_openai_spend_and_configuration_gates(self, req):
        for approval in [False, 'false', 1]:
            with self.assertRaises(IntegrationError):
                openai_research.start('question', approval)
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(IntegrationError):
                openai_research.start('question', True)
        req.assert_not_called()

    @patch.object(openai_research, 'request')
    def test_openai_request_preserves_full_response_and_citations(self, req):
        payload = {'id': 'resp_test', 'output': [{'type': 'message', 'content': [{'text': 'Result', 'annotations': [{'url': 'https://example.org'}]}]}]}
        req.return_value = (payload, {})
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'fake', 'OPENAI_RESEARCH_MODEL': 'configured-model'}):
            self.assertEqual(openai_research.start('question', True), payload)
        body = req.call_args.args[2]
        self.assertTrue(body['background'])
        self.assertEqual(body['tools'], [{'type': 'web_search'}])
        self.assertEqual(req.call_count, 1)

    def test_scispace_setup_dry_run_and_apply(self):
        script = ROOT / 'scripts/configure_research.py'
        spec = importlib.util.spec_from_file_location('setup_research', script)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        for url in ['http://scispace.com/mcp', 'https://attacker.org/mcp', 'https://scispace.com/mcp?key=secret']:
            with self.assertRaises(ValueError):
                mod.configure({}, url)
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / 'config.json'
            original = (ROOT / 'opencode.jsonc').read_text()
            path.write_text(original)
            args = [sys.executable, str(script), '--config', str(path), '--scispace-url', 'https://example.scispace.com/mcp', '--provider-confirmed']
            subprocess.run(args, check=True, capture_output=True)
            self.assertEqual(path.read_text(), original)
            subprocess.run(args + ['--apply'], check=True, capture_output=True)
            cfg = json.loads(path.read_text())
            self.assertTrue(cfg['mcp']['servers']['scispace']['disabled'])
            self.assertEqual(len(list(Path(d).glob('*.backup-*'))), 1)

    def test_real_stdio_mcp_catalog_and_no_network_preview(self):
        if not importlib.util.find_spec('mcp'):
            self.skipTest('Install research-tools[mcp,test] for stdio integration test')
        from mcp import ClientSession, StdioServerParameters
        from mcp.client.stdio import stdio_client
        async def check():
            params = StdioServerParameters(command=sys.executable, args=['-m', 'opencode_research_tools', 'serve-zotero'], env={**os.environ, 'PYTHONPATH': str(ROOT / 'integrations/research-tools/src')})
            async with stdio_client(params) as (read, write):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    catalog = await session.list_tools()
                    names = {t.name for t in catalog.tools}
                    self.assertIn('search', names)
                    self.assertIn('import_items', names)
                    self.assertNotIn('delete', names)
                    result = await session.call_tool('import_preview', {'items': [{'itemType': 'journalArticle', 'title': 'Test'}]})
                    self.assertFalse(result.isError)
                    bad = await session.call_tool('item', {'key': '../../private'})
                    self.assertTrue(bad.isError)
        asyncio.run(check())


class TestHTTPAndPermissions(unittest.TestCase):
    def test_redirect_does_not_forward_credentials(self):
        import threading
        from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
        from opencode_research_tools.http import request
        calls = []
        class Handler(BaseHTTPRequestHandler):
            def do_GET(self):
                calls.append(self.path)
                self.send_response(302)
                self.send_header('Location', '/unexpected-target')
                self.end_headers()
            def log_message(self, *args):
                pass
        server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            with self.assertRaisesRegex(IntegrationError, 'Redirect refused'):
                request(f'http://127.0.0.1:{server.server_port}/start', headers={'Authorization': 'Bearer fake'})
            self.assertEqual(calls, ['/start'])
        finally:
            server.shutdown()
            server.server_close()
            thread.join()

    def test_effective_agent_rules_keep_push_and_edits_restricted(self):
        import fnmatch
        import yaml
        cfg = json.loads((ROOT / 'opencode.jsonc').read_text())
        for name in ['deep-research', 'learn']:
            meta = yaml.safe_load((ROOT / f'agents/{name}.md').read_text().split('---', 2)[1])
            def effect(action, resource):
                result = None
                for r in cfg['permissions'] + meta['permissions']:
                    if fnmatch.fnmatchcase(action, r['action']) and fnmatch.fnmatchcase(resource, r['resource']):
                        result = r['effect']
                return result
            self.assertEqual(effect('shell', 'git push origin main'), 'deny')
            self.assertEqual(effect('edit', 'opencode.jsonc'), 'deny')
            self.assertEqual(effect('edit', 'research/report.md'), 'ask')
            self.assertEqual(effect('shell', 'opencode-research-tools run'), 'ask')
            self.assertEqual(effect('subagent', 'coder'), 'deny')
        self.assertTrue(all(s['disabled'] for s in cfg['mcp']['servers'].values()))
        self.assertNotIn('scispace', cfg['mcp']['servers'])

if __name__ == '__main__':
    unittest.main()
