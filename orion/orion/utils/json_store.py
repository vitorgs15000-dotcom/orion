import json
from pathlib import Path


def read_json(path, default):
    file_path = Path(path)
    if not file_path.exists():
        write_json(file_path, default)
        return default
    try:
        data = json.loads(file_path.read_text(encoding="utf-8"))
        return data if isinstance(data, type(default)) else default
    except (OSError, json.JSONDecodeError):
        return default


def write_json(path, data):
    file_path = Path(path)
    file_path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = file_path.with_suffix(".tmp")
    temp_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    temp_path.replace(file_path)
