"""Synthetic-fixture path and parser checks; no live config or MCP operations."""

import contextlib
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'integrations/research-tools/src'))
from opencode_research_tools.http import IntegrationError
from opencode_research_tools.state import Store


def load_script(name):
    spec = importlib.util.spec_from_file_location('path_safety_' + name, ROOT / 'scripts' / (name + '.py'))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class TestSafeStatePaths(unittest.TestCase):
    def test_linked_ancestor_cannot_create_state_outside_selected_path(self):
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp).resolve()
            outside = base / 'outside'
            outside.mkdir()
            link = base / 'link'
            link.symlink_to(outside, target_is_directory=True)
            with self.assertRaisesRegex(IntegrationError, 'symlink'):
                Store(link / 'state')
            self.assertEqual(list(outside.iterdir()), [])

    def test_dangling_link_and_non_directory_ancestor_are_refused(self):
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp).resolve()
            link = base / 'link'
            link.symlink_to(base / 'missing', target_is_directory=True)
            file = base / 'file'
            file.write_text('keep')
            for ancestor in (link, file):
                with self.subTest(path=ancestor), self.assertRaises(IntegrationError):
                    Store(ancestor / 'state')
            self.assertEqual(file.read_text(), 'keep')
            self.assertFalse((base / 'missing').exists())

    def test_state_remains_usable_at_an_ordinary_path(self):
        with tempfile.TemporaryDirectory() as temp:
            store = Store(Path(temp).resolve() / 'state')
            record = store.create('research', 'Synthetic question')
            self.assertEqual(store.get(record['id'])['question'], 'Synthetic question')
            self.assertEqual(store.path.stat().st_mode & 0o777, 0o600)

    def test_existing_store_rechecks_ancestors_before_opening(self):
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp).resolve()
            parent = base / 'parent'
            store = Store(parent / 'state')
            parent.rename(base / 'original-parent')
            outside = base / 'outside'
            outside.mkdir()
            parent.symlink_to(outside, target_is_directory=True)
            with self.assertRaisesRegex(IntegrationError, 'symlink'):
                store.list()
            self.assertEqual(list(outside.iterdir()), [])


class TestSafeSetupPaths(unittest.TestCase):
    def test_setup_refuses_linked_parent_before_reading_fixture(self):
        module = load_script('configure_research')
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp).resolve()
            outside = base / 'outside'
            outside.mkdir()
            fixture = outside / 'config.jsonc'
            fixture.write_text(json.dumps({'mcp': {'servers': {}}, 'permissions': [], 'policies': []}))
            original = fixture.read_bytes()
            link = base / 'link'
            link.symlink_to(outside, target_is_directory=True)
            argv = ['configure_research.py', '--config', str(link / fixture.name),
                    '--scispace-url', 'https://scispace.com/mcp', '--provider-confirmed']
            with patch.object(sys, 'argv', argv), patch.object(Path, 'read_text', return_value=original.decode()) as read, \
                    contextlib.redirect_stderr(io.StringIO()), contextlib.redirect_stdout(io.StringIO()):
                with self.assertRaises(SystemExit) as caught:
                    module.main()
                self.assertEqual(caught.exception.code, 2)
                read.assert_not_called()
            self.assertEqual(fixture.read_bytes(), original)
            self.assertEqual(list(outside.iterdir()), [fixture])

    def test_setup_dry_run_keeps_an_ordinary_fixture_unchanged(self):
        module = load_script('configure_research')
        with tempfile.TemporaryDirectory() as temp:
            fixture = Path(temp).resolve() / 'config.jsonc'
            text = json.dumps({'mcp': {'servers': {}}, 'permissions': [], 'policies': []})
            fixture.write_text(text)
            argv = ['configure_research.py', '--config', str(fixture),
                    '--scispace-url', 'https://scispace.com/mcp', '--provider-confirmed']
            stdout = io.StringIO()
            with patch.object(sys, 'argv', argv), contextlib.redirect_stdout(stdout):
                module.main()
            self.assertIn('Dry-run', stdout.getvalue())
            self.assertEqual(fixture.read_text(), text)

    def test_retirement_refuses_linked_source_and_archive_parents(self):
        module = load_script('retire_legacy_firecrawl')
        for linked in ('commands', 'archive'):
            with self.subTest(linked=linked), tempfile.TemporaryDirectory() as temp:
                base = Path(temp).resolve()
                config = base / 'config'
                config.mkdir()
                outside = base / 'outside'
                outside.mkdir()
                (config / linked).symlink_to(outside, target_is_directory=True)
                if linked != 'commands':
                    (config / 'commands').mkdir()
                target = config / 'commands/firecrawl-research.md'
                payload = b'synthetic known legacy command'
                target.write_bytes(payload)
                with patch.object(module, 'KNOWN_SHA256', hashlib.sha256(payload).hexdigest()), \
                        contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                    result = module.main(['--config-dir', str(config), '--apply'])
                self.assertEqual(result, 2)
                self.assertEqual(target.read_bytes(), payload)
                self.assertEqual(sorted(p.name for p in outside.iterdir()),
                                 [target.name] if linked == 'commands' else [])

    def test_retirement_archives_only_the_matching_ordinary_fixture(self):
        module = load_script('retire_legacy_firecrawl')
        with tempfile.TemporaryDirectory() as temp:
            config = Path(temp).resolve()
            (config / 'commands').mkdir()
            target = config / 'commands/firecrawl-research.md'
            payload = b'synthetic known legacy command'
            target.write_bytes(payload)
            with patch.object(module, 'KNOWN_SHA256', hashlib.sha256(payload).hexdigest()), \
                    contextlib.redirect_stdout(io.StringIO()):
                result = module.main(['--config-dir', str(config), '--apply'])
            self.assertEqual(result, 0)
            self.assertFalse(target.exists())
            archives = list((config / 'archive').glob('*/firecrawl-research.md'))
            self.assertEqual(len(archives), 1)
            self.assertEqual(archives[0].read_bytes(), payload)


class TestConfigurationParser(unittest.TestCase):
    def test_pure_json_and_jsonc_have_identical_server_inventory(self):
        module = load_script('mcpctl')
        expected = {'fixture': {'disabled': True}}
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / 'config.jsonc'
            for text in (json.dumps({'mcp': {'servers': expected}}),
                         '{ // synthetic fixture\n "mcp": {"servers": {"fixture": {"disabled": true,},},},}'):
                path.write_text(text)
                self.assertEqual(module.list_config(path), expected)

    def test_jsonc_missing_optional_parser_has_clear_error(self):
        module = load_script('mcpctl')
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / 'config.jsonc'
            path.write_text('{/*comment*/"mcp":{"servers":{}}}')
            with patch.dict(sys.modules, {'json5': None}), \
                    self.assertRaisesRegex(module.ControlError, 'json5'):
                module.list_config(path)

    def test_malformed_config_fails_with_control_error(self):
        module = load_script('mcpctl')
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / 'config.jsonc'
            for text in ('invalid', '[]', '{}', '{"mcp":{"servers":[]}}',
                         '{"mcp":{"servers":{"fixture":null}}}'):
                with self.subTest(text=text):
                    path.write_text(text)
                    with self.assertRaises(module.ControlError):
                        module.list_config(path)


if __name__ == '__main__':
    unittest.main()
