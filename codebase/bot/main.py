from __future__ import annotations

import asyncio
import os

import discord
from discord import app_commands
from dotenv import load_dotenv

from bot.commands import register_commands
from config.settings import BASE_DIR, load_runtime_settings
from reasoning.answer import answer_question
from reasoning.llm import LLMClient
from retrieval.embeddings import EmbeddingModel
from store.discord_history import DiscordHistoryStore

load_dotenv(BASE_DIR / ".env")

_settings = load_runtime_settings()
channel_ids = _settings["channel_ids"]
history_limit = _settings["history_limit"]
embedding_model_name = _settings["embedding_model_name"]
min_similarity = _settings["min_similarity"]
sync_interval_minutes = _settings["sync_interval_minutes"]

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

register_commands(
    tree,
    channel_ids=channel_ids,
    history_store=history_store,
    llm_client=llm_client,
    min_similarity=min_similarity,
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

    history_store.load_cache()
    print("Running startup sync...")
    await history_store.sync()

    if not _periodic_sync_started:
        _periodic_sync_started = True
        client.loop.create_task(periodic_sync(), name="periodic_sync")


def main() -> None:
    token = os.getenv("DISCORD_BOT_TOKEN")
    if not token:
        raise RuntimeError("Missing DISCORD_BOT_TOKEN in .env")
    if not channel_ids:
        raise RuntimeError("Missing DISCORD_SEARCH_CHANNEL_IDS in .env")
    client.run(token)


if __name__ == "__main__":
    main()
