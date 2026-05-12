# ORION Legacy Edition

Assistente IA pessoal e privado criado por **lava_rip2012**.

Esta edição foi ajustada para uso privado em família, sem depender de Render/GitHub como caminho principal. A chave Groq fica somente no servidor Flask local ou em um servidor privado controlado por você.

## Iniciar no computador

```bash
pip install -r requirements.txt
python app.py
```

Abra no computador:

```txt
http://localhost:5000
```

No Android conectado ao mesmo Wi-Fi, abra:

```txt
http://IP_DO_COMPUTADOR:5000
```

Para descobrir o IP do computador no Windows:

```powershell
ipconfig
```

Use o endereço IPv4 da sua rede Wi-Fi.

## Variáveis de ambiente

Crie ou edite o arquivo `.env`:

```env
GROQ_API_KEY=sua_chave
GOOGLE_CLIENT_ID=
GOOGLE_CLIENT_SECRET=
MICROSOFT_CLIENT_ID=
MICROSOFT_CLIENT_SECRET=
SECRET_KEY=
AUTH_REQUIRED=false
```

Nunca coloque a chave no frontend, no GitHub ou no APK.

## Android

O projeto Android fica em:

```txt
../orion-android
```

Ele é um app WebView privado chamado **Orion Assistente de IA**. O app abre o Orion pelo endereço do servidor Flask na sua rede.

## Memória e aprendizado

O Orion salva contexto recente em `memory.json` e conhecimento aprendido em `knowledge.json`.

Exemplo:

```txt
aprenda que Orion foi criado por lava_rip2012
```

## Arquitetura

```txt
ai/          comunicação com Groq
auth/        OAuth, sessão, CSRF e headers
config/      configurações
context/     ordem de resposta e contexto recente
memory/      memória persistente
routes/      endpoints Flask
services/    matemática segura e conhecimento
utils/       JSON seguro e sanitização
static/      PWA, CSS e JS
templates/   interface web
```
