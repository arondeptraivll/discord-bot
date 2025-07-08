import discord
from discord.ext import commands
import os
import asyncio
from keep_alive import keep_alive # Import hàm keep_alive

# --- CẤU HÌNH BOT ---
# Lấy token từ biến môi trường của Render
TOKEN = os.environ.get("DISCORD_TOKEN")

# Thiết lập Intents (Quyền của bot)
intents = discord.Intents.default()
intents.message_content = True  # Cần thiết để đọc nội dung tin nhắn
intents.guilds = True

# Khởi tạo bot với prefix '?'
bot = commands.Bot(command_prefix='?', intents=intents)

# Tạo một dictionary để lưu trữ các tin nhắn đã ghim
# { channel_id: { 'message_id': id, 'content': 'nội dung' } }
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

@bot.event
async def on_message(message):
    """Sự kiện xảy ra mỗi khi có tin nhắn mới."""
    # Bỏ qua tin nhắn từ chính bot để tránh vòng lặp vô hạn
    if message.author == bot.user:
        return
    
    # Xử lý các lệnh trước
    await bot.process_commands(message)

    # ---- Logic giữ tin nhắn ghim (sticky) ----
    # Kiểm tra xem kênh này có tin nhắn cần ghim không
    if message.channel.id in bot.pinned_messages:
        # Lấy thông tin tin nhắn đã lưu
        pinned_data = bot.pinned_messages[message.channel.id]
        
        try:
            # Tìm và xoá tin nhắn ghim cũ
            old_pinned_msg = await message.channel.fetch_message(pinned_data['message_id'])
            await old_pinned_msg.delete()
        except discord.NotFound:
            # Nếu tin nhắn không tìm thấy (đã bị xoá thủ công) thì không làm gì cả
            pass
        except discord.Forbidden:
            print(f"Lỗi: Bot không có quyền xóa tin nhắn trong kênh {message.channel.name}")
            # Có thể gửi một thông báo lỗi ở đây nếu muốn
            return
            
        # Gửi lại tin nhắn ghim và cập nhật ID mới
        new_pinned_msg = await message.channel.send(pinned_data['content'])
        bot.pinned_messages[message.channel.id]['message_id'] = new_pinned_msg.id


# --- KHỞI CHẠY BOT ---
if __name__ == "__main__":
    if TOKEN is None:
        print("Lỗi: Không tìm thấy DISCORD_TOKEN trong biến môi trường.")
    else:
        # Chạy web server trong một luồng riêng
        keep_alive() 
        # Chạy bot
        bot.run(TOKEN)
