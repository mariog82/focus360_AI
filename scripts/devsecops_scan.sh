#!/usr/bin/env bash
set -euo pipefail
python -m bandit -r gateway services shared -ll
python -m pip_audit || true
python -m compileall gateway services shared
