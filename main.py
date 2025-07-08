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
# Cần message_content để đọc nội dung tin nhắn lệnh.
# Cần guilds và members để lấy thông tin server và role của người dùng.
intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True

# Khởi tạo bot với prefix '?' và các intents đã thiết lập
bot = commands.Bot(command_prefix='?', intents=intents)

# Xóa lệnh help mặc định để có thể tự tạo lệnh help riêng sau này (nếu cần)
bot.remove_command('help')

# --- Event khi bot đã sẵn sàng ---
@bot.event
async def on_ready():
    """
    Hàm này được chạy khi bot đã kết nối thành công với Discord.
    """
    print(f'Logged in as {bot.user.name} ({bot.user.id})')
    print('Bot is ready and running!')
    print('-------------------')
    
    # Đặt trạng thái "Đang chơi" cho bot với nội dung bạn yêu cầu
    try:
        activity = discord.Game(name="💋Mẹ bạn thân")
        await bot.change_presence(status=discord.Status.online, activity=activity)
        print(f'Successfully set activity to "Playing {activity.name}"')
    except Exception as e:
        print(f"Error setting activity: {e}")


# --- Hàm chính để chạy bot ---
async def main():
    """
    Hàm bất đồng bộ chính để load các extension (cogs) và khởi động bot.
    """
    # Vòng lặp để load tất cả các file lệnh trong thư mục 'cogs'
    print("Loading cogs...")
    for filename in os.listdir('./cogs'):
        if filename.endswith('.py'):
            try:
                # Load extension bằng cách chỉ định đường dẫn 'cogs.ten_file'
                await bot.load_extension(f'cogs.{filename[:-3]}')
                print(f'✅ Loaded Cog: {filename}')
            except Exception as e:
                # In ra lỗi nếu không thể load được cog
                print(f'❌ Failed to load cog {filename}: {type(e).__name__} - {e}')
    
    # Bắt đầu server web để UptimeRobot có thể ping, giữ bot sống
    keep_alive()
    
    # Chạy bot với token từ biến môi trường
    # Sử dụng khối try-except để bắt lỗi sai token
    try:
        await bot.start(TOKEN)
    except discord.errors.LoginFailure:
        print("\n\n❌ LOGIN FAILED: The provided DISCORD_TOKEN is invalid. Please check your .env file or Render environment variables.")


# Chạy hàm main sử dụng asyncio
# Đây là điểm bắt đầu của chương trình
if __name__ == "__main__":
    asyncio.run(main())
