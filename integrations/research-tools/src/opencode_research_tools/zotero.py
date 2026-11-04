"""Official local/Web API access plus optional read-only Better BibTeX calls."""
import hashlib
import json
import os
import re
import urllib.parse
import uuid
from .http import request, IntegrationError


def doi(value):
    value = str(value or '').strip().lower()
    return re.sub(r'^(?:https?://(?:dx\.)?doi\.org/|doi:\s*)', '', value)


def item_key(value):
    if not isinstance(value, str) or not re.fullmatch(r'[A-Z0-9]{8}', value):
        raise IntegrationError('Expected an eight-character Zotero item/collection key')
    return value


class Zotero:
    def __init__(self, mode=None):
        self.mode = mode or os.environ.get('ZOTERO_MODE', 'local')
        if self.mode == 'local':
            self.base = 'http://127.0.0.1:23119/api'
            self.library = 'users/0'
            self.headers = {'Zotero-API-Version': '3'}
        elif self.mode == 'web':
            user = os.environ.get('ZOTERO_USER_ID', '')
            key = os.environ.get('ZOTERO_API_KEY', '')
            if not user.isdigit() or not key:
                raise IntegrationError('Web mode needs ZOTERO_USER_ID and ZOTERO_API_KEY')
            self.base = 'https://api.zotero.org'
            self.library = 'users/' + user
            self.headers = {'Zotero-API-Version': '3', 'Zotero-API-Key': key}
        else:
            raise IntegrationError('ZOTERO_MODE must be local or web')

    def read(self, path, params=None):
        url = f'{self.base}/{self.library}/{path}'
        if params:
            url += '?' + urllib.parse.urlencode(params)
        data, _ = request(url, headers=self.headers)
        return {'source_url': url, 'mode': self.mode, 'data': data}

    def status(self):
        url = self.base + '/' if self.mode == 'local' else f'{self.base}/{self.library}/items?limit=1'
        _, headers = request(url, headers=self.headers)
        lower = {k.lower(): v for k, v in headers.items()}
        return {'mode': self.mode, 'api_version': lower.get('zotero-api-version'),
                'server_id': lower.get('zotero-server-id'),
                'local_write_authorization_available': self.mode == 'local' and bool(lower.get('zotero-server-id'))}

    def search(self, query, limit=20, start=0):
        if not isinstance(query, str) or not query.strip() or len(query) > 1000:
            raise IntegrationError('Search query must contain 1–1000 characters')
        if type(limit) is not int or not 1 <= limit <= 100 or type(start) is not int or start < 0:
            raise IntegrationError('Use limit 1–100 and start >= 0')
        return self.read('items/top', {'q': query, 'qmode': 'everything', 'limit': limit, 'start': start})

    def get(self, key):
        return self.read('items/' + item_key(key))

    def collections(self, limit=50, start=0):
        if type(limit) is not int or not 1 <= limit <= 100 or type(start) is not int or start < 0:
            raise IntegrationError('Use limit 1–100 and start >= 0')
        return self.read('collections', {'limit': limit, 'start': start})

    def collection_items(self, key, limit=50, start=0):
        if type(limit) is not int or not 1 <= limit <= 100 or type(start) is not int or start < 0:
            raise IntegrationError('Use limit 1–100 and start >= 0')
        return self.read('collections/' + item_key(key) + '/items/top', {'limit': limit, 'start': start})

    def tags(self, limit=50, start=0):
        if type(limit) is not int or not 1 <= limit <= 100 or type(start) is not int or start < 0:
            raise IntegrationError('Use limit 1–100 and start >= 0')
        return self.read('tags', {'limit': limit, 'start': start})

    def children(self, key):
        return self.read('items/' + item_key(key) + '/children', {'limit': 100})

    def fulltext(self, attachment_key):
        # Indexed text does not supply reliable PDF page coordinates.
        return self.read('items/' + item_key(attachment_key) + '/fulltext')

    def export(self, keys, format='bibtex'):
        if format not in ('bibtex', 'biblatex', 'ris', 'csljson'):
            raise IntegrationError('Supported export formats: bibtex, biblatex, ris, csljson')
        if not isinstance(keys, list) or not 1 <= len(keys) <= 50:
            raise IntegrationError('Select 1–50 item keys')
        return self.read('items', {'itemKey': ','.join(item_key(k) for k in keys), 'format': format})

    def preview_import(self, items):
        if not isinstance(items, list) or not 1 <= len(items) <= 50:
            raise IntegrationError('Provide 1–50 Zotero item JSON objects')
        seen = set()
        for entry in items:
            if not isinstance(entry, dict) or not entry.get('itemType') or not entry.get('title'):
                raise IntegrationError('Every item needs itemType and title')
            d = doi(entry.get('DOI'))
            if d:
                if d in seen:
                    raise IntegrationError('Duplicate DOI in proposed import')
                seen.add(d)
        digest = hashlib.sha256(json.dumps(items, sort_keys=True, ensure_ascii=False).encode()).hexdigest()
        return {'items': items, 'digest': digest, 'duplicates_checked': False,
                'warning': 'Review all fields. Import rechecks DOI matches and requires explicit confirmation.'}

    def import_items(self, items, confirm_digest):
        plan = self.preview_import(items)
        if not confirm_digest or confirm_digest != plan['digest']:
            raise IntegrationError('Import needs the exact digest of the reviewed preview')
        for entry in items:
            d = doi(entry.get('DOI'))
            if d:
                start = 0
                while True:
                    candidates = self.search(d, limit=100, start=start)['data']
                    if not isinstance(candidates, list):
                        raise IntegrationError('Unexpected duplicate-search response; import stopped')
                    if any(doi(x.get('data', x).get('DOI')) == d for x in candidates):
                        raise IntegrationError('Existing DOI found; import stopped without writes')
                    if len(candidates) < 100:
                        break
                    start += 100
                    if start >= 1000:
                        raise IntegrationError('Duplicate search is too broad; review manually')
        headers = dict(self.headers)
        if self.mode == 'local':
            info = self.status()
            if not info['server_id']:
                raise IntegrationError('Local writes require Zotero 10+ capability; use manual import on older versions')
            headers['Zotero-Server-ID'] = info['server_id']
            grant, _ = request(self.base + '/local/authorize', 'POST', {'appName': 'OpenCode Research Tools'}, headers)
            if not isinstance(grant, dict) or not grant.get('key'):
                raise IntegrationError('Zotero did not authorize the import')
            headers['Zotero-API-Key'] = grant['key']
        headers['Zotero-Write-Token'] = uuid.uuid4().hex
        result, _ = request(f'{self.base}/{self.library}/items', 'POST', items, headers)
        return {'result': result, 'warning': 'Check failed/unchanged/successful entries; do not blindly retry a partial import'}


def better_bibtex(method, params=None):
    if method not in ('api.ready', 'item.citationkey', 'item.export'):
        raise IntegrationError('Only Better BibTeX readiness, citation-key lookup and selected export are exposed')
    result, _ = request('http://127.0.0.1:23119/better-bibtex/json-rpc', 'POST',
                        {'jsonrpc': '2.0', 'id': 1, 'method': method, 'params': params or []})
    if not isinstance(result, dict) or result.get('error'):
        raise IntegrationError('Better BibTeX returned an error; check installation and arguments')
    return result.get('result')
