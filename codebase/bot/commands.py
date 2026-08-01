from __future__ import annotations

from typing import TYPE_CHECKING

import discord
from discord import app_commands

from reasoning.answer import answer_question

if TYPE_CHECKING:
    from reasoning.llm import LLMClient
    from store.discord_history import DiscordHistoryStore


def register_commands(
    tree: app_commands.CommandTree,
    *,
    channel_ids: list[int],
    history_store: DiscordHistoryStore,
    llm_client: LLMClient,
    min_similarity: float,
) -> None:
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
