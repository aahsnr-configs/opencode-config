#!/bin/sh
set -eu
python -m pip install --no-cache-dir -r /tmp/requirements.txt
python -m pip freeze > /opt/packages.lock
