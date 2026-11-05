ARG BASE
FROM ${BASE}
RUN apt-get update && apt-get install -y --no-install-recommends python3 python3-pip python3-venv ca-certificates && rm -rf /var/lib/apt/lists/*
COPY python.requirements.txt /opt/requirements.txt
RUN python3 -m venv /opt/bootstrap && /opt/bootstrap/bin/pip install --no-cache-dir uv==0.7.13 && /opt/bootstrap/bin/uv python install 3.13.5 --install-dir /opt/python && UV_PYTHON_INSTALL_DIR=/opt/python /opt/bootstrap/bin/uv venv --python 3.13.5 /opt/venv && /opt/bootstrap/bin/uv pip install --python /opt/venv/bin/python -r /opt/requirements.txt 'cupy-cuda12x==13.4.1' && /opt/bootstrap/bin/uv pip freeze --python /opt/venv/bin/python > /opt/packages.lock
ENV PATH=/opt/venv/bin:$PATH MPLBACKEND=Agg PYTHONDONTWRITEBYTECODE=1
WORKDIR /output
