import os
import secrets

from dotenv import load_dotenv
from flask import Flask, jsonify
from flask_cors import CORS
from werkzeug.exceptions import HTTPException
from werkzeug.middleware.proxy_fix import ProxyFix

from auth.system import init_auth, register_auth_routes, security_headers
from config import Settings
from routes.web import register_routes


load_dotenv(".env")


def create_app():
    app = Flask(__name__)
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)
    app.secret_key = Settings.SECRET_KEY or secrets.token_hex(32)
    app.config.update(
        MAX_CONTENT_LENGTH=Settings.MAX_CONTENT_LENGTH,
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
        SESSION_COOKIE_SECURE=Settings.IS_PRODUCTION,
        PERMANENT_SESSION_LIFETIME=60 * 60 * 24 * Settings.SESSION_DAYS,
        JSON_SORT_KEYS=False,
    )
    if Settings.CORS_ORIGINS:
        CORS(app, supports_credentials=True, origins=Settings.CORS_ORIGINS)

    init_auth(app)
    app.after_request(security_headers)
    register_auth_routes(app)
    register_routes(app)

    @app.errorhandler(HTTPException)
    def http_error(error):
        return jsonify({"error": error.description or error.name}), error.code

    @app.errorhandler(500)
    def internal_error(_error):
        return jsonify({"error": "internal server error"}), 500

    return app


app = create_app()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
