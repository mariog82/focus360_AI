#!/usr/bin/env bash
set -e
for url in \
  http://localhost:8080/health \
  http://localhost:8080/health/services \
  http://localhost:8001/health \
  http://localhost:8002/health \
  http://localhost:8003/health \
  http://localhost:8004/health \
  http://localhost:8005/health \
  http://localhost:8006/health \
  http://localhost:8007/health \
  http://localhost:8008/health \
  http://localhost:8009/health; do
  echo "\n== $url =="
  curl -sS "$url" || true
  echo
done
