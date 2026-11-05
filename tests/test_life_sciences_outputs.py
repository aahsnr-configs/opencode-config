"""Offline regression checks for standalone helper raw-output safety."""
import contextlib
import importlib.util
import io
import inspect
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
EXCLUDED = {'variant_resolution.py', 'gtex_eqtl.py', 'map_locus_to_gene.py'}


def load(path):
    name = 'output_test_' + path.parent.parent.name.replace('-', '_') + '_' + path.stem
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


class RawOutputSafety(unittest.TestCase):
    def savers(self):
        for path in sorted((ROOT / 'skills').glob('*/scripts/*.py')):
            if (path.name.startswith('test') or path.name in EXCLUDED
                    or path.name.endswith('_phewas.py')):
                continue
            module = load(path)
            for name in ('_save_raw_output', '_save_raw_text', '_save_raw', '_save'):
                function = getattr(module, name, None)
                if function is not None:
                    yield path, module, function
                    break

    def save(self, function, output_path):
        args = {
            'raw_output': 'saved', 'raw_text': 'saved', 'raw_output_path': output_path,
            'base_url': 'https://example.org', 'suffix': 'json', 'rid': 'TEST123',
            'result_format': 'json2', 'data': {'saved': True},
        }
        return function(**{name: args[name] for name in inspect.signature(function).parameters})

    def test_symlink_cannot_overwrite_an_existing_file(self):
        module = load(ROOT / 'skills/alphafold-skill/scripts/rest_request.py')
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp) / 'keep.txt'
            target.write_text('keep this')
            link = Path(temp) / 'raw.json'
            link.symlink_to(target)
            with self.assertRaises(FileExistsError):
                module._save_raw_output('replacement', str(link), 'https://example.org', 'json')
            self.assertEqual(target.read_text(), 'keep this')

    def test_all_savers_refuse_existing_outputs(self):
        for path, module, function in self.savers():
            with self.subTest(path=path), tempfile.TemporaryDirectory() as temp:
                target = Path(temp) / 'existing.json'
                target.write_text('keep this')
                link = Path(temp) / 'link.json'
                link.symlink_to(target)
                for output in (target, link):
                    with self.assertRaises(FileExistsError):
                        self.save(function, str(output))
                self.assertEqual(target.read_text(), 'keep this')

    def test_all_savers_use_unique_private_default_directories(self):
        make_directory = tempfile.mkdtemp
        for path, module, function in self.savers():
            with self.subTest(path=path), tempfile.TemporaryDirectory() as temp:
                with patch.object(module.tempfile, 'mkdtemp',
                                  side_effect=lambda **kw: make_directory(dir=temp, **kw)):
                    first = Path(self.save(function, None))
                    second = Path(self.save(function, None))
                self.assertNotEqual(first, second)
                self.assertEqual(first.parent.stat().st_mode & 0o777, 0o700)
                self.assertTrue(first.read_text())
                self.assertTrue(second.read_text())

    def test_missing_query_files_return_json_errors(self):
        scripts = [
            'bgee-skill/scripts/sparql_request.py',
            'civic-skill/scripts/civic_graphql.py',
            'gnomad-graphql-skill/scripts/gnomad_graphql.py',
            'opentargets-skill/scripts/opentargets_graphql.py',
        ]
        with tempfile.TemporaryDirectory() as temp:
            for script in scripts:
                with self.subTest(script=script):
                    module = load(ROOT / 'skills' / script)
                    output = io.StringIO()
                    payload = {'query_path': str(Path(temp) / 'absent.graphql')}
                    with patch.object(sys, 'stdin', io.StringIO(json.dumps(payload))), \
                         contextlib.redirect_stdout(output):
                        code = module.main()
                    self.assertEqual(code, 1)
                    self.assertEqual(json.loads(output.getvalue())['error']['code'], 'file_error')

    def test_inline_savers_refuse_symlinks_and_use_unique_defaults(self):
        cases = [
            ('bgee-skill/scripts/sparql_request.py', {'query': 'ASK {}'}, {'boolean': True}),
            ('civic-skill/scripts/civic_graphql.py', {'query': '{ __typename }'}, {'data': {'__typename': 'Query'}}),
            ('gnomad-graphql-skill/scripts/gnomad_graphql.py', {'query': '{ __typename }'}, {'data': {'__typename': 'Query'}}),
            ('opentargets-skill/scripts/opentargets_graphql.py', {'query': '{ __typename }'}, {'data': {'__typename': 'Query'}}),
            ('opentargets-skill/scripts/opentargets_disease_heatmap.py', {'ensembl_id': 'ENSG00000141510'},
             {'data': {'target': {'id': 'ENSG00000141510', 'approvedSymbol': 'TP53',
                                 'associatedDiseases': {'count': 0, 'rows': []}}}}),
            ('ncbi-clinicaltables-skill/scripts/ncbi_gene_clinicaltables.py', {'terms': 'TP53'}, [0, [], {}, []]),
        ]
        from unittest.mock import Mock
        make_directory = tempfile.mkdtemp
        for script, payload, response_data in cases:
            with self.subTest(script=script), tempfile.TemporaryDirectory() as temp:
                module = load(ROOT / 'skills' / script)
                response = Mock()
                response.headers = {'content-type': 'application/json'}
                response.text = json.dumps(response_data)
                response.status_code = 200
                response.encoding = 'utf-8'
                response.iter_content.side_effect = lambda **kw: iter([response.text.encode('utf-8')])
                response.json.return_value = response_data
                response.raise_for_status.return_value = None
                target = Path(temp) / 'existing.json'
                target.write_text('keep this')
                link = Path(temp) / 'link.json'
                link.symlink_to(target)
                with patch.object(module.requests, 'get', return_value=response), \
                     patch.object(module.requests, 'post', return_value=response), \
                     patch.object(module.tempfile, 'mkdtemp',
                                  side_effect=lambda **kw: make_directory(dir=temp, **kw)):
                    for output in (target, link):
                        stdout = io.StringIO()
                        value = {**payload, 'save_raw': True, 'raw_output_path': str(output)}
                        with patch.object(sys, 'stdin', io.StringIO(json.dumps(value))), \
                             contextlib.redirect_stdout(stdout):
                            code = module.main()
                        self.assertEqual(code, 1)
                        self.assertEqual(json.loads(stdout.getvalue())['error']['code'], 'file_error')
                    first = module.execute({**payload, 'save_raw': True})
                    second = module.execute({**payload, 'save_raw': True})
                self.assertTrue(first['ok'], first)
                self.assertTrue(second['ok'], second)
                self.assertNotEqual(first['raw_output_path'], second['raw_output_path'])
                self.assertEqual(Path(first['raw_output_path']).parent.stat().st_mode & 0o777, 0o700)
                self.assertEqual(target.read_text(), 'keep this')


if __name__ == '__main__':
    unittest.main()
