"""Offline physics runtime contracts; scientific checks run in installed profiles."""
import contextlib
import importlib.util
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('physics_runtime', ROOT / 'skills/physics-research/scripts/physics_research.py')
runtime = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runtime)


class PhysicsRuntimeTests(unittest.TestCase):
    def test_preview_is_read_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            state = Path(tmp) / 'absent'
            with mock.patch.object(runtime, 'capture', side_effect=AssertionError('preview executed')), contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(runtime.main(['setup', '--state-dir', str(state), '--cuda']), 0)
            self.assertFalse(state.exists())

    def test_apt_changes_invalidate_profile_fingerprint(self):
        before = runtime.fingerprint('analysis')
        with mock.patch.dict(runtime.APT, {'analysis': ['different-system-dependency']}):
            self.assertNotEqual(before, runtime.fingerprint('analysis'))

    def test_jax_cuda_profile_requires_gpu(self):
        self.assertIn('pymbar-cuda', runtime.GPU)
        self.assertNotIn('pymbar-cuda', runtime.CUDA_TOOLKIT_GPU)
        self.assertIn('jax[cuda12]==0.12.0.1', runtime.PROFILES['pymbar-cuda'])

    def test_analysis_enables_pymbar_jax_extra(self):
        self.assertIn('pymbar[jax]==4.0.3', runtime.PROFILES['analysis'])

    def test_gpu_selection_is_explicit(self):
        self.assertFalse(set(runtime.selected('all', False)) & runtime.GPU)
        self.assertEqual(set(runtime.selected('all', True)), set(runtime.PROFILES))
        with self.assertRaises(runtime.RuntimeErrorSafe):
            runtime.selected('openmm-cuda', False)

    def test_every_profile_has_recipe_and_scientific_fixture(self):
        for name in runtime.PROFILES:
            self.assertTrue((runtime.ROOT / 'environments' / (name + '.Containerfile')).is_file(), name)
            self.assertIn(name, runtime.CASES)

    def test_failed_required_profile_fails_acceptance(self):
        self.assertFalse(runtime.accepted({'a': {'status': 'completed'}, 'b': {'status': 'failed'}}))
        self.assertFalse(runtime.accepted({}))
        self.assertTrue(runtime.accepted({'a': {'status': 'completed'}}))

    def test_checks_reject_nan_and_empty(self):
        self.assertFalse(runtime.valid_report({'checks': []}))
        self.assertFalse(runtime.valid_report({'checks': [{'name': 'x', 'passed': 1}]}))
        self.assertTrue(runtime.valid_report({'checks': [{'name': 'x', 'passed': True}]}))

    def test_boundary_is_offline_and_gpu_explicit(self):
        cmd = runtime.container_command('image', ['python', 'model.py'], gpu=True)
        self.assertIn('--network=none', cmd)
        self.assertIn('--read-only', cmd)
        self.assertIn('nvidia.com/gpu=0', cmd)
        self.assertNotIn('--privileged', cmd)

    def test_tampering_fails_without_execution(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp)
            (path / 'artifacts').mkdir()
            report = {'checks': [{'name': 'test', 'passed': True}]}
            runtime.write_json(path / 'artifacts/experiment.json', report)
            runtime.write_json(path / 'result.json', {'execution': {'status': 'completed'}, 'experiment': report, 'artifacts': runtime.artifact_hashes(path)})
            with mock.patch.object(runtime, 'capture', side_effect=AssertionError('verify executed')):
                self.assertTrue(runtime.verify_path(path))
                (path / 'artifacts/extra').write_text('tampering')
                self.assertFalse(runtime.verify_path(path))

    def test_unknown_request_does_not_create_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp)
            (path / 'input.json').write_text(json.dumps({'experiment': 'unknown'}))
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(runtime.main(['run', '--input', str(path / 'input.json'), '--output-dir', str(path / 'out')]), 1)
            self.assertFalse((path / 'out').exists())
