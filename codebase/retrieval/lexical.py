import re
from typing import Any

from retrieval.ranking import SearchResult
from utils.text import has_any, normalize_vi_text

STOPWORDS = {
    "a",
    "anh",
    "ban",
    "bot",
    "cai",
    "cho",
    "co",
    "chuong",
    "cua",
    "du",
    "duoc",
    "em",
    "gi",
    "ha",
    "hay",
    "he",
    "hoi",
    "hoc",
    "khong",
    "khoa",
    "la",
    "lam",
    "minh",
    "mot",
    "nao",
    "neu",
    "nhung",
    "nhu",
    "o",
    "qua",
    "sang",
    "server",
    "theo",
    "thi",
    "the",
    "thong",
    "trinh",
    "trong",
    "tu",
    "va",
    "ve",
    "vien",
    "voi",
}

TOKEN_ALIASES: dict[str, tuple[str, ...]] = {
    "ddl": ("deadline", "han", "nop"),
    "deadline": ("han", "nop"),
    "day": ("ngay",),
    "d5": ("5", "ngay"),
    "faq": ("chatbot", "rag"),
    "topic": ("de", "tai", "chu", "de"),
    "pr": ("pull", "request"),
    "lt": ("ly", "thuyet"),
    "logger": ("log", "nhat", "ky"),
    "enrolled": ("not", "enrolled", "myvinuni"),
    "wording": ("dien", "dat", "khac"),
    "ranking": ("top",),
    "refund": ("hoan", "hoc", "phi"),
    "model": ("workflow", "bai", "toan"),
    "framework": ("workflow", "bai", "toan"),
    "samsung": ("smartphone", "android"),
    "dien": ("smartphone",),
    "thoai": ("smartphone",),
}


def lexical_tokens(value: str) -> list[str]:
    normalized = normalize_vi_text(value)
    raw_tokens = re.findall(r"[a-z0-9_./:+-]+", normalized)
    tokens: list[str] = []
    for token in raw_tokens:
        if len(token) <= 1 and not token.isdigit():
            continue
        if token in STOPWORDS:
            continue
        tokens.append(token)
        tokens.extend(TOKEN_ALIASES.get(token, ()))
    return tokens


def document_text(item: dict[str, Any]) -> str:
    return "\n".join(
        part
        for part in [
            item.get("channel_name"),
            item.get("thread_name"),
            item.get("question_context"),
            item.get("answer"),
        ]
        if part
    )


def lexical_score(query: str, item: dict[str, Any]) -> float:
    query_tokens = set(lexical_tokens(query))
    if not query_tokens:
        return 0.0

    doc = document_text(item)
    doc_normalized = normalize_vi_text(doc)
    doc_tokens = set(lexical_tokens(doc))
    overlap = query_tokens & doc_tokens
    score = len(overlap) / max(len(query_tokens), 1)

    normalized_query = normalize_vi_text(query)
    if normalized_query and normalized_query in doc_normalized:
        score += 0.35

    thread = normalize_vi_text(item.get("thread_name") or "")
    if thread:
        thread_hits = set(lexical_tokens(thread)) & query_tokens
        score += min(0.25, 0.08 * len(thread_hits))

    answer = normalize_vi_text(item.get("answer") or "")
    if has_any(normalized_query, ("deadline", "ddl", "han nop")) and has_any(
        answer,
        ("han nop", "deadline", "10:30"),
    ):
        score += 0.2
    if "xp" in query_tokens and "xp" in doc_tokens:
        score += 0.2
    if {"opencode", "codex"} & query_tokens:
        tool_tokens = {"opencode", "codex"} & query_tokens & doc_tokens
        if tool_tokens:
            score += 0.35
        elif {"opencode", "codex"} & doc_tokens:
            score -= 0.25
    if has_any(normalized_query, ("faq", "tra cuu")) and "agent" in query_tokens:
        if "chatbot" in doc_tokens and "rag" in doc_tokens:
            score += 0.45
        if has_any(doc_normalized, ("hybrid architecture", "user router chatbot agent human")):
            score += 0.35
    if has_any(normalized_query, ("model", "framework", "san pham ai")):
        if "bai toan kinh doanh" in doc_normalized:
            score += 0.45
        if "workflow hien tai" in doc_normalized and "bottleneck" in doc_normalized:
            score += 0.45
    if has_any(normalized_query, ("samsung", "dien thoai", "the hoc vien")) and has_any(
        doc_normalized,
        ("samsung", "smartphone", "android"),
    ):
        score += 0.7

    return round(score, 4)


def lexical_search(
    query: str,
    items: list[dict[str, Any]],
    top_k: int = 8,
    min_score: float = 0.12,
) -> list[SearchResult]:
    scored: list[SearchResult] = []
    for item in items:
        score = lexical_score(query, item)
        if score < min_score:
            continue
        enriched = dict(item)
        enriched["similarity"] = score
        enriched["lexical_score"] = score
        scored.append(SearchResult(item=enriched, score=score))

    scored.sort(key=lambda result: result.score, reverse=True)
    return scored[:top_k]


def merge_search_results(
    primary: list[SearchResult],
    secondary: list[SearchResult],
    top_k: int = 8,
) -> list[SearchResult]:
    by_id: dict[str, SearchResult] = {}
    for result in primary + secondary:
        message_id = result.item.get("source_message_id")
        if not message_id:
            continue
        old = by_id.get(message_id)
        if old is None or result.score > old.score:
            by_id[message_id] = result
    merged = list(by_id.values())
    merged.sort(key=lambda result: result.score, reverse=True)
    return merged[:top_k]
