import re
import time
import unicodedata
from functools import wraps
from html import escape

from flask import jsonify, render_template, request, session

from auth import auth_required, current_user_id, oauth_status, validate_csrf
from context_manager import generate_reply
from memory import clear_history, forget_fact, get_history, get_profile, remember_fact, remember_user_name


MAX_MESSAGE_LENGTH = 1000
RATE_LIMIT_WINDOW = 60
RATE_LIMIT_MAX_REQUESTS = 30
RATE_BUCKETS = {}


def register_routes(app):
    @app.get("/")
    def index():
        return render_template(
            "index.html",
            user=session.get("user"),
            csrf_token=session["csrf_token"],
            auth=oauth_status(),
        )

    @app.get("/health")
    def health():
        return jsonify({"status": "ok", "name": "Orion", "version": "V1.1 Foundation"})

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
            payload = generate_reply(user_id, message)
            if remembered:
                payload["remembered"] = remembered
            return jsonify(payload)
        except PermissionError:
            return jsonify({"error": "csrf token invalid"}), 403
        except Exception:
            return jsonify({"error": "Orion encontrou um erro interno."}), 500


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
