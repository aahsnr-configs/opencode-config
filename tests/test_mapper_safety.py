"""Offline checks for allele ambiguity, evidence attribution and output safety."""
import importlib.util
import json
from pathlib import Path
import tempfile
import sys
import types
import unittest
from unittest.mock import Mock, patch

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / 'skills/locus-to-gene-mapper-skill/scripts/map_locus_to_gene.py'
spec = importlib.util.spec_from_file_location('mapper_safety', SCRIPT)
mapper = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mapper)


def placement(alts=('T',), position=10):
    return {'seq_id': 'NC_000010.11', 'placement_annot': {'seq_id_traits_by_assembly': [
        {'assembly_name': 'GRCh38.p14', 'is_top_level': True, 'is_chromosome': True}]},
        'alleles': [{'allele': {'spdi': {'position': position, 'deleted_sequence': 'C',
                                       'inserted_sequence': alt}}} for alt in ('C', *alts)]}


class MapperSafety(unittest.TestCase):
    def test_figure_contributions_match_the_scoring_components(self):
        pyplot = types.ModuleType('matplotlib.pyplot')
        figure, axis = Mock(), Mock()
        pyplot.subplots = Mock(return_value=(figure, axis))
        pyplot.close = Mock()
        matplotlib = types.ModuleType('matplotlib')
        matplotlib.pyplot = pyplot
        evidence = {'l2g_max': 0.9, 'coloc_max_h4': 0, 'eqtl_tissues': [],
                    'rare_variant_support': 'none', 'coding_support': 'coding',
                    'clinvar_support': 'not_assessed'}
        with tempfile.TemporaryDirectory() as temp, patch.dict(sys.modules, {
            'matplotlib': matplotlib, 'matplotlib.pyplot': pyplot}):
            mapper.generate_optional_figures([{'locus_id': 'test', 'candidate_genes': [
                {'symbol': 'GENE1', 'evidence': evidence}]}], Path(temp) / 'figures', [])
        contributions = {call.kwargs['label']: call.args[1][0] for call in axis.bar.call_args_list}
        self.assertAlmostEqual(contributions['coding'], 0.06)
        self.assertAlmostEqual(sum(contributions.values()), 0.42)
        self.assertAlmostEqual(axis.imshow.call_args.args[0][0][-1], 0.6)

    def test_ambiguous_alleles_and_placements_are_not_selected(self):
        for placements in ([placement(('G', 'T'))], [placement(position=10), placement(position=20)]):
            with self.subTest(placements=placements):
                warnings = []
                payload = {'primary_snapshot_data': {'placements_with_allele': placements}}
                with patch.object(mapper, 'fetch_refsnp_payload', return_value=payload):
                    result = mapper.resolve_refsnp_coordinates('rs123', warnings, [])
                self.assertNotIn('grch38', result)
                self.assertTrue(any('ambiguous' in message.lower() for message in warnings))

    def test_biallelic_placement_is_preserved(self):
        result = mapper.coordinate_from_placement(placement())
        self.assertEqual((result['pos'], result['ref'], result['alt']), (11, 'C', 'T'))

    def test_existing_and_linked_outputs_fail_before_retrieval(self):
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            outside = base / 'outside'
            outside.mkdir()
            existing = base / 'keep.json'
            existing.write_text('keep')
            linked = base / 'linked'
            linked.symlink_to(outside, target_is_directory=True)
            for output in (existing, linked / 'new.json'):
                with self.subTest(output=output), patch.object(mapper, 'resolve_efo', side_effect=AssertionError('retrieval must not run')) as retrieve:
                    with self.assertRaises((FileExistsError, ValueError)):
                        mapper.map_locus_to_gene({'seed_rsids': ['rs123'], 'mapping_output_path': str(output),
                            'summary_output_path': str(base / 'summary.md')})
                    retrieve.assert_not_called()
            self.assertEqual(existing.read_text(), 'keep')
            self.assertEqual(list(outside.iterdir()), [])

    def test_annotations_do_not_invent_clinvar_or_gene_specific_coloc(self):
        anchor = {'rsid': 'rs123', 'locus_id': 'chr10:1-100', 'mapped_genes': ['GENE1'],
                  'grch38': {'chr': '10', 'pos': 11, 'ref': 'C', 'alt': 'T'}}
        mocks = {'resolve_efo': {}, 'build_anchors': [anchor],
                 'fetch_ot_l2g_coloc_for_anchors': {'per_anchor': {'rs123': {
                     'l2g': [{'symbol': 'GENE1', 'score': 0.9}], 'coloc': [{'h4': 0.99}]}}},
                 'fetch_gtex_support': {}, 'fetch_refsnp_annotations': {
                     'rs123': {'genes': ['GENE1'], 'coding_genes': ['GENE1']}},
                 'resolve_ensembl_ids_for_symbols': {}, 'fetch_genebass_support': {}}
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / 'mapping.json'
            with patch.multiple(mapper, **{name: Mock(return_value=value)
                                          for name, value in mocks.items()}):
                mapper.map_locus_to_gene({'seed_rsids': ['rs123'], 'mapping_output_path': str(output),
                    'summary_output_path': str(Path(temp) / 'summary.md'),
                    'include_gnomad_context': False, 'include_hpa_tissue_context': False})
            data = json.loads(output.read_text())
            gene = data['loci'][0]['candidate_genes'][0]
            self.assertEqual(gene['evidence']['clinvar_support'], 'not_assessed')
            self.assertEqual(gene['evidence']['coloc_max_h4'], 0)
            self.assertAlmostEqual(gene['overall_score'], 0.42)
            self.assertNotIn('clinvar-variation-skill', data['meta']['sources_queried'])


if __name__ == '__main__':
    unittest.main()
