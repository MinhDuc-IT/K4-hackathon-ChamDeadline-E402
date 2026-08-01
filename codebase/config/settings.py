import os
from datetime import timedelta, timezone
from pathlib import Path
from typing import TypedDict

BASE_DIR = Path(__file__).resolve().parent.parent
CACHE_DIR = BASE_DIR / "cache"
MESSAGES_CACHE_PATH = CACHE_DIR / "messages.json"
EMBEDDINGS_CACHE_PATH = CACHE_DIR / "embeddings.npy"
META_CACHE_PATH = CACHE_DIR / "meta.json"

VN_TZ = timezone(timedelta(hours=7))

DEFAULT_EMBEDDING_MODEL = "intfloat/multilingual-e5-large"


class RuntimeSettings(TypedDict):
    channel_ids: list[int]
    history_limit: int
    embedding_model_name: str
    min_similarity: float
    sync_interval_minutes: int


def parse_channel_ids(raw_value: str | None) -> list[int]:
    if not raw_value:
        return []
    ids: list[int] = []
    for part in raw_value.split(","):
        part = part.strip()
        if not part:
            continue
        ids.append(int(part))
    return ids


def load_runtime_settings() -> RuntimeSettings:
    return {
        "channel_ids": parse_channel_ids(os.getenv("DISCORD_SEARCH_CHANNEL_IDS")),
        "history_limit": int(os.getenv("DISCORD_HISTORY_LIMIT", "100")),
        "embedding_model_name": os.getenv("EMBEDDING_MODEL", DEFAULT_EMBEDDING_MODEL),
        "min_similarity": float(os.getenv("EMBEDDING_MIN_SCORE", "0.82")),
        "sync_interval_minutes": int(os.getenv("SYNC_INTERVAL_MINUTES", "10")),
    }
