"""Transactional, revision-checked local research and learning records."""
import csv
import contextlib
import datetime
import io
import json
import os
from pathlib import Path
import sqlite3
import urllib.parse
import uuid
from .http import IntegrationError
from .zotero import doi

TRANSITIONS = {
    'planned': {'running', 'cancelled'},
    'running': {'paused', 'awaiting_approval', 'completed', 'failed', 'cancelled'},
    'paused': {'running', 'cancelled'},
    'awaiting_approval': {'running', 'cancelled'},
    'failed': {'running', 'cancelled'},
    'completed': set(), 'cancelled': set(),
}


def now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def canonical_url(value):
    if not isinstance(value, str):
        raise IntegrationError('Source URL must be text')
    parsed = urllib.parse.urlsplit(value)
    if parsed.scheme not in ('https', 'http') or not parsed.hostname or parsed.username or parsed.password:
        raise IntegrationError('Source URL must be an HTTP(S) URL without credentials')
    return urllib.parse.urlunsplit((parsed.scheme.lower(), parsed.netloc.lower(), parsed.path, parsed.query, ''))


def _check_directory_path(path):
    """Reject linked/non-directory ancestors; intentional links need canonical paths.

    This preflight check does not prevent concurrent path replacement.
    """
    path = path.absolute()
    for ancestor in reversed((path, *path.parents)):
        if ancestor.is_symlink() or (ancestor.exists() and not ancestor.is_dir()):
            raise IntegrationError('State directory path must not contain a symlink or non-directory parent')


class Store:
    def __init__(self, root=None):
        root = Path(root or os.environ.get('OPENCODE_RESEARCH_STATE_DIR',
            str(Path(os.environ.get('XDG_STATE_HOME', str(Path.home() / '.local/state'))) / 'opencode-research')))
        _check_directory_path(root)
        root.mkdir(parents=True, exist_ok=True, mode=0o700)
        self.path = root / 'runs.sqlite3'
        if self.path.is_symlink():
            raise IntegrationError('State database must not be a symlink')
        with self.connect() as con:
            con.execute('CREATE TABLE IF NOT EXISTS runs (id TEXT PRIMARY KEY, kind TEXT NOT NULL, revision INTEGER NOT NULL, data TEXT NOT NULL)')
        os.chmod(self.path, 0o600)

    @contextlib.contextmanager
    def connect(self):
        _check_directory_path(self.path.parent)
        if self.path.is_symlink():
            raise IntegrationError('State database must not be a symlink')
        con = sqlite3.connect(self.path, timeout=10)
        try:
            with con:
                yield con
        finally:
            con.close()

    def create(self, kind, question, scope=None):
        if kind not in ('research', 'learning') or not isinstance(question, str) or not question.strip():
            raise IntegrationError('Choose research/learning and a nonempty question')
        if scope is not None and not isinstance(scope, dict):
            raise IntegrationError('Scope must be an object')
        record = {'id': uuid.uuid4().hex, 'kind': kind, 'question': question, 'scope': scope or {},
                  'state': 'planned', 'revision': 0, 'created_utc': now(), 'evidence': [],
                  'screening': [], 'queries': [], 'jobs': {}, 'attempts': [], 'report': None, 'history': []}
        with self.connect() as con:
            con.execute('INSERT INTO runs VALUES (?,?,?,?)', (record['id'], kind, 0, json.dumps(record)))
        return record

    def get(self, run_id):
        with self.connect() as con:
            row = con.execute('SELECT data FROM runs WHERE id=?', (run_id,)).fetchone()
        if row is None:
            raise IntegrationError('Unknown run ID')
        return json.loads(row[0])

    def list(self, kind=None):
        if kind not in (None, 'research', 'learning'):
            raise IntegrationError('Unknown run kind')
        with self.connect() as con:
            rows = con.execute('SELECT data FROM runs' + (' WHERE kind=?' if kind else ''), (kind,) if kind else ()).fetchall()
        return [{k: r[k] for k in ('id', 'kind', 'question', 'state', 'revision', 'created_utc')}
                for r in (json.loads(x[0]) for x in rows)]

    def update(self, run_id, expected_revision, action, payload):
        if not isinstance(payload, dict):
            raise IntegrationError('Payload must be an object')
        with self.connect() as con:
            con.execute('BEGIN IMMEDIATE')
            row = con.execute('SELECT data FROM runs WHERE id=?', (run_id,)).fetchone()
            if not row:
                raise IntegrationError('Unknown run ID')
            r = json.loads(row[0])
            if r['revision'] != expected_revision:
                raise IntegrationError('Revision conflict; reload the run before updating')
            if action == 'transition':
                target = payload.get('state')
                if target not in TRANSITIONS[r['state']]:
                    raise IntegrationError('Invalid state transition')
                if target == 'completed' and r['kind'] == 'research' and (not r['evidence'] or not r['report']):
                    raise IntegrationError('Research completion requires evidence and a report')
                r['state'] = target
            else:
                if r['state'] in ('completed', 'cancelled'):
                    raise IntegrationError('Terminal runs are immutable; create a follow-up run')
                self.apply(r, action, payload)
            r['revision'] += 1
            r['history'].append({'revision': r['revision'], 'action': action, 'at_utc': now()})
            con.execute('UPDATE runs SET revision=?,data=? WHERE id=?', (r['revision'], json.dumps(r), run_id))
        return r

    def apply(self, r, action, payload):
        if action == 'evidence':
            if r['kind'] != 'research':
                raise IntegrationError('Use a research run for source evidence')
            p = dict(payload)
            if not p.get('title') or not p.get('provider'):
                raise IntegrationError('Evidence needs title, provider and URL')
            p['url'] = canonical_url(p.get('url'))
            p['doi'] = doi(p.get('doi'))
            p.setdefault('access', 'metadata')
            if p['access'] not in ('metadata', 'abstract', 'fulltext'):
                raise IntegrationError('Access must be metadata, abstract or fulltext')
            p['retrieved_utc'] = p.get('retrieved_utc') or now()
            for old in r['evidence']:
                if (p['doi'] and old.get('doi') == p['doi']) or old['url'] == p['url']:
                    raise IntegrationError('Duplicate evidence; refer to the existing evidence ID')
            p['id'] = uuid.uuid4().hex
            r['evidence'].append(p)
        elif action == 'query':
            if not payload.get('provider') or not payload.get('query'):
                raise IntegrationError('Query needs provider and query')
            r['queries'].append({**payload, 'at_utc': now()})
        elif action == 'screen':
            if payload.get('decision') not in ('include', 'exclude', 'uncertain') or not payload.get('reason'):
                raise IntegrationError('Screening needs decision and reason')
            ids = {e['id'] for e in r['evidence']}
            if payload.get('evidence_id') not in ids:
                raise IntegrationError('Screening evidence ID not found')
            r['screening'].append({**payload, 'at_utc': now()})
        elif action == 'job':
            if not payload.get('provider') or not payload.get('job_id') or not payload.get('status'):
                raise IntegrationError('Job needs provider, job_id and status')
            key = str(payload['provider']) + ':' + str(payload['job_id'])
            r['jobs'][key] = {**payload, 'at_utc': now()}
        elif action == 'report':
            if not isinstance(payload.get('text'), str) or not payload['text'].strip():
                raise IntegrationError('Report text is required')
            known = {e['id'] for e in r['evidence']}
            if not isinstance(payload.get('evidence_ids'), list) or not payload['evidence_ids']:
                raise IntegrationError('Report must reference evidence IDs')
            if not set(payload['evidence_ids']) <= known:
                raise IntegrationError('Report contains unknown evidence IDs')
            r['report'] = {**payload, 'validation': 'reference-integrity-only; claims require human review'}
        elif action == 'attempt':
            if r['kind'] != 'learning' or not payload.get('question') or not isinstance(payload.get('response'), str):
                raise IntegrationError('Learning attempt needs question and response')
            p = {**payload, 'at_utc': now()}
            p.pop('correct', None)
            if 'correct_answer' in p:
                p['correct'] = str(p['response']).strip().casefold() == str(p['correct_answer']).strip().casefold()
                p['grading'] = 'exact-normalized-text'
            else:
                p['grading'] = 'qualitative-unverified'
            r['attempts'].append(p)
        else:
            raise IntegrationError('Unsupported update action')

    def export(self, run_id):
        r = self.get(run_id)
        if r['kind'] == 'learning':
            text = '# Learning record\n\n' + r['question'] + '\n\n'
            for a in r['attempts']:
                text += f"- {a['question']}: {a['response']} ({a['grading']})\n"
        else:
            text = '# Research report\n\n' + (r['report']['text'] if r['report'] else 'No report saved.') + '\n\n## Sources\n'
            for e in r['evidence']:
                text += f"\n- [{e['title']}]({e['url']}) — {e['access']}; {e['id']}\n"
        buf = io.StringIO()
        writer = csv.DictWriter(buf, fieldnames=['id', 'title', 'doi', 'url', 'provider', 'access', 'retrieved_utc'], extrasaction='ignore')
        writer.writeheader()
        writer.writerows(r['evidence'])
        # JSON and CSV preserve source fields without inventing bibliographic metadata.
        return {'record': r, 'markdown': text, 'evidence_csv': buf.getvalue()}
