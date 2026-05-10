import hmac
import os
import re
import secrets
import time
import unicodedata
from functools import wraps
from html import escape

from authlib.integrations.flask_client import OAuth
from dotenv import load_dotenv
from flask import Flask, jsonify, redirect, render_template, request, session, url_for
from flask_cors import CORS
from werkzeug.middleware.proxy_fix import ProxyFix

from ai_service import ask_ai
from knowledge import search_knowledge_base, search_wikipedia
from memory import (
    add_message,
    clear_history,
    forget_fact,
    get_history,
    get_profile,
    get_recent_messages,
    remember_fact,
    remember_user_name,
)

load_dotenv(".env")

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

oauth = OAuth(app)
MAX_MESSAGE_LENGTH = 1000
RATE_LIMIT_WINDOW = 60
RATE_LIMIT_MAX_REQUESTS = 30
RATE_BUCKETS = {}


def register_oauth_clients():
    google_id = os.getenv("GOOGLE_CLIENT_ID")
    google_secret = os.getenv("GOOGLE_CLIENT_SECRET")
    if google_id and google_secret:
        oauth.register(
            name="google",
            client_id=google_id,
            client_secret=google_secret,
            server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
            client_kwargs={"scope": "openid email profile"},
        )

    microsoft_id = os.getenv("MICROSOFT_CLIENT_ID")
    microsoft_secret = os.getenv("MICROSOFT_CLIENT_SECRET")
    if microsoft_id and microsoft_secret:
        oauth.register(
            name="microsoft",
            client_id=microsoft_id,
            client_secret=microsoft_secret,
            server_metadata_url="https://login.microsoftonline.com/common/v2.0/.well-known/openid-configuration",
            client_kwargs={"scope": "openid email profile"},
        )


register_oauth_clients()


@app.before_request
def prepare_session():
    session.permanent = True
    session.setdefault("csrf_token", secrets.token_urlsafe(32))


@app.after_request
def security_headers(response):
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
    if request.is_secure:
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return response


@app.get("/")
def index():
    user = session.get("user")
    return render_template(
        "index.html",
        user=user,
        csrf_token=session["csrf_token"],
        auth={
            "google": "google" in oauth._clients,
            "microsoft": "microsoft" in oauth._clients,
        },
    )


@app.get("/health")
def health():
    return jsonify({"status": "ok", "name": "Orion"})


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


def rate_limited(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        key = session.get("user", {}).get("id") or request.remote_addr or "anonymous"
        now = time.time()
        bucket = [t for t in RATE_BUCKETS.get(key, []) if now - t < RATE_LIMIT_WINDOW]
        if len(bucket) >= RATE_LIMIT_MAX_REQUESTS:
            return jsonify({"error": "rate limit exceeded"}), 429
        bucket.append(now)
        RATE_BUCKETS[key] = bucket
        return view(*args, **kwargs)

    return wrapped


@app.get("/memory")
def memory_view():
    user_id = current_user_id(request.args.get("user_id"))
    return jsonify({"profile": get_profile(user_id), "history": get_history(user_id)})


@app.post("/memory")
@rate_limited
def memory_save():
    try:
        validate_csrf()
        data = request.get_json(silent=True) or {}
        key = sanitize_key(data.get("key", ""))
        value = sanitize_message(data.get("value", ""))
        if not key or not value:
            return jsonify({"error": "key and value are required"}), 400
        user_id = current_user_id(data.get("user_id"))
        return jsonify({"profile": remember_fact(user_id, key, value)})
    except PermissionError:
        return jsonify({"error": "csrf token invalid"}), 403


@app.delete("/memory/<key>")
def memory_delete(key):
    try:
        validate_csrf()
        user_id = current_user_id(request.args.get("user_id"))
        return jsonify({"profile": forget_fact(user_id, sanitize_key(key))})
    except PermissionError:
        return jsonify({"error": "csrf token invalid"}), 403


@app.post("/history/clear")
def history_clear():
    try:
        validate_csrf()
        data = request.get_json(silent=True) or {}
        user_id = current_user_id(data.get("user_id"))
        clear_history(user_id)
        return jsonify({"ok": True})
    except PermissionError:
        return jsonify({"error": "csrf token invalid"}), 403


@app.post("/chat")
@rate_limited
def chat():
    try:
        if auth_required() and not session.get("user"):
            return jsonify({"error": "authentication required"}), 401

        validate_csrf()
        data = request.get_json(silent=True) or {}
        message = data.get("message", "")
        user_id = current_user_id(data.get("user_id"))

        error = validate_message(message)
        if error:
            return jsonify({"error": error}), 400

        message = sanitize_message(message)
        remembered = remember_name_if_requested(user_id, message)
        context = get_recent_messages(user_id, limit=8)
        add_message(user_id, "user", message)

        for responder in (ask_ai_response, knowledge_response, wikipedia_response):
            result = responder(message, context)
            if result:
                reply, source = result
                return save_and_reply(user_id, reply, source, remembered)

        fallback = (
            "Ainda nao encontrei uma resposta confiavel. Posso tentar de novo com mais "
            "contexto, consultar minha base local ou guardar uma informacao para voce."
        )
        return save_and_reply(user_id, fallback, "fallback", remembered)
    except PermissionError:
        return jsonify({"error": "csrf token invalid"}), 403
    except Exception:
        return jsonify({"error": "Orion encontrou um erro interno."}), 500


def ask_ai_response(message, context):
    reply = ask_ai(message, context=context)
    return (reply, "ai") if reply else None


def knowledge_response(message, _context):
    reply = search_knowledge_base(message)
    return (reply, "knowledge_base") if reply else None


def wikipedia_response(message, _context):
    result = search_wikipedia(message)
    if not result:
        return None
    return result["answer"], result["source"]


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("user"):
            return jsonify({"error": "authentication required"}), 401
        return view(*args, **kwargs)

    return wrapped


def auth_required():
    return os.getenv("AUTH_REQUIRED", "false").lower() == "true"


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


def validate_message(message):
    if not isinstance(message, str):
        return "message must be text"
    if not message.strip():
        return "message is required"
    if len(message.strip()) > MAX_MESSAGE_LENGTH:
        return "message is too long"
    return None


def sanitize_key(key):
    key = normalize_text(str(key or "")).lower()
    key = re.sub(r"[^a-z0-9_-]+", "_", key).strip("_")
    return key[:48]


def sanitize_message(message):
    return escape(message.strip(), quote=False)


def remember_name_if_requested(user_id, message):
    normalized = normalize_text(message)
    patterns = [
        r"^(meu nome e|lembrar nome:|lembre meu nome:)\s*(.+)$",
        r"^(pode me chamar de)\s*(.+)$",
    ]

    for pattern in patterns:
        match = re.match(pattern, normalized, flags=re.IGNORECASE)
        if match:
            name = message.strip()[-len(match.group(2).strip()):].strip()
            if name:
                remember_user_name(user_id, name)
                return {"name": name}
    return None


def normalize_text(text):
    without_accents = unicodedata.normalize("NFKD", text)
    without_accents = "".join(
        char for char in without_accents if not unicodedata.combining(char)
    )
    return without_accents.strip()


def save_and_reply(user_id, reply, source, remembered=None):
    add_message(user_id, "assistant", reply)
    payload = {"reply": reply, "source": source}
    if remembered:
        payload["remembered"] = remembered
    return jsonify(payload)


@app.errorhandler(404)
def not_found(_error):
    return jsonify({"error": "route not found"}), 404


@app.errorhandler(500)
def internal_error(_error):
    return jsonify({"error": "internal server error"}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
