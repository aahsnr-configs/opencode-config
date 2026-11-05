"""Offline safety/record checks; actual backend smoke tests remain separate."""
import contextlib
import importlib.util
import io
import json
from pathlib import Path
import tempfile
import unittest
import sys
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("math_runtime", ROOT / "skills/math-research/scripts/math_research.py")
runtime = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(runtime)


class MathRuntimeTests(unittest.TestCase):
    def test_setup_preview_has_no_process_calls_or_writes(self):
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp) / "uncreated"
            with mock.patch.object(runtime.subprocess, "run", side_effect=AssertionError("preview must not execute")):
                with contextlib.redirect_stdout(io.StringIO()):
                    self.assertEqual(runtime.main(["setup", "--state-dir", str(target), "--profile", "all", "--cuda"]), 0)
            self.assertFalse(target.exists())

    def test_symlink_and_existing_output_are_refused(self):
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            (base / "real").mkdir()
            (base / "link").symlink_to(base / "real", target_is_directory=True)
            with self.assertRaises(runtime.RuntimeErrorSafe):
                runtime.checked_path(base / "link" / "new", new=True)
            with self.assertRaises(runtime.RuntimeErrorSafe):
                runtime.checked_path(base / "real", new=True)

    def test_runtime_boundary_has_no_network_and_no_shell(self):
        command = runtime.container_command("sha256:example", ["python", "/inputs/model.py"], gpu=True)
        for value in ["--network=none", "--read-only", "--cap-drop=all", "--pull=never", "--pids-limit=256", "--memory=8g"]:
            self.assertIn(value, command)
        self.assertIn("nvidia.com/gpu=0", command)
        self.assertNotIn("--privileged", command)
        self.assertIn("--security-opt=label=disable", command)

    def test_sage_bypasses_image_shell_entrypoint(self):
        command = runtime.container_command("sha256:example", runtime.PROFILES["sage"][1], entrypoint="/usr/bin/env")
        self.assertEqual(command[-6:], ["--entrypoint", "/usr/bin/env", "sha256:example", *runtime.PROFILES["sage"][1]])

    def test_petsc_cuda_disables_gpu_aware_mpi_requirement(self):
        command = runtime.container_command("sha256:example", ["python"], gpu=True, petsc_gpu=True)
        self.assertIn("PETSC_OPTIONS=-use_gpu_aware_mpi 0", command)

    def test_gpu_device_rejects_host_paths(self):
        with self.assertRaises(runtime.RuntimeErrorSafe):
            runtime.container_command("sha256:example", ["python"], gpu=True, device="/dev/sda")

    def test_checks_require_nonempty_boolean_success(self):
        for data in [None, {}, {"checks": []}, {"checks": [{"name": "a", "passed": 1}]}, {"checks": [{"name": "a", "passed": False}]}]:
            self.assertFalse(runtime.validate_checks(data))
        self.assertTrue(runtime.validate_checks({"checks": [{"name": "a", "passed": True}]}))

    def test_verify_detects_tampering_without_process_or_writes(self):
        with tempfile.TemporaryDirectory() as temp:
            run = Path(temp)
            artifact = run / "data.txt"
            artifact.write_text("original")
            experiment = {"checks": [{"name": "exact", "passed": True}]}
            (run / "artifacts").mkdir()
            runtime.write_json(run / "artifacts/experiment.json", experiment)
            result = {"execution": {"status": "completed"}, "experiment": experiment, "artifacts": runtime.artifact_hashes(run)}
            runtime.write_json(run / "result.json", result)
            args = runtime.parser().parse_args(["verify", "--run-dir", str(run)])
            with mock.patch.object(runtime.subprocess, "run", side_effect=AssertionError("verification must be read-only")):
                with contextlib.redirect_stdout(io.StringIO()):
                    self.assertEqual(runtime.verify(args), 0)
                    artifact.write_text("changed")
                    self.assertEqual(runtime.verify(args), 1)

    def test_nested_result_artifacts_are_hashed(self):
        with tempfile.TemporaryDirectory() as temp:
            run = Path(temp)
            (run / "artifacts").mkdir()
            (run / "artifacts/result.json").write_text("{}")
            self.assertIn("artifacts/result.json", runtime.artifact_hashes(run))

    def test_cuda_requires_explicit_flag(self):
        args = runtime.parser().parse_args(["setup", "--profile", "cuda"])
        with self.assertRaises(runtime.RuntimeErrorSafe):
            runtime.profile_names(args)

    def test_invalid_timeout_fails_before_output_creation(self):
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(runtime.main(["run", "--input", "missing", "--output-dir", "missing", "--timeout", "0"]), 1)

    def test_process_allows_large_nonlog_files(self):
        with tempfile.TemporaryDirectory() as temp:
            directory = Path(temp)
            target = directory / "layer.data"
            code = "import sys; f=open(sys.argv[1], 'wb'); f.truncate(128 * 1024**2); f.close()"
            result = runtime.process([sys.executable, "-c", code, str(target)], directory / "build.log", timeout=10)
            self.assertEqual(result["status"], "completed", result)
            self.assertEqual(target.stat().st_size, 128 * 1024**2)

    def test_process_stops_log_growth_without_inherited_file_limit(self):
        with tempfile.TemporaryDirectory() as temp:
            log = Path(temp) / "noisy.log"
            code = "import sys,time; sys.stdout.write('x'*4096); sys.stdout.flush(); time.sleep(10)"
            result = runtime.process([sys.executable, "-c", code], log, timeout=5, log_limit=1024)
            self.assertEqual(result["status"], "log_limit", result)
            self.assertLess(result["seconds"], 5)


if __name__ == "__main__":
    unittest.main()
