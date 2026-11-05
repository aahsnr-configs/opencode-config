ARG BASE
FROM ${BASE}
USER root
RUN sage -c 'import sys; print(sys.version)' > /opt/packages.lock && sage --version >> /opt/packages.lock
WORKDIR /output
