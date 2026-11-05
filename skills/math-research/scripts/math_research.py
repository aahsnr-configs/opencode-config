#!/usr/bin/env python3
"""Local deterministic research runtime. No model, MCP, or AI API clients."""
from __future__ import annotations

import argparse
import contextlib
import hashlib
import json
import os
import re
from pathlib import Path
import shutil
import subprocess
import sys
import time
import uuid

ROOT = Path(__file__).resolve().parents[1]
PROFILES = {
    "python": ("docker.io/library/python:3.13.5-slim-bookworm", ["python", "-c", "import numpy,scipy,sympy,flint,cvxpy,jax; assert abs(float(numpy.linalg.solve([[2.,0.],[0.,3.]],[2.,3.])[0])-1)<1e-12; assert float(jax.jit(lambda x:x*x)(3.0))==9.0"]),
    "jax-cuda": ("@python", ["python", "-c", "import jax,jax.numpy as jnp; assert jax.default_backend() == \"gpu\"; x=jax.jit(lambda a:jnp.sum(a*a))(jnp.arange(8,dtype=jnp.float32)); x.block_until_ready(); assert float(x)==140.0; print(jax.devices())"]),
    "sage": ("docker.io/sagemath/sagemath:10.6", ["sage", "-c", "assert list(factor(10403)) == [(101, 1), (103, 1)]"]),
    "lean": ("docker.io/library/ubuntu:22.04", ["bash", "-c", "cd /opt/mathlib && lake env lean --version"]),
    "fenics": ("ghcr.io/fenics/dolfinx/dolfinx:stable", ["python3", "-c", "import dolfinx,gmsh; from petsc4py import PETSc; from slepc4py import SLEPc; assert PETSc.Sys.getVersion()[0] == 3"]),
    "sundials": ("@python", ["python", "-c", "import sundials4py"]),
    "cuda": ("docker.io/nvidia/cuda:12.8.1-devel-ubuntu22.04", ["python", "-c", "import cupy as c; x=c.arange(8,dtype=c.float64); assert float(x.sum())==28; c.cuda.Stream.null.synchronize(); print(c.cuda.runtime.getDeviceProperties(0)['name'])"]),
    "petsc-cuda": ("docker.io/nvidia/cuda:12.8.1-devel-ubuntu22.04", ["python", "-c", "from petsc4py import PETSc; v=PETSc.Vec().createSeq(4); v.setType('cuda'); v.set(1); assert abs(v.norm()-2)<1e-12; print(v.getType())"]),
}
GPU = {"cuda", "petsc-cuda", "jax-cuda"}


class RuntimeErrorSafe(Exception):
    """An operational error suitable for compact user-facing output."""


def digest(path):
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def checked_path(path, *, new=False):
    path = Path(os.path.abspath(os.path.expanduser(str(path))))
    for part in [path, *path.parents]:
        if part.is_symlink():
            raise RuntimeErrorSafe("Symlink paths are refused: " + str(part))
        if part != path and part.exists() and not part.is_dir():
            raise RuntimeErrorSafe("Non-directory ancestor: " + str(part))
    if new and path.exists():
        raise RuntimeErrorSafe("Output already exists: " + str(path))
    return path


def write_json(path, value):
    # Atomic replacement is confined to the private runtime state or new run.
    temp = path.with_name(path.name + ".tmp-" + uuid.uuid4().hex)
    with temp.open("x", encoding="utf-8") as stream:
        json.dump(value, stream, indent=2, allow_nan=False)
        stream.write("\n")
    temp.replace(path)


def load_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def state_dir(args):
    return checked_path(args.state_dir)


def bounded_files(path):
    total = count = 0
    for entry in path.rglob("*"):
        if entry.is_symlink():
            return False
        if entry.is_file():
            size = entry.stat().st_size
            total += size
            count += 1
            if size > 64 * 1024**2 or total > 512 * 1024**2 or count > 4096:
                return False
    return True


def process(command, log, timeout=120, artifact_dir=None, log_limit=64 * 1024**2):
    started = time.monotonic()
    try:
        with log.open("ab") as stream:
            stream.write(("\nCOMMAND " + json.dumps(command) + "\n").encode())
            with subprocess.Popen(command, stdout=stream, stderr=subprocess.STDOUT) as child:
                status = None
                while child.poll() is None:
                    if time.monotonic() - started > timeout:
                        status = "timeout"
                    elif log.stat().st_size > log_limit:
                        status = "log_limit"
                    elif artifact_dir and not bounded_files(artifact_dir):
                        status = "output_limit"
                    if status:
                        child.kill()
                        child.wait()
                        break
                    time.sleep(0.2)
                code = child.returncode
        return {"status": status or ("completed" if code == 0 else "failed"),
                "returncode": code, "seconds": time.monotonic() - started}
    except OSError as exc:
        return {"status": "launch_error", "error": type(exc).__name__,
                "returncode": None, "seconds": time.monotonic() - started}


def capture(command, timeout=30):
    try:
        result = subprocess.run(command, capture_output=True, text=True, timeout=timeout)
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise RuntimeErrorSafe("Preflight command failed: " + type(exc).__name__) from exc
    if result.returncode:
        raise RuntimeErrorSafe("Command failed: " + " ".join(command[:3]) + "; " + result.stderr.strip()[:500])
    return result.stdout.strip()


@contextlib.contextmanager
def exclusive(path):
    """Prevent simultaneous setup or GPU benchmarks sharing this state."""
    import fcntl
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a") as stream:
        try:
            fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise RuntimeErrorSafe("Another operation owns " + str(path)) from exc
        try:
            yield
        finally:
            fcntl.flock(stream, fcntl.LOCK_UN)


def profile_names(args):
    names = list(PROFILES) if args.profile == "all" else [args.profile]
    if not args.cuda:
        names = [name for name in names if name not in GPU]
    if not names:
        raise RuntimeErrorSafe("GPU profiles require --cuda")
    if ("sundials" in names or "jax-cuda" in names) and "python" not in names:
        names.insert(0, "python")
    return names


def source_fingerprint(name):
    files = [ROOT / "environments" / (name + ".Containerfile")]
    if name in {"python", "cuda"}:
        files.append(ROOT / "environments/python.requirements.txt")
    if name == "jax-cuda":
        files.append(ROOT / "environments/jax-cuda.requirements.txt")
    h = hashlib.sha256()
    for path in files:
        if path.is_file():
            h.update(path.name.encode())
            h.update(path.read_bytes())
    h.update(name.encode())
    if name in {"sundials", "jax-cuda"}:
        h.update(source_fingerprint("python").encode())
    return h.hexdigest()


def gpu_preflight():
    identity = capture(["nvidia-smi", "--query-gpu=uuid,name,driver_version,memory.total", "--format=csv,noheader"])
    devices = capture(["nvidia-ctk", "cdi", "list"])
    if "nvidia.com/gpu=" not in devices:
        raise RuntimeErrorSafe("No NVIDIA CDI device; host driver/CDI setup requires review")
    return {"identity": identity, "cdi_devices": devices}


def container_command(image, command, *, inputs=None, output=None, gpu=False,
                      device="nvidia.com/gpu=0", label_disable=False, name=None, entrypoint=None,
                      petsc_gpu=False):
    if gpu and not re.fullmatch(r"nvidia\.com/gpu=(?:all|[0-9]+|GPU-[0-9a-fA-F-]+)", device):
        raise RuntimeErrorSafe("GPU device must be an NVIDIA CDI selector")
    cmd = ["podman", "run", "--rm", "--pull=never", "--network=none", "--read-only",
           "--cap-drop=all", "--security-opt=no-new-privileges", "--pids-limit=256",
           "--cpus=4", "--memory=8g", "--userns=keep-id", "--user", f"{os.getuid()}:{os.getgid()}",
           "--tmpfs", "/tmp:rw,nosuid,nodev,size=1g,notmpcopyup", "--env", "HOME=/tmp",
           "--env", "OMP_NUM_THREADS=4", "--env", "OPENBLAS_NUM_THREADS=4",
           "--env", "CUDA_CACHE_PATH=/tmp/cuda-cache"]
    if petsc_gpu:
        cmd += ["--env", "PETSC_OPTIONS=-use_gpu_aware_mpi 0"]
    if name:
        cmd += ["--name", name]
    if label_disable or gpu:
        cmd += ["--security-opt=label=disable"]
    if gpu:
        cmd += ["--device", device]
    if inputs:
        cmd += ["--volume", str(inputs) + ":/inputs:ro,Z"]
    if output:
        cmd += ["--volume", str(output) + ":/output:rw,Z", "--workdir", "/output"]
    else:
        cmd += ["--workdir", "/tmp"]
    if entrypoint:
        cmd += ["--entrypoint", entrypoint]
    return cmd + [image] + command


def setup(args):
    names = profile_names(args)
    state = state_dir(args)
    if not args.apply:
        print(json.dumps({"action": "preview", "profiles": names, "state_dir": str(state),
                          "model_calls": 0, "llm_tokens_for_installer": 0,
                          "apply": "Add --apply to install; no host drivers are changed."}, indent=2))
        return 0
    state.mkdir(parents=True, exist_ok=True)
    with exclusive(state / "setup.lock"):
        return setup_locked(args, names, state)


def setup_locked(args, names, state):
    manifest_path = state / "installation.json"
    manifest = load_json(manifest_path) if manifest_path.exists() else {"schema_version": 1, "profiles": {}}
    bases_path = state / "resolved-bases.json"
    bases = load_json(bases_path) if bases_path.exists() else {}
    summary = {"status": "completed", "model_calls": 0, "profiles": {}, "logs": str(state / "logs")}
    (state / "logs").mkdir(exist_ok=True)
    try:
        rootless = capture(["podman", "info", "--format", "{{.Host.Security.Rootless}}"])
        if rootless.lower() != "true":
            raise RuntimeErrorSafe("Rootless Podman is required")
    except RuntimeErrorSafe as exc:
        summary.update(status="blocked", error=str(exc))
        write_json(state / "setup-summary.json", summary)
        print(json.dumps(summary, indent=2))
        return 1
    for name in names:
        log = state / "logs" / (name + ".log")
        print(f"[{name}] checking recorded installation; log: {log}", flush=True)
        expected = source_fingerprint(name)
        old = manifest["profiles"].get(name)
        if not args.rebuild and old and old.get("fingerprint") == expected and old.get("smoke", {}).get("status") == "completed":
            try:
                capture(["podman", "image", "exists", old["image_id"]])
                summary["profiles"][name] = {"status": "reused", "image_id": old["image_id"]}
                print(f"[{name}] reused {old['image_id']}", flush=True)
                continue
            except RuntimeErrorSafe:
                pass
        if old and old.get("fingerprint") != expected:
            summary["profiles"][name] = {"status": "blocked", "error": "Environment definition changed; use a new --state-dir to preserve the old installation."}
            summary["status"] = "incomplete"
            print(f"[{name}] blocked: environment definition changed", flush=True)
            continue
        try:
            gpu = gpu_preflight() if name in GPU else None
            base = PROFILES[name][0]
            if base.startswith("@"):
                parent = manifest["profiles"].get(base[1:])
                if not parent:
                    raise RuntimeErrorSafe("Required parent profile has not installed: " + base)
                base = parent["image_id"]
            elif old and old.get("base") and old.get("fingerprint") == expected:
                base = old["base"]
                capture(["podman", "image", "exists", base])
            elif name in bases:
                resolved = bases[name]
                if resolved["fingerprint"] != expected:
                    raise RuntimeErrorSafe("Definition changed after base resolution; select a new state directory")
                base = resolved["base"]
                capture(["podman", "image", "exists", base])
            else:
                print(f"[{name}] pulling {base}", flush=True)
                outcome = process(["podman", "pull", base], log, 1800)
                if outcome["status"] != "completed":
                    raise RuntimeErrorSafe("Base image pull failed; see " + str(log))
                details = json.loads(capture(["podman", "image", "inspect", base]))[0]
                base = next(iter(details.get("RepoDigests", [])), details["Id"])
                bases[name] = {"base": base, "fingerprint": expected}
                write_json(bases_path, bases)
            tag = "localhost/opencode-math-" + name + ":" + expected[:12]
            print(f"[{name}] building {tag} from {base}", flush=True)
            outcome = process(["podman", "build", "--pull=never", *(["--no-cache"] if args.rebuild else []), "--memory=12g", "--build-arg", "BASE=" + base,
                               "--file", str(ROOT / "environments" / (name + ".Containerfile")),
                               "--tag", tag, str(ROOT / "environments")], log, 7200)
            if outcome["status"] != "completed":
                raise RuntimeErrorSafe("Image build " + outcome["status"] + "; see " + str(log))
            image_id = json.loads(capture(["podman", "image", "inspect", tag]))[0]["Id"]
            lock = capture(["podman", "run", "--rm", "--pull=never", "--network=none", image_id, "cat", "/opt/packages.lock"])
            (state / (name + ".packages.lock")).write_text(lock + "\n")
            smoke = container_command(image_id, PROFILES[name][1], gpu=name in GPU,
                                      device=args.device, label_disable=args.selinux_label_disable,
                                      entrypoint="/usr/bin/env" if name == "sage" else None,
                                      petsc_gpu=name == "petsc-cuda")
            print(f"[{name}] smoke check {image_id}", flush=True)
            outcome = process(smoke, log, 300)
            record = {"image_id": image_id, "base": base, "fingerprint": expected,
                      "packages_sha256": digest(state / (name + ".packages.lock")),
                      "smoke": outcome, "gpu": gpu, "installed_at": time.time()}
            manifest["profiles"][name] = record
            write_json(manifest_path, manifest)
            summary["profiles"][name] = {"status": outcome["status"], "image_id": image_id}
            print(f"[{name}] smoke {outcome['status']}", flush=True)
            if outcome["status"] != "completed":
                summary["status"] = "incomplete"
        except RuntimeErrorSafe as exc:
            summary["profiles"][name] = {"status": "blocked", "error": str(exc)}
            summary["status"] = "incomplete"
            print(f"[{name}] blocked: {exc}", flush=True)
        write_json(state / "setup-summary.json", summary)
    print(json.dumps(summary, indent=2))
    return 0 if summary["status"] == "completed" else 1


def doctor(args):
    state = state_dir(args)
    path = state / "installation.json"
    if not path.exists():
        print(json.dumps({"status": "not_installed", "state_dir": str(state)}))
        return 1
    manifest = load_json(path)
    results = {}
    for name, item in manifest["profiles"].items():
        if name not in PROFILES:
            results[name] = {"status": "unsupported"}
            continue
        result = {"status": "recorded", "image_id": item["image_id"],
                  "definition_matches": item["fingerprint"] == source_fingerprint(name)}
        if args.smoke and name in GPU and not args.cuda:
            result["status"] = "not_requested"
        elif args.smoke:
            state.joinpath("logs").mkdir(exist_ok=True)
            cmd = container_command(item["image_id"], PROFILES[name][1], gpu=name in GPU,
                                    device=args.device, label_disable=args.selinux_label_disable,
                                    entrypoint="/usr/bin/env" if name == "sage" else None,
                                    petsc_gpu=name == "petsc-cuda")
            result.update(process(cmd, state / "logs" / (name + "-doctor.log"), 300))
        results[name] = result
    missing = [name for name in PROFILES if name not in manifest["profiles"] and (args.cuda or name not in GPU)]
    print(json.dumps({"status": "checked" if args.smoke else "recorded_only", "profiles": results, "missing_profiles": missing}, indent=2))
    return 0 if results and not missing and all(r.get("definition_matches", False) and (not args.smoke or r["status"] in {"completed", "not_requested"}) for r in results.values()) else 1


def prepare_request(request):
    if not isinstance(request, dict):
        raise RuntimeErrorSafe("Input must be a JSON object")
    parameters = request.get("parameters", {})
    if not isinstance(parameters, dict):
        raise RuntimeErrorSafe("parameters must be an object")
    if "experiment" in request:
        catalog = load_json(ROOT / "examples" / "catalog.json")
        catalog = catalog.get("experiments", catalog)
        try:
            spec = catalog[request["experiment"]]
        except (KeyError, TypeError) as exc:
            raise RuntimeErrorSafe("Unknown bundled experiment") from exc
        source = checked_path(ROOT / "examples" / spec["source"])
        files = [checked_path(ROOT / "examples" / value) for value in spec.get("files", [])]
        merged = {**spec.get("parameters", {}), **parameters}
        return spec["profile"], source, files, spec["command"], {**request, **merged, "parameters": merged}
    source = checked_path(request.get("source", ""))
    profile = request.get("profile")
    if profile not in PROFILES or not source.is_file():
        raise RuntimeErrorSafe("Explicit models require an existing source file and supported profile")
    if profile == "lean":
        if source.suffix != ".lean":
            raise RuntimeErrorSafe("Lean models require a .lean source")
        return profile, source, [ROOT / "scripts/lean_model.py"], ["python3", "/inputs/lean_model.py", "/inputs/input.json"], request
    commands = {"python": ["python"], "sage": ["sage", "-python"], "sundials": ["python"],
                "fenics": ["python3"], "cuda": ["python"],
                "petsc-cuda": ["python"], "lean": ["lake", "env", "lean"]}
    return profile, source, [], commands[profile] + ["/inputs/model" + source.suffix, "/inputs/input.json"], request


def artifact_hashes(run_dir):
    result = {}
    for path in sorted(run_dir.rglob("*")):
        if path.is_symlink():
            raise RuntimeErrorSafe("Run contains a symlink: " + str(path))
        if path.is_file() and path != run_dir / "result.json":
            result[str(path.relative_to(run_dir))] = digest(path)
    return result


def validate_checks(experiment):
    checks = experiment.get("checks") if isinstance(experiment, dict) else None
    return bool(isinstance(checks, list) and checks and all(
        isinstance(check, dict) and isinstance(check.get("name"), str)
        and check.get("passed") is True for check in checks))


def run(args):
    request_path = checked_path(args.input)
    request = load_json(request_path)
    profile, source, extra, command, prepared = prepare_request(request)
    if profile in GPU and not args.cuda:
        raise RuntimeErrorSafe("GPU execution requires explicit --cuda")
    run_dir = checked_path(args.output_dir, new=True)
    state = state_dir(args)
    manifest = load_json(state / "installation.json")
    if profile not in manifest["profiles"]:
        raise RuntimeErrorSafe("Profile is not installed: " + profile)
    record = manifest["profiles"][profile]
    if record.get("fingerprint") != source_fingerprint(profile):
        raise RuntimeErrorSafe("Environment definitions changed; install in a new state directory")
    package_lock = checked_path(state / (profile + ".packages.lock"))
    if not package_lock.is_file() or digest(package_lock) != record.get("packages_sha256"):
        raise RuntimeErrorSafe("Installed package-lock hash mismatch")
    if record.get("smoke", {}).get("status") != "completed":
        raise RuntimeErrorSafe("Profile has not passed installation smoke checks: " + profile)
    if not source.is_file():
        raise RuntimeErrorSafe("Experiment source does not exist")
    names = {"input.json", "model" + source.suffix}
    for path in extra:
        if not path.is_file() or path.name in names:
            raise RuntimeErrorSafe("Invalid or duplicate supporting source")
        names.add(path.name)
    run_dir.mkdir(parents=True)
    inputs = run_dir / "inputs"
    output = run_dir / "artifacts"
    inputs.mkdir()
    output.mkdir()
    shutil.copyfile(source, inputs / ("model" + source.suffix))
    for path in extra:
        shutil.copyfile(path, inputs / path.name)
    write_json(inputs / "input.json", prepared)
    write_json(run_dir / "request.json", request)
    container_name = "math-" + uuid.uuid4().hex
    cmd = container_command(record["image_id"], command, inputs=inputs, output=output,
                            gpu=profile in GPU, device=args.device,
                            label_disable=args.selinux_label_disable, name=container_name,
                            entrypoint="/usr/bin/env" if profile == "sage" else None,
                            petsc_gpu=profile == "petsc-cuda")
    lock = exclusive(state / "gpu.lock") if profile in GPU else contextlib.nullcontext()
    with lock:
        outcome = process(cmd, run_dir / "execution.log", args.timeout, artifact_dir=output)
        if outcome["status"] in {"timeout", "output_limit", "log_limit"}:
            process(["podman", "kill", container_name], run_dir / "execution.log", 15)
    experiment_path = output / "experiment.json"
    experiment = None
    if experiment_path.is_file() and not experiment_path.is_symlink():
        try:
            experiment = load_json(experiment_path)
        except (ValueError, OSError):
            pass
    result = {"schema_version": 1, "profile": profile, "environment": record,
              "command": cmd, "execution": outcome, "checks_passed": validate_checks(experiment),
              "mathematically_certified": False,
              "limitations": ["Declared checks cover this experiment only; execution and verification do not certify arbitrary mathematical claims."],
              "experiment": experiment, "artifacts": artifact_hashes(run_dir)}
    write_json(run_dir / "result.json", result)
    print(json.dumps({"run_dir": str(run_dir), "execution": outcome,
                      "checks_passed": result["checks_passed"]}, indent=2))
    return 0 if outcome["status"] == "completed" and result["checks_passed"] else 1


def verify(args):
    run_dir = checked_path(args.run_dir)
    result = load_json(checked_path(run_dir / "result.json"))
    actual = artifact_hashes(run_dir)
    intact = actual == result.get("artifacts")
    experiment_path = run_dir / "artifacts/experiment.json"
    experiment = load_json(experiment_path) if experiment_path.is_file() and not experiment_path.is_symlink() else None
    passed = intact and experiment == result.get("experiment") and result.get("execution", {}).get("status") == "completed" and validate_checks(experiment)
    print(json.dumps({"artifacts_intact": intact, "checks_passed": passed,
                      "mathematically_certified": False}, indent=2))
    return 0 if passed else 1


def benchmark(args):
    """Repeat complete runs; backend-specific kernel timings remain separate."""
    import copy
    import statistics
    if not 1 <= args.repetitions <= 50 or not 0 <= args.warmup <= 10:
        raise RuntimeErrorSafe("repetitions must be 1..50 and warmup 0..10")
    base = checked_path(args.output_dir, new=True)
    # Validate the input before creating the benchmark directory.
    profile, *_ = prepare_request(load_json(checked_path(args.input)))
    if profile in GPU and not args.cuda:
        raise RuntimeErrorSafe("GPU benchmarks require --cuda")
    base.mkdir(parents=True)
    elapsed = []
    passed = True
    for index in range(args.warmup + args.repetitions):
        child = copy.copy(args)
        prefix = "warmup-" if index < args.warmup else "measured-"
        child.output_dir = str(base / (prefix + str(index)))
        child.timeout = max(1, args.timeout // (args.warmup + args.repetitions))
        code = run(child)
        passed = passed and code == 0
        result_path = Path(child.output_dir) / "result.json"
        if index >= args.warmup and result_path.exists():
            elapsed.append(load_json(result_path)["execution"]["seconds"])
    report = {"checks_passed": passed, "warmup": args.warmup, "repetitions": args.repetitions,
              "measured_container_wall_seconds": elapsed,
              "median_container_wall_seconds": statistics.median(elapsed) if elapsed else None,
              "limitations": ["Container wall time includes startup, compilation, and transfers. Backend kernel timings must be read separately from each experiment; excluded warmup processes do not guarantee persistent JIT caches."]}
    write_json(base / "benchmark.json", report)
    print(json.dumps(report, indent=2))
    return 0 if passed else 1


def parser():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--state-dir", default=str(Path(os.environ.get("XDG_DATA_HOME", str(Path.home() / ".local/share"))) / "opencode/math-research-v2"))
    sub = p.add_subparsers(dest="action", required=True)
    for action in ("setup", "doctor", "run", "benchmark"):
        q = sub.add_parser(action)
        # Accept state selection after the subcommand as well as before it.
        q.add_argument("--state-dir", default=argparse.SUPPRESS)
        q.add_argument("--cuda", action="store_true")
        q.add_argument("--device", default="nvidia.com/gpu=0")
        q.add_argument("--selinux-label-disable", action="store_true", help="Disable container SELinux separation for non-GPU runs; CDI GPU runs require it")
        if action == "setup":
            q.add_argument("--apply", action="store_true")
            q.add_argument("--rebuild", action="store_true", help="Build every selected profile without cached layers and repeat smoke checks")
            q.add_argument("--plan", action="store_true")
            q.add_argument("--profile", choices=["all", *PROFILES], default="all")
        elif action == "doctor":
            q.add_argument("--offline", action="store_true")
            q.add_argument("--smoke", action="store_true")
        else:
            q.add_argument("--input", required=True)
            q.add_argument("--output-dir", required=True)
            q.add_argument("--timeout", type=int, default=900 if action == "benchmark" else 120)
            if action == "benchmark":
                q.add_argument("--repetitions", type=int, default=3)
                q.add_argument("--warmup", type=int, default=1)
    q = sub.add_parser("verify")
    q.add_argument("--run-dir", required=True)
    return p


def main(argv=None):
    args = parser().parse_args(argv)
    try:
        if hasattr(args, "timeout") and not 1 <= args.timeout <= 86400:
            raise RuntimeErrorSafe("timeout must be between 1 and 86400 seconds")
        if getattr(args, "plan", False) and args.apply:
            raise RuntimeErrorSafe("--plan and --apply are mutually exclusive")
        return {"setup": setup, "doctor": doctor, "run": run, "benchmark": benchmark, "verify": verify}[args.action](args)
    except (RuntimeErrorSafe, ValueError, OSError, KeyError) as exc:
        print(json.dumps({"status": "error", "error": str(exc)[:1000]}))
        return 1


if __name__ == "__main__":
    sys.exit(main())
