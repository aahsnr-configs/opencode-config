#!/usr/bin/env python3
"""Deterministic local physics environments and preserved experiments; no AI clients."""
from __future__ import annotations
import argparse
import contextlib
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import statistics
import sys
import time
import uuid

ROOT = Path(__file__).resolve().parents[1]
# Reuse the installed math skill's audited container/process primitives, without
# changing that module's profile globals or loading its research artifacts.
_support = ROOT.parent / 'math-research/scripts/math_research.py'
_spec = importlib.util.spec_from_file_location('physics_runtime_support', _support)
_support_module = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_support_module)
for _name in ('RuntimeErrorSafe', 'checked_path', 'digest', 'write_json', 'load_json',
              'capture', 'process', 'exclusive', 'container_command', 'artifact_hashes', 'gpu_preflight'):
    globals()[_name] = getattr(_support_module, _name)

# Direct PyPI requirements; no Conda solver or package channel is used.
PROFILES = {
    'analysis': ['numpy==2.2.6', 'scipy==1.15.3', 'sympy==1.14.0', 'ase==3.29.0', 'pymatgen==2026.9.24', 'spglib==2.6.0', 'seekpath==2.2.2', 'phonopy==4.8.6', 'MDAnalysis==2.11.0', 'pymbar[jax]==4.0.3', 'matplotlib==3.10.8'],
    'pymbar-cuda': ['numpy==2.2.6', 'scipy==1.15.3', 'pymbar[jax]==4.0.3', 'jax[cuda12]==0.12.0.1'],
    'preparation': ['openff-toolkit @ https://github.com/openforcefield/openff-toolkit/archive/refs/tags/0.19.0.tar.gz', 'openff-utilities @ https://github.com/openforcefield/openff-utilities/archive/4fc551250f568b86d42555d3108d34e4868376b6.tar.gz', 'openff-forcefields @ https://github.com/openforcefield/openff-forcefields/archive/1a4063b18a16636833a0f0f0a119a9d741cf3c61.tar.gz', 'openff-units==0.3.2', 'rdkit==2025.9.4', 'openmm==8.4.0', 'numpy==2.2.6', 'networkx==3.4.2', 'cachetools==5.5.2', 'xmltodict==0.14.2', 'python-constraint==1.4.0', 'packaging==25.0'],
    'openmm': ['openmm==8.4.0'],
    'gromacs': ['numpy==2.2.6'], 'lammps': ['numpy==2.2.6'], 'hoomd': ['numpy==2.2.6', 'pybind11==2.13.6'],
    'qe': [], 'cp2k': [],
    'pyscf': ['pyscf==2.11.0'],
    'quantum': ['qutip==5.2.3', 'physics-tenpy==1.1.1'],
    'kwant': ['kwant==1.5.0'],
    'openmm-cuda': ['openmm==8.4.0'], 'hoomd-cuda': ['numpy==2.2.6', 'pybind11==2.13.6'],
    'gromacs-cuda': ['numpy==2.2.6'], 'lammps-cuda': ['numpy==2.2.6'],
}
APT = {
    'analysis': [], 'pymbar-cuda': [], 'preparation': [], 'openmm': [], 'openmm-cuda': [],
    'gromacs': ['cmake', 'g++', 'libfftw3-dev', 'pkg-config'],
    'gromacs-cuda': ['cmake', 'g++', 'libfftw3-dev', 'pkg-config'],
    'lammps': ['cmake', 'g++', 'pkg-config'],
    'lammps-cuda': ['cmake', 'g++', 'pkg-config'],
    'hoomd': ['cmake', 'g++', 'git', 'libeigen3-dev'], 'hoomd-cuda': ['cmake', 'g++', 'git', 'libeigen3-dev'],
    'qe': ['quantum-espresso'], 'cp2k': ['cp2k', 'cp2k-data'],
    'pyscf': [], 'quantum': [], 'kwant': ['g++', 'python3-dev', 'gfortran', 'libopenblas-dev', 'liblapack-dev'],
}

GPU = {p for p in PROFILES if p.endswith('-cuda')}
CUDA_TOOLKIT_GPU = GPU - {'pymbar-cuda'}
SOURCES = {
    'gromacs.tar.gz': 'https://ftp.gromacs.org/gromacs/gromacs-2025.3.tar.gz',
    'lammps.tar.gz': 'https://github.com/lammps/lammps/archive/refs/tags/stable_22Jul2025_update3.tar.gz',
    'plumed.tar.gz': 'https://github.com/plumed/plumed2/archive/90dec6d6ebf97ad5f2580e50e563b70c1728c4e6.tar.gz',
    'Si.pbe-rrkj.UPF': 'https://raw.githubusercontent.com/QEF/q-e/qe-7.4.1/test-suite/pseudo/Si.pbe-rrkj.UPF',
}
CASES = {p: p.split('-cuda')[0] for p in PROFILES}
PYTHON = 'docker.io/library/python:3.13-slim-trixie'
CUDA = 'docker.io/nvidia/cuda:12.8.1-devel-ubuntu22.04'


def selected(profile, cuda):
    if profile not in {'all', *PROFILES}:
        raise RuntimeErrorSafe('Unknown profile')
    if profile in GPU and not cuda:
        raise RuntimeErrorSafe('GPU profiles require --cuda')
    return [p for p in PROFILES if cuda or p not in GPU] if profile == 'all' else [profile]


def accepted(results):
    return bool(results) and all(v.get('status') in {'completed', 'reused'} for v in results.values())


def valid_report(report):
    checks = report.get('checks') if isinstance(report, dict) else None
    return bool(isinstance(checks, list) and checks and all(isinstance(c, dict) and isinstance(c.get('name'), str) and c.get('passed') is True for c in checks))


def fingerprint(name):
    h = hashlib.sha256(json.dumps({'pip': PROFILES[name], 'apt': APT[name], 'python': PYTHON, 'cuda': CUDA}, sort_keys=True).encode())
    for filename in (name + '.Containerfile', 'install.sh', 'source_build.sh'):
        h.update((ROOT / 'environments' / filename).read_bytes())
    h.update((ROOT / 'examples/checks.py').read_bytes())
    h.update(Path(__file__).read_bytes())
    for filename, url in sorted(SOURCES.items()):
        if filename in {'gromacs.tar.gz'} and not name.startswith('gromacs'):
            continue
        if filename in {'lammps.tar.gz'} and not name.startswith('lammps'):
            continue
        if filename == 'Si.pbe-rrkj.UPF' and name != 'qe':
            continue
        h.update(filename.encode() + url.encode())
    return h.hexdigest()


def state_path(args):
    return checked_path(args.state_dir)


def image_digest(tag, log):
    result = process(['podman', 'pull', tag], log, 1800)
    if result['status'] != 'completed':
        raise RuntimeErrorSafe('Image pull failed: ' + tag)
    details = json.loads(capture(['podman', 'image', 'inspect', tag]))[0]
    return next(iter(details.get('RepoDigests', [])), details['Id'])


def fetch_source(context, filename):
    import urllib.request
    path = context / filename
    record_path = context / (filename + '.json')
    if path.exists():
        if not record_path.exists() or digest(path) != load_json(record_path)['sha256']:
            raise RuntimeErrorSafe('Source archive integrity mismatch: ' + filename)
        return
    temp = context / (filename + '.partial')
    with urllib.request.urlopen(SOURCES[filename], timeout=120) as response, temp.open('wb') as stream:
        total = int(response.headers.get('Content-Length', '0'))
        copied = 0
        last_report = 0
        while chunk := response.read(1024 * 1024):
            stream.write(chunk)
            copied += len(chunk)
            if copied - last_report >= 16 * 1024 * 1024:
                size = str(total) if total else 'unknown'
                print('[{}] downloaded {}/{} bytes'.format(filename, copied, size), flush=True)
                last_report = copied
        stream.flush()
        os.fsync(stream.fileno())
    temp.replace(path)
    write_json(record_path, {'url': SOURCES[filename], 'sha256': digest(path),
                             'trust': 'First retrieval over HTTPS; preserved checksum thereafter'})


def setup(args):
    names = selected(args.profile, args.cuda)
    state = state_path(args)
    if not args.apply:
        print(json.dumps({'action': 'preview', 'profiles': names, 'state_dir': str(state),
                          'model_calls': 0, 'build_order': 'sequential',
                          'disk_estimate_gib': [40, 100], 'estimate_is_not_measurement': True,
                          'gpu_selinux_label_exception': bool(args.cuda),
                          'packages': {n: PROFILES[n] for n in names}}, indent=2))
        return 0
    state.mkdir(parents=True, exist_ok=True)
    with exclusive(state / 'setup.lock'):
        return install(args, names, state)


def install(args, names, state):
    logs = state / 'logs'
    logs.mkdir(exist_ok=True)
    manifest_path = state / 'installation.json'
    manifest = load_json(manifest_path) if manifest_path.exists() else {'schema_version': 1, 'profiles': {}}
    summary = {'status': 'incomplete', 'model_calls': 0, 'profiles': {}}
    if capture(['podman', 'info', '--format', '{{.Host.Security.Rootless}}']).lower() != 'true':
        raise RuntimeErrorSafe('Rootless Podman required')
    bases_file = state / 'bases.json'
    bases = load_json(bases_file) if bases_file.exists() else {}
    for name in names:
        log = logs / (name + '.log')
        print(f'[{name}] setup; verbose log: {log}', flush=True)
        try:
            expected = fingerprint(name)
            old = manifest['profiles'].get(name)
            if old and old['fingerprint'] != expected:
                raise RuntimeErrorSafe('Definition changed: choose a new state directory')
            old_lock = state / 'build' / name / 'packages.lock'
            if old and old_lock.exists() and digest(old_lock) != old.get('lock_sha256'):
                raise RuntimeErrorSafe('Recorded package lock changed: use a new state directory')
            if (old and not args.rebuild and old.get('smoke', {}).get('status') == 'completed'
                    and old_lock.is_file() and digest(old_lock) == old.get('lock_sha256')):
                capture(['podman', 'image', 'exists', old['image_id']])
                summary['profiles'][name] = {'status': 'reused'}
                continue
            if name in GPU:
                gpu_preflight()
            tag_base = PYTHON
            base_key = tag_base
            if base_key not in bases:
                bases[base_key] = image_digest(tag_base, log)
                write_json(bases_file, bases)
            context = state / 'build' / name
            context.mkdir(parents=True, exist_ok=True)
            lock = context / 'packages.lock'
            specs_path = context / 'specs.json'
            requested = {'pip': PROFILES[name], 'apt': APT[name]}
            if specs_path.exists() and load_json(specs_path) != requested:
                if old and old.get('smoke', {}).get('status') == 'completed':
                    raise RuntimeErrorSafe('Successful profile definition changed: use a new state directory')
                specs_path.replace(context / ('specs.previous-' + digest(specs_path)[:12] + '.json'))
            write_json(specs_path, requested)
            (context / 'requirements.txt').write_text('\n'.join(PROFILES[name]) + ('\n' if PROFILES[name] else ''))
            dockerfile = ['ARG BASE']
            if name in CUDA_TOOLKIT_GPU:
                cuda_key = CUDA
                if cuda_key not in bases:
                    bases[cuda_key] = image_digest(CUDA, log)
                    write_json(bases_file, bases)
                dockerfile += ['FROM ' + bases[cuda_key] + ' AS cuda']
            dockerfile += ['FROM ${BASE}', 'USER root']
            if name in CUDA_TOOLKIT_GPU:
                dockerfile += ['COPY --from=cuda /usr/local/cuda-12.8 /usr/local/cuda-12.8', 'ENV CUDA_HOME=/usr/local/cuda-12.8', 'ENV PATH=/usr/local/cuda-12.8/bin:$PATH', 'ENV LD_LIBRARY_PATH=/usr/local/cuda-12.8/lib64:$LD_LIBRARY_PATH']
            apt = ['ca-certificates', 'python3', 'python3-pip', 'python3-venv', 'python-is-python3', *APT[name], 'make', 'libgsl-dev', 'liblapack-dev', 'libblas-dev']
            dockerfile += ['ENV DEBIAN_FRONTEND=noninteractive',
                'RUN apt-get update && apt-get install -y --no-install-recommends ' + ' '.join(apt) + ' && rm -rf /var/lib/apt/lists/*']
            dockerfile += ['RUN python -c "import sys; assert sys.version_info[:2] == (3, 13)" && python -m venv /opt/physics', 'ENV PATH=/opt/physics/bin:$PATH', 'COPY requirements.txt /tmp/requirements.txt']
            if PROFILES[name]:
                dockerfile += ['RUN python -m pip install --no-cache-dir -r /tmp/requirements.txt']
            if name.startswith(('gromacs', 'lammps')) or name.startswith('hoomd'):
                dockerfile += ['ENV PLUMED_KERNEL=/usr/local/lib/libplumedKernel.so', 'COPY source_build.sh /tmp/source_build.sh', 'COPY . /tmp/physics-source', 'RUN sh /tmp/source_build.sh ' + name]
            if name == 'qe':
                dockerfile += ['COPY Si.pbe-rrkj.UPF /opt/Si.pbe-rrkj.UPF']
            dockerfile += ['COPY checks.py /opt/checks.py', 'ENTRYPOINT []',
                           f'CMD ["python", "/opt/checks.py", "{name}", "--smoke"]']
            (context / (name + '.Containerfile')).write_text('\n'.join(dockerfile) + '\n')
            shutil.copyfile(ROOT / 'examples/checks.py', context / 'checks.py')
            shutil.copyfile(ROOT / 'environments/source_build.sh', context / 'source_build.sh')
            sources = (['gromacs.tar.gz'] if name.startswith('gromacs') else ['lammps.tar.gz'] if name.startswith('lammps') else ['Si.pbe-rrkj.UPF'] if name == 'qe' else [])
            if name.startswith(('gromacs', 'lammps')):
                sources.append('plumed.tar.gz')
            for filename in sources:
                fetch_source(context, filename)
            tag = 'localhost/opencode-physics-' + name + ':' + expected[:12]
            base = bases[base_key]
            command = ['podman', 'build', '--pull=never', '--memory=12g', '--jobs=1',
                       *(['--no-cache'] if args.rebuild else []), '--build-arg', 'BASE=' + base,
                       '-f', str(context / (name + '.Containerfile')), '-t', tag, str(context)]
            outcome = process(command, log, args.build_timeout)
            if outcome['status'] != 'completed':
                raise RuntimeErrorSafe('Build ' + outcome['status'] + '; see ' + str(log))
            image = json.loads(capture(['podman', 'image', 'inspect', tag]))[0]['Id']
            package_lock = capture(['podman', 'run', '--rm', '--pull=never', image, 'sh', '-lc', 'python -m pip freeze; dpkg-query -W'])
            lock.write_text(package_lock + '\n')
            smoke = process(container_command(image, ['python', '/opt/checks.py', name, '--smoke'], gpu=name in GPU, device=args.device), log, 600)
            manifest['profiles'][name] = {'image_id': image, 'fingerprint': expected, 'base': base,
                'lock_sha256': digest(lock), 'smoke': smoke, 'installed_at': time.time()}
            write_json(manifest_path, manifest)
            summary['profiles'][name] = smoke
        except (RuntimeErrorSafe, ValueError, OSError, KeyError) as exc:
            summary['profiles'][name] = {'status': 'failed', 'error': str(exc)[:1000]}
        summary['status'] = 'completed' if accepted(summary['profiles']) else 'incomplete'
        write_json(state / 'setup-summary.json', summary)
    summary['status'] = 'completed' if accepted(summary['profiles']) and len(summary['profiles']) == len(names) else 'incomplete'
    write_json(state / 'setup-summary.json', summary)
    print(json.dumps(summary, indent=2))
    return 0 if summary['status'] == 'completed' else 1


def installed(state, profile):
    record = load_json(state / 'installation.json')['profiles'][profile]
    if record['fingerprint'] != fingerprint(profile) or record['smoke']['status'] != 'completed':
        raise RuntimeErrorSafe('Profile definition changed or smoke check failed: ' + profile)
    lock = state / 'build' / profile / 'packages.lock'
    if not lock.is_file() or digest(lock) != record.get('lock_sha256'):
        raise RuntimeErrorSafe('Package lock missing or changed: ' + profile)
    capture(['podman', 'image', 'exists', record['image_id']])
    return record


def doctor(args):
    state = state_path(args)
    results = {}
    for name in selected(args.profile, args.cuda):
        try:
            record = installed(state, name)
            results[name] = {'status': 'completed', 'image_id': record['image_id'], 'evidence': 'recorded_installation'}
            if args.smoke:
                (state / 'logs').mkdir(exist_ok=True)
                results[name] = process(container_command(record['image_id'], ['python', '/opt/checks.py', name, '--smoke'], gpu=name in GPU, device=args.device), state / 'logs' / (name + '-doctor.log'), 600)
        except (RuntimeErrorSafe, OSError, KeyError, ValueError) as exc:
            results[name] = {'status': 'failed', 'error': str(exc)[:500]}
    print(json.dumps({'profiles': results, 'all_passed': accepted(results), 'scientifically_validated': False}, indent=2))
    return 0 if accepted(results) else 1


def run(args):
    request = load_json(checked_path(args.input))
    profile = request.get('profile')
    if profile not in PROFILES:
        raise RuntimeErrorSafe('Request requires a supported profile')
    if profile in GPU and not args.cuda:
        raise RuntimeErrorSafe('GPU execution requires --cuda')
    if request.get('experiment') not in {None, CASES[profile]}:
        raise RuntimeErrorSafe('Unknown bundled experiment')
    source = checked_path(request['source']) if 'source' in request else ROOT / 'examples/checks.py'
    if source.suffix != '.py' or not source.is_file():
        raise RuntimeErrorSafe('Explicit models require a reviewed Python source')
    record = installed(state_path(args), profile)
    directory = checked_path(args.output_dir, new=True)
    directory.mkdir(parents=True)
    (directory / 'inputs').mkdir()
    (directory / 'artifacts').mkdir()
    shutil.copyfile(source, directory / 'inputs/model.py')
    write_json(directory / 'inputs/input.json', request)
    command = ['python', '/inputs/model.py', '/inputs/input.json'] if 'source' in request else ['python', '/inputs/model.py', profile]
    name = 'physics-' + uuid.uuid4().hex
    cmd = container_command(record['image_id'], command, inputs=directory / 'inputs', output=directory / 'artifacts', gpu=profile in GPU, device=args.device, name=name)
    lock = exclusive(state_path(args) / 'gpu.lock') if profile in GPU else contextlib.nullcontext()
    with lock:
        outcome = process(cmd, directory / 'execution.log', args.timeout, artifact_dir=directory / 'artifacts')
        if outcome['status'] in {'timeout', 'output_limit', 'log_limit'}:
            process(['podman', 'kill', name], directory / 'execution.log', 15)
    report_path = directory / 'artifacts/experiment.json'
    report = load_json(report_path) if report_path.is_file() and not report_path.is_symlink() else None
    environment = {'profile': profile, 'image_id': record['image_id'],
        'profile_fingerprint': record['fingerprint'], 'package_lock_sha256': record['lock_sha256'],
        'runtime_helpers': {str(_support): digest(_support)},
        'bundled_fixture_sha256': digest(ROOT / 'examples/checks.py'),
        'source_inputs': {p.name: digest(p) for p in (directory / 'inputs').iterdir() if p.is_file()},
        'source_archives': {key: load_json(state_path(args) / 'build' / profile / (key + '.json'))
            for key in (['gromacs.tar.gz'] if profile.startswith('gromacs') else ['lammps.tar.gz'] if profile.startswith('lammps') else ['Si.pbe-rrkj.UPF'] if profile == 'qe' else [])},
        'check_provenance': 'caller_supplied' if 'source' in request else 'bundled_fixture'}
    write_json(directory / 'environment.json', environment)
    result = {'schema_version': 1, 'environment': environment, 'profile': profile, 'execution': outcome,
              'experiment': report, 'checks_passed': valid_report(report), 'command': cmd,
              'limitations': ['Declared checks cover this fixture only; they do not validate arbitrary research.'],
              'artifacts': artifact_hashes(directory)}
    write_json(directory / 'result.json', result)
    return 0 if outcome['status'] == 'completed' and valid_report(report) else 1


def verify_path(directory):
    directory = checked_path(directory)
    result = load_json(checked_path(directory / 'result.json'))
    report = load_json(checked_path(directory / 'artifacts/experiment.json'))
    return artifact_hashes(directory) == result['artifacts'] and report == result['experiment'] and valid_report(report) and result['execution']['status'] == 'completed'


def acceptance(args):
    root = checked_path(args.output_dir, new=True)
    root.mkdir(parents=True)
    results = {}
    import copy
    for profile in selected(args.profile, args.cuda):
        request = root / (profile + '.json')
        write_json(request, {'profile': profile, 'experiment': CASES[profile]})
        child = copy.copy(args)
        child.input, child.output_dir = str(request), str(root / profile)
        try:
            code = run(child)
            results[profile] = {'status': 'completed' if code == 0 and verify_path(root / profile) else 'failed'}
        except (RuntimeErrorSafe, OSError, KeyError, ValueError) as exc:
            results[profile] = {'status': 'failed', 'error': str(exc)[:500]}
        write_json(root / 'acceptance.json', {'all_passed': accepted(results), 'profiles': results, 'model_calls': 0})
    print(json.dumps({'all_passed': accepted(results), 'profiles': results}, indent=2))
    return 0 if accepted(results) else 1


def benchmark(args):
    import copy
    root = checked_path(args.output_dir, new=True)
    root.mkdir(parents=True)
    measured, statuses = [], []
    for i in range(args.warmup + args.repetitions):
        child = copy.copy(args)
        child.output_dir = str(root / ('warmup-' if i < args.warmup else 'measured-') / str(i))
        code = run(child)
        statuses.append(code == 0)
        if i >= args.warmup:
            measured.append(load_json(Path(child.output_dir) / 'result.json')['execution']['seconds'])
    report = {'checks_passed': all(statuses), 'container_wall_seconds': measured,
              'median_container_wall_seconds': statistics.median(measured),
              'limitations': ['Includes process startup and transfers; not a kernel benchmark or speedup claim.']}
    write_json(root / 'benchmark.json', report)
    return 0 if all(statuses) else 1


def parser():
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest='action', required=True)
    for action in ('setup', 'doctor', 'run', 'verify', 'acceptance', 'benchmark'):
        q = sub.add_parser(action)
        q.add_argument('--state-dir', default=str(Path(os.environ.get('XDG_DATA_HOME', str(Path.home() / '.local/share'))) / 'opencode/physics-research-v5'))
        q.add_argument('--cuda', action='store_true')
        q.add_argument('--device', default='nvidia.com/gpu=0')
        if action in {'setup', 'doctor', 'acceptance'}:
            q.add_argument('--profile', choices=['all', *PROFILES], default='all')
        if action == 'setup':
            q.add_argument('--apply', action='store_true')
            q.add_argument('--rebuild', action='store_true')
            q.add_argument('--build-timeout', type=int, default=14400)
        if action == 'doctor':
            q.add_argument('--offline', action='store_true')
            q.add_argument('--smoke', action='store_true')
        if action in {'run', 'benchmark'}:
            q.add_argument('--input', required=True)
        if action in {'run', 'benchmark', 'acceptance'}:
            q.add_argument('--output-dir', required=True)
            q.add_argument('--timeout', type=int, default=900)
        if action == 'verify':
            q.add_argument('--run-dir', required=True)
        if action == 'benchmark':
            q.add_argument('--repetitions', type=int, choices=range(1, 51), default=3)
            q.add_argument('--warmup', type=int, choices=range(0, 11), default=1)
    return p


def main(argv=None):
    args = parser().parse_args(argv)
    try:
        if hasattr(args, 'timeout') and not 1 <= args.timeout <= 86400:
            raise RuntimeErrorSafe('timeout must be 1..86400 seconds')
        if args.action == 'verify':
            passed = verify_path(args.run_dir)
            print(json.dumps({'artifacts_and_declared_checks_passed': passed, 'scientifically_certified': False}))
            return 0 if passed else 1
        return globals()[args.action](args)
    except (RuntimeErrorSafe, OSError, ValueError, KeyError) as exc:
        print(json.dumps({'status': 'failed', 'error': str(exc)[:1000]}))
        return 1


if __name__ == '__main__':
    sys.exit(main())
