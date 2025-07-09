# main.py
import discord
from discord.ext import commands
import os
import asyncio
from dotenv import load_dotenv

# THAY ĐỔI TẠI ĐÂY
# Import hàm khởi động server từ file app/server.py
from app.server import start_web_server 

# Load biến môi trường từ file .env
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

# Cài đặt Intents cho bot
intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True

# Khởi tạo bot
bot = commands.Bot(command_prefix='!', intents=intents)

# Xóa lệnh help mặc định (nếu bạn có help_cog riêng)
bot.remove_command('help')

# --- Event khi bot đã sẵn sàng ---
@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name} ({bot.user.id})')
    print('Bot is ready and running!')
    print(f'Command prefix is: {bot.command_prefix}')
    print('-------------------')
    
    # Đặt trạng thái "Đang chơi" cho bot
    try:
        activity = discord.Game(name="💋Mẹ bạn thân")
        await bot.change_presence(status=discord.Status.online, activity=activity)
        print(f'Successfully set activity to "Playing {activity.name}"')
    except Exception as e:
        print(f"Error setting activity: {e}")

# --- Hàm chính để chạy bot ---
async def main():
    # Load cogs
    print("Loading cogs...")
    for filename in os.listdir('./cogs'):
        if filename.endswith('.py') and not filename.startswith('_'):
            try:
                await bot.load_extension(f'cogs.{filename[:-3]}')
                print(f'✅ Loaded Cog: {filename}')
            except Exception as e:
                print(f'❌ Failed to load cog {filename}: {type(e).__name__} - {e}')
    
    # BẮT ĐẦU WEB SERVER (thay thế cho keep_alive)
    start_web_server(bot)
    
    # Chạy bot
    try:
        await bot.start(TOKEN)
    except discord.errors.LoginFailure:
        print("\n\n❌ LOGIN FAILED: The provided DISCORD_TOKEN is invalid. Please check your .env file or Render environment variables.")

# Chạy hàm main
if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nBot is shutting down.")
