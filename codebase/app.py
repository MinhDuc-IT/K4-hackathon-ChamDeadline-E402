"""Thin entrypoint — re-exports runtime symbols for `python app.py` and benchmarks."""

from bot.main import (
    LLMClient,
    answer_question,
    channel_ids,
    client,
    embedding_model,
    history_limit,
    history_store,
    llm_client,
    main,
    min_similarity,
    sync_interval_minutes,
    tree,
)

__all__ = [
    "LLMClient",
    "answer_question",
    "channel_ids",
    "client",
    "embedding_model",
    "history_limit",
    "history_store",
    "llm_client",
    "main",
    "min_similarity",
    "sync_interval_minutes",
    "tree",
]


if __name__ == "__main__":
    main()
