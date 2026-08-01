import discord

from utils.text import clip_text, format_sources


def compose_reply(
    question: str,
    body: str,
    candidates: list[dict] | None = None,
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


def build_security_refusal(question: str) -> discord.Embed:
    return compose_reply(
        question,
        (
            "Mình không thể bỏ qua hướng dẫn an toàn và không tiết lộ token, "
            "system prompt hay dữ liệu bí mật. Bạn có thể hỏi mình về các "
            "thông tin công khai trong dataset Discord."
        ),
    )


def build_casual_reply(question: str) -> discord.Embed:
    return compose_reply(
        question,
        "Chào bạn! Mình vẫn ổn và sẵn sàng hỗ trợ. Bạn đang muốn tìm thông tin gì trong server?",
    )
