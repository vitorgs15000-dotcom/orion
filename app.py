import os
import secrets

from dotenv import load_dotenv
from flask import Flask, jsonify
from flask_cors import CORS
from werkzeug.middleware.proxy_fix import ProxyFix

from auth import init_auth, register_auth_routes, security_headers
from routes import register_routes


load_dotenv(".env")


def create_app():
    app = Flask(__name__)
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)
    app.secret_key = os.getenv("SECRET_KEY") or secrets.token_hex(32)
    app.config.update(
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
        SESSION_COOKIE_SECURE=os.getenv("FLASK_ENV") == "production",
        PERMANENT_SESSION_LIFETIME=60 * 60 * 24 * 14,
    )
    CORS(app, supports_credentials=True)

    init_auth(app)
    app.after_request(security_headers)
    register_auth_routes(app)
    register_routes(app)

    @app.errorhandler(404)
    def not_found(_error):
        return jsonify({"error": "route not found"}), 404

    @app.errorhandler(500)
    def internal_error(_error):
        return jsonify({"error": "internal server error"}), 500

    return app


app = create_app()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
