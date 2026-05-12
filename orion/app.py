from pathlib import Path
import hmac
import importlib.util
import os
import secrets
import sys

from flask import jsonify, redirect, render_template_string, request, session, url_for

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

spec = importlib.util.spec_from_file_location("orion_root_app", ROOT / "app.py")
module = importlib.util.module_from_spec(spec)
sys.modules["orion_root_app"] = module
spec.loader.exec_module(module)
app = module.app

TEXT_REPLACEMENTS = {
    "ORION V1.1": "ORION Legacy Edition",
    "ORION LEGACY": "ORION Legacy Edition",
    "ORION IA": "ORION Legacy IA",
    "Navega????o": "Navega??o",
    "Mem??ria": "Mem?ria",
    "Configura????es": "Configura??es",
    "Ol??": "Ol?",
    "conte??do": "conte?do",
    "informa????es": "informa??es",
    "N??cleo": "N?cleo",
    "Edi????o": "Edi??o",
    "mem??ria": "mem?ria",
    "c??lculo": "c?lculo",
    "Usu??rio": "Usu?rio",
    "r??pido": "r?pido",
    "hist??rico": "hist?rico",
    "Hist??rico": "Hist?rico",
    "execu????o": "execu??o",
    "Informa????es": "Informa??es",
    "Anima????es": "Anima??es",
    "Indispon??vel": "Indispon?vel",
    "Vers??o": "Vers?o",
    "fam??lia": "fam?lia",
    "h??": "h?",
    "m??s": "m?s",
    "s??o": "s?o",
    "instal??vel": "instal?vel",
    "Sobreposi????o": "Sobreposi??o",
    "Conex??o": "Conex?o",
    "est??vel": "est?vel",
    "sequ??ncia": "sequ?ncia",
    "sint??tica": "sint?tica",
    "Voc??": "Voc?",
    "Conclu??da": "Conclu?da",
    "???": "?",
    "???": "?",
}


def private_auth_enabled():
    return os.getenv("AUTH_REQUIRED", "false").lower() == "true"


def private_credentials_ready():
    return bool(os.getenv("ORION_USERNAME") and os.getenv("ORION_PASSWORD"))


def private_user():
    return {
        "provider": "private",
        "id": os.getenv("ORION_USERNAME", "orion"),
        "name": os.getenv("ORION_USERNAME", "orion"),
        "email": os.getenv("ORION_USERNAME", "orion"),
    }


@app.before_request
def orion_private_gate():
    session.permanent = True
    session.setdefault("csrf_token", secrets.token_urlsafe(32))
    if not private_auth_enabled():
        return None
    if session.get("private_user") or session.get("user"):
        return None
    if request.endpoint in {"static", "health", "orion_private_login", "orion_private_login_post"}:
        return None
    if request.path.startswith("/static/"):
        return None
    if request.method == "GET":
        return redirect(url_for("orion_private_login"))
    return jsonify({"error": "authentication required"}), 401


@app.after_request
def orion_legacy_text_filter(response):
    content_type = response.headers.get("Content-Type", "")
    if any(kind in content_type for kind in ("text/html", "javascript", "application/json")):
        try:
            text = response.get_data(as_text=True)
            for old, new in TEXT_REPLACEMENTS.items():
                text = text.replace(old, new)
            response.set_data(text)
            response.headers["Content-Length"] = str(len(response.get_data()))
        except Exception:
            pass
    return response


LOGIN_TEMPLATE = """
<!doctype html>
<html lang="pt-BR">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no" />
    <meta name="theme-color" content="#0D1117" />
    <title>ORION Legacy Edition - Acesso privado</title>
    <link rel="icon" href="/static/icon-192.png" />
    <style>
      :root { color-scheme: dark; font-family: Inter, Segoe UI, Arial, sans-serif; }
      * { box-sizing: border-box; }
      body { min-height: 100vh; min-height: 100dvh; margin: 0; display: grid; place-items: center; padding: 20px; color: #F5F7FA; background: radial-gradient(circle at 20% 15%, rgba(0,229,255,.16), transparent 28%), radial-gradient(circle at 85% 20%, rgba(123,47,255,.15), transparent 30%), #0D1117; }
      .card { width: min(430px, 100%); display: grid; gap: 14px; padding: 28px; border: 1px solid rgba(0,229,255,.22); border-radius: 26px; background: rgba(26,31,43,.78); box-shadow: inset 0 0 44px rgba(0,140,255,.06), 0 28px 90px rgba(0,0,0,.34); backdrop-filter: blur(18px); }
      img { width: 54px; height: 54px; border-radius: 50%; border: 1px solid rgba(0,229,255,.7); box-shadow: 0 0 18px rgba(0,229,255,.28); }
      h1, p { margin: 0; } p, small { color: rgba(245,247,250,.68); }
      .eyebrow { color: #00E5FF; font-size: 12px; font-weight: 900; }
      form { display: grid; gap: 12px; }
      label { display: grid; gap: 7px; color: rgba(245,247,250,.72); font-size: 13px; font-weight: 800; }
      input { width: 100%; min-height: 50px; border: 1px solid rgba(0,229,255,.2); border-radius: 15px; padding: 0 14px; color: #F5F7FA; background: rgba(13,17,23,.78); outline: none; font-size: 16px; }
      input:focus { border-color: rgba(0,229,255,.7); box-shadow: 0 0 0 3px rgba(0,229,255,.08); }
      button { min-height: 50px; border: 0; border-radius: 15px; color: #0D1117; background: #00E5FF; box-shadow: 0 0 24px rgba(0,229,255,.28); cursor: pointer; font-weight: 900; font-size: 16px; }
      .error { padding: 12px; border: 1px solid rgba(255,86,86,.35); border-radius: 14px; color: #ffd9d9; background: rgba(255,86,86,.10); }
      .signature { position: fixed; right: 16px; bottom: 12px; color: rgba(0,229,255,.42); font-size: 11px; text-shadow: 0 0 12px rgba(0,229,255,.28); }
    </style>
  </head>
  <body>
    <main class="card">
      <img src="/static/icon-192.png" alt="Logo Orion" />
      <p class="eyebrow">ORION Legacy Edition</p>
      <h1>Acesso privado</h1>
      <p>Assistente pessoal de lava_rip2012 e fam?lia.</p>
      {% if error %}<div class="error">{{ error }}</div>{% endif %}
      <form method="post" action="{{ url_for('orion_private_login_post') }}">
        <input type="hidden" name="csrf_token" value="{{ csrf_token }}" />
        <label>Usu?rio<input name="username" autocomplete="username" required /></label>
        <label>Senha<input name="password" type="password" autocomplete="current-password" required /></label>
        <button type="submit">Entrar</button>
      </form>
      <small>Credenciais protegidas por vari?veis do servidor.</small>
    </main>
    <p class="signature">created by lava_rip2012</p>
  </body>
</html>
"""


@app.get("/private-login")
def orion_private_login():
    session.setdefault("csrf_token", secrets.token_urlsafe(32))
    return render_template_string(LOGIN_TEMPLATE, error=None, csrf_token=session["csrf_token"])


@app.post("/private-login")
def orion_private_login_post():
    session.setdefault("csrf_token", secrets.token_urlsafe(32))
    if request.form.get("csrf_token") != session.get("csrf_token"):
        return render_template_string(LOGIN_TEMPLATE, error="Sess?o expirada. Recarregue e tente novamente.", csrf_token=session["csrf_token"]), 400
    if not private_credentials_ready():
        return render_template_string(LOGIN_TEMPLATE, error="Login privado ainda n?o configurado no servidor.", csrf_token=session["csrf_token"]), 503
    username = (request.form.get("username") or "").strip()
    password = request.form.get("password") or ""
    valid_user = hmac.compare_digest(username, os.getenv("ORION_USERNAME", ""))
    valid_password = hmac.compare_digest(password, os.getenv("ORION_PASSWORD", ""))
    if not (valid_user and valid_password):
        return render_template_string(LOGIN_TEMPLATE, error="Usu?rio ou senha inv?lidos.", csrf_token=session["csrf_token"]), 401
    session["private_user"] = private_user()
    session["user"] = private_user()
    return redirect(url_for("index"))


@app.post("/logout")
def orion_private_logout():
    session.clear()
    return jsonify({"status": "ok"})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
