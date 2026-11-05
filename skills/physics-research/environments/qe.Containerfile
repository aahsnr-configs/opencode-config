# Reference recipe; setup writes the resolved digest and build context.
ARG BASE
FROM ${BASE}
USER root
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y --no-install-recommends ca-certificates python3 python3-pip python3-venv python-is-python3 quantum-espresso make libgsl-dev liblapack-dev libblas-dev && rm -rf /var/lib/apt/lists/*
RUN python -c "import sys; assert sys.version_info[:2] == (3, 13)" && python -m venv /opt/physics
ENV PATH=/opt/physics/bin:$PATH
COPY requirements.txt /tmp/requirements.txt
COPY Si.pbe-rrkj.UPF /opt/Si.pbe-rrkj.UPF
COPY checks.py /opt/checks.py
ENTRYPOINT []
CMD ["python", "/opt/checks.py", "qe", "--smoke"]
