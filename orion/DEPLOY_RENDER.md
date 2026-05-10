# Deploy do Orion no Render

## Arquivos de producao

O projeto inclui:

```text
requirements.txt
Procfile
runtime.txt
```

O `Procfile` usa:

```text
web: gunicorn app:app
```

## Configurar no Render

1. Envie a pasta `orion` para um repositorio GitHub.
2. No Render, crie um novo Web Service ou Blueprint.
3. Selecione o repositorio.
4. Se usar Web Service manual, configure:

```text
Build Command: pip install -r requirements.txt
Start Command: gunicorn app:app
```

5. Em Environment Variables, adicione:

```text
GROQ_API_KEY=sua_chave
GROQ_MODEL=llama-3.1-8b-instant
SECRET_KEY=uma_chave_longa_aleatoria
GOOGLE_CLIENT_ID=seu_google_client_id
GOOGLE_CLIENT_SECRET=seu_google_client_secret
MICROSOFT_CLIENT_ID=seu_microsoft_client_id
MICROSOFT_CLIENT_SECRET=seu_microsoft_client_secret
AUTH_REQUIRED=false
FLASK_ENV=production
```

Nao coloque nenhuma chave direto no codigo.

O arquivo `render.yaml` tambem esta pronto para Blueprint deploy.

Para obrigar login antes do chat em producao:

```text
AUTH_REQUIRED=true
```

## OAuth redirect URLs

No Google Cloud Console:

```text
https://SEU-APP.onrender.com/auth/google/callback
```

No Microsoft Azure:

```text
https://SEU-APP.onrender.com/auth/microsoft/callback
```

## Android/PWA

Depois do deploy, abra a URL HTTPS do Render no Chrome Android.
O Chrome deve oferecer a opcao de instalar o app ou adicionar a tela inicial.
