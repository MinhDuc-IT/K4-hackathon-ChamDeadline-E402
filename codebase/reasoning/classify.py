from typing import Any

from retrieval.ranking import detect_polarity


def apply_llm_classification(
    candidates: list[dict[str, Any]],
    classification: dict[str, Any],
) -> list[dict[str, Any]]:
    def as_bool(value: Any) -> bool | None:
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            normalized = value.strip().lower()
            if normalized in {"true", "yes", "1", "relevant"}:
                return True
            if normalized in {"false", "no", "0", "irrelevant"}:
                return False
        return None

    by_id = {
        item.get("source_message_id"): item
        for item in classification.get("sources", [])
        if item.get("source_message_id")
    }
    preferred_id = str(classification.get("preferred_source_message_id") or "")
    enriched: list[dict[str, Any]] = []
    for item in candidates:
        cloned = dict(item)
        message_id = str(item.get("source_message_id") or "")
        meta = by_id.get(item.get("source_message_id"), {})
        polarity = meta.get("polarity")
        if polarity not in {"affirm", "deny", "neutral"}:
            polarity = detect_polarity(item.get("answer") or "")
        cloned["polarity"] = polarity
        if message_id and message_id == preferred_id:
            cloned["relevant"] = True
        elif "relevant" in meta:
            relevant = as_bool(meta.get("relevant"))
            if relevant is not None:
                cloned["relevant"] = relevant
        elif classification.get("sources"):
            cloned["relevant"] = False
        if meta.get("stance_summary"):
            cloned["stance_summary"] = meta["stance_summary"]
        enriched.append(cloned)
    return enriched
