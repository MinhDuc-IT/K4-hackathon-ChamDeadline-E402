import json
import os
import re
import unicodedata
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import discord
import requests
from discord import app_commands
from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parent
DEFAULT_DATASET_PATH = (BASE_DIR / "../discord_dataset_with_ids.json").resolve()
DEFAULT_KNOWLEDGE_PATH = BASE_DIR / "knowledge.json"
SYSTEM_PROMPT = """Ban la tro ly Discord cua khoa hoc.

Chi su dung thong tin trong KNOWLEDGE de tra loi cau hoi.
Neu thong tin khong du chac chan, phai noi ro la chua du can cu va khuyen hoi TA.
Tra loi ngan gon bang tieng Viet.
Neu tra loi duoc, phai kem nguon tom tat o cuoi cau tra loi."""


def normalize_text(value: str) -> str:
    decomposed = unicodedata.normalize("NFKD", value)
    without_accents = "".join(ch for ch in decomposed if not unicodedata.combining(ch))
    lowered = without_accents.lower()
    return re.sub(r"[^a-z0-9\s]", " ", lowered)


def tokenize(value: str) -> set[str]:
    return {token for token in normalize_text(value).split() if len(token) > 1}


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def save_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def build_knowledge(dataset_path: Path) -> list[dict[str, Any]]:
    dataset = load_json(dataset_path)
    items: list[dict[str, Any]] = []

    for thread in dataset.get("threads", []):
        messages = thread.get("messages", [])
        if len(messages) < 2:
            continue

        question_message = messages[0]
        question = question_message.get("content", "").strip()
        if not question:
            continue

        for answer_message in messages[1:]:
            answer = answer_message.get("content", "").strip()
            if not answer:
                continue

            author = answer_message.get("author", {})
            items.append(
                {
                    "question": question,
                    "answer": answer,
                    "thread_id": thread.get("thread_id"),
                    "thread_title": thread.get("title"),
                    "category": thread.get("category"),
                    "source_message_id": answer_message.get("message_id"),
                    "source_author": author.get("display_name"),
                    "source_role": author.get("role"),
                    "source_user_label": author.get("user_label"),
                    "timestamp": answer_message.get("timestamp"),
                    "source_url": None,
                }
            )

    return items


@dataclass
class SearchResult:
    item: dict[str, Any]
    score: float


class KnowledgeStore:
    def __init__(self, dataset_path: Path, knowledge_path: Path) -> None:
        self.dataset_path = dataset_path
        self.knowledge_path = knowledge_path
        self.items: list[dict[str, Any]] = []

    def ensure_loaded(self) -> None:
        if self.knowledge_path.exists():
            self.items = load_json(self.knowledge_path)
            return

        self.items = build_knowledge(self.dataset_path)
        save_json(self.knowledge_path, self.items)

    def search(self, query: str, top_k: int = 3) -> list[SearchResult]:
        query_tokens = tokenize(query)
        results: list[SearchResult] = []

        for item in self.items:
            question_tokens = tokenize(item["question"])
            answer_tokens = tokenize(item["answer"])
            combined_tokens = question_tokens | answer_tokens
            overlap = len(query_tokens & combined_tokens)
            if overlap == 0:
                continue

            trusted_bonus = 0.0
            role = (item.get("source_role") or "").lower()
            label = (item.get("source_user_label") or "").lower()
            if "coach" in label or "ta" in label or role in {"ta", "coach", "mentor"}:
                trusted_bonus = 1.5

            score = overlap + trusted_bonus
            results.append(SearchResult(item=item, score=score))

        results.sort(key=lambda result: result.score, reverse=True)
        return results[:top_k]


class LLMClient:
    def __init__(self) -> None:
        self.api_key = os.getenv("LLM_API_KEY")
        self.base_url = os.getenv("LLM_BASE_URL", "").rstrip("/")
        self.model = os.getenv("LLM_MODEL", "")

    @property
    def enabled(self) -> bool:
        return bool(self.api_key and self.base_url and self.model)

    def generate_answer(self, question: str, candidates: list[dict[str, Any]]) -> str:
        if not self.enabled:
            raise RuntimeError("LLM is not configured.")

        knowledge_block = json.dumps(candidates, ensure_ascii=False, indent=2)
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": (
                        f"QUESTION:\n{question}\n\n"
                        f"KNOWLEDGE:\n{knowledge_block}\n\n"
                        "Neu khong du can cu, hay noi rang chua du thong tin va de nghi hoi TA."
                    ),
                },
            ],
            "temperature": 0.2,
        }
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


def format_sources(candidates: list[dict[str, Any]]) -> str:
    lines = []
    for item in candidates:
        line = (
            f"- {item['thread_title']} | {item['source_author']} | "
            f"{item['timestamp']} | message_id={item['source_message_id']}"
        )
        lines.append(line)
    return "\n".join(lines)


def build_fallback_answer(question: str, candidates: list[dict[str, Any]]) -> str:
    if not candidates:
        return (
            "Mình chưa tìm thấy thông tin phù hợp trong dữ liệu hiện có.\n"
            "Bạn nên hỏi TA hoặc mentor để được xác nhận."
        )

    best = candidates[0]
    answer = best["answer"].strip()
    sources = format_sources(candidates)
    return (
        f"{answer}\n\n"
        f"Nguồn tham khảo:\n{sources}\n\n"
        "Neu can do chinh xac cao hon, hay kiem tra lai thread goc hoac hoi TA."
    )


async def answer_question(
    question: str,
    knowledge_store: KnowledgeStore,
    llm_client: LLMClient,
) -> str:
    knowledge_store.ensure_loaded()
    matches = knowledge_store.search(question, top_k=3)
    candidates = [match.item for match in matches]

    if not candidates:
        return build_fallback_answer(question, [])

    if llm_client.enabled:
        try:
            llm_answer = llm_client.generate_answer(question, candidates)
            return f"{llm_answer}\n\nNguồn tham khảo:\n{format_sources(candidates)}"
        except Exception:
            return build_fallback_answer(question, candidates)

    return build_fallback_answer(question, candidates)


def resolve_path(env_name: str, default_path: Path) -> Path:
    raw_value = os.getenv(env_name)
    if not raw_value:
        return default_path
    return (BASE_DIR / raw_value).resolve()


load_dotenv(BASE_DIR / ".env")

dataset_path = resolve_path("DATASET_PATH", DEFAULT_DATASET_PATH)
knowledge_path = resolve_path("KNOWLEDGE_PATH", DEFAULT_KNOWLEDGE_PATH)
knowledge_store = KnowledgeStore(dataset_path=dataset_path, knowledge_path=knowledge_path)
llm_client = LLMClient()

intents = discord.Intents.default()
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)


@client.event
async def on_ready() -> None:
    guild_id = os.getenv("DISCORD_GUILD_ID")
    if guild_id:
        guild = discord.Object(id=int(guild_id))
        synced = await tree.sync(guild=guild)
        print(f"Synced {len(synced)} guild commands to {guild_id}")
    else:
        synced = await tree.sync()
        print(f"Synced {len(synced)} global commands")

    print(f"Logged in as {client.user}")


@tree.command(name="ask", description="Hoi bot ve thong tin trong dataset")
@app_commands.describe(question="Cau hoi ban muon bot tim trong knowledge base")
async def ask(interaction: discord.Interaction, question: str) -> None:
    await interaction.response.defer(thinking=True)
    answer = await answer_question(question, knowledge_store, llm_client)
    await interaction.followup.send(answer[:1900])


def main() -> None:
    token = os.getenv("DISCORD_BOT_TOKEN")
    if not token:
        raise RuntimeError("Missing DISCORD_BOT_TOKEN in .env")
    client.run(token)


if __name__ == "__main__":
    main()
