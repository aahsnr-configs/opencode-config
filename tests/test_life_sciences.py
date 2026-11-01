import importlib.util
import io
import json
import pathlib
import unittest
from unittest.mock import patch

path = pathlib.Path(__file__).resolve().parents[1] / 'life-sciences' / 'lookup.py'
spec = importlib.util.spec_from_file_location('lookup', path)
lookup = importlib.util.module_from_spec(spec)
spec.loader.exec_module(lookup)

class Response(io.BytesIO):
    pass

class TestLookups(unittest.TestCase):
    def test_urls_encode_query(self):
        url = lookup.build_url('literature', 'TP53 & EGFR', 5)
        self.assertIn('TP53+%26+EGFR', url)
        self.assertIn('pageSize=5', url)

    def test_invalid_inputs(self):
        for kind, query, limit in [('alphafold', '../bad', 10), ('literature', '', 10), ('literature', 'x', 101)]:
            with self.assertRaises(ValueError):
                lookup.build_url(kind, query, limit)

    @patch.object(lookup.urllib.request, 'urlopen')
    def test_result_and_provenance(self, open_url):
        open_url.return_value = Response(json.dumps([{'entryId':'P00520'}]).encode())
        result = lookup.lookup('alphafold', 'P00520')
        self.assertEqual(result['data'][0]['entryId'], 'P00520')
        self.assertTrue(result['source_url'].endswith('/P00520'))
        self.assertIn('retrieved_utc', result)
        self.assertEqual(open_url.call_args.kwargs['timeout'], 30)

    @patch.object(lookup.urllib.request, 'urlopen')
    def test_reject_unexpected_shape(self, open_url):
        open_url.return_value = Response(b'{}')
        with self.assertRaises(ValueError):
            lookup.lookup('alphafold', 'P00520')

if __name__ == '__main__':
    unittest.main()
