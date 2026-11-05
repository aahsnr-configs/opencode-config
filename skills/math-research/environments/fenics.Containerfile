ARG BASE
FROM ${BASE}
USER root
RUN python3 -c 'import dolfinx, petsc4py, slepc4py, gmsh, mpi4py; print(dolfinx.__version__); print(petsc4py.__version__); print(slepc4py.__version__); print(gmsh.__version__)' > /opt/packages.lock
ENV MPLBACKEND=Agg PYTHONDONTWRITEBYTECODE=1
WORKDIR /output
