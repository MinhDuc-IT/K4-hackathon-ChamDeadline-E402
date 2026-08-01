from __future__ import annotations

import asyncio
import json
from datetime import datetime, timezone
from typing import Any

import discord
import numpy as np

from config.settings import (
    CACHE_DIR,
    EMBEDDINGS_CACHE_PATH,
    MESSAGES_CACHE_PATH,
    META_CACHE_PATH,
)
from retrieval.embeddings import EmbeddingModel
from retrieval.ranking import SearchResult


def passage_text(item: dict[str, Any]) -> str:
    answer = (item.get("answer") or "").strip()
    question_context = (item.get("question_context") or "").strip()
    thread_name = (item.get("thread_name") or "").strip()

    if question_context:
        return f"Câu hỏi: {question_context}\nCâu trả lời: {answer}"
    if thread_name:
        return f"{thread_name}\n{answer}"
    return answer


class DiscordHistoryStore:
    def __init__(
        self,
        client: discord.Client,
        channel_ids: list[int],
        embedding_model: EmbeddingModel,
        history_limit: int = 100,
    ) -> None:
        self.client = client
        self.channel_ids = channel_ids
        self.embedding_model = embedding_model
        self.history_limit = history_limit
        self.items: list[dict[str, Any]] = []
        self.embeddings: np.ndarray = np.zeros((0, 1), dtype=np.float32)
        self.last_synced_at: str | None = None
        self._lock = asyncio.Lock()

    def load_cache(self) -> bool:
        if not MESSAGES_CACHE_PATH.exists():
            return False

        self.items = json.loads(MESSAGES_CACHE_PATH.read_text(encoding="utf-8"))
        if EMBEDDINGS_CACHE_PATH.exists():
            self.embeddings = np.load(EMBEDDINGS_CACHE_PATH)
        else:
            print("Messages cache exists without embeddings. Vector search disabled.")
            self.embeddings = np.zeros((len(self.items), 1), dtype=np.float32)

        if META_CACHE_PATH.exists():
            meta = json.loads(META_CACHE_PATH.read_text(encoding="utf-8"))
            self.last_synced_at = meta.get("last_synced_at")

        if len(self.items) != len(self.embeddings):
            print("Cache mismatch between messages and embeddings. Vector search disabled.")
            self.embeddings = np.zeros((len(self.items), 1), dtype=np.float32)

        print(f"Loaded cache: {len(self.items)} messages")
        return True

    def save_cache(self) -> None:
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        MESSAGES_CACHE_PATH.write_text(
            json.dumps(self.items, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        np.save(EMBEDDINGS_CACHE_PATH, self.embeddings)
        META_CACHE_PATH.write_text(
            json.dumps(
                {
                    "last_synced_at": self.last_synced_at,
                    "model": self.embedding_model.model_name,
                    "count": len(self.items),
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )

    async def collect_messages(self) -> list[dict[str, Any]]:
        items: list[dict[str, Any]] = []

        for channel_id in self.channel_ids:
            channel = self.client.get_channel(channel_id)
            if channel is None:
                try:
                    channel = await self.client.fetch_channel(channel_id)
                except Exception as error:
                    print(f"Cannot fetch channel {channel_id}: {error}")
                    continue

            if isinstance(channel, discord.TextChannel):
                await self._collect_text_channel(channel, items)
            elif isinstance(channel, discord.ForumChannel):
                await self._collect_forum_channel(channel, items)
            else:
                print(f"Skip unsupported channel type {channel_id}: {type(channel)}")

        return items

    async def _append_message(
        self,
        message: discord.Message,
        channel_name: str,
        items: list[dict[str, Any]],
        thread_name: str | None = None,
        question_context: str | None = None,
        is_forum_reply: bool = False,
        min_length: int = 12,
    ) -> None:
        content = (message.content or "").strip()
        if not content:
            return
        if message.author.bot:
            return
        if len(content) < min_length:
            return

        items.append(
            {
                "answer": content,
                "question_context": question_context,
                "channel_name": channel_name,
                "thread_name": thread_name,
                "channel_id": str(message.channel.id),
                "source_author": message.author.display_name,
                "source_message_id": str(message.id),
                "timestamp": message.created_at.isoformat(),
                "source_url": message.jump_url,
                "is_forum_reply": is_forum_reply,
            }
        )

    async def _collect_text_channel(
        self,
        channel: discord.TextChannel,
        items: list[dict[str, Any]],
    ) -> None:
        try:
            async for message in channel.history(limit=self.history_limit):
                await self._append_message(message, channel.name, items)
        except Exception as error:
            print(f"Cannot read history from #{channel.name}: {error}")

    async def _collect_forum_channel(
        self,
        channel: discord.ForumChannel,
        items: list[dict[str, Any]],
    ) -> None:
        try:
            threads = list(channel.threads)
            archived = [
                thread async for thread in channel.archived_threads(limit=50)
            ]
            all_threads = threads + archived
            # Mỗi thread lấy nhiều tin hơn để không miss reply.
            per_thread_limit = max(50, self.history_limit)

            for thread in all_threads:
                try:
                    messages = [
                        message
                        async for message in thread.history(
                            limit=per_thread_limit,
                            oldest_first=True,
                        )
                    ]
                    if not messages:
                        continue

                    starter = messages[0]
                    starter_content = (starter.content or "").strip()
                    question_context = "\n".join(
                        part
                        for part in [thread.name, starter_content]
                        if part
                    ).strip()

                    replies = messages[1:]
                    if replies:
                        # Index các câu trả lời kèm context câu hỏi của post.
                        for message in replies:
                            await self._append_message(
                                message,
                                channel.name,
                                items,
                                thread_name=thread.name,
                                question_context=question_context,
                                is_forum_reply=True,
                                min_length=5,
                            )
                    else:
                        # Chưa có reply: vẫn giữ post gốc để bot biết có câu hỏi tồn.
                        await self._append_message(
                            starter,
                            channel.name,
                            items,
                            thread_name=thread.name,
                            question_context=thread.name,
                            is_forum_reply=False,
                        )
                except Exception as error:
                    print(f"Cannot read forum thread {thread.name}: {error}")
        except Exception as error:
            print(f"Cannot read forum channel #{channel.name}: {error}")

    async def sync(self, force_reembed: bool = False) -> dict[str, int]:
        async with self._lock:
            fresh_items = await self.collect_messages()
            if not fresh_items:
                self.items = []
                self.embeddings = np.zeros((0, 1), dtype=np.float32)
                self.last_synced_at = datetime.now(timezone.utc).isoformat()
                self.save_cache()
                return {"total": 0, "new": 0, "reused": 0}

            old_by_id = {
                item["source_message_id"]: (item, self.embeddings[index])
                for index, item in enumerate(self.items)
                if len(self.embeddings) == len(self.items)
            }

            reused_vectors: list[np.ndarray] = []
            reused_items: list[dict[str, Any]] = []
            new_items: list[dict[str, Any]] = []

            for item in fresh_items:
                message_id = item["source_message_id"]
                if not force_reembed and message_id in old_by_id:
                    old_item, old_vector = old_by_id[message_id]
                    # Keep freshest metadata but reuse embedding if content unchanged.
                    if (
                        old_item.get("answer") == item.get("answer")
                        and old_item.get("question_context") == item.get("question_context")
                        and not force_reembed
                    ):
                        reused_items.append(item)
                        reused_vectors.append(old_vector)
                        continue
                new_items.append(item)

            new_vectors = np.zeros((0, 1), dtype=np.float32)
            if new_items:
                print(f"Embedding {len(new_items)} new/updated messages...")
                texts = [passage_text(item) for item in new_items]
                try:
                    new_vectors = await asyncio.to_thread(
                        self.embedding_model.embed_passages,
                        texts,
                    )
                except Exception as error:
                    print(f"Embedding failed, saving messages for lexical search only: {error}")
                    self.items = fresh_items
                    self.embeddings = np.zeros((len(self.items), 1), dtype=np.float32)
                    self.last_synced_at = datetime.now(timezone.utc).isoformat()
                    self.save_cache()
                    return {
                        "total": len(self.items),
                        "new": len(new_items),
                        "reused": len(reused_items),
                    }

            merged_items = reused_items + new_items
            if reused_vectors and new_items:
                merged_embeddings = np.vstack([np.vstack(reused_vectors), new_vectors])
            elif reused_vectors:
                merged_embeddings = np.vstack(reused_vectors)
            else:
                merged_embeddings = new_vectors

            self.items = merged_items
            self.embeddings = merged_embeddings.astype(np.float32)
            self.last_synced_at = datetime.now(timezone.utc).isoformat()
            self.save_cache()

            print(
                f"Sync done: total={len(self.items)} new={len(new_items)} "
                f"reused={len(reused_items)}"
            )
            return {
                "total": len(self.items),
                "new": len(new_items),
                "reused": len(reused_items),
            }

    async def search(
        self,
        query: str,
        top_k: int = 5,
        min_score: float = 0.82,
    ) -> list[SearchResult]:
        query = query.strip()
        if not query:
            return []
        if not self.items or len(self.embeddings) == 0:
            return []
        if self.embedding_model.load_error:
            return []

        query_vector = await asyncio.to_thread(self.embedding_model.embed_query, query)
        query_norm = np.linalg.norm(query_vector) + 1e-12
        passage_norms = np.linalg.norm(self.embeddings, axis=1, keepdims=True) + 1e-12
        scores = (self.embeddings / passage_norms) @ (query_vector / query_norm)

        ranked_indices = np.argsort(scores)[::-1]
        best_score = float(scores[ranked_indices[0]]) if len(ranked_indices) else 0.0
        relative_floor = best_score - 0.08

        results: list[SearchResult] = []
        for index in ranked_indices:
            score = float(scores[index])
            item = dict(self.items[int(index)])
            # Ưu tiên câu trả lời trong forum hơn chính post hỏi.
            if item.get("is_forum_reply"):
                score += 0.03
            if score < min_score or score < relative_floor:
                continue
            item["similarity"] = round(score, 4)
            results.append(SearchResult(item=item, score=score))
            if len(results) >= top_k:
                break

        results.sort(key=lambda result: result.score, reverse=True)
        return results[:top_k]
