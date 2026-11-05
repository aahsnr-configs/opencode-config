ARG BASE
COPY jax-cuda.requirements.txt /opt/jax-cuda.requirements.txt
FROM ${BASE}
RUN /usr/local/bin/uv pip install --python /opt/venv/bin/python -r /opt/jax-cuda.requirements.txt && /usr/local/bin/uv pip freeze --python /opt/venv/bin/python > /opt/packages.lock
WORKDIR /output
