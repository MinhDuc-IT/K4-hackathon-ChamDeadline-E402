from __future__ import annotations

from typing import TYPE_CHECKING

from retrieval.lexical import lexical_search, merge_search_results
from retrieval.ranking import SearchResult

if TYPE_CHECKING:
    from store.discord_history import DiscordHistoryStore


async def retrieve_candidates(
    question: str,
    history_store: DiscordHistoryStore,
    min_score: float,
    top_k: int = 8,
) -> list[SearchResult]:
    lexical_results = lexical_search(question, history_store.items, top_k=top_k)
    try:
        vector_results = await history_store.search(
            question,
            top_k=top_k,
            min_score=min_score,
        )
    except Exception as error:
        print(f"Vector search failed, using lexical fallback: {error}")
        return lexical_results
    return merge_search_results(vector_results, lexical_results, top_k=top_k)
