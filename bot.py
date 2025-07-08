import discord
from discord.ext import commands
import os
import asyncio
from keep_alive import keep_alive

# --- CẤU HÌNH BOT ---
TOKEN = os.environ.get("DISCORD_TOKEN")
intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
bot = commands.Bot(command_prefix='?', intents=intents)
bot.pinned_messages = {}

# --- SỰ KIỆN ---
@bot.event
async def on_ready():
    """Sự kiện xảy ra khi bot đã sẵn sàng hoạt động."""
    print(f'Đăng nhập thành công với tên {bot.user}')
    print('Bot đã sẵn sàng!')
    for filename in os.listdir('./cogs'):
        if filename.endswith('.py'):
            try:
                await bot.load_extension(f'cogs.{filename[:-3]}')
                print(f'-> Đã load {filename}')
            except Exception as e:
                print(f'Lỗi khi load {filename}: {e}')

# SỬA LẠI HOÀN TOÀN HÀM ON_MESSAGE
@bot.event
async def on_message(message):
    """
    Sự kiện xảy ra mỗi khi có tin nhắn mới.
    Logic mới: Ưu tiên xử lý lệnh trước. Nếu tin nhắn không phải là lệnh,
    mới kiểm tra và chạy cơ chế sticky.
    """
    # Bỏ qua tin nhắn từ chính bot để tránh vòng lặp vô hạn
    if message.author.id == bot.user.id:
        return
    
    # 1. Ưu tiên xử lý lệnh trước tiên
    # Dòng này sẽ kiểm tra xem tin nhắn có phải là lệnh không và thực thi nó
    await bot.process_commands(message)

    # 2. Kiểm tra xem tin nhắn vừa gửi có phải là một lệnh hợp lệ không
    # Nếu là lệnh, chúng ta sẽ không chạy logic sticky nữa
    ctx = await bot.get_context(message)
    if ctx.valid:
        return # Tin nhắn là một lệnh (?pin, ?stoppin), dừng tại đây.

    # 3. Nếu tin nhắn không phải lệnh, lúc này mới chạy logic sticky
    if message.channel.id in bot.pinned_messages:
        pinned_data = bot.pinned_messages[message.channel.id]
        
        try:
            old_pinned_msg = await message.channel.fetch_message(pinned_data['message_id'])
            await old_pinned_msg.delete()
        except (discord.NotFound, discord.Forbidden):
            # Nếu tin nhắn không tìm thấy hoặc bot không có quyền, bỏ qua
            pass
            
        new_pinned_msg = await message.channel.send(pinned_data['content'])
        bot.pinned_messages[message.channel.id]['message_id'] = new_pinned_msg.id


# --- KHỞI CHẠY BOT ---
if __name__ == "__main__":
    if TOKEN is None:
        print("Lỗi: Không tìm thấy DISCORD_TOKEN trong biến môi trường.")
    else:
        keep_alive()
        bot.run(TOKEN)
