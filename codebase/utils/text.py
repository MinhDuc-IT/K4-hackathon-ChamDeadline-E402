import re
import unicodedata
from datetime import datetime, timezone
from typing import Any

from config.settings import VN_TZ


def parse_timestamp(value: str | None) -> datetime:
    if not value:
        return datetime.min.replace(tzinfo=timezone.utc)
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return datetime.min.replace(tzinfo=timezone.utc)


def format_chat_time(value: str | None) -> str:
    dt = parse_timestamp(value)
    if dt == datetime.min.replace(tzinfo=timezone.utc):
        return "không rõ thời gian"
    local = dt.astimezone(VN_TZ)
    return local.strftime("%H:%M ngày %d/%m/%Y")


def format_channel_label(item: dict[str, Any]) -> str:
    channel = item.get("channel_name") or "không rõ kênh"
    thread_name = item.get("thread_name")
    if thread_name:
        return f"#{channel} / {thread_name}"
    return f"#{channel}"


def format_sources(candidates: list[dict[str, Any]]) -> str:
    lines = []
    for item in candidates:
        author = item.get("source_author") or "Không rõ"
        channel = format_channel_label(item)
        when = format_chat_time(item.get("timestamp"))
        source_url = item.get("source_url") or "không có link"
        lines.append(
            f"- {author} đã chat ở kênh {channel} lúc {when}\n  {source_url}"
        )
        question_context = (item.get("question_context") or "").strip()
        if question_context:
            short_q = question_context.replace("\n", " ")
            if len(short_q) > 120:
                short_q = short_q[:117] + "..."
            lines.append(f"  (trả lời cho: {short_q})")
    return "\n".join(lines)


def clip_text(value: str, limit: int) -> str:
    value = value.strip()
    if len(value) <= limit:
        return value
    return value[: max(limit - 3, 0)] + "..."


def normalize_vi_text(value: str) -> str:
    """Normalize Vietnamese text for intent detection and lexical retrieval."""

    text = unicodedata.normalize("NFD", value.lower())
    text = "".join(ch for ch in text if unicodedata.category(ch) != "Mn")
    text = text.replace("đ", "d")
    text = re.sub(r"[^a-z0-9_./:+-]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def has_any(text: str, terms: tuple[str, ...]) -> bool:
    return any(term in text for term in terms)


def has_all(text: str, terms: tuple[str, ...]) -> bool:
    return all(term in text for term in terms)
