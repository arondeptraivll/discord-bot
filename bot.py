import discord
from discord.ext import commands
import os
from dotenv import load_dotenv
from flask import Flask
from threading import Thread

# --- Cấu hình Web Server cho UptimeRobot ---
app = Flask('')
@app.route('/')
def home():
    return "Bot is alive and running!"
def run():
    app.run(host='0.0.0.0', port=8080)
def keep_alive():
    t = Thread(target=run)
    t.start()

# --- Cấu hình Bot Discord ---
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.messages = True

bot = commands.Bot(command_prefix='?', intents=intents)
bot.sticky_messages = {}

@bot.event
async def on_ready():
    print(f'Đăng nhập thành công với tên {bot.user}')
    for filename in os.listdir('./cogs'):
        if filename.endswith('.py'):
            try:
                await bot.load_extension(f'cogs.{filename[:-3]}')
                print(f'✅ Đã load thành công cog: {filename}')
            except Exception as e:
                print(f'❌ Lỗi khi load cog {filename}: {e}')

# --- BỘ LẮNG NGHE MỚI, THAY THẾ HOÀN TOÀN on_message CŨ ---
# Listener này chỉ chạy cho logic tin nhắn ghim, không can thiệp vào lệnh.
@bot.listen('on_message')
async def sticky_message_handler(message):
    # 1. Bỏ qua nếu tin nhắn từ bot (chính nó hoặc bot khác)
    if message.author.bot:
        return

    # 2. Kiểm tra xem tin nhắn có phải là một lệnh hợp lệ không. Nếu phải, bỏ qua.
    #    Điều này ngăn listener chạy khi bạn gõ ?pin, ?stoppin...
    ctx = await bot.get_context(message)
    if ctx.valid:
        return

    # 3. Chỉ thực hiện khi kênh này có trong danh sách ghim
    if message.channel.id in bot.sticky_messages:
        sticky_info = bot.sticky_messages[message.channel.id]
        
        # Xóa tin nhắn ghim cũ
        try:
            await sticky_info['last_message'].delete()
        except (discord.NotFound, discord.Forbidden):
            pass # Bỏ qua nếu không tìm thấy hoặc không có quyền

        # Gửi lại tin nhắn ghim mới và cập nhật
        new_sticky_message = await message.channel.send(sticky_info['content'])
        bot.sticky_messages[message.channel.id]['last_message'] = new_sticky_message


# Khi không định nghĩa hàm on_message, bot.process_commands sẽ tự động được gọi.
# Chúng ta không cần thêm dòng đó nữa.

# --- Chạy Bot và Web Server ---
if __name__ == "__main__":
    keep_alive()
    bot.run(TOKEN)
