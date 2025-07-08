import discord
from discord.ext import commands
import os
from dotenv import load_dotenv
from flask import Flask
from threading import Thread

# --- Cấu hình Web Server cho UptimeRobot ---
# Tạo một ứng dụng web Flask đơn giản
app = Flask('')

@app.route('/')
def home():
    # Khi UptimeRobot truy cập vào URL của bot, nó sẽ nhận được dòng chữ này
    return "Bot is alive and running!"

def run():
    # Chạy web server trên port 8080
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    # Chạy web server trong một luồng (thread) riêng để không chặn bot
    t = Thread(target=run)
    t.start()

# --- Cấu hình Bot Discord ---
# Load biến môi trường từ file .env (khi chạy local)
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

# Cấp quyền (Intents) cho bot để đọc được nội dung tin nhắn
intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.messages = True

# Khởi tạo bot với prefix '?' và intents
bot = commands.Bot(command_prefix='?', intents=intents)

# Tạo một dictionary để lưu trữ các tin nhắn ghim
# Dictionary này sẽ được chia sẻ với các cogs
bot.sticky_messages = {}

# Sự kiện khi bot sẵn sàng
@bot.event
async def on_ready():
    print(f'Đăng nhập thành công với tên {bot.user}')
    # Load tất cả các file command trong thư mục cogs
    for filename in os.listdir('./cogs'):
        if filename.endswith('.py'):
            try:
                await bot.load_extension(f'cogs.{filename[:-3]}')
                print(f'✅ Đã load thành công cog: {filename}')
            except Exception as e:
                print(f'❌ Lỗi khi load cog {filename}: {e}')

# Sự kiện khi có tin nhắn mới trong kênh
@bot.event
async def on_message(message):
    # Bỏ qua tin nhắn của chính bot để tránh vòng lặp vô tận
    if message.author == bot.user:
        return

    # Kiểm tra xem kênh này có tin nhắn ghim đang hoạt động không
    if message.channel.id in bot.sticky_messages:
        sticky_info = bot.sticky_messages[message.channel.id]
        
        # Xóa tin nhắn ghim cũ
        try:
            await sticky_info['last_message'].delete()
        except discord.NotFound:
            # Tin nhắn có thể đã bị xóa thủ công, bỏ qua lỗi
            print(f"Tin nhắn ghim cũ ở kênh #{message.channel.name} không tìm thấy, có thể đã bị xóa.")
        except discord.Forbidden:
            print(f"Không có quyền xóa tin nhắn ở kênh #{message.channel.name}.")

        # Gửi lại tin nhắn ghim mới và cập nhật lại thông tin
        new_sticky_message = await message.channel.send(sticky_info['content'])
        bot.sticky_messages[message.channel.id]['last_message'] = new_sticky_message
        print(f"Đã gửi lại tin nhắn ghim tại kênh #{message.channel.name}")

    # Xử lý các lệnh command (quan trọng, nếu không có dòng này bot sẽ không nhận lệnh)
    await bot.process_commands(message)

# --- Chạy Bot và Web Server ---
if __name__ == "__main__":
    # Bật web server
    keep_alive()
    # Chạy bot
    bot.run(TOKEN)
