import discord
from discord.ext import commands

# Hàm kiểm tra quyền: Chỉ Admin hoặc người có role "Supporter" mới được dùng
async def is_admin_or_supporter(ctx):
    # Kiểm tra xem người dùng có phải là admin của server không
    if ctx.author.guild_permissions.administrator:
        return True
    # Kiểm tra xem người dùng có vai trò tên là "Supporter" không
    supporter_role = discord.utils.get(ctx.guild.roles, name="Supporter")
    if supporter_role and supporter_role in ctx.author.roles:
        return True
    return False

class PinCog(commands.Cog):
    def __init__(self, bot, sticky_messages):
        self.bot = bot
        # Đây là một dictionary được chia sẻ từ file bot.py chính
        # để lưu trữ tin nhắn ghim của mỗi kênh
        self.sticky_messages = sticky_messages

    # Định nghĩa command `?pin`
    @commands.command(name='pin')
    # Áp dụng điều kiện kiểm tra quyền vừa tạo
    @commands.check(is_admin_or_supporter)
    async def pin_message(self, ctx, *, message_content: str):
        """Ghim một tin nhắn và giữ nó luôn ở dưới cùng kênh chat."""
        # Xóa tin nhắn gốc của người dùng để giữ kênh chat sạch sẽ
        try:
            await ctx.message.delete()
        except discord.Forbidden:
            print(f"Không thể xóa tin nhắn của {ctx.author} tại kênh {ctx.channel.name}.")
        except discord.NotFound:
            pass # Tin nhắn có thể đã bị xóa

        # Định dạng nội dung tin nhắn ghim
        formatted_content = f"## 📌 Tin Nhắn Được Ghim\n\n{message_content}"

        # Gửi tin nhắn ghim mới
        new_sticky_message = await ctx.send(formatted_content)

        # Lưu thông tin về tin nhắn ghim vào dictionary
        # Key là ID của kênh, value là nội dung và đối tượng tin nhắn đã gửi
        self.sticky_messages[ctx.channel.id] = {
            'content': formatted_content,
            'last_message': new_sticky_message
        }
        print(f"Đã ghim tin nhắn mới tại kênh #{ctx.channel.name}")

    # Xử lý lỗi nếu người dùng không có quyền
    @pin_message.error
    async def pin_error(self, ctx, error):
        if isinstance(error, commands.CheckFailure):
            await ctx.send("Bạn không có quyền sử dụng lệnh này. Cần quyền Admin hoặc vai trò `Supporter`.", delete_after=10)

# Hàm này bắt buộc phải có để bot.py có thể load Cog
async def setup(bot):
    # Truyền bot instance và sticky_messages dictionary vào Cog
    await bot.add_cog(PinCog(bot, bot.sticky_messages))
