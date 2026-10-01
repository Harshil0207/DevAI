import json
import os
from typing import Any, Dict

CONFIG_DIR = os.path.expanduser("~/.devai")
CONFIG_PATH = os.path.join(CONFIG_DIR, "config.json")

DEFAULTS = {
    "model": "qwen2.5-coder:7b",
    "host": "http://127.0.0.1:11434",
    "temperature": 0.2,
    "num_ctx": 8192,
}


def load() -> Dict[str, Any]:
    cfg = dict(DEFAULTS)
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as fh:
            cfg.update(json.load(fh))
    except (OSError, ValueError):
        pass
    env_model = os.environ.get("DEVAI_MODEL", "").strip()
    if env_model:
        cfg["model"] = env_model
    env_host = os.environ.get("OLLAMA_HOST", "").strip()
    if env_host:
        cfg["host"] = env_host if "://" in env_host else "http://" + env_host
    return cfg


def save(**changes: Any) -> Dict[str, Any]:
    cfg = dict(DEFAULTS)
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as fh:
            cfg.update(json.load(fh))
    except (OSError, ValueError):
        pass
    for key, value in changes.items():
        if value is not None:
            cfg[key] = value
    os.makedirs(CONFIG_DIR, exist_ok=True)
    with open(CONFIG_PATH, "w", encoding="utf-8") as fh:
        json.dump(cfg, fh, indent=2)
    return cfg
