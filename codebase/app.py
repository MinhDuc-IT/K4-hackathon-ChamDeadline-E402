import asyncio
import json
import os
import re
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import discord
import numpy as np
import requests
from discord import app_commands
from dotenv import load_dotenv
from fastembed import TextEmbedding


BASE_DIR = Path(__file__).resolve().parent
CACHE_DIR = BASE_DIR / "cache"
MESSAGES_CACHE_PATH = CACHE_DIR / "messages.json"
EMBEDDINGS_CACHE_PATH = CACHE_DIR / "embeddings.npy"
META_CACHE_PATH = CACHE_DIR / "meta.json"

SYSTEM_PROMPT = """Bạn là trợ lý Discord của khóa học.

Chỉ sử dụng thông tin trong KNOWLEDGE để trả lời câu hỏi.
Nếu KNOWLEDGE có thông tin mâu thuẫn, phải nói rõ là có xung đột nguồn và khuyên hỏi TA/BTC. Không tự chọn một bên.
Nếu thông tin không đủ chắc chắn, phải nói rõ là chưa đủ căn cứ và khuyên hỏi TA.
Ưu tiên nguồn BTC/TA/mentor và tin mới hơn khi không có mâu thuẫn cứng.
Trả lời ngắn gọn bằng tiếng Việt.
Chỉ viết phần câu trả lời nội dung. Không tự ghi nguồn, không ghi "Nguồn:", không gắn link — hệ thống sẽ gắn phần chat gốc phía dưới."""

VN_TZ = timezone(timedelta(hours=7))

DEFAULT_EMBEDDING_MODEL = "intfloat/multilingual-e5-large"

# Fallback heuristics khi LLM classify lỗi / chưa cấu hình.
AUTHORITY_KEYWORDS = (
    "btc",
    "ban to chuc",
    "ban tổ chức",
    "ta",
    "mentor",
    "coach",
    "admin",
    "mod",
    "giang vien",
    "giảng viên",
)

AFFIRM_MARKERS = (
    "duoc tinh",
    "được tính",
    "tinh vao",
    "tính vào",
    "co duoc",
    "có được",
    "van duoc",
    "vẫn được",
    "deu duoc",
    "đều được",
    "se duoc",
    "sẽ được",
    "dung roi",
    "đúng rồi",
    "la dung",
    "là đúng",
)

DENY_MARKERS = (
    "khong tinh",
    "không tính",
    "khong duoc",
    "không được",
    "khong con",
    "không còn",
    "khac diem",
    "khác điểm",
    "khac xp",
    "khác xp",
    "se khac",
    "sẽ khác",
    "la khac",
    "là khác",
    "xac nhan lai",
    "xác nhận lại",
    "khong phai",
    "không phải",
    "sai roi",
    "sai rồi",
)

CLASSIFY_SYSTEM_PROMPT = """Bạn là bộ phân loại nguồn cho trợ lý Discord khóa học.
Nhiệm vụ: đọc câu hỏi và các nguồn, rồi trả về ĐÚNG một JSON hợp lệ, không markdown.
Schema:
{
  "conflict": boolean,
  "reason": string,
  "preferred_source_message_id": string | null,
  "sources": [
    {
      "source_message_id": string,
      "polarity": "affirm" | "deny" | "neutral",
      "stance_summary": string
    }
  ]
}
Quy tắc:
- affirm: nguồn khẳng định/ủng hộ điều user hỏi theo chiều dương.
- deny: nguồn phủ định, nói khác, bác bỏ, hoặc xác nhận lại theo chiều ngược.
- neutral: không đủ để kết luận về câu hỏi.
- conflict=true khi có ít nhất một affirm và một deny cùng liên quan câu hỏi.
- preferred_source_message_id: chọn nguồn đáng tin hơn nếu phải gợi ý (ưu tiên BTC/TA/mentor và tin mới hơn), hoặc null nếu không chắc.
- Nếu một nguồn nói "BTC xác nhận lại" hoặc rõ ràng mới hơn và phủ định nguồn cũ, ưu tiên nguồn đó khi chọn preferred_source_message_id.
- Chỉ dùng thông tin trong nguồn được cung cấp."""


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


def passage_text(item: dict[str, Any]) -> str:
    answer = (item.get("answer") or "").strip()
    question_context = (item.get("question_context") or "").strip()
    thread_name = (item.get("thread_name") or "").strip()

    if question_context:
        return f"Câu hỏi: {question_context}\nCâu trả lời: {answer}"
    if thread_name:
        return f"{thread_name}\n{answer}"
    return answer


@dataclass
class SearchResult:
    item: dict[str, Any]
    score: float


def parse_timestamp(value: str | None) -> datetime:
    if not value:
        return datetime.min.replace(tzinfo=timezone.utc)
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return datetime.min.replace(tzinfo=timezone.utc)


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


def build_conflict_answer(
    question: str,
    candidates: list[dict[str, Any]],
    reason: str | None = None,
    preferred_source_message_id: str | None = None,
) -> discord.Embed:
    affirm = [item for item in candidates if item.get("polarity") == "affirm"]
    deny = [item for item in candidates if item.get("polarity") == "deny"]

    sides: list[dict[str, Any]] = []
    if affirm:
        sides.append(affirm[0])
    if deny:
        sides.append(deny[0])
    if len(sides) < 2:
        sides = candidates[:2]

    # Hiển thị theo thời gian tăng dần: cũ → mới.
    sides = sorted(sides, key=lambda item: parse_timestamp(item.get("timestamp")))

    lines = [
        "Mình tìm thấy thông tin không thống nhất giữa các nguồn trong Discord:",
        "",
    ]
    if reason:
        lines.append(f"Lý do: {reason}")
        lines.append("")

    for index, item in enumerate(sides, start=1):
        snippet = item["answer"].strip().replace("\n", " ")
        if len(snippet) > 180:
            snippet = snippet[:177] + "..."
        when = format_chat_time(item.get("timestamp"))
        author = item.get("source_author", "không rõ")
        channel = format_channel_label(item)
        stance = item.get("stance_summary")
        polarity = item.get("polarity")
        polarity_text = f" [{polarity}]" if polarity else ""
        extra = f" — {stance}" if stance else ""
        lines.append(
            f"{index}) {author}{polarity_text} ở {channel} lúc {when}: {snippet}{extra}"
        )

    preferred = pick_preferred_source(sides, preferred_source_message_id)
    preferred_snippet = preferred["answer"].strip().replace("\n", " ")
    if len(preferred_snippet) > 120:
        preferred_snippet = preferred_snippet[:117] + "..."

    lines.extend(
        [
            "",
            (
                f"Gợi ý tạm thời: nghiêng về tin của "
                f"{preferred.get('source_author')} "
                f"({format_chat_time(preferred.get('timestamp'))}): "
                f"\"{preferred_snippet}\". "
                "Vì còn mâu thuẫn nên mình chưa trả lời chắc chắn."
            ),
            "Bạn nên hỏi TA/BTC để xác nhận bản mới nhất.",
        ]
    )
    return compose_reply(question, "\n".join(lines), sides)


class EmbeddingModel:
    def __init__(self, model_name: str) -> None:
        self.model_name = model_name
        self._model: TextEmbedding | None = None

    @property
    def uses_e5_prefix(self) -> bool:
        return "e5" in self.model_name.lower()

    def load(self) -> None:
        if self._model is not None:
            return
        print(f"Loading embedding model: {self.model_name}")
        self._model = TextEmbedding(model_name=self.model_name)
        print("Embedding model ready")

    @property
    def model(self) -> TextEmbedding:
        self.load()
        assert self._model is not None
        return self._model

    def _prepare_query(self, query: str) -> str:
        if self.uses_e5_prefix:
            return f"query: {query}"
        return query

    def _prepare_passage(self, text: str) -> str:
        if self.uses_e5_prefix:
            return f"passage: {text}"
        return text

    def embed_query(self, query: str) -> np.ndarray:
        vector = next(self.model.embed([self._prepare_query(query)]))
        return np.asarray(vector, dtype=np.float32)

    def embed_passages(self, texts: list[str]) -> np.ndarray:
        if not texts:
            return np.zeros((0, 1), dtype=np.float32)
        prepared = [self._prepare_passage(text) for text in texts]
        vectors = list(self.model.embed(prepared))
        return np.asarray(vectors, dtype=np.float32)


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
        if not MESSAGES_CACHE_PATH.exists() or not EMBEDDINGS_CACHE_PATH.exists():
            return False

        self.items = json.loads(MESSAGES_CACHE_PATH.read_text(encoding="utf-8"))
        self.embeddings = np.load(EMBEDDINGS_CACHE_PATH)

        if META_CACHE_PATH.exists():
            meta = json.loads(META_CACHE_PATH.read_text(encoding="utf-8"))
            self.last_synced_at = meta.get("last_synced_at")

        if len(self.items) != len(self.embeddings):
            print("Cache mismatch between messages and embeddings. Will rebuild.")
            self.items = []
            self.embeddings = np.zeros((0, 1), dtype=np.float32)
            return False

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
                new_vectors = await asyncio.to_thread(
                    self.embedding_model.embed_passages,
                    texts,
                )

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


class LLMClient:
    def __init__(self) -> None:
        self.api_key = os.getenv("OPENAI_API_KEY") or os.getenv("LLM_API_KEY")
        self.base_url = os.getenv("LLM_BASE_URL", "").rstrip("/")
        self.model = os.getenv("LLM_MODEL", "")

    @property
    def enabled(self) -> bool:
        return bool(self.api_key and self.base_url and self.model)

    def _chat(self, system_prompt: str, user_prompt: str, temperature: float = 0.2) -> str:
        if not self.enabled:
            raise RuntimeError("LLM is not configured.")

        payload: dict[str, Any] = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        }
        # Một số model (gpt-5.x) không cho temperature tùy chỉnh.
        if not str(self.model).startswith("gpt-5"):
            payload["temperature"] = temperature

        response = requests.post(
            f"{self.base_url}/chat/completions",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            json=payload,
            timeout=45,
        )
        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"].strip()

    def generate_answer(self, question: str, candidates: list[dict[str, Any]]) -> str:
        knowledge_block = json.dumps(candidates, ensure_ascii=False, indent=2)
        return self._chat(
            SYSTEM_PROMPT,
            (
                f"QUESTION:\n{question}\n\n"
                f"KNOWLEDGE:\n{knowledge_block}\n\n"
                "Nếu không đủ căn cứ, hãy nói rằng chưa đủ thông tin và đề nghị hỏi TA."
            ),
            temperature=0.2,
        )

    def classify_sources(
        self,
        question: str,
        candidates: list[dict[str, Any]],
    ) -> dict[str, Any]:
        compact_sources = [
            {
                "source_message_id": item.get("source_message_id"),
                "source_author": item.get("source_author"),
                "channel_name": item.get("channel_name"),
                "thread_name": item.get("thread_name"),
                "timestamp": item.get("timestamp"),
                "similarity": item.get("similarity"),
                "answer": item.get("answer"),
            }
            for item in candidates
        ]
        raw = self._chat(
            CLASSIFY_SYSTEM_PROMPT,
            (
                f"QUESTION:\n{question}\n\n"
                f"SOURCES:\n{json.dumps(compact_sources, ensure_ascii=False, indent=2)}\n\n"
                "Trả về đúng một JSON theo schema đã cho."
            ),
            temperature=0.0,
        )
        return parse_llm_json(raw)


def parse_llm_json(raw: str) -> dict[str, Any]:
    text = raw.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    return json.loads(text)


def apply_llm_classification(
    candidates: list[dict[str, Any]],
    classification: dict[str, Any],
) -> list[dict[str, Any]]:
    by_id = {
        item.get("source_message_id"): item
        for item in classification.get("sources", [])
        if item.get("source_message_id")
    }
    enriched: list[dict[str, Any]] = []
    for item in candidates:
        cloned = dict(item)
        meta = by_id.get(item.get("source_message_id"), {})
        polarity = meta.get("polarity")
        if polarity not in {"affirm", "deny", "neutral"}:
            polarity = detect_polarity(item.get("answer") or "")
        cloned["polarity"] = polarity
        if meta.get("stance_summary"):
            cloned["stance_summary"] = meta["stance_summary"]
        enriched.append(cloned)
    return enriched


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


def compose_reply(
    question: str,
    body: str,
    candidates: list[dict[str, Any]] | None = None,
) -> discord.Embed:
    """Hiển thị câu hỏi ngay trên tin nhắn bot (không phụ thuộc popup used /ask)."""
    embed = discord.Embed(color=0x5865F2)
    embed.add_field(
        name="Câu hỏi",
        value=clip_text(question, 1024),
        inline=False,
    )
    embed.add_field(
        name="Trả lời",
        value=clip_text(body, 1024),
        inline=False,
    )
    if candidates:
        embed.add_field(
            name="Từ chat",
            value=clip_text(format_sources(candidates), 1024),
            inline=False,
        )
    return embed


def build_fallback_answer(
    question: str,
    candidates: list[dict[str, Any]],
) -> discord.Embed:
    if not candidates:
        return compose_reply(
            question,
            (
                "Mình chưa tìm thấy thông tin phù hợp trong lịch sử chat Discord hiện có.\n"
                "Bạn nên hỏi TA hoặc mentor để được xác nhận."
            ),
        )

    best = candidates[0]
    answer = best["answer"].strip()
    body = (
        f"{answer}\n\n"
        "Nếu cần độ chính xác cao hơn, hãy kiểm tra lại tin nhắn gốc hoặc hỏi TA."
    )
    return compose_reply(question, body, candidates[:3])


async def answer_question(
    question: str,
    history_store: DiscordHistoryStore,
    llm_client: LLMClient,
    min_score: float = 0.82,
) -> discord.Embed:
    matches = await history_store.search(question, top_k=8, min_score=min_score)
    raw_candidates = [match.item for match in matches]

    if not raw_candidates:
        return build_fallback_answer(question, [])

    # Rerank nhẹ bằng authority/recency trước khi đưa vào LLM classify.
    candidates = rerank_candidates(raw_candidates)[:6]
    classification: dict[str, Any] | None = None

    if llm_client.enabled:
        try:
            classification = await asyncio.to_thread(
                llm_client.classify_sources,
                question,
                candidates,
            )
            candidates = apply_llm_classification(candidates, classification)
            classify_log = (
                f"LLM classify: conflict={classification.get('conflict')} "
                f"preferred={classification.get('preferred_source_message_id')}"
            )
            print(classify_log.encode("ascii", errors="replace").decode("ascii"))
        except Exception as error:
            err_text = str(error).encode("ascii", errors="replace").decode("ascii")
            print(f"LLM classify failed, using marker fallback: {err_text}")
            classification = None

    conflict = False
    if classification is not None and "conflict" in classification:
        conflict = bool(classification.get("conflict"))
        # Safety net: nếu LLM nói không conflict nhưng polarities vẫn affirm+deny.
        if not conflict and detect_conflict(candidates):
            conflict = True
            print("Override: marker polarities still show conflict")
    else:
        conflict = detect_conflict(candidates)
        if conflict:
            print("Conflict detected by marker fallback")

    if conflict:
        return build_conflict_answer(
            question,
            candidates,
            reason=(classification or {}).get("reason"),
            preferred_source_message_id=(classification or {}).get(
                "preferred_source_message_id"
            ),
        )

    candidates = candidates[:5]
    if llm_client.enabled:
        try:
            llm_answer = await asyncio.to_thread(
                llm_client.generate_answer,
                question,
                candidates,
            )
            return compose_reply(question, llm_answer, candidates)
        except Exception as error:
            print(f"LLM call failed, using fallback: {error}")
            return build_fallback_answer(question, candidates)

    return build_fallback_answer(question, candidates)


load_dotenv(BASE_DIR / ".env")

channel_ids = parse_channel_ids(os.getenv("DISCORD_SEARCH_CHANNEL_IDS"))
history_limit = int(os.getenv("DISCORD_HISTORY_LIMIT", "100"))
embedding_model_name = os.getenv("EMBEDDING_MODEL", DEFAULT_EMBEDDING_MODEL)
min_similarity = float(os.getenv("EMBEDDING_MIN_SCORE", "0.82"))
sync_interval_minutes = int(os.getenv("SYNC_INTERVAL_MINUTES", "10"))
llm_client = LLMClient()
embedding_model = EmbeddingModel(embedding_model_name)

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True

client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)
history_store = DiscordHistoryStore(
    client=client,
    channel_ids=channel_ids,
    embedding_model=embedding_model,
    history_limit=history_limit,
)


_periodic_sync_started = False


async def periodic_sync() -> None:
    await client.wait_until_ready()
    while not client.is_closed():
        await asyncio.sleep(max(sync_interval_minutes, 1) * 60)
        try:
            print("Running periodic sync...")
            await history_store.sync()
        except Exception as error:
            print(f"Periodic sync failed: {error}")


@client.event
async def on_ready() -> None:
    global _periodic_sync_started

    guild_id = os.getenv("DISCORD_GUILD_ID")
    if guild_id:
        guild = discord.Object(id=int(guild_id))
        tree.copy_global_to(guild=guild)
        synced = await tree.sync(guild=guild)
        print(f"Synced {len(synced)} guild commands to {guild_id}")
    else:
        synced = await tree.sync()
        print(f"Synced {len(synced)} global commands")

    print(f"Logged in as {client.user}")
    print(f"Search channels: {channel_ids}")
    print(f"History limit per channel: {history_limit}")
    print(
        f"Retrieval: local embedding cache | min_score={min_similarity} | "
        f"sync_every={sync_interval_minutes}m"
    )

    embedding_model.load()
    history_store.load_cache()
    print("Running startup sync...")
    await history_store.sync()

    if not _periodic_sync_started:
        _periodic_sync_started = True
        client.loop.create_task(periodic_sync(), name="periodic_sync")


@tree.command(name="ask", description="Hỏi bot dựa trên lịch sử chat Discord đã sync")
@app_commands.describe(question="Câu hỏi bạn muốn bot tìm trong chat Discord")
async def ask(interaction: discord.Interaction, question: str) -> None:
    await interaction.response.defer(thinking=True)

    if not channel_ids:
        await interaction.followup.send(
            "Bot chưa được cấu hình DISCORD_SEARCH_CHANNEL_IDS trong .env."
        )
        return

    if not history_store.items:
        await interaction.followup.send(
            "Cache đang trống. Hãy chạy `/sync` rồi hỏi lại."
        )
        return

    answer_embed = await answer_question(
        question,
        history_store,
        llm_client,
        min_score=min_similarity,
    )
    await interaction.followup.send(embed=answer_embed)


@tree.command(name="sync", description="Đồng bộ lại history Discord và cập nhật embedding local")
async def sync(interaction: discord.Interaction) -> None:
    await interaction.response.defer(thinking=True)
    stats = await history_store.sync()
    await interaction.followup.send(
        "Sync xong.\n"
        f"- Tổng tin trong cache: {stats['total']}\n"
        f"- Tin mới/cập nhật đã embed: {stats['new']}\n"
        f"- Tin tái sử dụng embedding: {stats['reused']}\n"
        f"- Lúc sync: {history_store.last_synced_at}"
    )


def main() -> None:
    token = os.getenv("DISCORD_BOT_TOKEN")
    if not token:
        raise RuntimeError("Missing DISCORD_BOT_TOKEN in .env")
    if not channel_ids:
        raise RuntimeError("Missing DISCORD_SEARCH_CHANNEL_IDS in .env")
    client.run(token)


if __name__ == "__main__":
    main()
