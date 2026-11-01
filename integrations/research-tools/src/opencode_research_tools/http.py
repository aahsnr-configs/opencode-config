"""Bounded HTTP requests with no redirects or automatic retries."""
import json
import urllib.error
import urllib.request

class IntegrationError(Exception):
    pass

class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise IntegrationError('Redirect refused; credentials were not forwarded')


def request(url, method='GET', body=None, headers=None):
    merged = {'Accept': 'application/json', 'User-Agent': 'opencode-research-tools/0.1'}
    merged.update(headers or {})
    data = None
    if body is not None:
        data = json.dumps(body).encode()
        merged['Content-Type'] = 'application/json'
    req = urllib.request.Request(url, data=data, method=method, headers=merged)
    try:
        with urllib.request.build_opener(NoRedirect).open(req, timeout=30) as response:
            raw = response.read(5_000_001)
            if len(raw) > 5_000_000:
                raise IntegrationError('Response exceeds 5 MB; use a smaller selection')
            text = raw.decode('utf-8')
            content = json.loads(text) if 'json' in response.headers.get('Content-Type', '') and text else text
            return content, dict(response.headers)
    except urllib.error.HTTPError as exc:
        # Do not expose response bodies, credentials or request parameters.
        retry = exc.headers.get('Retry-After') if exc.headers else None
        raise IntegrationError(f'HTTP {exc.code}' + (f'; Retry-After: {retry}' if retry else '')) from None
    except (urllib.error.URLError, TimeoutError, UnicodeError, ValueError):
        raise IntegrationError('Network, decoding or response-format error; no automatic retry was made') from None
