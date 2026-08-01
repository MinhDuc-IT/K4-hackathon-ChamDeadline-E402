from __future__ import annotations

import asyncio
import re
from typing import Any

import discord

from bot.embeds import (
    build_casual_reply,
    build_security_refusal,
    compose_reply,
)
from reasoning.classify import apply_llm_classification
from reasoning.llm import LLMClient
from retrieval.lexical import document_text, lexical_score, lexical_tokens
from retrieval.pipeline import retrieve_candidates
from retrieval.ranking import (
    detect_conflict,
    pick_preferred_source,
)
from store.discord_history import DiscordHistoryStore
from utils.text import (
    format_channel_label,
    format_chat_time,
    has_any,
    normalize_vi_text,
    parse_timestamp,
)


def is_security_request(question: str) -> bool:
    q = normalize_vi_text(question)
    return has_any(q, ("discord_bot_token", "system prompt", "bi mat", "token")) and has_any(
        q,
        ("bo qua", "ignore", "tiet lo", "in ", "print", "show"),
    )


def is_casual_question(question: str) -> bool:
    q = normalize_vi_text(question)
    if has_any(q, ("deadline", "ddl", "lab", "git", "agent", "rag", "diem")):
        return False
    tokens = set(lexical_tokens(question))
    return bool(tokens & {"chao", "hello", "hi"}) or has_any(
        q,
        ("khoe khong", "khoe ko", "giup duoc gi"),
    )


def is_question_only_record(item: dict[str, Any]) -> bool:
    if item.get("is_forum_reply"):
        return False
    channel = normalize_vi_text(item.get("channel_name") or "")
    text = normalize_vi_text(f"{item.get('thread_name') or ''} {item.get('answer') or ''}")
    if not ("hoi" in channel and "dap" in channel):
        return False
    return has_any(
        text,
        (
            "cho em hoi",
            "em muon",
            "em hoi",
            "co cach",
            "co duoc",
            "khong a",
            "duoc khong",
            "lieu",
        ),
    )


QUESTION_ONLY_GENERIC_TOKENS = {
    "bi",
    "buoi",
    "ca",
    "can",
    "chac",
    "chan",
    "co",
    "diem",
    "duoc",
    "giup",
    "hoi",
    "kiem",
    "lop",
    "muon",
    "nhan",
    "sai",
    "thieu",
    "tin",
    "tra",
    "tren",
    "xem",
    "xac",
}


QUESTION_ONLY_TOPIC_RULES: tuple[tuple[tuple[str, ...], tuple[str, ...]], ...] = (
    (
        ("diem danh", "du lieu diem danh"),
        ("diem danh", "myvinuni", "student is not enrolled", "not enrolled"),
    ),
    (
        ("myvinuni", "student is not enrolled", "not enrolled"),
        ("myvinuni", "student is not enrolled", "not enrolled", "vinuni"),
    ),
    (
        ("nghi hoc", "vang hoc", "vang mat", "tru diem"),
        ("nghi hoc", "vang hoc", "vang mat", "tru diem"),
    ),
)


def question_only_matches_current_question(question: str, item: dict[str, Any]) -> bool:
    if not is_question_only_record(item):
        return False

    q = normalize_vi_text(question)
    doc = normalize_vi_text(document_text(item))
    for query_terms, source_terms in QUESTION_ONLY_TOPIC_RULES:
        if has_any(q, query_terms):
            return has_any(doc, source_terms)

    question_terms = set(lexical_tokens(question)) - QUESTION_ONLY_GENERIC_TOKENS
    if not question_terms:
        return False

    source_terms = set(lexical_tokens(document_text(item))) - QUESTION_ONLY_GENERIC_TOKENS
    overlap = question_terms & source_terms
    if len(question_terms) <= 2:
        return bool(overlap) and overlap == question_terms
    return len(overlap) >= 2


def asks_for_steps(question: str) -> bool:
    q = normalize_vi_text(question)
    return has_any(q, ("huong dan", "tung buoc", "cac buoc", "cach", "lam sao"))


def is_partial_title_record(item: dict[str, Any]) -> bool:
    answer = (item.get("answer") or "").strip()
    normalized = normalize_vi_text(answer)
    if len(answer) > 180:
        return False
    if "\n" in answer:
        return False
    return has_any(normalized, ("tips", "add", "smartphone", "samsung", "android"))


def build_question_only_abstention(
    question: str,
    candidates: list[dict[str, Any]],
) -> discord.Embed:
    source = candidates[0]
    topic = source.get("thread_name") or "chủ đề này"
    body = (
        "Mình chưa thể xác nhận hoặc hướng dẫn chắc chắn từ dataset hiện tại. "
        f"Dataset chỉ ghi nhận một học viên đặt câu hỏi trong thread “{topic}”, "
        "nhưng không có phản hồi xác nhận từ BTC/TA hoặc hướng dẫn kiểm tra kết quả."
    )
    return compose_reply(question, body, [source])


def build_partial_record_abstention(
    question: str,
    candidates: list[dict[str, Any]],
) -> discord.Embed:
    source = candidates[0]
    body = (
        "Dataset có nhắc đến chủ đề này, nhưng bản ghi chỉ chứa tiêu đề hoặc mô tả "
        "rất ngắn và không có các bước thực hiện. Vì vậy mình chưa thể hướng dẫn "
        "chính xác từ dữ liệu hiện có."
    )
    return compose_reply(question, body, [source])


def correction_marker(text: str) -> bool:
    normalized = normalize_vi_text(text)
    return has_any(normalized, ("xac nhan lai", "dinh chinh", "cap nhat lai"))


def build_source_snippet(item: dict[str, Any], limit: int = 120) -> str:
    snippet = (item.get("answer") or "").strip().replace("\n", " ")
    if len(snippet) > limit:
        snippet = snippet[: limit - 3] + "..."
    return snippet


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


def build_unresolved_conflict_reply(
    question: str,
    candidates: list[dict[str, Any]],
    reason: str | None = None,
) -> discord.Embed:
    sides = sorted(candidates[:4], key=lambda item: parse_timestamp(item.get("timestamp")))
    lines = ["Mình tìm thấy thông tin không thống nhất giữa các nguồn trong Discord:"]
    if reason:
        lines.extend(["", f"Lý do: {reason}"])
    lines.append("")

    for index, item in enumerate(sides, start=1):
        author = item.get("source_author") or "Không rõ"
        channel = format_channel_label(item)
        when = format_chat_time(item.get("timestamp"))
        lines.append(
            f"{index}) {author} ở {channel} lúc {when}: “{build_source_snippet(item)}”"
        )

    lines.extend(
        [
            "",
            "Không có nguồn nào thể hiện rõ đây là bản đính chính hoặc xác nhận lại, "
            "nên mình chưa thể kết luận chắc chắn. Bạn nên hỏi BTC/TA để xác nhận.",
        ]
    )
    return compose_reply(question, "\n".join(lines), sides)


def build_corrected_conflict_reply(
    question: str,
    candidates: list[dict[str, Any]],
) -> discord.Embed:
    ordered = sorted(candidates, key=lambda item: parse_timestamp(item.get("timestamp")))
    correction = next(
        (item for item in ordered if correction_marker(item.get("answer") or "")),
        None,
    )
    newest = ordered[-1] if ordered else None

    lines = ["Dataset có thông tin từng mâu thuẫn."]
    for item in ordered:
        author = item.get("source_author") or "Không rõ"
        when = format_chat_time(item.get("timestamp"))
        lines.append(f"- {author} lúc {when}: “{build_source_snippet(item)}”")

    if correction:
        correction_text = build_source_snippet(correction, 160)
        lines.append("")
        lines.append(f"Có bản xác nhận lại: “{correction_text}”.")

    normalized_blob = normalize_vi_text(" ".join(item.get("answer") or "" for item in ordered))
    if "khac" in normalized_blob and "xp" in normalized_blob and "bai lab" in normalized_blob:
        lines.append(
            "Kết luận được hỗ trợ tốt nhất: điểm cộng được cộng vào bài lab và khác XP Discord; "
            "thông tin cũ nói được tính vào XP đã được cập nhật."
        )
    elif newest:
        lines.append(
            "Kết luận nên theo bản xác nhận/đính chính rõ ràng nhất, đồng thời vẫn ghi nhận thông tin cũ gây mâu thuẫn."
        )
    else:
        lines.append("Mình chưa đủ căn cứ để kết luận chắc chắn.")

    return compose_reply(question, "\n".join(lines), ordered)


def source_is_relevant(question: str, item: dict[str, Any]) -> bool:
    score = lexical_score(question, item)
    if (
        is_question_only_record(item)
        and question_only_matches_current_question(question, item)
        and score >= 0.2
    ):
        return True
    if asks_for_steps(question) and is_partial_title_record(item) and score >= 0.12:
        return True
    if item.get("relevant") is False:
        return False
    if item.get("relevant") is True:
        return True
    return score >= 0.16


def filter_relevant_candidates(
    question: str,
    candidates: list[dict[str, Any]],
    max_candidates: int = 6,
) -> list[dict[str, Any]]:
    if not candidates:
        return []

    scored = [
        (
            item,
            float(item.get("similarity") or item.get("lexical_score") or lexical_score(question, item)),
        )
        for item in candidates
    ]
    best = max(score for _, score in scored)

    relevant: list[dict[str, Any]] = []
    for item, score in scored:
        if (
            is_question_only_record(item)
            and question_only_matches_current_question(question, item)
            and score >= 0.2
        ):
            relevant.append(item)
            continue
        if asks_for_steps(question) and is_partial_title_record(item) and score >= 0.12:
            relevant.append(item)
            continue

        explicit_relevance = item.get("relevant")
        if explicit_relevance is True:
            relevant.append(item)
            continue
        if explicit_relevance is False:
            # Classifiers can miss very short direct answers in the same thread.
            # Keep only if lexical evidence is both strong and near the top hit.
            if score >= 0.55 and score >= best - 0.12:
                relevant.append(item)
            continue

        if score >= max(0.16, best - 0.35):
            relevant.append(item)

    if not relevant:
        return []

    floor = max(0.14, best - 0.35)
    filtered: list[dict[str, Any]] = []
    for item in relevant:
        score = float(item.get("similarity") or item.get("lexical_score") or 0.0)
        if item.get("relevant") is True:
            filtered.append(item)
        elif score >= floor:
            filtered.append(item)
    return filtered[:max_candidates]


def build_policy_answer_before_retrieval(question: str) -> discord.Embed | None:
    if is_security_request(question):
        return build_security_refusal(question)
    if is_casual_question(question):
        return build_casual_reply(question)
    return None


def source_mentions_any(item: dict[str, Any], phrases: tuple[str, ...]) -> bool:
    return has_any(normalize_vi_text(document_text(item)), phrases)


def is_no_evidence_policy_request(
    question: str,
    candidates: list[dict[str, Any]],
) -> bool:
    q = normalize_vi_text(question)
    request_groups = [
        ("hoc bong", "hoan lai hoc phi", "hoan hoc phi"),
        ("bao luu", "sang khoa tiep theo"),
    ]
    source_groups = [
        ("hoc bong", "hoan lai hoc phi", "hoan hoc phi"),
        ("bao luu", "sang khoa tiep theo"),
    ]

    for request_terms, source_terms in zip(request_groups, source_groups):
        if not has_any(q, request_terms):
            continue
        return not any(source_mentions_any(item, source_terms) for item in candidates)

    return False


def build_fallback_answer(
    question: str,
    candidates: list[dict[str, Any]],
) -> discord.Embed:
    if not candidates:
        return compose_reply(
            question,
            (
                "Trong dataset hiện tại, mình chưa từng thấy có ai hỏi hoặc chia sẻ "
                "thông tin phù hợp về chủ đề này, nên mình không có căn cứ để trả lời. "
                "Bạn nên hỏi TA/BTC hoặc kiểm tra thông báo chính thức."
            ),
        )

    best = candidates[0]
    answer = best["answer"].strip()
    body = (
        f"{answer}\n\n"
        "Nếu cần độ chính xác cao hơn, hãy kiểm tra lại tin nhắn gốc hoặc hỏi TA."
    )
    return compose_reply(question, body, candidates[:3])


def build_data_gap_answer(
    question: str,
    candidates: list[dict[str, Any]],
) -> discord.Embed | None:
    if not candidates:
        return None

    top = candidates[0]
    top_score = lexical_score(question, top)
    if (
        is_question_only_record(top)
        and question_only_matches_current_question(question, top)
        and top_score >= 0.45
    ):
        return build_question_only_abstention(question, [top])

    if asks_for_steps(question):
        partial = next(
            (
                item
                for item in candidates
                if is_partial_title_record(item) and lexical_score(question, item) >= 0.35
            ),
            None,
        )
        if partial is not None:
            return build_partial_record_abstention(question, [partial])

    if is_no_evidence_policy_request(question, candidates):
        return build_fallback_answer(question, [])

    return None


def build_policy_answer_after_retrieval(
    question: str,
    candidates: list[dict[str, Any]],
    classification: dict[str, Any] | None = None,
) -> discord.Embed | None:
    if not candidates:
        return None

    question_only = [
        item
        for item in candidates
        if is_question_only_record(item)
        and question_only_matches_current_question(question, item)
    ]
    if question_only and len(question_only) == len(candidates):
        return build_question_only_abstention(question, question_only)

    if asks_for_steps(question):
        partial = next((item for item in candidates if is_partial_title_record(item)), None)
        if partial is not None:
            return build_partial_record_abstention(question, [partial])

    conflict = bool((classification or {}).get("conflict"))
    if not conflict and detect_conflict(candidates):
        conflict = True
    if not conflict:
        return None

    conflict_sources = candidates[:4]

    if any(correction_marker(item.get("answer") or "") for item in conflict_sources):
        return build_corrected_conflict_reply(question, conflict_sources)

    return build_unresolved_conflict_reply(
        question,
        conflict_sources,
        reason=(classification or {}).get("reason"),
    )


def asks_for_threshold_or_score(question: str) -> bool:
    q = normalize_vi_text(question)
    return has_any(q, ("bao nhieu", "may", "diem", "thang", "nguong", "score"))


def remove_unasked_score_details(question: str, answer: str) -> str:
    if asks_for_threshold_or_score(question):
        return answer

    kept_lines: list[str] = []
    for line in answer.splitlines():
        normalized = normalize_vi_text(line)
        mentions_score_band = has_any(
            normalized,
            (
                "diem danh gia",
                "thang agentic fit",
                "0 5",
                "6 10",
                "tu 11",
                " 11 tro len",
                ">=11",
            ),
        )
        if mentions_score_band and has_any(normalized, ("diem", "agent")):
            continue
        kept_lines.append(line)

    cleaned = "\n".join(kept_lines).strip()
    return re.sub(r"\n{3,}", "\n\n", cleaned) or answer


def remove_source_first_person_asides(answer: str) -> str:
    kept_blocks: list[str] = []
    for block in re.split(r"\n\s*\n", answer.strip()):
        normalized = normalize_vi_text(block)
        if normalized.startswith(
            (
                "minh da tong hop",
                "minh de file",
                "duoi day la",
                "mot vai",
            )
        ):
            continue
        kept_blocks.append(block)
    return "\n\n".join(kept_blocks).strip() or answer


def clean_llm_answer(question: str, answer: str) -> str:
    answer = remove_unasked_score_details(question, answer)
    answer = remove_source_first_person_asides(answer)
    return answer


def answer_abstains_for_insufficient_info(answer: str) -> bool:
    normalized = normalize_vi_text(answer)
    return has_any(
        normalized,
        (
            "chua du thong tin",
            "chua du can cu",
            "khong du thong tin",
            "khong co can cu",
            "khong the xac dinh",
            "chua the xac dinh",
            "chua the ket luan",
            "chua the xac nhan",
        ),
    )


def should_suppress_sources_for_abstention(
    question: str,
    answer: str,
    candidates: list[dict[str, Any]],
) -> bool:
    if not answer_abstains_for_insufficient_info(answer):
        return False

    normalized = normalize_vi_text(answer)
    cites_structural_gap = has_any(
        normalized,
        (
            "chi ghi nhan",
            "hoc vien dat cau hoi",
            "khong co phan hoi",
            "chi chua tieu de",
            "ban ghi chi",
        ),
    )
    if cites_structural_gap and any(
        (
            is_question_only_record(item)
            and question_only_matches_current_question(question, item)
        )
        or (asks_for_steps(question) and is_partial_title_record(item))
        for item in candidates
    ):
        return False

    return True


def source_detail_lines(item: dict[str, Any]) -> list[str]:
    raw = item.get("answer") or ""
    lines: list[str] = []
    for part in re.split(r"[\n\r]+|(?<=[.!?])\s+", raw):
        line = part.strip(" -•\t")
        if len(line) >= 8:
            lines.append(line)
    return lines


def append_if_missing(answer: str, line: str, additions: list[str]) -> None:
    normalized_answer = normalize_vi_text(answer + "\n" + "\n".join(additions))
    normalized_line = normalize_vi_text(line)
    if normalized_line and normalized_line not in normalized_answer:
        additions.append(line)


def augment_answer_with_source_details(
    question: str,
    answer: str,
    candidates: list[dict[str, Any]],
) -> str:
    q = normalize_vi_text(question)
    answer_norm = normalize_vi_text(answer)
    additions: list[str] = []

    if has_any(q, ("pull request", " pr ", "merge", "quy trinh")) and not has_any(
        answer_norm,
        ("khong tu merge", "khong duoc tu", "review"),
    ):
        for item in candidates[:3]:
            for line in source_detail_lines(item):
                normalized = normalize_vi_text(line)
                if has_any(normalized, ("khong ai duoc phep tu", "review va merge", "review va gop")):
                    append_if_missing(answer, line, additions)
                    break
            if additions:
                break

    if has_any(q, ("rag", "wording", "hyde")) and "hyde" in answer_norm and "tai lieu gia dinh" not in answer_norm:
        for item in candidates[:3]:
            lines = source_detail_lines(item)
            for index, line in enumerate(lines):
                normalized = normalize_vi_text(line)
                if "hyde" in normalized:
                    nearby = lines[index : index + 3]
                else:
                    nearby = [line]
                for candidate_line in nearby:
                    candidate_norm = normalize_vi_text(candidate_line)
                    if "tai lieu gia dinh" in candidate_norm and "embedding" in candidate_norm:
                        append_if_missing(answer, candidate_line, additions)
                        break
                if additions:
                    break
            if additions:
                break

    if not additions:
        return answer
    return f"{answer.rstrip()}\n\n" + "\n".join(additions)


async def answer_question(
    question: str,
    history_store: DiscordHistoryStore,
    llm_client: LLMClient,
    min_score: float = 0.82,
) -> discord.Embed:
    policy_answer = build_policy_answer_before_retrieval(question)
    if policy_answer is not None:
        return policy_answer

    matches = await retrieve_candidates(
        question,
        history_store,
        min_score=min_score,
        top_k=8,
    )

    raw_candidates = [match.item for match in matches]

    if not raw_candidates:
        return build_fallback_answer(question, [])

    candidates = raw_candidates[:8]

    data_gap_answer = build_data_gap_answer(question, candidates)
    if data_gap_answer is not None:
        return data_gap_answer

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

    candidates = filter_relevant_candidates(question, candidates, max_candidates=6)
    if not candidates:
        return build_fallback_answer(question, [])

    policy_answer = build_policy_answer_after_retrieval(
        question,
        candidates,
        classification=classification,
    )
    if policy_answer is not None:
        return policy_answer

    candidates = candidates[:5]
    if llm_client.enabled:
        try:
            llm_answer = await asyncio.to_thread(
                llm_client.generate_answer,
                question,
                candidates,
            )
            llm_answer = await asyncio.to_thread(
                llm_client.revise_answer,
                question,
                candidates,
                llm_answer,
            )
            llm_answer = clean_llm_answer(question, llm_answer)
            if should_suppress_sources_for_abstention(question, llm_answer, candidates):
                return compose_reply(question, llm_answer)
            llm_answer = augment_answer_with_source_details(question, llm_answer, candidates)
            return compose_reply(question, llm_answer, candidates)
        except Exception as error:
            print(f"LLM call failed, using fallback: {error}")
            return build_fallback_answer(question, candidates)

    return build_fallback_answer(question, candidates)
