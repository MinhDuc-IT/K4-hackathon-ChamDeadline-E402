import os
import json
import discord
from datetime import timedelta, timezone
from src import config

# Danh sách ID các kênh cần được index dữ liệu
TARGET_CHANNEL_IDS = [
    1532551992906485760, # thong-bao
    1532552021436137592, # tai-nguyen
    1532333267292782674, # hoi-dap
    1532333376806195310, # chia-se
    1532333595727888474  # bai-hoc
]

# ID của Role MOD trên Discord server
MOD_ROLE_ID = 1532584932386537583

def is_mod_member(member: discord.Member) -> bool:
    """
    Kiểm tra xem một thành viên có Role MOD hay không.
    """
    if not hasattr(member, 'roles'):
        return False
    return any(role.id == MOD_ROLE_ID for role in member.roles)

async def process_text_channel(channel: discord.TextChannel, documents: list):
    print(f"Đang xử lý Kênh Văn bản (Text Channel): {channel.name}")
    try:
        # Duyệt qua các tin nhắn lịch sử (tối đa 1000 tin để tránh API Rate Limit)
        async for message in channel.history(limit=1000):
            if message.author.bot or not message.content.strip():
                continue

            # Kiểm tra Role MOD của tác giả
            author_is_mod = False
            if isinstance(message.author, discord.Member):
                author_is_mod = is_mod_member(message.author)
                
            # Chuyển đổi múi giờ sang Việt Nam (GMT+7)
            vietnam_tz = timezone(timedelta(hours=7))
            created_at_vn = message.created_at.astimezone(vietnam_tz).strftime("%H:%M ngày %d/%m/%Y")
            
            documents.append({
                "text": message.content,
                "channel": channel.name,
                "thread": "",
                "url": message.jump_url,
                "author": str(message.author.display_name if hasattr(message.author, 'display_name') else message.author),
                "is_mod": author_is_mod,
                "message_id": str(message.id),
                "created_at": created_at_vn
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
            thread_messages = []
            first_message_url = ""
            first_message_author = ""
            first_message_is_mod = False
            
            # oldest_first=True để lấy tin nhắn theo thứ tự thời gian (từ cũ đến mới)
            async for message in thread.history(limit=100, oldest_first=True):
                if message.author.bot or not message.content.strip():
                    continue
                    
                if not first_message_url:
                    first_message_url = message.jump_url
                    first_message_author = str(message.author.display_name if hasattr(message.author, 'display_name') else message.author)
                    if isinstance(message.author, discord.Member):
                        first_message_is_mod = is_mod_member(message.author)
                    
                # Chuyển đổi múi giờ sang Việt Nam (GMT+7)
                vietnam_tz = timezone(timedelta(hours=7))
                created_at_vn = message.created_at.astimezone(vietnam_tz).strftime("%H:%M ngày %d/%m/%Y")
                author_name = str(message.author.display_name if hasattr(message.author, 'display_name') else message.author)

                # Đánh dấu [MOD] nếu tác giả có Role MOD
                if isinstance(message.author, discord.Member) and is_mod_member(message.author):
                    author_name = f"[MOD] {author_name}"

                # Format tin nhắn kèm tác giả và thời gian
                thread_messages.append(f"{author_name} ({created_at_vn}): {message.content}")

            if not thread_messages:
                continue
                
            combined_text = "\n\n".join(thread_messages)
            
            # Xác định nếu luồng có ít nhất 1 câu trả lời từ MOD
            has_mod_reply = any("[MOD]" in msg for msg in thread_messages)
            
            documents.append({
                "text": combined_text,
                "channel": channel.name,
                "thread": thread.name,
                "url": first_message_url if first_message_url else thread.jump_url,
                "author": "Nhiều người" if len(thread_messages) > 1 else first_message_author,
                "is_mod": first_message_is_mod or has_mod_reply,
                "message_id": str(thread.id),
                "created_at": ""  # Thời gian đã được nhúng vào trong text của từng reply
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
    
    # Đọc dữ liệu cũ (nếu có) để so sánh
    old_documents = []
    old_message_ids = set()
    data_path = "data/discord/documents.json"
    if os.path.exists(data_path):
        try:
            with open(data_path, "r", encoding="utf-8") as f:
                old_documents = json.load(f)
                old_message_ids = {doc.get("message_id") for doc in old_documents}
        except Exception:
            pass
    
    documents = []
    channel_stats = {}  # Thống kê theo từng kênh
    
    for channel in guild.channels:
        # Kiểm tra xem ID kênh có nằm trong danh sách mục tiêu không
        if channel.id in TARGET_CHANNEL_IDS:
            before_count = len(documents)
            if isinstance(channel, discord.TextChannel):
                await process_text_channel(channel, documents)
            elif isinstance(channel, discord.ForumChannel):
                await process_forum_channel(channel, documents)
            channel_stats[channel.name] = len(documents) - before_count
    
    # Debug: So sánh dữ liệu cũ và mới
    new_message_ids = {doc.get("message_id") for doc in documents}
    added = new_message_ids - old_message_ids    # Tin nhắn mới hoàn toàn
    removed = old_message_ids - new_message_ids  # Tin nhắn đã bị xóa
    unchanged = new_message_ids & old_message_ids  # Tin nhắn giữ nguyên
    
    print(f"\n[DEBUG] 📊 Thống kê thu thập dữ liệu:")
    print(f"  - Dữ liệu CŨ: {len(old_documents)} tin nhắn")
    print(f"  - Dữ liệu MỚI: {len(documents)} tin nhắn")
    print(f"  - Giữ nguyên: {len(unchanged)} | Thêm mới: {len(added)} | Đã xóa: {len(removed)}")
    print(f"  - Theo kênh:")
    for ch_name, count in channel_stats.items():
        print(f"    • {ch_name}: {count} tin nhắn")
                
    os.makedirs("data/discord", exist_ok=True)
    with open(data_path, "w", encoding="utf-8") as f:
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
