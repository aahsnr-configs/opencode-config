#!/usr/bin/env python3
"""Print required model IDs and compare against `opencode models`; never makes model calls."""
from pathlib import Path
import subprocess, sys, yaml
root=Path(__file__).resolve().parents[1]
requirements={}
for path in sorted((root/'agents').glob('*.md')):
    text=path.read_text(); front=yaml.safe_load(text.split('---',2)[1]); model=front.get('model')
    if model: requirements[path.stem]=model
if not requirements:
    print('No explicit agent models configured'); sys.exit(0)
print('Required agent models:')
for n,m in requirements.items():print(f'  {n:20s} {m}')
try:
    result=subprocess.run(['opencode','models'],capture_output=True,text=True,timeout=30)
except (FileNotFoundError,subprocess.TimeoutExpired) as e:
    print(f'NOT VERIFIED: cannot query CLI model catalog ({e}).');sys.exit(2)
if result.returncode!=0:
    print('NOT VERIFIED: opencode models failed; check provider login and catalog.');sys.exit(2)
available={line.strip().split()[0] for line in result.stdout.splitlines() if line.strip()}
missing=[]
for n,m in requirements.items():
    exact=m.split('#',1)[0]
    if exact not in available:missing.append((n,m))
if missing:
    print('UNAVAILABLE in this CLI catalog (could be provider- or account-specific):')
    for n,m in missing:print(f'  {n}: {m}')
    print('Choose a supported OpenAI model from /models and edit agents/<name>.md before using that agent.')
    sys.exit(3)
print('PASS: all required base model IDs occur in `opencode models`.')
print('NOTE: optional #high variant availability is not proven by this check. Verify in /models.')
