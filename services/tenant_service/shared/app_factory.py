
import os
from flask import Flask, jsonify
from .models import db

def create_service_app(name: str):
    app = Flask(name)
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:////tmp/focus360_micro.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-change-me')
    db.init_app(app)
    with app.app_context():
        db.create_all()
    @app.get('/health')
    def health():
        return jsonify({'service': name, 'status': 'ok'})
    return app
