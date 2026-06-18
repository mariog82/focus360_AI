"""Render/Gunicorn entrypoint for Focus360 AI Alpha Microservices.

Render's default start command often uses `gunicorn app:app`.
The real API Gateway lives in `gateway/app.py`, so this small adapter
exposes the same Flask object at the repository root.
"""
from gateway.app import app

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
