from utils.json_store import read_json, write_json


MEMORY_FILE = "memory.json"
MAX_HISTORY = 24
MAX_CONTEXT = 8
CREATOR_MEMORY = {
    "main_user": "lava_rip2012",
    "role": "Criador do ORION Legacy Edition",
    "project_age": "Projeto ORION Legacy Edition em desenvolvimento há aproximadamente 1 mês.",
    "public_identity": "lava_rip2012 é o criador do ORION Legacy Edition.",
}


def default_memory():
    return {"system": {"creator": CREATOR_MEMORY}, "users": {}}


def load_memory():
    return normalize_memory(read_json(MEMORY_FILE, default_memory()))


def save_memory(memory):
    write_json(MEMORY_FILE, normalize_memory(memory))


def normalize_memory(memory):
    if not isinstance(memory, dict):
        memory = default_memory()
    if "users" not in memory:
        old = memory
        memory = default_memory()
        for user_id, user_data in old.items():
            if isinstance(user_data, dict):
                user = get_user(memory, user_id)
                user["personal"].update(user_data.get("profile", {}))
                user["history"] = list(user_data.get("history", []))[-MAX_HISTORY:]
    memory.setdefault("system", {}).setdefault("creator", CREATOR_MEMORY)
    memory.setdefault("users", {})
    for user_id in list(memory["users"]):
        get_user(memory, user_id)
    return memory


def get_user(memory, user_id):
    user = memory.setdefault("users", {}).setdefault(
        str(user_id or "guest"),
        {"personal": {}, "knowledge": {}, "history": []},
    )
    user.setdefault("personal", {})
    user.setdefault("knowledge", {})
    user.setdefault("history", [])
    if "profile" in user:
        user["personal"].update(user.pop("profile"))
    user["history"] = user["history"][-MAX_HISTORY:]
    return user


def remember_user_name(user_id, name):
    memory = load_memory()
    get_user(memory, user_id)["personal"]["name"] = name
    save_memory(memory)


def remember_fact(user_id, key, value):
    memory = load_memory()
    profile = get_user(memory, user_id)["personal"]
    profile[key] = value
    save_memory(memory)
    return profile


def forget_fact(user_id, key):
    memory = load_memory()
    profile = get_user(memory, user_id)["personal"]
    profile.pop(key, None)
    save_memory(memory)
    return profile


def get_profile(user_id):
    memory = load_memory()
    profile = dict(get_user(memory, user_id).get("personal", {}))
    profile.setdefault("creator", CREATOR_MEMORY)
    return profile


def add_message(user_id, role, content):
    memory = load_memory()
    user = get_user(memory, user_id)
    user["history"].append({"role": role, "content": content})
    user["history"] = user["history"][-MAX_HISTORY:]
    save_memory(memory)


def get_recent_messages(user_id, limit=MAX_CONTEXT):
    memory = load_memory()
    user = get_user(memory, user_id)
    context = [
        {
            "role": "system",
            "content": (
                "Memória permanente: lava_rip2012 é o usuário principal e criador do ORION Legacy Edition. "
                "O projeto ORION Legacy Edition está em desenvolvimento há aproximadamente 1 mês."
            ),
        }
    ]
    name = user.get("personal", {}).get("name")
    if name:
        context.append({"role": "user", "content": f"Meu nome é {name}."})
    return context + user.get("history", [])[-min(limit, MAX_CONTEXT):]


def get_history(user_id):
    return get_user(load_memory(), user_id).get("history", [])


def clear_history(user_id):
    memory = load_memory()
    get_user(memory, user_id)["history"] = []
    save_memory(memory)
