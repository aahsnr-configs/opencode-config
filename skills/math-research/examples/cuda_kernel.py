"""Compile the bundled kernel and require a clean Compute Sanitizer run."""
import json
from pathlib import Path
import subprocess

compile_result = subprocess.run(["nvcc", "-arch=sm_75", "-lineinfo", "/inputs/vector_add.cu", "-o", "/output/vector_add"], capture_output=True, text=True, timeout=120)
Path("/output/compile.log").write_text(compile_result.stdout+compile_result.stderr)
checks = [{"name": "nvcc_compile", "passed": compile_result.returncode == 0}]
if compile_result.returncode == 0:
    run = subprocess.run(["compute-sanitizer", "--tool", "memcheck", "--error-exitcode", "99", "/output/vector_add"], capture_output=True, text=True, timeout=120)
    Path("/output/sanitizer.log").write_text(run.stdout+run.stderr)
    checks.append({"name": "kernel_result_and_memcheck", "passed": run.returncode == 0 and "ERROR SUMMARY: 0 errors" in run.stdout+run.stderr})
Path("/output/experiment.json").write_text(json.dumps({"checks": checks, "metrics": {"target_architecture": "sm_75", "elements": 1025}, "limitations": ["A clean sanitizer report applies to this bounded vector-add kernel and tested execution only."]}, indent=2)+"\n")
raise SystemExit(0 if all(c["passed"] for c in checks) else 1)
