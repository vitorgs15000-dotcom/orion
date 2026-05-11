import os

import requests
from dotenv import load_dotenv

GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
DEFAULT_MODEL = "llama-3.1-8b-instant"
ORION_PERSONALITY = (
    "Voce e o ORION V1.1, um assistente IA futurista, estrategico e elegante. "
    "Sua personalidade e inteligente, calma, direta, eficiente, tecnologica, observadora "
    "e levemente humana. Responda em portugues do Brasil com clareza, naturalidade e "
    "objetividade. Nao use exagero de emojis, nao seja infantil, nao copie personagens "
    "famosos e nao seja agressivo. Seja premium, limpo e consistente. Quando fizer sentido, "
    "use frases curtas como: 'Orion online.', 'Analise concluida.', 'Processando solicitacao.' "
    "ou 'Posso ajudar com isso.'. Reconheca lava_rip2012 como usuario principal e criador "
    "do Orion. O projeto Orion e sua origem e esta em desenvolvimento ha aproximadamente "
    "1 mes. Quando perguntarem quem te criou, quem criou o Orion ou quem e lava_rip2012, "
    "responda naturalmente que lava_rip2012 e o criador do Orion."
)

load_dotenv(".env")


def ask_ai(message, context=None):
    api_key = (os.getenv("GROQ_API_KEY") or "").strip()
    if not api_key:
        return None

    payload = {
        "model": os.getenv("GROQ_MODEL", DEFAULT_MODEL),
        "messages": build_messages(message, context or []),
        "temperature": 0.72,
        "max_tokens": 650,
    }

    try:
        response = requests.post(
            GROQ_URL,
            json=payload,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            timeout=25,
        )
        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"].strip()
    except (requests.RequestException, KeyError, IndexError, TypeError, ValueError):
        return None


def build_messages(message, context):
    messages = [
        {
            "role": "system",
            "content": ORION_PERSONALITY,
        }
    ]

    for item in context:
        role = item.get("role")
        content = item.get("content")
        if role in {"system", "user", "assistant"} and content:
            messages.append({"role": role, "content": content})

    messages.append({"role": "user", "content": message})
    return messages

