import os, time
from flask import Flask, jsonify
from .models import db


def create_service_app(name: str):
    app = Flask(name)
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', f"sqlite:////data/{name.replace('-', '_')}.db")
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-change-me')
    db.init_app(app)

    # In ambiente Docker locale molti servizi partono insieme: con SQLite condiviso si possono
    # generare lock all'avvio. Ogni servizio usa un DB separato e l'inizializzazione è tollerante.
    if os.getenv('SKIP_DB_INIT', '0') != '1':
        with app.app_context():
            last_error = None
            for _ in range(10):
                try:
                    db.create_all()
                    last_error = None
                    break
                except Exception as exc:
                    last_error = exc
                    time.sleep(0.5)
            if last_error:
                app.logger.warning('DB init skipped after retries: %s', last_error)

    @app.get('/health')
    def health():
        return jsonify({'service': name, 'status': 'ok'})

    @app.get('/')
    def index():
        return jsonify({'service': name, 'status': 'running', 'health': '/health'})

    return app
