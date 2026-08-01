import json
import os
import re
from typing import Any

import requests

from config.prompts import CLASSIFY_SYSTEM_PROMPT, REVISE_SYSTEM_PROMPT, SYSTEM_PROMPT


def parse_llm_json(raw: str) -> dict[str, Any]:
    text = raw.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    return json.loads(text)


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
                "Hãy trả lời bằng cách tổng hợp các nguồn relevant. "
                "Nếu nguồn trực tiếp chứa danh sách, file, lệnh, khoảng điểm, ngưỡng, "
                "hoặc quy tắc đi kèm cùng quy trình, hãy giữ đủ các chi tiết đó. "
                "Không đưa khoảng điểm/ngưỡng nếu câu hỏi không hỏi về điểm hoặc ngưỡng. "
                "Nếu không đủ căn cứ, hãy nói rằng chưa đủ thông tin và đề nghị hỏi TA."
            ),
            temperature=0.0,
        )

    def revise_answer(
        self,
        question: str,
        candidates: list[dict[str, Any]],
        draft_answer: str,
    ) -> str:
        knowledge_block = json.dumps(candidates, ensure_ascii=False, indent=2)
        return self._chat(
            REVISE_SYSTEM_PROMPT,
            (
                f"QUESTION:\n{question}\n\n"
                f"KNOWLEDGE:\n{knowledge_block}\n\n"
                f"DRAFT_ANSWER:\n{draft_answer}\n\n"
                "Hãy trả về bản trả lời cuối cùng đã sửa."
            ),
            temperature=0.0,
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
