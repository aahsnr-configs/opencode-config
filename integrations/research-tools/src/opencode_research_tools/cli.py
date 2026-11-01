"""JSON-stdin CLI; no network work unless a provider operation is selected."""
import argparse
import importlib.util
import json
import os
import sys
import sqlite3
from .http import IntegrationError


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['doctor', 'serve-zotero', 'zotero', 'run', 'scispace-import', 'openai-research'])
    args = parser.parse_args(argv)
    try:
        if args.command == 'serve-zotero':
            from .server import build_server
            build_server().run(transport='stdio')
            return 0
        if args.command == 'doctor':
            result = {'mcp_sdk': bool(importlib.util.find_spec('mcp')),
                'zotero_mode': os.environ.get('ZOTERO_MODE', 'local'),
                'zotero_web_credentials_configured': bool(os.environ.get('ZOTERO_API_KEY') and os.environ.get('ZOTERO_USER_ID')),
                'scispace': 'provider-confirmed MCP URL required; no REST schema assumed',
                'openai_research_configured': bool(os.environ.get('OPENAI_API_KEY') and os.environ.get('OPENAI_RESEARCH_MODEL')),
                'live_connections_tested': False}
        else:
            raw = sys.stdin.read(5_000_001)
            if len(raw.encode()) > 5_000_000:
                raise IntegrationError('Input exceeds 5 MB')
            p = json.loads(raw)
            if not isinstance(p, dict):
                raise IntegrationError('Input must be a JSON object')
            if args.command == 'run':
                from .state import Store
                op = p.pop('operation', None)
                if op not in ('create', 'get', 'list', 'update', 'export'):
                    raise IntegrationError('Unsupported run operation')
                result = getattr(Store(), op)(**p)
            elif args.command == 'zotero':
                from .zotero import Zotero, better_bibtex
                op = p.pop('operation', None)
                if op == 'better_bibtex':
                    result = better_bibtex(**p)
                elif op in ('status', 'search', 'get', 'collections', 'collection_items', 'tags', 'children', 'fulltext', 'export', 'preview_import', 'import_items'):
                    result = getattr(Zotero(), op)(**p)
                else:
                    raise IntegrationError('Unsupported Zotero operation')
            elif args.command == 'scispace-import':
                from .scispace import import_table
                result = import_table(**p)
            else:
                from . import openai_research
                op = p.pop('operation', None)
                if op not in ('start', 'retrieve'):
                    raise IntegrationError('Choose start or retrieve')
                result = getattr(openai_research, op)(**p)
        print(json.dumps({'ok': True, 'result': result}, ensure_ascii=False, indent=2))
        return 0
    except (IntegrationError, ValueError, TypeError, OSError, ImportError, sqlite3.Error) as exc:
        print(json.dumps({'ok': False, 'error': str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
