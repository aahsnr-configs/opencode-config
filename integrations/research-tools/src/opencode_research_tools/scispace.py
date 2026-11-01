"""Import provider-exported tables; no undocumented SciSpace API calls."""
import csv
import io
import json
from .http import IntegrationError


def import_table(text, format='csv'):
    if not isinstance(text, str) or len(text.encode()) > 5_000_000:
        raise IntegrationError('Export must be text smaller than 5 MB')
    if format == 'csv':
        rows = list(csv.DictReader(io.StringIO(text)))
    elif format == 'json':
        rows = json.loads(text)
    else:
        raise IntegrationError('Choose csv or json')
    if not isinstance(rows, list) or len(rows) > 1000 or not all(isinstance(row, dict) for row in rows):
        raise IntegrationError('Export must contain at most 1000 row objects')
    # Keep arbitrary analytical columns and explicit evidence provenance.
    return {'provider': 'scispace', 'origin': 'user-supplied-export', 'rows': rows,
            'verification': 'imported, not independently verified',
            'warning': 'Check row IDs, DOI metadata and abstract/full-text grounding before adding research evidence.'}
