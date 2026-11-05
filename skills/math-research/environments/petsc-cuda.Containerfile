ARG BASE
FROM ${BASE}
RUN apt-get update && apt-get install -y --no-install-recommends python3 python3-dev python3-pip python3-venv build-essential gfortran git ca-certificates openmpi-bin libopenmpi-dev && rm -rf /var/lib/apt/lists/*
RUN python3 -m venv /opt/venv && /opt/venv/bin/pip install 'numpy==2.2.6' 'Cython==3.0.12' wheel && git clone --depth 1 --branch v3.23.2 https://gitlab.com/petsc/petsc.git /opt/petsc && cd /opt/petsc && PETSC_ARCH=arch-linux-cuda ./configure --with-debugging=0 --with-cuda=1 --with-cuda-arch=75 --with-shared-libraries=1 --with-fc=0 --with-python-exec=/opt/venv/bin/python --download-f2cblaslapack=1 && PETSC_ARCH=arch-linux-cuda make all && PETSC_DIR=/opt/petsc PETSC_ARCH=arch-linux-cuda /opt/venv/bin/pip install --no-build-isolation --no-deps ./src/binding/petsc4py && /opt/venv/bin/pip freeze > /opt/packages.lock && git rev-parse HEAD >> /opt/packages.lock
ENV PATH=/opt/venv/bin:$PATH PETSC_DIR=/opt/petsc PETSC_ARCH=arch-linux-cuda
WORKDIR /output
