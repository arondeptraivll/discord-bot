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
    # Load tất cả các cogs (commands)
    for filename in os.listdir('./cogs'):
        if filename.endswith('.py'):
            try:
                await bot.load_extension(f'cogs.{filename[:-3]}')
                print(f'-> Đã load {filename}')
            except Exception as e:
                print(f'Lỗi khi load {filename}: {e}')

# XÓA HOÀN TOÀN HÀM on_message CŨ. THAY BẰNG LISTENER.
@bot.listen('on_message')
async def sticky_message_handler(message):
    """
    Bộ lắng nghe này chỉ làm một việc: xử lý tin nhắn dính (sticky).
    Nó chạy song song và không can thiệp vào việc xử lý lệnh.
    """
    # 1. Bỏ qua tất cả tin nhắn từ bot (quan trọng nhất!)
    if message.author.bot:
        return

    # 2. Kiểm tra xem tin nhắn có phải là một lệnh hợp lệ không.
    # Nếu là lệnh, bỏ qua hoàn toàn và để hệ thống lệnh tự xử lý.
    ctx = await bot.get_context(message)
    if ctx.valid:
        return

    # 3. Nếu tin nhắn là của người dùng và KHÔNG phải lệnh,
    # thì lúc này mới thực thi logic sticky.
    if message.channel.id in bot.pinned_messages:
        pinned_data = bot.pinned_messages[message.channel.id]
        
        try:
            # Xóa tin nhắn ghim cũ
            old_pinned_msg = await message.channel.fetch_message(pinned_data['message_id'])
            await old_pinned_msg.delete()
        except (discord.NotFound, discord.Forbidden):
            # Bỏ qua nếu không tìm thấy tin nhắn hoặc không có quyền xóa
            pass
            
        # Gửi lại tin nhắn ghim và cập nhật ID mới
        new_pinned_msg = await message.channel.send(pinned_data['content'])
        bot.pinned_messages[message.channel.id]['message_id'] = new_pinned_msg.id


# --- KHỞI CHẠY BOT ---
if __name__ == "__main__":
    if TOKEN is None:
        print("Lỗi: Không tìm thấy DISCORD_TOKEN trong biến môi trường.")
    else:
        keep_alive() 
        bot.run(TOKEN)
