#!/usr/bin/env python3
"""Isolated home integration tests. Does not touch the real HOME."""

import os, pathlib, subprocess, tempfile, shutil

root = pathlib.Path(__file__).resolve().parents[1]
with tempfile.TemporaryDirectory(prefix="opencode-installer-test-") as temp:
    env = os.environ.copy()
    env["HOME"] = temp
    env["XDG_CONFIG_HOME"] = temp + "/xdg"
    target = pathlib.Path(env["XDG_CONFIG_HOME"]) / "opencode"

    def run(*a, ok=True):
        r = subprocess.run(
            ["bash", str(root / "install.sh"), *a],
            env=env,
            capture_output=True,
            text=True,
        )
        if ok:
            assert r.returncode == 0, (a, r.returncode, r.stdout, r.stderr)
        return r

    assert not target.exists()
    run("--dry-run")
    assert not target.exists()
    run("--apply")
    assert (target / "opencode.jsonc").exists()
    assert (target / "cli.json").exists()
    run("--apply")
    assert not list(pathlib.Path(env["XDG_CONFIG_HOME"]).glob("opencode-backup-*"))
    cfg = target / "opencode.jsonc"
    cfg.write_text("existing user config\n")
    cli = target / "cli.json"
    cli.write_text("existing CLI config\n")
    r = run("--apply", ok=False)
    assert r.returncode == 3 and cfg.read_text() == "existing user config\n"
    assert cli.read_text() == "existing CLI config\n"
    run("--apply", "--replace")
    assert "existing user config" not in cfg.read_text()
    backs = list(pathlib.Path(env["XDG_CONFIG_HOME"]).glob("opencode-backup-*"))
    assert (
        len(backs) == 1
        and (backs[0] / "opencode.jsonc").read_text() == "existing user config\n"
    )
    assert (backs[0] / "cli.json").read_text() == "existing CLI config\n"
print(
    "PASS: installer dry-run, first install, idempotency, conflict abort, backup+replace"
)

# A linked parent must be refused before any bundled files are written.
for linked_path in ('opencode', 'opencode/agents', 'opencode/skills', '.'):
    with tempfile.TemporaryDirectory(prefix="opencode-installer-path-test-") as temp:
        base = pathlib.Path(temp)
        external = base / 'external'
        external.mkdir()
        xdg = base / 'xdg'
        link = xdg if linked_path == '.' else xdg / linked_path
        link.parent.mkdir(parents=True, exist_ok=True)
        link.symlink_to(external, target_is_directory=True)
        env = {**os.environ, 'HOME': temp, 'XDG_CONFIG_HOME': str(xdg)}
        result = subprocess.run(
            ['bash', str(root / 'install.sh'), '--apply', '--replace'],
            env=env, capture_output=True, text=True,
        )
        assert result.returncode == 4, (linked_path, result.returncode, result.stderr)
        assert not list(external.iterdir()), linked_path
        assert not (xdg / 'opencode/opencode.jsonc').exists(), linked_path

with tempfile.TemporaryDirectory(prefix="opencode-installer-directory-test-") as temp:
    xdg = pathlib.Path(temp) / 'xdg'
    (xdg / 'opencode/opencode.jsonc').mkdir(parents=True)
    env = {**os.environ, 'HOME': temp, 'XDG_CONFIG_HOME': str(xdg)}
    result = subprocess.run(
        ['bash', str(root / 'install.sh'), '--apply', '--replace'],
        env=env, capture_output=True, text=True,
    )
    assert result.returncode == 4, (result.returncode, result.stderr)
    assert not (xdg / 'opencode/AGENTS.md').exists()
    assert not list(xdg.glob('opencode-backup-*'))
print('PASS: installer refuses linked parents and directory destinations before writing')

# Missing source directories and enumeration errors must not produce partial installs.
with tempfile.TemporaryDirectory(prefix='opencode-installer-source-test-') as temp:
    base = pathlib.Path(temp)
    source = base / 'source'
    source.mkdir()
    for name in ('install.sh', 'opencode.jsonc', 'cli.json', 'AGENTS.md'):
        shutil.copy2(root / name, source / name)
    env = {**os.environ, 'HOME': temp, 'XDG_CONFIG_HOME': str(base / 'xdg')}
    result = subprocess.run(['bash', str(source / 'install.sh'), '--apply'],
                            env=env, capture_output=True, text=True)
    assert result.returncode != 0, (result.stdout, result.stderr)
    assert not (base / 'xdg/opencode').exists()
    for name in ('agents', 'commands', 'skills'):
        (source / name).mkdir()
    bin_dir = base / 'bin'
    bin_dir.mkdir()
    fake_find = bin_dir / 'find'
    fake_find.write_text('#!/bin/sh\nexit 1\n')
    fake_find.chmod(0o755)
    env['PATH'] = str(bin_dir) + os.pathsep + env['PATH']
    result = subprocess.run(['bash', str(source / 'install.sh'), '--apply'],
                            env=env, capture_output=True, text=True)
    assert result.returncode != 0, (result.stdout, result.stderr)
    assert not (base / 'xdg/opencode').exists()
print('PASS: installer rejects missing source directories and enumeration errors')

# Exercise live links against a disposable source tree, never the checkout.
with tempfile.TemporaryDirectory(prefix='opencode-installer-link-test-') as temp:
    base = pathlib.Path(temp)
    source = base / 'source'
    source.mkdir()
    for name in ('install.sh', 'opencode.jsonc', 'cli.json', 'AGENTS.md'):
        shutil.copy2(root / name, source / name)
    for name in ('agents', 'commands', 'skills'):
        shutil.copytree(root / name, source / name)
    xdg = base / 'custom-config'
    target = xdg / 'opencode'
    env = {**os.environ, 'HOME': str(base), 'XDG_CONFIG_HOME': str(xdg)}

    def link_run(*args):
        return subprocess.run(['bash', str(source / 'install.sh'), '--link', *args],
                              env=env, capture_output=True, text=True)

    result = link_run('--dry-run')
    assert result.returncode == 0, result.stderr
    assert not target.exists()
    result = link_run('--apply')
    assert result.returncode == 0, (result.stdout, result.stderr)
    names = ('opencode.jsonc', 'cli.json', 'AGENTS.md', 'agents', 'commands', 'skills')
    for name in names:
        assert (target / name).is_symlink(), name
        assert (target / name).resolve() == (source / name).resolve(), name
    result = link_run('--apply')
    assert result.returncode == 0, (result.stdout, result.stderr)
    assert not list(xdg.glob('opencode-backup-*'))
    (source / 'cli.json').write_text('live edit\n')
    assert (target / 'cli.json').read_text() == 'live edit\n'
    added = source / 'agents' / 'live-test.md'
    added.write_text('new agent\n')
    assert (target / 'agents/live-test.md').read_text() == 'new agent\n'
    added.unlink()
    assert not (target / 'agents/live-test.md').exists()

with tempfile.TemporaryDirectory(prefix='opencode-installer-link-conflict-test-') as temp:
    base = pathlib.Path(temp)
    xdg = base / 'xdg'
    target = xdg / 'opencode'
    target.mkdir(parents=True)
    (target / 'cli.json').write_text('old config\n')
    (target / 'agents').mkdir()
    (target / 'agents/custom.md').write_text('custom agent\n')
    (target / 'unrelated').write_text('keep\n')
    env = {**os.environ, 'HOME': str(base), 'XDG_CONFIG_HOME': str(xdg)}
    cmd = ['bash', str(root / 'install.sh'), '--link', '--apply']
    result = subprocess.run(cmd, env=env, capture_output=True, text=True)
    assert result.returncode != 0, (result.stdout, result.stderr)
    assert not (target / 'opencode.jsonc').exists()
    assert (target / 'cli.json').read_text() == 'old config\n'
    assert not list(xdg.glob('opencode-backup-*'))
    result = subprocess.run(cmd + ['--replace'], env=env, capture_output=True, text=True)
    assert result.returncode == 0, (result.stdout, result.stderr)
    backups = list(xdg.glob('opencode-backup-*'))
    assert len(backups) == 1
    assert (backups[0] / 'cli.json').read_text() == 'old config\n'
    assert (backups[0] / 'agents/custom.md').read_text() == 'custom agent\n'
    assert (target / 'unrelated').read_text() == 'keep\n'
    assert (target / 'agents').is_symlink()
print('PASS: link mode dry-run, live updates, idempotency, conflicts and backups')
