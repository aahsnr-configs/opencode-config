#!/usr/bin/env python3
"""Isolated home integration tests. Does not touch the real HOME."""
import os, pathlib, subprocess, tempfile, shutil
root=pathlib.Path(__file__).resolve().parents[1]
with tempfile.TemporaryDirectory(prefix='opencode-installer-test-') as temp:
 env=os.environ.copy(); env['HOME']=temp; env['XDG_CONFIG_HOME']=temp+'/xdg'
 target=pathlib.Path(env['XDG_CONFIG_HOME'])/'opencode'
 def run(*a,ok=True):
  r=subprocess.run(['bash',str(root/'install.sh'),*a],env=env,capture_output=True,text=True)
  if ok: assert r.returncode==0,(a,r.returncode,r.stdout,r.stderr)
  return r
 assert not target.exists()
 run('--dry-run'); assert not target.exists()
 run('--apply'); assert (target/'opencode.jsonc').exists()
 run('--apply'); assert not list(pathlib.Path(env['XDG_CONFIG_HOME']).glob('opencode-backup-*'))
 cfg=target/'opencode.jsonc'; cfg.write_text('existing user config\n')
 r=run('--apply',ok=False); assert r.returncode==3 and cfg.read_text()=='existing user config\n'
 run('--apply','--replace'); assert 'existing user config' not in cfg.read_text()
 backs=list(pathlib.Path(env['XDG_CONFIG_HOME']).glob('opencode-backup-*'))
 assert len(backs)==1 and (backs[0]/'opencode.jsonc').read_text()=='existing user config\n'
print('PASS: installer dry-run, first install, idempotency, conflict abort, backup+replace')
