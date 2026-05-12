import re
import unicodedata
from html import escape


def normalize_text(text):
    value = unicodedata.normalize("NFKD", str(text or ""))
    value = "".join(char for char in value if not unicodedata.combining(char))
    return value.strip().lower()


def sanitize_message(message):
    return escape(str(message or "").strip(), quote=False)


def sanitize_key(key):
    key = normalize_text(key)
    key = re.sub(r"[^a-z0-9_-]+", "_", key).strip("_")
    return key[:48]


def token_set(text):
    return {
        token
        for token in re.findall(r"[a-z0-9_áéíóúâêôãõç]+", str(text or "").lower())
        if len(token) > 2
    }
