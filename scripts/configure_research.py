#!/usr/bin/env python3
"""Human-run, dry-run by default setup for a provider-confirmed SciSpace MCP URL."""
import argparse
import datetime
import json
import os
from pathlib import Path
import tempfile
import urllib.parse


def configure(config, url):
    u = urllib.parse.urlsplit(url)
    if u.scheme != 'https' or not u.hostname or u.username or u.password or u.fragment or u.query:
        raise ValueError('Use the provider-confirmed HTTPS MCP endpoint without embedded credentials or query parameters')
    if u.hostname != 'scispace.com' and not u.hostname.endswith('.scispace.com'):
        raise ValueError('Endpoint must belong to scispace.com; obtain an official endpoint from SciSpace')
    config['mcp']['servers']['scispace'] = {'type': 'remote', 'url': url, 'disabled': True, 'codemode': False}
    permission = {'action': 'scispace_*', 'resource': '*', 'effect': 'ask'}
    policy = {'action': 'mcp.use', 'resource': 'scispace', 'effect': 'allow'}
    for key, entry in [('permissions', permission), ('policies', policy)]:
        if entry not in config[key]:
            config[key].append(entry)
    return config


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', type=Path, required=True)
    parser.add_argument('--scispace-url', required=True)
    parser.add_argument('--provider-confirmed', action='store_true', help='Confirm SciSpace supplied this endpoint for your client/account')
    parser.add_argument('--apply', action='store_true')
    args = parser.parse_args()
    if not args.provider_confirmed:
        parser.error('Obtain provider confirmation, then supply --provider-confirmed; a third-party directory listing is insufficient')
    if args.config.is_symlink():
        parser.error('Refusing a symlink configuration')
    try:
        text = args.config.read_text()
        try:
            config = json.loads(text)
        except ValueError:
            import json5
            config = json5.loads(text)
        result = json.dumps(configure(config, args.scispace_url), indent=2) + '\n'
        print('SciSpace will be configured DISABLED. No authentication or network request is performed.')
        if args.apply:
            backup = args.config.with_name(args.config.name + '.backup-' + datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'))
            with backup.open('x') as f:
                f.write(text)
            os.chmod(backup, 0o600)
            fd, name = tempfile.mkstemp(dir=args.config.parent, prefix='.research-config-')
            try:
                with os.fdopen(fd, 'w') as f:
                    f.write(result)
                os.replace(name, args.config)
            finally:
                if os.path.exists(name):
                    os.unlink(name)
            print('Saved configuration with backup. JSONC comments, if any, were normalized away.')
        else:
            print('Dry-run: no files written. Review before adding --apply.')
    except (ValueError, KeyError, OSError, ImportError) as exc:
        parser.exit(1, f'Setup failed: {exc}\n')


if __name__ == '__main__':
    main()
