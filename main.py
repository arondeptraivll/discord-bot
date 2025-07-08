import discord
from discord.ext import commands
import os
import asyncio
from dotenv import load_dotenv
from keep_alive import keep_alive

# Load biến môi trường từ file .env
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

# Cài đặt Intents cho bot (quyền bot cần)
# Cần message_content để đọc nội dung tin nhắn lệnh
intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True # Cần để lấy thông tin role của người dùng

# Khởi tạo bot với prefix '?'
bot = commands.Bot(command_prefix='?', intents=intents)

# Xóa lệnh help mặc định để có thể tự tạo lệnh help riêng sau này
bot.remove_command('help')

# Event khi bot đã sẵn sàng
@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')
    print('Bot is ready and running!')
    print('-------------------')
    # Đặt status cho bot
    await bot.change_presence(activity=discord.Game(name="?embed | ?deletebotmsg"))


# Hàm chính để chạy bot
async def main():
    # Vòng lặp để load tất cả các file lệnh trong thư mục 'cogs'
    for filename in os.listdir('./cogs'):
        if filename.endswith('.py'):
            try:
                await bot.load_extension(f'cogs.{filename[:-3]}')
                print(f'✅ Loaded Cog: {filename}')
            except Exception as e:
                print(f'❌ Failed to load cog {filename}: {e}')
    
    # Bắt đầu server để giữ bot sống
    keep_alive()
    
    # Chạy bot với token
    await bot.start(TOKEN)

# Chạy hàm main bằng asyncio
if __name__ == "__main__":
    asyncio.run(main())
