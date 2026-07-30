import os
import json
import discord
from src import config

# Danh sách các kênh cần được index dữ liệu
TARGET_CHANNELS = ["hỏi-đáp", "chia-sẻ", "bài-học"]

async def process_text_channel(channel: discord.TextChannel, documents: list):
    print(f"Đang xử lý Kênh Văn bản (Text Channel): {channel.name}")
    try:
        # Duyệt qua các tin nhắn lịch sử (tối đa 1000 tin để tránh API Rate Limit)
        async for message in channel.history(limit=1000):
            if message.author.bot or not message.content.strip():
                continue
                
            documents.append({
                "text": message.content,
                "channel": channel.name,
                "thread": "",
                "url": message.jump_url,
                "author": str(message.author),
                "message_id": str(message.id)
            })
    except Exception as e:
        print(f"Lỗi khi đọc kênh {channel.name}: {e}")

async def process_forum_channel(channel: discord.ForumChannel, documents: list):
    print(f"Đang xử lý Kênh Diễn đàn (Forum Channel): {channel.name}")
    try:
        threads = channel.threads
        async for thread in channel.archived_threads(limit=100):
            threads.append(thread)
            
        for thread in threads:
            async for message in thread.history(limit=100):
                if message.author.bot or not message.content.strip():
                    continue
                    
                documents.append({
                    "text": message.content,
                    "channel": channel.name,
                    "thread": thread.name,
                    "url": message.jump_url,
                    "author": str(message.author),
                    "message_id": str(message.id)
                })
    except Exception as e:
        print(f"Lỗi khi đọc kênh {channel.name}: {e}")

async def collect_data(client: discord.Client, guild_id: int):
    """
    Hàm thu thập dữ liệu có thể được gọi từ bot chính.
    """
    guild = client.get_guild(guild_id)
    if not guild:
        print("Không tìm thấy Server để thu thập dữ liệu.")
        return

    print("Bắt đầu thu thập dữ liệu từ Discord...")
    documents = []
    
    for channel in guild.channels:
        # Kiểm tra xem tên kênh có chứa một trong các từ khóa mục tiêu không (để bỏ qua Emoji ở đầu)
        if any(target in channel.name for target in TARGET_CHANNELS):
            if isinstance(channel, discord.TextChannel):
                await process_text_channel(channel, documents)
            elif isinstance(channel, discord.ForumChannel):
                await process_forum_channel(channel, documents)
                
    os.makedirs("data/discord", exist_ok=True)
    with open("data/discord/documents.json", "w", encoding="utf-8") as f:
        json.dump(documents, f, ensure_ascii=False, indent=2)
        
    print(f"Thu thập hoàn tất. Đã lưu {len(documents)} tin nhắn.")

# Giữ lại khả năng chạy độc lập
if __name__ == "__main__":
    intents = discord.Intents.default()
    intents.message_content = True
    client = discord.Client(intents=intents)

    @client.event
    async def on_ready():
        print(f'Đã đăng nhập thành công với tên {client.user}')
        if config.DISCORD_GUILD_ID:
            await collect_data(client, int(config.DISCORD_GUILD_ID))
        await client.close()

    if config.DISCORD_TOKEN:
        client.run(config.DISCORD_TOKEN)
    else:
        print("Vui lòng thiết lập biến DISCORD_TOKEN trong file .env")
