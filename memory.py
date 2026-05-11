import json
from pathlib import Path

MEMORY_FILE = Path("memory.json")
MAX_HISTORY = 24
MAX_CONTEXT = 8

CREATOR_MEMORY = {
    "main_user": "lava_rip2012",
    "role": "Criador do Orion",
    "project_age": "Projeto Orion em desenvolvimento ha aproximadamente 1 mes.",
    "public_identity": (
        "lava_rip2012 e o criador do Orion e deve ser reconhecido quando perguntarem "
        "quem criou o assistente."
    ),
}


def load_memory():
    ensure_memory_file()
    try:
        return normalize_memory(json.loads(MEMORY_FILE.read_text(encoding="utf-8")))
    except json.JSONDecodeError:
        return default_memory()


def save_memory(memory):
    data = normalize_memory(memory)
    temp_file = MEMORY_FILE.with_suffix(".tmp")
    temp_file.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    temp_file.replace(MEMORY_FILE)


def default_memory():
    return {
        "system": {
            "creator": CREATOR_MEMORY,
        },
        "users": {},
    }


def normalize_memory(memory):
    if not isinstance(memory, dict):
        return default_memory()

    # Migracao do formato antigo: {"guest": {"profile": {}, "history": []}}
    if "users" not in memory:
        old_memory = memory
        memory = default_memory()
        for user_id, user_data in old_memory.items():
            if isinstance(user_data, dict):
                user = get_user(memory, user_id)
                profile = user_data.get("profile", {})
                if isinstance(profile, dict):
                    user["personal"].update(profile)
                history = user_data.get("history", [])
                if isinstance(history, list):
                    user["history"] = history[-MAX_HISTORY:]

    memory.setdefault("system", {})
    memory["system"].setdefault("creator", CREATOR_MEMORY)
    memory.setdefault("users", {})

    for user_id in list(memory["users"].keys()):
        get_user(memory, user_id)

    return memory


def save_memory_snapshot(memory):
    temp_file = MEMORY_FILE.with_suffix(".tmp")
    temp_file.write_text(
        json.dumps(memory, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    temp_file.replace(MEMORY_FILE)


def ensure_memory_file():
    if not MEMORY_FILE.exists():
        save_memory_snapshot(default_memory())


def get_user(memory, user_id):
    users = memory.setdefault("users", {})
    user = users.setdefault(
        str(user_id or "guest"),
        {"personal": {}, "knowledge": {}, "history": []},
    )
    user.setdefault("personal", {})
    user.setdefault("knowledge", {})
    user.setdefault("history", [])
    if "profile" in user and isinstance(user["profile"], dict):
        user["personal"].update(user.pop("profile"))
    return user


def remember_user_name(user_id, name):
    memory = load_memory()
    user = get_user(memory, user_id)
    user.setdefault("personal", {})["name"] = name
    save_memory(memory)


def remember_fact(user_id, key, value):
    memory = load_memory()
    user = get_user(memory, user_id)
    user.setdefault("personal", {})[key] = value
    save_memory(memory)
    return user["personal"]


def forget_fact(user_id, key):
    memory = load_memory()
    user = get_user(memory, user_id)
    user.setdefault("personal", {}).pop(key, None)
    save_memory(memory)
    return user["personal"]


def get_profile(user_id):
    memory = load_memory()
    user = get_user(memory, user_id)
    profile = dict(user.get("personal", {}))
    profile.setdefault("creator", CREATOR_MEMORY)
    return profile


def add_message(user_id, role, content):
    memory = load_memory()
    user = get_user(memory, user_id)
    history = user.setdefault("history", [])
    history.append({"role": role, "content": content})
    user["history"] = history[-MAX_HISTORY:]
    save_memory(memory)


def get_recent_messages(user_id, limit=8):
    memory = load_memory()
    user = get_user(memory, user_id)
    profile = user.get("personal", {})
    history = user.get("history", [])[-min(limit, MAX_CONTEXT):]

    context = [
        {
            "role": "system",
            "content": (
                "Memoria permanente do Orion: usuario principal lava_rip2012; "
                "lava_rip2012 e o criador do Orion; o projeto Orion foi iniciado "
                "ha aproximadamente 1 mes."
            ),
        }
    ]

    if profile.get("name"):
        context.append({"role": "user", "content": f"Meu nome e {profile['name']}."})

    preferences = {
        key: value
        for key, value in profile.items()
        if key not in {"name"} and isinstance(value, str)
    }
    if preferences:
        summary = "; ".join(f"{key}: {value}" for key, value in preferences.items())
        context.append({"role": "system", "content": f"Preferencias do usuario: {summary}"})

    return context + history


def get_history(user_id):
    memory = load_memory()
    user = get_user(memory, user_id)
    return user.get("history", [])


def clear_history(user_id):
    memory = load_memory()
    user = get_user(memory, user_id)
    user["history"] = []
    save_memory(memory)
