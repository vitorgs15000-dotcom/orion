import time
from functools import wraps

from flask import jsonify, render_template, request, session

from auth.system import auth_required, current_session_user, current_user_id, is_authenticated, oauth_status, validate_csrf
from config import Settings
from context.manager import generate_reply
from memory.store import clear_history, forget_fact, get_history, get_profile, remember_fact, remember_user_name
from utils.text import sanitize_key, sanitize_message, normalize_text


RATE_LIMIT_WINDOW = 60
RATE_BUCKETS = {}


def register_routes(app):
    @app.get("/")
    def index():
        return render_template(
            "index.html",
            user=current_session_user(),
            csrf_token=session["csrf_token"],
            auth=oauth_status(),
        )

    @app.get("/health")
    def health():
        return jsonify({"status": "ok", "name": Settings.APP_NAME, "version": Settings.VERSION})

    @app.get("/memory")
    @rate_limited
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
                return jsonify({"error": "Chave e valor são obrigatórios."}), 400
            user_id = current_user_id(data.get("user_id"))
            return jsonify({"profile": remember_fact(user_id, key, value)})
        except PermissionError:
            return jsonify({"error": "Token de segurança inválido. Recarregue a página."}), 403

    @app.delete("/memory/<key>")
    @rate_limited
    def memory_delete(key):
        try:
            validate_csrf()
            user_id = current_user_id(request.args.get("user_id"))
            return jsonify({"profile": forget_fact(user_id, sanitize_key(key))})
        except PermissionError:
            return jsonify({"error": "Token de segurança inválido. Recarregue a página."}), 403

    @app.post("/history/clear")
    @rate_limited
    def history_clear():
        try:
            validate_csrf()
            data = request.get_json(silent=True) or {}
            user_id = current_user_id(data.get("user_id"))
            clear_history(user_id)
            return jsonify({"ok": True})
        except PermissionError:
            return jsonify({"error": "Token de segurança inválido. Recarregue a página."}), 403

    @app.post("/chat")
    @rate_limited
    def chat():
        try:
            if auth_required() and not is_authenticated():
                return jsonify({"error": "Acesso privado necessário."}), 401

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
            return jsonify({"error": "Token de segurança inválido. Recarregue a página."}), 403
        except Exception:
            return jsonify({"error": "ORION Legacy Edition encontrou um erro interno."}), 500


def rate_limited(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        key = (
            session.get("user", {}).get("id")
            or session.get("private_user", {}).get("id")
            or request.remote_addr
            or "anonymous"
        )
        now = time.time()
        bucket = [t for t in RATE_BUCKETS.get(key, []) if now - t < RATE_LIMIT_WINDOW]
        if len(bucket) >= Settings.RATE_LIMIT_MAX_REQUESTS:
            return jsonify({"error": "Muitas solicitações em pouco tempo. Aguarde alguns segundos."}), 429
        bucket.append(now)
        RATE_BUCKETS[key] = bucket
        return view(*args, **kwargs)

    return wrapped


def validate_message(message):
    if not isinstance(message, str):
        return "A mensagem precisa ser texto."
    if not message.strip():
        return "Digite uma mensagem para o Orion."
    if len(message.strip()) > Settings.MAX_MESSAGE_LENGTH:
        return "Mensagem muito longa. Envie um texto menor."
    return None


def remember_name_if_requested(user_id, message):
    normalized = normalize_text(message)
    patterns = (
        "meu nome e ",
        "lembrar nome: ",
        "lembre meu nome: ",
        "pode me chamar de ",
    )
    for pattern in patterns:
        if normalized.startswith(pattern):
            name = message.strip()[len(pattern):].strip()
            if name:
                remember_user_name(user_id, name)
                return {"name": name}
    return None
