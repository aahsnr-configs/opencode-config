# Reference recipe; setup writes the resolved digest and build context.
ARG BASE
ARG CUDA_BASE
FROM ${CUDA_BASE} AS cuda
FROM ${BASE}
USER root
COPY --from=cuda /usr/local/cuda-12.8 /usr/local/cuda-12.8
ENV CUDA_HOME=/usr/local/cuda-12.8
ENV PATH=/usr/local/cuda-12.8/bin:$PATH
ENV LD_LIBRARY_PATH=/usr/local/cuda-12.8/lib64:$LD_LIBRARY_PATH
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y --no-install-recommends ca-certificates python3 python3-pip python3-venv python-is-python3 cmake g++ libfftw3-dev pkg-config make libgsl-dev liblapack-dev libblas-dev && rm -rf /var/lib/apt/lists/*
RUN python -c "import sys; assert sys.version_info[:2] == (3, 13)" && python -m venv /opt/physics
ENV PATH=/opt/physics/bin:$PATH
COPY requirements.txt /tmp/requirements.txt
RUN python -m pip install --no-cache-dir -r /tmp/requirements.txt
ENV PLUMED_KERNEL=/usr/local/lib/libplumedKernel.so
COPY source_build.sh /tmp/source_build.sh
COPY . /tmp/physics-source
RUN sh /tmp/source_build.sh gromacs-cuda
COPY checks.py /opt/checks.py
ENTRYPOINT []
CMD ["python", "/opt/checks.py", "gromacs-cuda", "--smoke"]
