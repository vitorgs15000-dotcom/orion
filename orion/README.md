# ORION

Assistente IA web futurista com Flask, Groq, OAuth Google/Microsoft, memoria JSON, PWA e deploy pronto para Render.

## Iniciar localmente

```bash
pip install -r requirements.txt
python app.py
```

Abra:

```text
http://localhost:5000
```

Se a porta 5000 estiver ocupada, libere a porta ou rode via Flask em outra porta para teste:

```bash
python -m flask --app app run --host 0.0.0.0 --port 5064
```

## Variaveis de ambiente

Use `.env` localmente e Environment Variables no Render:

```env
GROQ_API_KEY=sua_chave
GROQ_MODEL=llama-3.1-8b-instant
GOOGLE_CLIENT_ID=
GOOGLE_CLIENT_SECRET=
MICROSOFT_CLIENT_ID=
MICROSOFT_CLIENT_SECRET=
SECRET_KEY=
AUTH_REQUIRED=false
FLASK_ENV=production
```

Nunca envie `.env` ao GitHub.

## Render

```text
Build Command: pip install -r requirements.txt
Start Command: gunicorn app:app
```

O projeto ja inclui `Procfile` e `runtime.txt`.

## OAuth

Google callback:

```text
https://SEU-APP.onrender.com/auth/google/callback
```

Microsoft callback:

```text
https://SEU-APP.onrender.com/auth/microsoft/callback
```

Depois coloque os client IDs/secrets no Render.

## Android/PWA

Abra a URL HTTPS do Render no Chrome Android e escolha instalar/adicionar a tela inicial.

## Atualizar o Orion

1. Edite arquivos em `templates/`, `static/` ou serviços Python.
2. Teste localmente.
3. Faça commit e push para o GitHub.
4. O Render redeploya automaticamente se estiver conectado ao repositorio.
