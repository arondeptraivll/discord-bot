import discord
from discord.ext import commands
import os
from keep_alive import keep_alive

# --- HÀM TRUNG TÂM ---
# Hàm này sẽ chịu trách nhiệm xóa tin ghim cũ và gửi tin mới.
async def update_sticky_message(channel: discord.TextChannel, bot_instance):
    """
    Hàm duy nhất xử lý việc xóa và đăng lại tin nhắn sticky.
    """
    if channel.id not in bot_instance.pinned_messages:
        return # Không có gì để làm nếu kênh này không được ghim

    data = bot_instance.pinned_messages[channel.id]
    
    # Xóa tin nhắn ghim cũ nếu nó tồn tại
    if data.get('message_id'):
        try:
            old_msg = await channel.fetch_message(data['message_id'])
            await old_msg.delete()
        except (discord.NotFound, discord.Forbidden):
            # Bỏ qua nếu tin nhắn đã bị xóa hoặc không có quyền
            pass

    # Gửi tin nhắn mới và cập nhật ID vào bộ nhớ
    try:
        new_msg = await channel.send(data['content'])
        bot_instance.pinned_messages[channel.id]['message_id'] = new_msg.id
    except discord.Forbidden:
        print(f"Lỗi: Không có quyền gửi tin nhắn trong kênh {channel.name}")
        # Xóa ghim khỏi bộ nhớ nếu không gửi được để tránh lỗi lặp
        bot_instance.pinned_messages.pop(channel.id, None)


# --- CẤU HÌNH BOT ---
TOKEN = os.environ.get("DISCORD_TOKEN")
intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True

# Thêm hàm update_sticky_message vào bot để các cog có thể truy cập
class StickyBot(commands.Bot):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.pinned_messages = {}

    # Gắn hàm trung tâm vào bot
    async def update_sticky(self, channel):
        await update_sticky_message(channel, self)

bot = StickyBot(command_prefix='?', intents=intents)


# --- SỰ KIỆN VÀ BỘ LẮNG NGHE ---
@bot.event
async def on_ready():
    print(f'Đăng nhập thành công với tên {bot.user}')
    # Load cogs
    for filename in os.listdir('./cogs'):
        if filename.endswith('.py'):
            await bot.load_extension(f'cogs.{filename[:-3]}')
            print(f'-> Đã load {filename}')
    print('Bot đã sẵn sàng!')

@bot.listen('on_message')
async def sticky_listener(message):
    """Bộ lắng nghe này CHỈ cập nhật tin nhắn sticky khi có tin nhắn hợp lệ."""
    # Bỏ qua nếu tin nhắn từ bot hoặc là một lệnh
    if message.author.bot or (await bot.get_context(message)).valid:
        return
    
    # Nếu kênh có ghim, gọi hàm trung tâm để cập nhật
    if message.channel.id in bot.pinned_messages:
        await bot.update_sticky(message.channel)


# --- KHỞI CHẠY BOT ---
if __name__ == "__main__":
    keep_alive() 
    bot.run(TOKEN)
