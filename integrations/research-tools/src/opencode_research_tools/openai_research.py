"""Optional Responses API web research. No bundled model or account access."""
import os
import re
from .http import IntegrationError, request


def start(question, approve_spend=False, max_output_tokens=4000):
    key = os.environ.get('OPENAI_API_KEY')
    model = os.environ.get('OPENAI_RESEARCH_MODEL')
    if approve_spend is not True:
        raise IntegrationError('Paid API execution requires explicit approve_spend=true after reviewing model and limits')
    if not key or not model:
        raise IntegrationError('Set OPENAI_API_KEY and OPENAI_RESEARCH_MODEL; no model is assumed')
    if not isinstance(question, str) or not question.strip() or not 1 <= max_output_tokens <= 16000:
        raise IntegrationError('Provide a question and max_output_tokens between 1 and 16000')
    result, _ = request('https://api.openai.com/v1/responses', 'POST',
        {'model': model, 'input': question, 'tools': [{'type': 'web_search'}],
         'background': True, 'max_output_tokens': max_output_tokens},
        {'Authorization': 'Bearer ' + key})
    return result


def retrieve(response_id):
    if not isinstance(response_id, str) or not re.fullmatch(r'resp_[A-Za-z0-9_-]+', response_id):
        raise IntegrationError('Expected a Responses API response ID')
    key = os.environ.get('OPENAI_API_KEY')
    if not key:
        raise IntegrationError('OPENAI_API_KEY is required')
    result, _ = request('https://api.openai.com/v1/responses/' + response_id,
                        headers={'Authorization': 'Bearer ' + key})
    return result
