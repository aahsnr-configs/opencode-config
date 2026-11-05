"""Offline GTEx pagination metadata regression checks."""
import contextlib
import importlib.util
import io
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

SCRIPTS = Path(__file__).resolve().parents[1] / 'skills/gtex-eqtl-skill/scripts'
sys.path.insert(0, str(SCRIPTS))
spec = importlib.util.spec_from_file_location('gtex_pagination', SCRIPTS / 'gtex_eqtl.py')
gtex = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gtex)
sys.path.pop(0)


class GTExPagination(unittest.TestCase):
    def run_page(self, page, limit=None):
        stdout = io.StringIO()
        payload = {'grch38': '1-100-A-G'}
        if limit is not None:
            payload['max_results'] = limit
        with patch.object(gtex, 'fetch_eqtls', return_value=page), \
             patch.object(sys, 'stdin', io.StringIO(json.dumps(payload))), contextlib.redirect_stdout(stdout):
            code = gtex.main()
        return code, json.loads(stdout.getvalue())

    def test_multiple_server_pages_are_not_complete(self):
        code, result = self.run_page({'data': [{'geneSymbol': 'TEST'}],
                                    'paging_info': {'numberOfPages': 2, 'page': 0}})
        self.assertEqual(code, 0)
        self.assertTrue(result['truncated'])
        self.assertIsNone(result['eqtl_count_total'])
        self.assertTrue(result['warnings'])

    def test_local_limit_and_single_page_total(self):
        code, result = self.run_page({'data': [{}, {}], 'paging_info': {'numberOfPages': 1, 'page': 0}}, 1)
        self.assertEqual(code, 0)
        self.assertEqual(result['eqtl_count_total'], 2)
        self.assertEqual(result['eqtl_count'], 1)
        self.assertTrue(result['truncated'])

    def test_server_total_is_preserved(self):
        code, result = self.run_page({'data': [{}], 'paging_info': {
            'numberOfPages': 2, 'page': 0, 'maxItemsPerPage': 5, 'totalNumberOfItems': 10}})
        self.assertEqual(code, 0)
        self.assertEqual(result['eqtl_count_total'], 10)
        self.assertTrue(result['truncated'])

    def test_wrong_response_shape_is_an_error(self):
        code, result = self.run_page({'message': 'wrong endpoint'})
        self.assertEqual(code, 1)
        self.assertEqual(result['error']['code'], 'invalid_response')

    def test_boolean_limit_is_not_an_integer(self):
        with self.assertRaises(ValueError):
            gtex.parse_input({'grch38': '1-100-A-G', 'max_results': True})


if __name__ == '__main__':
    unittest.main()
