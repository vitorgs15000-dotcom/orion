import os

import requests
from dotenv import load_dotenv

from config import Settings


GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
ORION_PERSONALITY = (
    "Você é o ORION Legacy Edition, um assistente IA pessoal, privado e futurista criado por "
    "lava_rip2012. Sua personalidade é inteligente, estratégica, tecnológica, lógica, "
    "eficiente, elegante, observadora, calma e levemente humana. Responda em português "
    "do Brasil com clareza, naturalidade e objetividade. Não aja como meme, não seja "
    "infantil, não copie personagens famosos e não seja agressivo. Reconheça lava_rip2012 "
    "como usuário principal e criador do Orion. O projeto Orion está em desenvolvimento "
    "há aproximadamente 1 mês e esta versão Legacy preserva um marco histórico do projeto."
)

load_dotenv(".env")


def ask_ai(message, context=None):
    api_key = (os.getenv("GROQ_API_KEY") or "").strip()
    if not api_key:
        return None

    payload = {
        "model": Settings.GROQ_MODEL,
        "messages": build_messages(message, context or []),
        "temperature": 0.65,
        "max_tokens": 650,
    }

    try:
        response = requests.post(
            GROQ_URL,
            json=payload,
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            timeout=25,
        )
        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"].strip()
    except (requests.RequestException, KeyError, IndexError, TypeError, ValueError):
        return None


def build_messages(message, context):
    messages = [{"role": "system", "content": ORION_PERSONALITY}]
    for item in context:
        role = item.get("role")
        content = item.get("content")
        if role in {"system", "user", "assistant"} and content:
            messages.append({"role": role, "content": content})
    messages.append({"role": "user", "content": message})
    return messages
