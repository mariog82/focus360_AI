#!/usr/bin/env bash
set -euo pipefail
python -m pytest tests/integration tests/system tests/acceptance tests/security -q
