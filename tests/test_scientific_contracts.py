"""Controlled-response regression checks for standalone scientific clients."""
import importlib.util
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
import zipfile

ROOT = Path(__file__).resolve().parents[1]


def load(relative):
    path = ROOT / 'skills' / relative
    name = 'contracts_' + relative.replace('/', '_').replace('-', '_').replace('.', '_')
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


class Response:
    encoding = 'utf-8'
    def __init__(self, data=None, text=None, status=200, chunks=None):
        self.text = text if text is not None else json.dumps(data)
        self.content = self.text.encode()
        self.status_code = status
        self.headers = {'content-type': 'application/json'}
        self.chunks = chunks
        self.closed = False
    def iter_content(self, chunk_size=65536):
        yield from self.chunks if self.chunks is not None else [self.content]
    def close(self):
        self.closed = True
    def raise_for_status(self):
        if self.status_code >= 400:
            import requests
            raise requests.HTTPError('fake credential URL ?api_key=FAKE_KEY', response=self)
    def json(self):
        return json.loads(self.text)


class ScientificContracts(unittest.TestCase):
    def test_ncbi_network_errors_do_not_echo_credentials(self):
        for relative, payload in [('ncbi-entrez-skill/scripts/ncbi_entrez.py', {'endpoint': 'esearch'}),
                                  ('ncbi-pmc-skill/scripts/ncbi_pmc.py', {})]:
            module = load(relative)
            with self.subTest(relative=relative), patch.object(module.requests, 'get', return_value=Response(status=403)):
                result = module.execute(payload)
                self.assertFalse(result['ok'])
                self.assertNotIn('FAKE_KEY', json.dumps(result))
                self.assertNotIn('api_key', json.dumps(result))

    def test_xml_attributes_survive_compaction(self):
        for relative in ('ncbi-entrez-skill/scripts/ncbi_entrez.py', 'ncbi-pmc-skill/scripts/ncbi_pmc.py'):
            module = load(relative)
            result = module._xml_to_simple(module.ET.fromstring('<record id="PMC123"><link format="tgz" href="https://example.test/archive"/></record>'), 5, 3)
            self.assertEqual(result['_attributes']['id'], 'PMC123')
            self.assertEqual(result['link']['_attributes']['format'], 'tgz')
            self.assertEqual(result['link']['_attributes']['href'], 'https://example.test/archive')

    def test_graphql_array_is_a_structured_error(self):
        for relative in ('civic-skill/scripts/civic_graphql.py', 'gnomad-graphql-skill/scripts/gnomad_graphql.py',
                         'opentargets-skill/scripts/opentargets_graphql.py'):
            module = load(relative)
            with self.subTest(relative=relative), patch.object(module.requests, 'post', return_value=Response([])):
                result = module.execute({'query': '{__typename}'})
                self.assertEqual(result['error']['code'], 'invalid_response')

    def test_clinvar_invalid_action_is_structured(self):
        module = load('clinvar-variation-skill/scripts/clinvar_variation.py')
        for action in ('bogus', [], {}):
            stdout = io.StringIO()
            with patch.object(sys, 'stdin', io.StringIO(json.dumps({'action': action}))), patch.object(sys, 'stdout', stdout):
                self.assertNotEqual(module.main(), 0)
            self.assertEqual(json.loads(stdout.getvalue())['error']['code'], 'invalid_input')

    def test_local_slicing_sets_truncation(self):
        for relative, payload in [('clinvar-variation-skill/scripts/clinvar_variation.py', {'action': 'search', 'terms': 'TP53'}),
                                  ('ncbi-clinicaltables-skill/scripts/ncbi_gene_clinicaltables.py', {'terms': 'TP53'})]:
            module = load(relative)
            with self.subTest(relative=relative), patch.object(module.requests, 'get', return_value=Response([4, [1,2,3,4], {}, [[1],[2],[3],[4]]])):
                result = module.execute({**payload, 'max_items': 1})
                self.assertTrue(result['truncated'])
                self.assertEqual(result['record_count_returned'], 1)

    def test_blast_rejects_rid_traversal_from_input_and_server(self):
        module = load('ncbi-blast-skill/scripts/ncbi_blast.py')
        with self.assertRaises(ValueError):
            module.parse_input({'action': 'fetch', 'rid': 'x/../../escape'})
        with self.assertRaises(ValueError):
            module._derive_raw_output_path('../escape', 'json2', None)
        config = module.parse_input({'action': 'submit', 'program': 'blastp', 'database': 'swissprot', 'query_fasta': 'MTEY', 'email': 'test@example.test'})
        throttle = type('Throttle', (), {'request': lambda *a, **kw: Response(text='RID = x/../../escape\nRTOE = 1\n')})()
        with self.assertRaises(ValueError):
            module.submit_search(None, throttle, config)

    def test_blast_zip_expansion_and_bad_nested_results(self):
        module = load('ncbi-blast-skill/scripts/ncbi_blast.py')
        with self.assertRaises(ValueError):
            module._summarize_json2_payload({'BlastOutput2': [{'report': {'results': []}}]}, 5, 5)
        archive = io.BytesIO()
        with zipfile.ZipFile(archive, 'w', compression=zipfile.ZIP_DEFLATED) as z:
            z.writestr('large.json', b' ' * 101)
        with zipfile.ZipFile(io.BytesIO(archive.getvalue())) as z, patch.object(module, 'MAX_RESPONSE_BYTES', 100):
            with self.assertRaises(ValueError):
                module._load_json_member(z, 'large.json')

    def test_bounded_requests_refuse_redirects_and_oversize(self):
        module = load('ncbi-entrez-skill/scripts/ncbi_entrez.py')
        for response in (Response(status=302), Response(chunks=[b'x' * 101])):
            with patch.object(module, 'MAX_RESPONSE_BYTES', 100), self.assertRaises(ValueError):
                module._bounded_request(lambda *a, **kw: response, 'https://example.test')
            self.assertTrue(response.closed)

    def test_raw_saver_rejects_linked_parent(self):
        module = load('ncbi-pmc-skill/scripts/ncbi_pmc.py')
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp); outside = base / 'outside'; outside.mkdir()
            link = base / 'link'; link.symlink_to(outside, target_is_directory=True)
            with self.assertRaises(OSError):
                module._save_raw_text('do not write', str(link / 'new.xml'), 'xml')
            self.assertEqual(list(outside.iterdir()), [])

    def test_studies_and_heatmap_reject_bad_response_shapes(self):
        module = load('clinicaltrials-skill/scripts/clinicaltrials_client.py')
        for data in ([], {'studies': [1]}, {'studies': 1}):
            session = type('Session', (), {'headers': {}, 'get': lambda *a, **kw: Response(data), 'close': lambda *a: None})()
            with patch.object(module.requests, 'Session', return_value=session):
                result = module.execute({})
            self.assertEqual(result['error']['code'], 'invalid_response')
        module = load('opentargets-skill/scripts/opentargets_disease_heatmap.py')
        for data in ([], {'data': {'target': {'associatedDiseases': {'rows': [1]}}}}):
            with patch.object(module.requests, 'post', return_value=Response(data)):
                result = module.execute({'ensembl_id': 'ENSG00000141510'})
            self.assertEqual(result['error']['code'], 'invalid_response')
        self.assertIsNone(module.safe_float(True))
        self.assertIsNone(module.safe_float('nan'))

    def test_eqtl_same_origin_and_error_redaction(self):
        module = load('eqtl-catalogue-skill/scripts/rest_request.py')
        with self.assertRaises(ValueError):
            module._build_url('https://approved.example/api', 'https://other.example/collect')
        session = type('Session', (), {'headers': {}, 'request': lambda *a, **kw: Response({'message': 'FAKE_KEY'}, status=400), 'close': lambda *a: None})()
        with patch.object(module.requests, 'Session', return_value=session):
            result = module.execute({'base_url': 'https://approved.example', 'path': '/test', 'headers': {'X-Key': 'FAKE_KEY'}})
        self.assertNotIn('FAKE_KEY', json.dumps(result))
        self.assertEqual(result['error']['code'], 'http_error')

    def test_deep_graphql_response_is_a_structured_error(self):
        module = load('civic-skill/scripts/civic_graphql.py')
        nested = '{"data":' + '[' * 2000 + '0' + ']' * 2000 + '}'
        with patch.object(module.requests, 'post', return_value=Response(text=nested)):
            result = module.execute({'query': '{__typename}'})
        self.assertEqual(result['error']['code'], 'invalid_response')
        self.assertIn('nesting', result['error']['message'])

    def test_invalid_header_errors_do_not_echo_secrets(self):
        module = load('eqtl-catalogue-skill/scripts/rest_request.py')
        # Requests validates this header before making any socket connection.
        with patch.object(module.requests.sessions.Session, 'send') as send:
            result = module.execute({'base_url': 'https://approved.example', 'path': '/test',
                                     'headers': {'X-API-Key': 'FAKE_SECRET\ninvalid'}})
        send.assert_not_called()
        self.assertFalse(result['ok'])
        self.assertNotIn('FAKE_SECRET', json.dumps(result))
        self.assertEqual(result['error']['code'], 'network_error')

    def test_blast_rejects_duplicate_manifest_members(self):
        module = load('ncbi-blast-skill/scripts/ncbi_blast.py')
        archive = io.BytesIO()
        with zipfile.ZipFile(archive, 'w', compression=zipfile.ZIP_DEFLATED) as zipped:
            zipped.writestr('manifest.json', json.dumps({'BlastJSON': [{'File': 'payload.json'}] * 100}))
            zipped.writestr('payload.json', json.dumps({'BlastOutput2': [{'report': {}}]}))
        response = Response(text='')
        response.content = archive.getvalue()
        response.headers = {'content-type': 'application/zip'}
        with self.assertRaisesRegex(ValueError, 'duplicate'):
            module._extract_json2_payload(response)

    def test_boolean_and_nonfinite_limits_are_rejected(self):
        for relative, payload in [('ncbi-entrez-skill/scripts/ncbi_entrez.py', {'endpoint': 'esearch', 'max_items': True}),
                                  ('civic-skill/scripts/civic_graphql.py', {'query': '{}', 'max_items': True})]:
            module = load(relative)
            with self.assertRaises(ValueError):
                module.parse_input(payload)
        sys.path.insert(0, str(ROOT/'skills/tpmi-phewas-skill/scripts'))
        try:
            module = load('tpmi-phewas-skill/scripts/tpmi_phewas.py')
            for timeout in (True, float('nan'), float('inf')):
                with self.assertRaises(ValueError):
                    module.parse_input({'grch38': '10:2-C-T', 'timeout_sec': timeout})
        finally:
            sys.path.pop(0)


if __name__ == '__main__':
    unittest.main()
