ARG BASE
FROM ${BASE}
RUN apt-get update && apt-get install -y --no-install-recommends ca-certificates curl git zstd python3 && rm -rf /var/lib/apt/lists/*
ENV ELAN_HOME=/opt/elan PATH=/opt/elan/bin:$PATH
RUN curl --fail --location --retry 2 https://github.com/leanprover/elan/releases/download/v4.1.2/elan-x86_64-unknown-linux-gnu.tar.gz -o /tmp/elan.tar.gz && tar -xzf /tmp/elan.tar.gz -C /tmp && /tmp/elan-init -y --no-modify-path --default-toolchain leanprover/lean4:v4.19.0 && git clone --depth 1 --branch v4.19.0 https://github.com/leanprover-community/mathlib4.git /opt/mathlib && cd /opt/mathlib && lake exe cache get && printf 'Lean v4.19.0\nmathlib ' > /opt/packages.lock && git rev-parse HEAD >> /opt/packages.lock && cat lake-manifest.json >> /opt/packages.lock
RUN for repo in /opt/mathlib /opt/mathlib/.lake/packages/*; do git config --system --add safe.directory "$repo"; done
WORKDIR /output
