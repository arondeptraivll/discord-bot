import discord
from discord.ext import commands

class PinCommand(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # Hàm kiểm tra quyền hạn tùy chỉnh
    async def check_permissions(self, ctx):
        if ctx.author.guild_permissions.administrator:
            return True
        supporter_role = discord.utils.get(ctx.guild.roles, name="Supporter")
        if supporter_role and supporter_role in ctx.author.roles:
            return True
        return False

    @commands.command(name='pin')
    async def pin_message(self, ctx, *, message_content: str):
        """Ghim một tin nhắn và giữ nó luôn ở cuối kênh."""
        # Xóa tin nhắn lệnh gốc của người dùng ngay lập tức
        # Điều này rất quan trọng để tránh chính nó kích hoạt lại cơ chế sticky
        try:
            await ctx.message.delete()
        except discord.Forbidden:
            print(f"Không thể xóa tin nhắn lệnh của người dùng trong kênh {ctx.channel.name}")
            # Bot sẽ vẫn hoạt động nhưng tin nhắn lệnh sẽ không bị xóa

        if not await self.check_permissions(ctx):
            await ctx.send("⚠️ Bạn không có quyền sử dụng lệnh này. Cần quyền Administrator hoặc vai trò 'Supporter'.", ephemeral=True, delete_after=10)
            return

        if ctx.channel.id in self.bot.pinned_messages:
            await ctx.send("⚠️ Kênh này đã có một tin nhắn được ghim. Vui lòng dùng `?stoppin` trước khi ghim tin nhắn mới.", ephemeral=True, delete_after=10)
            return
        
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
        # Xóa tin nhắn lệnh gốc của người dùng nếu có lỗi
        try:
            await ctx.message.delete()
        except discord.Forbidden:
            pass

        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send("Vui lòng nhập nội dung tin nhắn cần ghim. Ví dụ: `?pin Nội dung của bạn`", ephemeral=True, delete_after=10)
        elif isinstance(error, commands.CheckFailure):
             await ctx.send("⚠️ Bạn không có quyền sử dụng lệnh này.", ephemeral=True, delete_after=10)
        else:
            print(f"Lỗi lệnh pin: {error}")

async def setup(bot):
    await bot.add_cog(PinCommand(bot))
