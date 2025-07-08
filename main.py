import discord
from discord.ext import commands
import os
import asyncio
from dotenv import load_dotenv
from keep_alive import keep_alive

# Load biến môi trường từ file .env
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

# Cài đặt Intents cho bot (các quyền mà bot cần)
intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True

# === THAY ĐỔI TẠI ĐÂY ===
# Khởi tạo bot với prefix '!' và các intents đã thiết lập
bot = commands.Bot(command_prefix='!', intents=intents) # <--- ĐÃ SỬA
# ========================

# Xóa lệnh help mặc định
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
    print("Loading cogs...")
    for filename in os.listdir('./cogs'):
        if filename.endswith('.py'):
            try:
                await bot.load_extension(f'cogs.{filename[:-3]}')
                print(f'✅ Loaded Cog: {filename}')
            except Exception as e:
                print(f'❌ Failed to load cog {filename}: {type(e).__name__} - {e}')
    
    # Giữ bot sống trên Render
    keep_alive()
    
    # Chạy bot
    try:
        await bot.start(TOKEN)
    except discord.errors.LoginFailure:
        print("\n\n❌ LOGIN FAILED: The provided DISCORD_TOKEN is invalid. Please check your .env file or Render environment variables.")

# Chạy hàm main
if __name__ == "__main__":
    asyncio.run(main())
