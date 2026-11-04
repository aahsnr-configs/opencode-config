"""Offline regression checks for safe, allele-specific variant resolution."""
import importlib.util
import contextlib
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
COHORTS = {
    'biobankjapan-phewas-skill': 'biobankjapan_phewas.py',
    'finngen-phewas-skill': 'finngen_phewas.py',
    'tpmi-phewas-skill': 'tpmi_phewas.py',
    'ukb-topmed-phewas-skill': 'ukb_topmed_phewas.py',
    'gtex-eqtl-skill': 'gtex_eqtl.py',
}


def load_resolver(skill):
    path = ROOT / 'skills' / skill / 'scripts' / 'variant_resolution.py'
    name = 'test_resolver_' + skill.replace('-', '_')
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


class TestVariantResolution(unittest.TestCase):
    def test_native_coordinates_remain_offline_and_normalized(self):
        for skill in COHORTS:
            m = load_resolver(skill)
            with self.subTest(skill=skill), patch.object(m, '_get_json', side_effect=AssertionError('native inputs need no network')):
                r = m.resolve_query_variant(input_type='grch38', input_value='chr1:100:a:g', target_build='GRCh38')
                self.assertEqual(r['query_variant']['canonical'], '1:100-A-G')

    def test_invalid_chromosomes_and_alleles_are_rejected(self):
        for skill in COHORTS:
            m = load_resolver(skill)
            for value in ('0-100-A-G', '23-100-A-G', '99-100-A-G', '1-100-Z-G', '1-100-A-A'):
                with self.subTest(skill=skill, value=value), self.assertRaises(ValueError):
                    m.parse_variant_string(value)

    def test_rsid_refuses_multiple_assembly_mappings(self):
        for skill in COHORTS:
            m = load_resolver(skill)
            rows = {'mappings': [
                {'assembly_name': 'GRCh38', 'seq_region_name': '1', 'start': 100, 'allele_string': 'A/G', 'strand': 1},
                {'assembly_name': 'GRCh38', 'seq_region_name': '2', 'start': 200, 'allele_string': 'A/G', 'strand': 1},
            ]}
            with self.subTest(skill=skill), patch.object(m, '_get_json', return_value=rows), self.assertRaises(m.VariantResolutionError):
                m.lookup_rsid('rs123', 'GRCh38')

    def test_cross_build_selects_exact_input_alleles(self):
        for skill in COHORTS:
            m = load_resolver(skill)
            rows = [
                {'id': 'rs111', 'seq_region_name': '1', 'start': 100, 'alleles': ['A', 'G']},
                {'id': 'rs222', 'seq_region_name': '1', 'start': 100, 'alleles': ['C', 'T']},
            ]
            with self.subTest(skill=skill), patch.object(m, '_get_json', return_value=rows), patch.object(
                m, 'lookup_rsid', return_value=m.Coord('1', 200, 'C', ['T'])
            ):
                r = m.resolve_query_variant(input_type='grch37', input_value='1-100-C-T', target_build='GRCh38')
                self.assertEqual(r['rsid'], 'rs222')
                self.assertEqual(r['query_variant']['canonical'], '1:200-C-T')

    def test_cross_build_never_substitutes_an_unmatched_allele(self):
        for skill in COHORTS:
            m = load_resolver(skill)
            rows = [{'id': 'rs111', 'seq_region_name': '1', 'start': 100, 'alleles': ['A', 'G']}]
            with self.subTest(skill=skill), patch.object(m, '_get_json', return_value=rows), patch.object(
                m, 'lookup_rsid', return_value=m.Coord('1', 200, 'A', ['G'])
            ), self.assertRaises(m.VariantResolutionError):
                m.resolve_query_variant(input_type='grch37', input_value='1-100-C-T', target_build='GRCh38')

    def test_cross_build_rejects_overlapping_variant_at_another_position(self):
        for skill in COHORTS:
            m = load_resolver(skill)
            rows = [{'id': 'rs111', 'seq_region_name': '1', 'start': 99, 'alleles': ['C', 'T']}]
            with self.subTest(skill=skill), patch.object(m, '_get_json', return_value=rows), patch.object(
                m, 'lookup_rsid', return_value=m.Coord('1', 200, 'C', ['T'])
            ), self.assertRaises(m.VariantResolutionError):
                m.resolve_query_variant(input_type='grch37', input_value='1-100-C-T', target_build='GRCh38')

    def test_rsid_preserves_assembly_specific_alleles(self):
        for skill in COHORTS:
            m = load_resolver(skill)
            with self.subTest(skill=skill), patch.object(m, 'lookup_rsid', side_effect=[
                m.Coord('1', 200, 'A', ['G']), m.Coord('1', 100, 'T', ['C']),
            ]):
                r = m.resolve_query_variant(input_type='rsid', input_value='rs123', target_build='GRCh37')
                self.assertEqual(r['query_variant']['canonical'], '1:100-T-C')
                self.assertEqual(r['grch38']['canonical'], '1:200-A-G')

    def test_multiallelic_rsid_requires_explicit_allele(self):
        for skill in COHORTS:
            m = load_resolver(skill)
            with self.subTest(skill=skill), patch.object(m, 'lookup_rsid', return_value=m.Coord('1', 100, 'A', ['C', 'G'])), self.assertRaises(m.VariantResolutionError):
                m.resolve_query_variant(input_type='rsid', input_value='rs123', target_build='GRCh38')

    def test_cross_build_rejects_uncertain_allele_mapping(self):
        for skill in COHORTS:
            m = load_resolver(skill)
            rows = [{'id': 'rs123', 'seq_region_name': '1', 'start': 100, 'alleles': ['C', 'T']}]
            with self.subTest(skill=skill), patch.object(m, '_get_json', return_value=rows), patch.object(
                m, 'lookup_rsid', return_value=m.Coord('1', 200, 'A', ['G'])
            ), self.assertRaises(m.VariantResolutionError):
                m.resolve_query_variant(input_type='grch37', input_value='1-100-C-T', target_build='GRCh38')

    def test_callers_report_malformed_variant_as_json(self):
        for skill, script in COHORTS.items():
            with self.subTest(skill=skill):
                result = subprocess.run(
                    [sys.executable, '-B', str(ROOT / 'skills' / skill / 'scripts' / script)],
                    input=json.dumps({'grch37': 'not-a-variant'}), text=True, capture_output=True,
                )
                self.assertEqual(result.returncode, 2, result.stderr)
                error = json.loads(result.stdout)
                self.assertFalse(error['ok'])
                self.assertEqual(error['error']['code'], 'invalid_input')
                self.assertNotIn('Traceback', result.stderr)

    def test_cohort_raw_outputs_are_unique_and_do_not_overwrite(self):
        for skill, script in COHORTS.items():
            if skill == 'gtex-eqtl-skill':
                continue
            spec = importlib.util.spec_from_file_location('raw_' + skill.replace('-', '_'), ROOT / 'skills' / skill / 'scripts' / script)
            m = importlib.util.module_from_spec(spec)
            with patch.dict(sys.modules, {'variant_resolution': load_resolver(skill)}):
                spec.loader.exec_module(m)
            with self.subTest(skill=skill), tempfile.TemporaryDirectory() as temp, patch.object(tempfile, 'tempdir', temp):
                first = m.resolve_raw_output_path('1:100-A-G', None)
                second = m.resolve_raw_output_path('1:100-A-G', None)
                self.assertNotEqual(first, second)
                self.assertEqual(first.parent.stat().st_mode & 0o777, 0o700)
                m.write_raw_json(first, {'value': 1})
                with self.assertRaises(OSError):
                    m.write_raw_json(first, {'value': 2})
                self.assertEqual(json.loads(first.read_text()), {'value': 1})
                link = Path(temp) / 'raw-link.json'
                link.symlink_to(first)
                with self.assertRaises(OSError):
                    m.write_raw_json(link, {})

    def test_cohort_cli_reports_temporary_directory_failures_as_json(self):
        fetch_names = {
            'biobankjapan-phewas-skill': 'fetch_bbj_variant',
            'finngen-phewas-skill': 'fetch_finngen_variant',
            'tpmi-phewas-skill': 'fetch_tpmi_variant',
            'ukb-topmed-phewas-skill': 'fetch_variant',
        }
        for skill, fetch_name in fetch_names.items():
            script = ROOT / 'skills' / skill / 'scripts' / COHORTS[skill]
            spec = importlib.util.spec_from_file_location('write_failure_' + skill.replace('-', '_'), script)
            m = importlib.util.module_from_spec(spec)
            with patch.dict(sys.modules, {'variant_resolution': load_resolver(skill)}):
                spec.loader.exec_module(m)
            stdout = io.StringIO()
            with self.subTest(skill=skill), patch.object(sys, 'stdin', io.StringIO(json.dumps({
                'grch37': '1-100-A-G', 'save_raw': True,
            }))), contextlib.redirect_stdout(stdout), patch.object(
                m, 'resolve_query_variant', return_value={
                    'query_variant': {'canonical': '1:100-A-G'}, 'warnings': [],
                }
            ), patch.object(m.requests, 'Session'), patch.object(
                m, fetch_name, return_value=({}, 200)
            ), patch.object(m.tempfile, 'mkdtemp', side_effect=OSError('disk unavailable')):
                self.assertEqual(m.main(), 1)
                result = json.loads(stdout.getvalue())
                self.assertFalse(result['ok'])
                self.assertEqual(result['error']['code'], 'write_error')


if __name__ == '__main__':
    unittest.main()
