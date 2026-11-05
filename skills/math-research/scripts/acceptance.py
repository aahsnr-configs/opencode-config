#!/usr/bin/env python3
"""Run the research acceptance suite locally, without model or provider calls."""
import argparse
import json
from pathlib import Path
import subprocess
import sys


def main():
    # Keep importing this script side-effect free under repository-wide audits.
    from math_research import ROOT, GPU, checked_path, load_json, write_json
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--state-dir', required=True)
    p.add_argument('--output-dir', required=True)
    p.add_argument('--cuda', action='store_true')
    p.add_argument('--selinux-label-disable', action='store_true')
    args = p.parse_args()
    output = checked_path(args.output_dir, new=True)
    output.mkdir(parents=True)
    catalog = load_json(ROOT / 'examples/catalog.json')
    catalog = catalog.get('experiments', catalog)
    summary = {'status': 'running', 'model_calls': 0, 'cases': {}}
    launcher = str(ROOT / 'scripts/math_research.py')
    for name, spec in catalog.items():
        if spec['profile'] in GPU and not args.cuda:
            summary['cases'][name] = {'status': 'not_requested'}
            continue
        request = output / (name + '-input.json')
        write_json(request, {'experiment': name})
        run_dir = output / name
        command = [sys.executable, launcher, 'run', '--state-dir', args.state_dir,
                   '--input', str(request), '--output-dir', str(run_dir), '--timeout', '900']
        if spec['profile'] in GPU:
            command.append('--cuda')
        if args.selinux_label_disable:
            command.append('--selinux-label-disable')
        with (output / (name + '.log')).open('x') as log:
            result = subprocess.run(command, stdout=log, stderr=subprocess.STDOUT)
            verified = subprocess.run([sys.executable, launcher, 'verify', '--run-dir', str(run_dir)],
                                      stdout=log, stderr=subprocess.STDOUT) if result.returncode == 0 else None
        summary['cases'][name] = {'status': 'passed' if result.returncode == 0 and verified.returncode == 0 else 'failed'}
        write_json(output / 'summary.json', summary)
    summary['status'] = 'passed' if all(
        case['status'] in ('passed', 'not_requested') for case in summary['cases'].values()) else 'failed'
    write_json(output / 'summary.json', summary)
    print(json.dumps({'status': summary['status'], 'summary': str(output / 'summary.json')}))
    return 0 if summary['status'] == 'passed' else 1


if __name__ == '__main__':
    sys.exit(main())
