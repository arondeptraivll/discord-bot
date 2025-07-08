import os
import discord
from discord.ext import commands
from dotenv import load_dotenv
from flask import Flask
from threading import Thread

# --- CẤU HÌNH WEB SERVER ĐỂ GIỮ BOT 24/7 ---
app = Flask('')

@app.route('/')
def home():
    return "Bot is alive!"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()

# --- CẤU HÌNH BOT DISCORD ---
# Load biến môi trường từ file .env (khi chạy local)
# Trên Render, nó sẽ tự động lấy từ Environment Variables
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

# Cần bật đủ Intents trong Discord Developer Portal
intents = discord.Intents.default()
intents.message_content = True  # Bắt buộc để bot đọc được nội dung tin nhắn
intents.guilds = True
intents.messages = True

# Khởi tạo bot với prefix '?'
bot = commands.Bot(command_prefix='?', intents=intents)

@bot.event
async def on_ready():
    print(f'{bot.user} đã kết nối tới Discord!')
    # Load tất cả các Cogs từ thư mục 'cogs'
    for filename in os.listdir('./cogs'):
        if filename.endswith('.py'):
            try:
                await bot.load_extension(f'cogs.{filename[:-3]}')
                print(f'Đã load {filename}')
            except Exception as e:
                print(f'Lỗi khi load {filename}: {e}')

# Chạy web server và bot
if __name__ == "__main__":
    keep_alive()
    try:
        bot.run(TOKEN)
    except discord.errors.LoginFailure:
        print("Lỗi: Token không hợp lệ. Vui lòng kiểm tra lại DISCORD_TOKEN.")
    except Exception as e:
        print(f"Đã xảy ra lỗi khi chạy bot: {e}")
