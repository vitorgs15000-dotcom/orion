import hmac
import os
import secrets

from authlib.integrations.flask_client import OAuth
from flask import jsonify, redirect, request, session, url_for


oauth = OAuth()


def init_auth(app):
    oauth.init_app(app)
    register_oauth_clients()


def register_oauth_clients():
    google_id = os.getenv("GOOGLE_CLIENT_ID")
    google_secret = os.getenv("GOOGLE_CLIENT_SECRET")
    if google_id and google_secret and "google" not in oauth._clients:
        oauth.register(
            name="google",
            client_id=google_id,
            client_secret=google_secret,
            server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
            client_kwargs={"scope": "openid email profile"},
        )

    microsoft_id = os.getenv("MICROSOFT_CLIENT_ID")
    microsoft_secret = os.getenv("MICROSOFT_CLIENT_SECRET")
    if microsoft_id and microsoft_secret and "microsoft" not in oauth._clients:
        oauth.register(
            name="microsoft",
            client_id=microsoft_id,
            client_secret=microsoft_secret,
            server_metadata_url="https://login.microsoftonline.com/common/v2.0/.well-known/openid-configuration",
            client_kwargs={"scope": "openid email profile"},
        )


def register_auth_routes(app):
    @app.before_request
    def prepare_session():
        session.permanent = True
        session.setdefault("csrf_token", secrets.token_urlsafe(32))

    @app.get("/login/<provider>")
    def login(provider):
        if provider not in {"google", "microsoft"} or provider not in oauth._clients:
            return redirect(url_for("index"))
        redirect_uri = url_for("auth_callback", provider=provider, _external=True)
        return oauth.create_client(provider).authorize_redirect(redirect_uri)

    @app.get("/auth/<provider>/callback")
    def auth_callback(provider):
        if provider not in {"google", "microsoft"} or provider not in oauth._clients:
            return redirect(url_for("index"))

        client = oauth.create_client(provider)
        token = client.authorize_access_token()
        userinfo = token.get("userinfo") or client.parse_id_token(token)
        session["user"] = {
            "provider": provider,
            "id": userinfo.get("sub") or userinfo.get("oid") or userinfo.get("email"),
            "name": userinfo.get("name") or userinfo.get("preferred_username") or "Operador Orion",
            "email": userinfo.get("email") or userinfo.get("preferred_username"),
        }
        session["csrf_token"] = secrets.token_urlsafe(32)
        return redirect(url_for("index"))

    @app.post("/logout")
    def logout():
        validate_csrf()
        session.clear()
        return jsonify({"ok": True})

    @app.get("/session")
    def current_session():
        return jsonify({"user": session.get("user"), "authenticated": bool(session.get("user"))})


def security_headers(response):
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
    if request.is_secure:
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return response


def validate_csrf():
    token = request.headers.get("X-CSRF-Token", "")
    expected = session.get("csrf_token", "")
    if not token or not expected or not hmac.compare_digest(token, expected):
        raise PermissionError("Invalid CSRF token")


def current_user_id(fallback_id=None):
    user = session.get("user")
    if user and user.get("id"):
        return f"{user['provider']}:{user['id']}"
    return str(fallback_id or "guest").strip() or "guest"


def auth_required():
    return os.getenv("AUTH_REQUIRED", "false").lower() == "true"


def oauth_status():
    return {
        "google": "google" in oauth._clients,
        "microsoft": "microsoft" in oauth._clients,
    }
