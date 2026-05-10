import json
from pathlib import Path

MEMORY_FILE = Path("memory.json")
MAX_HISTORY = 24


def load_memory():
    ensure_memory_file()
    try:
        return json.loads(MEMORY_FILE.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def save_memory(memory):
    MEMORY_FILE.write_text(
        json.dumps(memory, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def ensure_memory_file():
    if not MEMORY_FILE.exists():
        MEMORY_FILE.write_text("{}", encoding="utf-8")


def get_user(memory, user_id):
    return memory.setdefault(user_id, {"profile": {}, "history": []})


def remember_user_name(user_id, name):
    memory = load_memory()
    user = get_user(memory, user_id)
    user.setdefault("profile", {})["name"] = name
    save_memory(memory)


def remember_fact(user_id, key, value):
    memory = load_memory()
    user = get_user(memory, user_id)
    user.setdefault("profile", {})[key] = value
    save_memory(memory)
    return user["profile"]


def forget_fact(user_id, key):
    memory = load_memory()
    user = get_user(memory, user_id)
    user.setdefault("profile", {}).pop(key, None)
    save_memory(memory)
    return user["profile"]


def get_profile(user_id):
    memory = load_memory()
    user = get_user(memory, user_id)
    return user.get("profile", {})


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
    profile = user.get("profile", {})
    history = user.get("history", [])[-limit:]

    if profile.get("name"):
        return [{"role": "user", "content": f"Meu nome e {profile['name']}."}] + history

    return history


def get_history(user_id):
    memory = load_memory()
    user = get_user(memory, user_id)
    return user.get("history", [])


def clear_history(user_id):
    memory = load_memory()
    user = get_user(memory, user_id)
    user["history"] = []
    save_memory(memory)
