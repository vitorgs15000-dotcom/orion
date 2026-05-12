import json
import re
from pathlib import Path

import requests

from utils.text import normalize_text, token_set


KNOWLEDGE_FILE = Path("knowledge.json")
LEGACY_KNOWLEDGE_FILE = Path("knowledge_base.json")
WIKIPEDIA_URL = "https://pt.wikipedia.org/api/rest_v1/page/summary/{title}"
CREATOR_ANSWER = (
    "Fui criado por lava_rip2012, o usuário principal e criador do projeto ORION Legacy Edition. "
    "O ORION Legacy Edition está em desenvolvimento há aproximadamente 1 mês, evoluindo como um "
    "assistente IA web futurista, pessoal e cada vez mais inteligente."
)


def load_knowledge_base():
    if not KNOWLEDGE_FILE.exists():
        save_knowledge_base(default_knowledge())

    try:
        knowledge = json.loads(KNOWLEDGE_FILE.read_text(encoding="utf-8"))
        if not isinstance(knowledge, dict):
            return default_knowledge()
        return {**default_knowledge(), **knowledge}
    except (OSError, json.JSONDecodeError):
        return default_knowledge()


def save_knowledge_base(knowledge):
    temp_file = KNOWLEDGE_FILE.with_suffix(".tmp")
    temp_file.write_text(
        json.dumps(knowledge, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    temp_file.replace(KNOWLEDGE_FILE)


def search_knowledge_base(query):
    normalized_query = normalize_text(query)
    query_tokens = token_set(normalized_query)
    creator_intent = bool(
        {"criador", "criou", "criado", "dono", "origem", "lava_rip2012"} & query_tokens
    )
    if creator_intent:
        return CREATOR_ANSWER

    best_match = None
    best_score = 0

    for key, value in load_knowledge_base().items():
        normalized_key = normalize_text(key)
        if normalized_key == "orion" and query_tokens - {"orion", "que", "sobre"}:
            continue
        if normalized_key in normalized_query or normalized_query in normalized_key:
            return value
        combined_tokens = token_set(f"{key} {value}")
        score = len(query_tokens & combined_tokens)
        if score > best_score:
            best_score = score
            best_match = value

    if best_score >= 2:
        return best_match
    return None


def learn_knowledge(text):
    fact = clean_fact(text)
    if not fact:
        return None

    knowledge = load_knowledge_base()
    key = make_key(fact)

    if key in knowledge:
        return {"key": key, "value": knowledge[key], "created": False}

    knowledge[key] = naturalize_fact(fact)
    save_knowledge_base(knowledge)
    return {"key": key, "value": knowledge[key], "created": True}


def clean_fact(text):
    fact = str(text or "").strip()
    fact = re.sub(r"\s+", " ", fact).strip(" .")
    if len(fact) < 4 or len(fact) > 400:
        return None
    return fact


def make_key(fact):
    key = normalize_text(fact)
    key = re.sub(r"[^a-z0-9]+", "_", key).strip("_")
    return key[:80] or "aprendizado"


def naturalize_fact(fact):
    return fact[:1].upper() + fact[1:] + "."


def search_wikipedia(query):
    title = query.strip().replace(" ", "_")
    if not title:
        return None

    try:
        response = requests.get(
            WIKIPEDIA_URL.format(title=title),
            timeout=8,
            headers={"User-Agent": "ORION-Legacy-Edition/1.0"},
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
    base = {
        "orion": (
            "ORION Legacy Edition é um assistente IA web com memória, interface futurista, cálculo seguro "
            "e suporte PWA para uso no navegador e no celular."
        ),
        "criador_do_orion": CREATOR_ANSWER,
        "lava_rip2012": (
            "lava_rip2012 é o usuário principal e criador do ORION Legacy Edition. O projeto ORION Legacy Edition "
            "tem aproximadamente 1 mês de desenvolvimento."
        ),
        "projeto_orion_duracao": (
            "O projeto ORION Legacy Edition foi criado por lava_rip2012 e está em desenvolvimento "
            "há aproximadamente 1 mês."
        ),
        "pwa": (
            "PWA significa Progressive Web App: um site que pode ser instalado no "
            "celular e funcionar com recursos de aplicativo."
        ),
        "groq": (
            "Groq oferece API de IA com modelos rápidos e planos gratuitos, ideal "
            "para protótipos como o ORION Legacy Edition."
        ),
    }

    if LEGACY_KNOWLEDGE_FILE.exists():
        try:
            legacy = json.loads(LEGACY_KNOWLEDGE_FILE.read_text(encoding="utf-8"))
            if isinstance(legacy, dict):
                base.update(legacy)
        except (OSError, json.JSONDecodeError):
            pass

    return base
