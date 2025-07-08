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

# --- SỬA LẠI LOGIC on_message ĐỂ KHẮC PHỤC LỖI ---
@bot.event
async def on_message(message):
    # Bỏ qua tin nhắn của chính bot
    if message.author == bot.user:
        return

    # Xử lý logic tin nhắn ghim
    # Chỉ gửi lại tin nhắn ghim nếu kênh có thiết lập và tin nhắn đến không phải là một lệnh
    is_sticky_channel = message.channel.id in bot.sticky_messages
    is_command = message.content.startswith(bot.command_prefix)

    if is_sticky_channel and not is_command:
        # Đây là tin nhắn thường trong kênh ghim -> gửi lại tin nhắn ghim
        sticky_info = bot.sticky_messages[message.channel.id]
        
        # Xóa tin ghim cũ
        try:
            await sticky_info['last_message'].delete()
        except discord.NotFound:
            print(f"Tin nhắn ghim cũ ở kênh #{message.channel.name} không tìm thấy.")
        except discord.Forbidden:
            print(f"Không có quyền xóa tin nhắn ở kênh #{message.channel.name}.")

        # Gửi lại tin ghim mới và cập nhật
        new_sticky_message = await message.channel.send(sticky_info['content'])
        bot.sticky_messages[message.channel.id]['last_message'] = new_sticky_message
    
    # Luôn xử lý các lệnh, để các lệnh như ?stoppin có thể hoạt động
    await bot.process_commands(message)

# --- Chạy Bot và Web Server ---
if __name__ == "__main__":
    keep_alive()
    bot.run(TOKEN)
