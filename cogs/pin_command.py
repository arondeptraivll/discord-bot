import discord
from discord.ext import commands

class PinCommand(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # Hàm kiểm tra quyền hạn tùy chỉnh
    async def check_permissions(self, ctx):
        # Kiểm tra nếu là Admin
        if ctx.author.guild_permissions.administrator:
            return True
        # Kiểm tra nếu có role "Supporter"
        supporter_role = discord.utils.get(ctx.guild.roles, name="Supporter")
        if supporter_role and supporter_role in ctx.author.roles:
            return True
        return False

    @commands.command(name='pin')
    async def pin_message(self, ctx, *, message_content: str):
        """Ghim một tin nhắn và giữ nó luôn ở cuối kênh."""
        if not await self.check_permissions(ctx):
            await ctx.send("⚠️ Bạn không có quyền sử dụng lệnh này. Cần quyền Administrator hoặc vai trò 'Supporter'.", ephemeral=True)
            return

        # Kiểm tra kênh đã có tin nhắn ghim chưa
        if ctx.channel.id in self.bot.pinned_messages:
            await ctx.send("⚠️ Kênh này đã có một tin nhắn được ghim. Vui lòng dùng `?stoppin` trước khi ghim tin nhắn mới.", ephemeral=True)
            return

        # Xóa tin nhắn lệnh gốc của người dùng
        await ctx.message.delete()

        # Định dạng tin nhắn sẽ ghim
        formatted_content = f"## 📌Pinned Messege\n\n{message_content}"
        
        # Gửi tin nhắn ghim và lưu trữ thông tin
        pinned_msg = await ctx.send(formatted_content)
        
        self.bot.pinned_messages[ctx.channel.id] = {
            'message_id': pinned_msg.id,
            'content': formatted_content
        }

    @pin_message.error
    async def pin_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send("Vui lòng nhập nội dung tin nhắn cần ghim. Ví dụ: `?pin Nội dung của bạn`", ephemeral=True)
        elif isinstance(error, commands.CheckFailure):
             await ctx.send("⚠️ Bạn không có quyền sử dụng lệnh này.", ephemeral=True)
        else:
            print(f"Lỗi lệnh pin: {error}")

async def setup(bot):
    await bot.add_cog(PinCommand(bot))
