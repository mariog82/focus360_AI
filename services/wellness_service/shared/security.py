
import os, hmac, hashlib, secrets, time
from functools import wraps
from flask import request, jsonify

DEFAULT_API_KEY = os.getenv('INTERNAL_API_KEY', 'dev-internal-key-change-me')

def hash_password(password: str) -> str:
    import werkzeug.security
    return werkzeug.security.generate_password_hash(password)

def verify_password(password_hash: str, password: str) -> bool:
    import werkzeug.security
    return werkzeug.security.check_password_hash(password_hash, password)

def require_internal_api_key(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        supplied = request.headers.get('X-Internal-API-Key','')
        if not hmac.compare_digest(supplied, DEFAULT_API_KEY):
            return jsonify({'error':'unauthorized internal service call'}), 401
        return fn(*args, **kwargs)
    return wrapper

def generate_token(prefix='F360'):
    return f"{prefix}-{secrets.token_hex(8).upper()}"

def sha256_record(payload: str) -> str:
    return hashlib.sha256(payload.encode('utf-8')).hexdigest()
