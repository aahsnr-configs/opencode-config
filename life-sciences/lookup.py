#!/usr/bin/env python3
"""Small read-only public research lookups; outputs upstream data with provenance."""
import argparse
import datetime
import json
import re
import sys
import urllib.error
import urllib.parse
import urllib.request

MAX_BYTES = 5_000_000

def build_url(kind, value, limit=10):
    if kind == 'alphafold':
        if not re.fullmatch(r'[A-Za-z0-9]{6,10}(?:-[0-9]+)?', value):
            raise ValueError('Expected a UniProt accession (e.g. P00520).')
        return 'https://alphafold.ebi.ac.uk/api/prediction/' + urllib.parse.quote(value, safe='')
    if kind == 'literature':
        if not value.strip() or len(value) > 1000:
            raise ValueError('Query must contain 1–1000 characters.')
        if not 1 <= limit <= 100:
            raise ValueError('Limit must be between 1 and 100.')
        q = urllib.parse.urlencode({'query': value, 'format': 'json', 'resultType': 'lite', 'pageSize': limit})
        return 'https://www.ebi.ac.uk/europepmc/webservices/rest/search?' + q
    raise ValueError('Unknown lookup type')

def lookup(kind, value, limit=10):
    url = build_url(kind, value, limit)
    request = urllib.request.Request(url, headers={'Accept': 'application/json', 'User-Agent': 'opencode-life-sciences/0.1'})
    with urllib.request.urlopen(request, timeout=30) as response:
        raw = response.read(MAX_BYTES + 1)
    if len(raw) > MAX_BYTES:
        raise ValueError('Response exceeds size limit')
    result = json.loads(raw)
    if kind == 'alphafold' and not isinstance(result, list):
        raise ValueError('Unexpected AlphaFold response shape')
    if kind == 'literature' and not isinstance(result, dict):
        raise ValueError('Unexpected Europe PMC response shape')
    return {'source_url': url, 'retrieved_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'data': result}

def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('kind', choices=['alphafold', 'literature'])
    parser.add_argument('query', help='UniProt accession or Europe PMC query')
    parser.add_argument('--limit', type=int, default=10, help='Maximum literature results (1–100)')
    args = parser.parse_args(argv)
    try:
        print(json.dumps(lookup(args.kind, args.query, args.limit), indent=2, ensure_ascii=False))
    except (ValueError, OSError, urllib.error.URLError) as exc:
        print(f'Lookup failed: {exc}', file=sys.stderr)
        return 1
    return 0

if __name__ == '__main__':
    sys.exit(main())
