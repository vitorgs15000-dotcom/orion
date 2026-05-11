from ai_service import ask_ai
from knowledge import learn_knowledge, search_knowledge_base, search_wikipedia
from math_service import answer_math
from memory import add_message, get_recent_messages


DEFAULT_FALLBACK = (
    "Ainda nao encontrei uma resposta confiavel. Posso tentar de novo com mais "
    "contexto, consultar minha base local ou guardar uma informacao para voce."
)


def build_context(user_id, limit=8):
    return get_recent_messages(user_id, limit=limit)


def learn_if_requested(message):
    normalized = message.strip().lower()
    prefixes = (
        "aprenda que ",
        "aprende que ",
        "lembre que ",
        "saiba que ",
        "ensine ao orion que ",
        "ensina ao orion que ",
    )
    for prefix in prefixes:
        if normalized.startswith(prefix):
            fact = message.strip()[len(prefix):].strip()
            return learn_knowledge(fact) if fact else None
    return None


def generate_reply(user_id, message):
    context = build_context(user_id)
    add_message(user_id, "user", message)

    learned = learn_if_requested(message)
    if learned:
        reply = "Aprendizado registrado. Vou reutilizar essa informacao quando ela for relevante."
        add_message(user_id, "assistant", reply)
        return {"reply": reply, "source": "learning"}

    for responder in (math_response, ai_response, knowledge_response, wikipedia_response):
        result = responder(message, context)
        if result:
            reply, source = result
            add_message(user_id, "assistant", reply)
            return {"reply": reply, "source": source}

    add_message(user_id, "assistant", DEFAULT_FALLBACK)
    return {"reply": DEFAULT_FALLBACK, "source": "fallback"}


def math_response(message, _context):
    reply = answer_math(message)
    return (reply, "math") if reply else None


def ai_response(message, context):
    reply = ask_ai(message, context=context)
    return (reply, "ai") if reply else None


def knowledge_response(message, _context):
    reply = search_knowledge_base(message)
    return (reply, "knowledge_base") if reply else None


def wikipedia_response(message, _context):
    result = search_wikipedia(message)
    if not result:
        return None
    return result["answer"], result["source"]
