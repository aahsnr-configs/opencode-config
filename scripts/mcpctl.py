#!/usr/bin/env python3
"""Manual MCP runtime switch for a *local* OpenCode V2 server.

Pure JSON needs no dependencies; JSONC comments/trailing commas require json5.
No remote URLs, silent approvals, model calls, or file writes.
Server runtime connect/disconnect routes are experimental and may change.
"""
import argparse
import base64
import json
import os
from pathlib import Path
import sys
import urllib.error
import urllib.parse
import urllib.request

ALLOWED = ("context7", "exa", "consensus", "alphaxiv", "undermind", "tamarind", "github", "ticktick", "playwright", "zotero", "scispace")

class ControlError(Exception):
    pass

def safe_origin(value):
    u = urllib.parse.urlsplit(value)
    if u.scheme != 'http' or (u.hostname or '').lower() not in ('127.0.0.1','localhost','::1'):
        raise ControlError('Only a loopback http:// server is permitted; refusing remote or redirected origins')
    if u.username or u.password or u.query or u.fragment or u.path not in ('', '/') or not u.port:
        raise ControlError('Use only a loopback origin including a port, e.g. http://127.0.0.1:4096')
    return f'http://{("["+u.hostname+"]") if ":" in u.hostname else u.hostname}:{u.port}'

def request(origin, method, path, password=None):
    # Disable redirects. A redirect could send Basic auth to an unexpected host.
    class NoRedirect(urllib.request.HTTPRedirectHandler):
        def redirect_request(self, req, fp, code, msg, headers, newurl):
            raise ControlError('Server redirected this request; refusing to forward credentials')
    headers={'Accept':'application/json'}
    if password:
        token=base64.b64encode(('opencode:'+password).encode()).decode()
        headers['Authorization']='Basic '+token
    req=urllib.request.Request(origin+path, method=method, headers=headers)
    try:
        with urllib.request.build_opener(NoRedirect).open(req, timeout=15) as r:
            data=r.read(2*1024*1024)
            if r.status not in (200,204):
                raise ControlError(f'Unexpected HTTP {r.status}')
            return json.loads(data) if data else None
    except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, ValueError) as exc:
        if isinstance(exc, urllib.error.HTTPError):
            detail=f'HTTP {exc.code}';
            if exc.code in (401, 403): detail+=': Check OPENCODE_PASSWORD and API access.'
            if exc.code in (404,405): detail+=': The experimental endpoint may not exist in this OpenCode build.'
            raise ControlError(detail) from exc
        raise ControlError(f'OpenCode API error: {exc}') from exc

def explicit_confirm(name):
    # Require a human attached to the terminal; a stdin pipe cannot approve.
    try:
        with open('/dev/tty', 'r+', encoding='utf-8') as tty:
            tty.write(f'Type the exact server name [{name}] to CONNECT: ')
            tty.flush()
            return tty.readline().strip()==name
    except OSError as exc:
        raise ControlError('Interactive human terminal required for connect/session') from exc

def list_config(path):
    # Configuration is JSONC-compatible; the bundled configuration is pure JSON.
    raw=Path(path).read_text(encoding='utf-8')
    try:
        config=json.loads(raw)
    except ValueError:
        try:
            import json5
        except ImportError as exc:
            raise ControlError('JSONC comments/trailing commas require the optional json5 package') from exc
        try:
            config=json5.loads(raw)
        except ValueError as exc:
            raise ControlError('Cannot parse installed MCP configuration as JSON or JSONC') from exc
    if not isinstance(config,dict) or not isinstance(config.get('mcp'),dict):
        raise ControlError('MCP configuration must contain an mcp object')
    servers=config['mcp'].get('servers')
    if not isinstance(servers,dict) or any(not isinstance(value,dict) for value in servers.values()):
        raise ControlError('MCP servers must be an object of server configurations')
    return servers

def statuses(payload):
    """Parse the documented V2 /api/mcp response; fail closed on unknown data.

    The API returns {location, data:[{name, status:{status: ...}}, ...]}.
    A pending or needs_auth server is NOT safe to treat as disconnected.
    """
    if not isinstance(payload, dict) or not isinstance(payload.get('data'), list):
        raise ControlError('Unexpected /api/mcp response: expected an object with data array')
    result=[]
    seen=set()
    allowed={'connected','pending','needs_auth','disabled','failed','disconnected'}
    for entry in payload['data']:
        if not isinstance(entry, dict) or not isinstance(entry.get('name'), str):
            raise ControlError('Malformed MCP server entry; refusing to infer connection state')
        name=entry['name']
        status=entry.get('status')
        if isinstance(status, dict):
            status=status.get('status')
        if not isinstance(status, str) or status.lower() not in allowed or name in seen:
            raise ControlError(f'Unexpected or duplicate MCP state for {name}; refusing activation')
        seen.add(name)
        result.append((name,status.lower()))
    return result

def do_disconnect(origin,password,name):
    request(origin,'POST','/api/experimental/mcp/'+urllib.parse.quote(name,safe='')+'/disconnect',password)
    print('Disconnected:',name)

def do_connect(origin,password,name):
    if not explicit_confirm(name):
        raise ControlError('Activation cancelled: explicit human confirmation was not given')
    request(origin,'POST','/api/experimental/mcp/'+urllib.parse.quote(name,safe='')+'/connect',password)
    print('Connected manually:',name,'(now approve each individual MCP tool call with Allow once)')

def main(argv=None):
    parser=argparse.ArgumentParser(description='Human-only, loopback OpenCode V2 MCP switch. No autonomous tool calls.')
    parser.add_argument('--url',default=os.environ.get('OPENCODE_MCP_CONTROL_URL','http://127.0.0.1:4096'))
    parser.add_argument('--config',default=str(Path(os.environ.get('XDG_CONFIG_HOME',str(Path.home()/'.config')))/'opencode'/'opencode.jsonc'))
    p=parser.add_subparsers(dest='action',required=True)
    for a in ('list','status'):
        p.add_parser(a)
    for a in ('connect','disconnect','session'):
        child=p.add_parser(a)
        child.add_argument('server',choices=ALLOWED)
    args=parser.parse_args(argv)
    if args.action=='list':
        data=list_config(args.config)
        for name in sorted(data):
            print(f'{name:14s} configured={"disabled" if data[name].get("disabled",False) else "ENABLED (unsafe baseline)"}')
        return 0
    origin=safe_origin(args.url)
    password=os.environ.get('OPENCODE_PASSWORD')
    if args.action=='status':
        for name,state in statuses(request(origin,'GET','/api/mcp',password)):
            print(f'{name:14s} {state}')
        return 0
    name=args.server
    try:
        data=list_config(args.config)
    except (KeyError,OSError,ValueError) as exc:
        raise ControlError('Cannot read installed MCP configuration; install kit first') from exc
    if name not in data or data[name].get('disabled') is not True:
        raise ControlError('Refusing to connect: named server must be present AND disabled in persistent config')
    if args.action=='disconnect':
        do_disconnect(origin,password,name)
        return 0
    # Prevent surprise concurrent MCP connection: fail closed if any other server looks active.
    active=[]
    for key,state in statuses(request(origin,'GET','/api/mcp',password)):
        if key!=name and state not in ('disabled','failed','disconnected'):
            active.append(key)
    if active:
        raise ControlError('Refusing to activate; disconnect existing MCP first: '+', '.join(active))
    do_connect(origin,password,name)
    if args.action=='session':
        print('Manual connection window open. Run your explicit user request in OpenCode/OpenChamber.')
        print('Press ENTER when done to disconnect; Ctrl+C also attempts disconnect.')
        try:
            with open('/dev/tty', 'r', encoding='utf-8') as tty:
                tty.readline()
        except (KeyboardInterrupt, EOFError, OSError):
            print('\nClosing connection window...')
        finally:
            do_disconnect(origin,password,name)
    return 0

if __name__=='__main__':
    try: sys.exit(main())
    except ControlError as exc:
        print('MCP CONTROL FAILED:',exc,file=sys.stderr); sys.exit(2)
