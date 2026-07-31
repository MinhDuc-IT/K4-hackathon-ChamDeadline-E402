import discord
import asyncio
from discord.ext import commands, tasks
from discord import app_commands
from src import config, rag, collector, ingest

class MyBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True # Đảm bảo quyền đọc tin nhắn được bật
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        # Đồng bộ (sync) các slash commands với Server (Guild) được chỉ định
        if config.DISCORD_GUILD_ID:
            guild = discord.Object(id=int(config.DISCORD_GUILD_ID))
            self.tree.copy_global_to(guild=guild)
            await self.tree.sync(guild=guild)
        else:
            await self.tree.sync()

bot = MyBot()

@tasks.loop(hours=24)
async def auto_update_knowledge():
    """
    Tác vụ chạy ngầm tự động cập nhật dữ liệu mỗi 24 giờ.
    """
    print("\n--- BẮT ĐẦU TỰ ĐỘNG CẬP NHẬT DỮ LIỆU ---")
    if not config.DISCORD_GUILD_ID:
        print("Lỗi: Không tìm thấy DISCORD_GUILD_ID, hủy cập nhật.")
        return
        
    try:
        # Bước 1: Thu thập tin nhắn mới nhất
        await collector.collect_data(bot, int(config.DISCORD_GUILD_ID))
        
        # Bước 2: Nạp dữ liệu vào FAISS index (chạy trong thread riêng để không block bot)
        await asyncio.to_thread(ingest.run_ingestion)
        
        print("--- HOÀN TẤT TỰ ĐỘNG CẬP NHẬT DỮ LIỆU ---\n")
    except Exception as e:
        print(f"Lỗi trong quá trình cập nhật tự động: {e}")

@auto_update_knowledge.before_loop
async def before_auto_update():
    # Đợi bot sẵn sàng hoàn toàn trước khi bắt đầu vòng lặp
    await bot.wait_until_ready()

@bot.event
async def on_ready():
    print(f'Đã đăng nhập thành công với tên {bot.user}')
    # Bắt đầu vòng lặp cập nhật tự động nếu chưa chạy
    if not auto_update_knowledge.is_running():
        auto_update_knowledge.start()

@bot.event
async def on_message(message: discord.Message):
    # Bỏ qua tin nhắn của chính bot hoặc các bot khác
    if message.author.bot:
        return

    # Kiểm tra xem bot có được tag (@BotName) hay không
    if bot.user in message.mentions:
        # Xóa chuỗi tag (@BotName) khỏi nội dung tin nhắn để lấy câu hỏi thực tế
        question = message.content.replace(f'<@{bot.user.id}>', '').strip()
        
        print(f"\n[DEBUG] 📩 Nhận câu hỏi từ {message.author}: {question}")
        
        if not question:
            await message.reply("Bạn cần hỏi gì đó sau khi tag tôi nhé!")
            return

        # Hiển thị trạng thái "đang gõ..."
        async with message.channel.typing():
            try:
                answer = rag.get_answer(question)
                if len(answer) > 2000:
                    answer = answer[:1996] + "..."
                await message.reply(answer)
            except Exception as e:
                print(f"Lỗi khi xử lý câu hỏi (tag): {e}")
                await message.reply("Đã xảy ra lỗi trong quá trình tạo câu trả lời.")
                
    # Dòng này cần thiết để bot vẫn xử lý các lệnh prefix (nếu có sau này)
    await bot.process_commands(message)

@bot.tree.command(name="ask", description="Hỏi bot dựa trên cơ sở tri thức của Discord")
@app_commands.describe(question="Câu hỏi của bạn")
async def ask(interaction: discord.Interaction, question: str):
    # Xác nhận lệnh và hiển thị trạng thái "đang suy nghĩ" (thinking) cho người dùng thấy
    await interaction.response.defer()
    
    print(f"\n[DEBUG] 📩 Nhận Slash Command /ask từ {interaction.user}: {question}")
    
    try:
        answer = rag.get_answer(question)
        if len(answer) > 2000:
            answer = answer[:1996] + "..."
            
        await interaction.followup.send(answer)
    except Exception as e:
        print(f"Lỗi khi xử lý câu hỏi: {e}")
        await interaction.followup.send("Đã xảy ra lỗi trong quá trình tạo câu trả lời.")

def run_bot():
    if not config.DISCORD_TOKEN:
        print("Lỗi: Chưa thiết lập DISCORD_TOKEN trong file .env")
        return
        
    bot.run(config.DISCORD_TOKEN)
