import hmac
import os
import secrets

from authlib.integrations.flask_client import OAuth
from flask import jsonify, redirect, render_template, request, session, url_for

try:
    from flask_limiter import Limiter
    from flask_limiter.util import get_remote_address
except ImportError:  # Local fallback when optional security packages are not installed yet.
    Limiter = None
    get_remote_address = None

try:
    from flask_talisman import Talisman
except ImportError:
    Talisman = None

try:
    from flask_wtf.csrf import CSRFProtect
except ImportError:
    CSRFProtect = None

from config import Settings


oauth = OAuth()
limiter = None
csrf = None


def init_auth(app):
    global limiter, csrf

    oauth.init_app(app)
    register_oauth_clients()

    if Talisman:
        Talisman(
            app,
            content_security_policy={
                "default-src": "'self'",
                "script-src": "'self'",
                "style-src": "'self' 'unsafe-inline'",
                "img-src": "'self' data:",
                "font-src": "'self' data:",
                "connect-src": "'self'",
                "base-uri": "'self'",
                "form-action": "'self'",
                "frame-ancestors": "'none'",
            },
            force_https=Settings.FLASK_ENV == "production",
            session_cookie_secure=Settings.IS_PRODUCTION,
        )

    if CSRFProtect:
        app.config.setdefault("WTF_CSRF_CHECK_DEFAULT", False)
        csrf = CSRFProtect(app)

    if Limiter and get_remote_address:
        limiter = Limiter(
            key_func=get_remote_address,
            app=app,
            default_limits=[],
            storage_uri=os.getenv("RATELIMIT_STORAGE_URI", "memory://"),
        )


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

    @app.before_request
    def protect_private_orion():
        if not auth_required():
            return None
        if is_authenticated():
            return None
        if request.endpoint in {
            "static",
            "health",
            "private_login",
            "private_login_post",
            "login",
            "auth_callback",
            "current_session",
        }:
            return None
        if request.path.startswith("/static/"):
            return None
        if request.method == "GET":
            return redirect(url_for("private_login"))
        return jsonify({"error": "authentication required"}), 401

    @app.get("/private-login")
    def private_login():
        return render_template(
            "login.html",
            csrf_token=session["csrf_token"],
            error=request.args.get("error"),
        )

    @app.post("/private-login")
    def private_login_post():
        try:
            validate_csrf_form()
        except PermissionError:
            return redirect(url_for("private_login", error="Sessão expirada. Tente novamente."))

        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        if not private_credentials_ready():
            return redirect(url_for("private_login", error="Login privado ainda não foi configurado no servidor."))

        valid_user = hmac.compare_digest(username, Settings.ORION_USERNAME)
        valid_password = hmac.compare_digest(password, Settings.ORION_PASSWORD)
        if not (valid_user and valid_password):
            return redirect(url_for("private_login", error="Usuário ou senha incorretos."))

        session["private_user"] = {
            "provider": "private",
            "id": username,
            "name": username,
            "email": username,
        }
        session["csrf_token"] = secrets.token_urlsafe(32)
        return redirect(url_for("index"))

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
        user = current_session_user()
        return jsonify({"user": user, "authenticated": bool(user)})


def security_headers(response):
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
    response.headers["Cross-Origin-Opener-Policy"] = "same-origin"
    response.headers["Cross-Origin-Resource-Policy"] = "same-origin"
    response.headers["X-XSS-Protection"] = "0"
    if request.path.startswith(("/private-login", "/login", "/auth", "/session")):
        response.headers["Cache-Control"] = "no-store"
    if request.is_secure:
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return response


def validate_csrf():
    token = request.headers.get("X-CSRF-Token", "")
    expected = session.get("csrf_token", "")
    if not token or not expected or not hmac.compare_digest(token, expected):
        raise PermissionError("Invalid CSRF token")


def validate_csrf_form():
    token = request.form.get("csrf_token", "")
    expected = session.get("csrf_token", "")
    if not token or not expected or not hmac.compare_digest(token, expected):
        raise PermissionError("Invalid CSRF token")


def private_credentials_ready():
    return bool(Settings.ORION_USERNAME and Settings.ORION_PASSWORD)


def current_session_user():
    return session.get("user") or session.get("private_user")


def is_authenticated():
    return bool(current_session_user())


def current_user_id(fallback_id=None):
    user = current_session_user()
    if user and user.get("id"):
        return f"{user['provider']}:{user['id']}"
    return str(fallback_id or "guest").strip() or "guest"


def auth_required():
    return Settings.AUTH_REQUIRED


def oauth_status():
    return {
        "google": "google" in oauth._clients,
        "microsoft": "microsoft" in oauth._clients,
    }
