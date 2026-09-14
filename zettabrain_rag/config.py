"""ZettaBrain — Configuration and first-run migration from 0.5.x.

Paths deliberately match where 0.5.x put things, so an upgrade finds the existing document
library and settings instead of starting empty. Settings used to live in a KEY=VALUE file
(zettabrain.env); they now live in config.json, and the old file is read once and converted.
"""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path

log = logging.getLogger(__name__)

# ── Locations ─────────────────────────────────────────────────────────────────
# 0.5.x installed to /opt/zettabrain with the application under src/. Keeping that layout
# is what makes an in-place upgrade keep working.

if os.name == "nt":
    _local_app = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
    BASE_DIR = Path(os.environ.get("ZETTABRAIN_DIR", _local_app / "ZettaBrain"))
    DEPLOY_DIR = BASE_DIR
else:
    BASE_DIR = Path(
        os.environ.get("ZETTABRAIN_DIR")
        or os.environ.get("ZETTABRAIN_LITE_DIR")  # 1.0 pre-release name
        or "/opt/zettabrain"
    )
    DEPLOY_DIR = BASE_DIR / "src"

CERT_DIR = BASE_DIR / "certs"
DATA_DIR = DEPLOY_DIR / "data"
SKILLS_DIR = DEPLOY_DIR / "skills"
STORAGE_CONF = DEPLOY_DIR / "storage.conf"
CONFIG_FILE = DEPLOY_DIR / "config.json"

# The 0.5.x settings file. Read once on first run, then left alone.
LEGACY_ENV_FILE = DEPLOY_DIR / "zettabrain.env"

# 0.5.x kept the vector store here. The environment variable wins so existing installs that
# moved it are still found.
CHROMA_PATH = Path(os.environ.get("ZETTABRAIN_CHROMA") or (DEPLOY_DIR / "zettabrain_vectorstore"))
CHROMA_DIR = CHROMA_PATH.parent

DATABASE_PATH = DATA_DIR / "zettabrain.db"
DATABASE_URL = f"sqlite:///{DATABASE_PATH}"

# File types the ingester can read. Every place that filters files — folder scans, uploads,
# and cloud storage sync — must use this set, or a format is silently dropped on one path
# while working on another.
SUPPORTED_EXTENSIONS = frozenset({".pdf", ".txt", ".md", ".docx", ".doc", ".xlsx", ".xls", ".csv"})

PORT = int(os.environ.get("ZETTABRAIN_PORT") or os.environ.get("ZETTABRAIN_LITE_PORT") or "7860")
OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
LLM_MODEL = os.environ.get("ZETTABRAIN_LLM_MODEL", "llama3.1:8b")
EMBED_MODEL = os.environ.get("ZETTABRAIN_EMBED_MODEL", "nomic-embed-text")

_DEFAULT_DOCS = str(BASE_DIR / "data") if os.name != "nt" else str(Path.home() / "Documents")

# ── Migration from the 0.5.x settings file ────────────────────────────────────

# Old KEY=VALUE name -> new config.json key.
_LEGACY_KEYS = {
    "OLLAMA_HOST": "ollama_host",
    "ZETTABRAIN_LLM_MODEL": "llm_model",
    "ZETTABRAIN_EMBED_MODEL": "embed_model",
    "ZETTABRAIN_DOCS": "docs_folder",
    "RAG_DATA_PATH": "docs_folder",
    "ZETTABRAIN_CHROMA": "chroma_path",
    "ZETTABRAIN_PORT": "port",
}


def read_legacy_env(path: Path | None = None) -> dict:
    """Parse a 0.5.x zettabrain.env into config.json keys. Returns {} when absent."""
    path = path or LEGACY_ENV_FILE
    if not path.exists():
        return {}
    settings: dict = {}
    try:
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            mapped = _LEGACY_KEYS.get(key.strip())
            if mapped:
                settings[mapped] = value.strip().strip('"').strip("'")
    except Exception:
        log.warning("Could not read the previous settings file at %s", path, exc_info=True)
        return {}
    return settings


def migrate_legacy_settings() -> dict:
    """Bring 0.5.x settings forward on first run. Returns what was migrated.

    Runs only when config.json does not yet exist, so it cannot overwrite newer settings,
    and it never deletes the old file — an upgrade that goes wrong should be reversible.
    """
    if CONFIG_FILE.exists():
        return {}
    legacy = read_legacy_env()
    if not legacy:
        return {}
    legacy["migrated_from"] = "0.5.x"
    save_config(legacy)
    log.info("Carried %d settings forward from %s", len(legacy) - 1, LEGACY_ENV_FILE)
    return legacy


def docs_folder() -> str:
    """Where the user's documents live. Honours the 0.5.x setting if one was migrated."""
    return (
        os.environ.get("ZETTABRAIN_DOCS")
        or get_setting("docs_folder")
        or _DEFAULT_DOCS
    )


# ── Config file ───────────────────────────────────────────────────────────────


def load_config() -> dict:
    """Load user config from config.json."""
    if CONFIG_FILE.exists():
        try:
            return json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
        except Exception:
            log.warning("config.json could not be read; using defaults", exc_info=True)
    return {}


def save_config(cfg: dict):
    """Persist user config to config.json."""
    CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
    CONFIG_FILE.write_text(json.dumps(cfg, indent=2), encoding="utf-8")


def get_setting(key: str, default=None):
    """Get a single setting value."""
    cfg = load_config()
    return cfg.get(key, default)


def set_setting(key: str, value):
    """Set a single setting value."""
    cfg = load_config()
    cfg[key] = value
    save_config(cfg)
