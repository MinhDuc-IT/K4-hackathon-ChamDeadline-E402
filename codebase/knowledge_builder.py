import json
from pathlib import Path
from typing import Any


def build_knowledge(dataset_path: Path) -> list[dict[str, Any]]:
    payload = json.loads(dataset_path.read_text(encoding="utf-8"))
    threads = payload.get("threads", [])
    items: list[dict[str, Any]] = []

    for thread in threads:
        messages = thread.get("messages", [])
        if len(messages) < 2:
            continue

        question_message = messages[0]
        thread_title = (thread.get("title") or "").strip()
        original_question = question_message.get("content", "").strip()
        question = thread_title or original_question
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
                    "original_question": original_question,
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


def main() -> None:
    base_dir = Path(__file__).resolve().parent
    dataset_path = (base_dir / "../discord_dataset_with_ids.json").resolve()
    output_path = base_dir / "knowledge.json"

    knowledge = build_knowledge(dataset_path)
    output_path.write_text(
        json.dumps(knowledge, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"Built {len(knowledge)} knowledge items at {output_path}")


if __name__ == "__main__":
    main()
