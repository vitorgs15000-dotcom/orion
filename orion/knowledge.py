import json
from pathlib import Path

import requests

KNOWLEDGE_FILE = Path("knowledge_base.json")
WIKIPEDIA_URL = "https://pt.wikipedia.org/api/rest_v1/page/summary/{title}"


def load_knowledge_base():
    if not KNOWLEDGE_FILE.exists():
        KNOWLEDGE_FILE.write_text(
            json.dumps(default_knowledge(), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    try:
        return json.loads(KNOWLEDGE_FILE.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return default_knowledge()


def search_knowledge_base(query):
    normalized_query = query.lower().strip()
    for key, value in load_knowledge_base().items():
        normalized_key = key.lower().strip()
        if normalized_key in normalized_query or normalized_query in normalized_key:
            return value
    return None


def search_wikipedia(query):
    title = query.strip().replace(" ", "_")
    if not title:
        return None

    try:
        response = requests.get(
            WIKIPEDIA_URL.format(title=title),
            timeout=8,
            headers={"User-Agent": "Orion-PWA/1.0"},
        )
        if response.status_code != 200:
            return None

        data = response.json()
        answer = data.get("extract")
        source = data.get("content_urls", {}).get("desktop", {}).get("page")

        if not answer:
            return None

        return {"answer": answer, "source": source or "wikipedia"}
    except requests.RequestException:
        return None


def default_knowledge():
    return {
        "orion": (
            "Orion e um assistente IA web com memoria simples, interface futurista "
            "e suporte PWA para uso no navegador e no celular."
        ),
        "pwa": (
            "PWA significa Progressive Web App: um site que pode ser instalado no "
            "celular e funcionar com recursos de aplicativo."
        ),
        "groq": (
            "Groq oferece API de IA com modelos rapidos e planos gratuitos, ideal "
            "para prototipos como o Orion."
        ),
    }
