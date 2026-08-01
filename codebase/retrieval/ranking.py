from dataclasses import dataclass
from datetime import datetime
from typing import Any

from config.prompts import AFFIRM_MARKERS, AUTHORITY_KEYWORDS, DENY_MARKERS
from utils.text import parse_timestamp


@dataclass
class SearchResult:
    item: dict[str, Any]
    score: float


def authority_score(item: dict[str, Any]) -> float:
    author = (item.get("source_author") or "").lower()
    channel = (item.get("channel_name") or "").lower()
    text = f"{author} {channel}"
    score = 0.0
    for keyword in AUTHORITY_KEYWORDS:
        if keyword in text:
            score += 0.05
    # Stronger boost for explicit BTC mentions in content.
    content = (item.get("answer") or "").lower()
    if "btc" in content or "ban tổ chức" in content or "ban to chuc" in content:
        score += 0.08
    if "xác nhận lại" in content or "xac nhan lai" in content:
        score += 0.06
    return min(score, 0.2)


def detect_polarity(text: str) -> str:
    lowered = text.lower()
    affirm_hits = sum(1 for marker in AFFIRM_MARKERS if marker in lowered)
    deny_hits = sum(1 for marker in DENY_MARKERS if marker in lowered)

    if deny_hits > affirm_hits and deny_hits > 0:
        return "deny"
    if affirm_hits > deny_hits and affirm_hits > 0:
        return "affirm"
    if "khác" in lowered or "khac" in lowered:
        return "deny"
    return "neutral"


def rerank_candidates(candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if not candidates:
        return []

    timestamps = [parse_timestamp(item.get("timestamp")) for item in candidates]
    newest = max(timestamps)

    ranked: list[tuple[float, dict[str, Any]]] = []
    for item, timestamp in zip(candidates, timestamps):
        similarity = float(item.get("similarity") or 0.0)
        auth = authority_score(item)
        # Newer messages get a small boost; newest gets full boost.
        age_seconds = max((newest - timestamp).total_seconds(), 0.0)
        recency = max(0.0, 0.05 - min(age_seconds / (7 * 24 * 3600), 1.0) * 0.05)
        final_score = similarity + auth + recency
        enriched = dict(item)
        enriched["polarity"] = detect_polarity(item.get("answer") or "")
        enriched["authority_score"] = round(auth, 4)
        enriched["final_score"] = round(final_score, 4)
        ranked.append((final_score, enriched))

    ranked.sort(key=lambda pair: pair[0], reverse=True)
    return [item for _, item in ranked]


def detect_conflict(candidates: list[dict[str, Any]]) -> bool:
    if len(candidates) < 2:
        return False

    best = float(candidates[0].get("similarity") or 0.0)
    close_candidates = [
        item
        for item in candidates
        if float(item.get("similarity") or 0.0) >= best - 0.06
    ]
    polarities = {item.get("polarity") for item in close_candidates}
    return "affirm" in polarities and "deny" in polarities


def pick_preferred_source(
    sides: list[dict[str, Any]],
    preferred_source_message_id: str | None = None,
) -> dict[str, Any]:
    """Chọn nguồn gợi ý theo authority + recency; LLM preferred chỉ là tie-breaker."""

    def rank_key(item: dict[str, Any]) -> tuple[float, datetime]:
        return (authority_score(item), parse_timestamp(item.get("timestamp")))

    heuristic = max(sides, key=rank_key)
    if not preferred_source_message_id:
        return heuristic

    llm_pick = next(
        (
            item
            for item in sides
            if item.get("source_message_id") == preferred_source_message_id
        ),
        None,
    )
    if llm_pick is None:
        return heuristic

    h_auth, h_time = rank_key(heuristic)
    l_auth, l_time = rank_key(llm_pick)

    # Bỏ LLM preferred nếu yếu authority hơn, hoặc cùng authority nhưng cũ hơn.
    if l_auth < h_auth - 0.01:
        return heuristic
    if abs(l_auth - h_auth) <= 0.01 and l_time < h_time:
        return heuristic
    return llm_pick
