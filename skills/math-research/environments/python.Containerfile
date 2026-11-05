ARG BASE
FROM ${BASE}
COPY python.requirements.txt /opt/requirements.txt
RUN python -m pip install --no-cache-dir uv==0.7.13 && uv venv /opt/venv && uv pip install --python /opt/venv/bin/python -r /opt/requirements.txt && uv pip freeze --python /opt/venv/bin/python > /opt/packages.lock
ENV PATH=/opt/venv/bin:$PATH MPLBACKEND=Agg PYTHONDONTWRITEBYTECODE=1
WORKDIR /output
