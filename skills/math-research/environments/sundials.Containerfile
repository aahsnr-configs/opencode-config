ARG BASE
FROM ${BASE}
RUN uv pip install --python /opt/venv/bin/python 'sundials4py==7.9.0' && uv pip freeze --python /opt/venv/bin/python > /opt/packages.lock
WORKDIR /output
