import discord
from discord.ext import commands

class PinCommand(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
    # Hàm kiểm tra quyền hạn (không đổi)
    async def check_permissions(self, ctx):
        if ctx.author.guild_permissions.administrator:
            return True
        supporter_role = discord.utils.get(ctx.guild.roles, name="Supporter")
        return supporter_role and supporter_role in ctx.author.roles

    @commands.command(name='pin')
    async def pin_message(self, ctx, *, message_content: str):
        """Ghim một tin nhắn và giữ nó ở cuối kênh."""
        try:
            # Xóa tin nhắn lệnh của người dùng
            await ctx.message.delete()
        except discord.Forbidden:
            print(f"Lỗi: Không có quyền xóa tin nhắn trong kênh {ctx.channel.name}")

        # Kiểm tra quyền hạn
        if not await self.check_permissions(ctx):
            await ctx.send("⚠️ Bạn không có quyền sử dụng lệnh này.", delete_after=2)
            return

        # Kiểm tra kênh đã có ghim chưa
        if ctx.channel.id in self.bot.pinned_messages:
            await ctx.send("⚠️ Kênh này đã có một tin nhắn được ghim. Dùng `?stoppin` để gỡ.", delete_after=2)
            return

        # Tạo và gửi tin nhắn ghim (tin này sẽ KHÔNG tự xóa)
        formatted_content = f"## 📌Pinned Messege\n\n{message_content}"
        pinned_msg = await ctx.send(formatted_content)
        
        # Lưu lại thông tin
        self.bot.pinned_messages[ctx.channel.id] = {
            'message_id': pinned_msg.id, 
            'content': formatted_content
        }
    
    # Xử lý khi lệnh ?pin thiếu nội dung
    @pin_message.error
    async def pin_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            try:
                await ctx.message.delete()
            except discord.NotFound:
                pass
            await ctx.send("Vui lòng nhập nội dung tin nhắn. Ví dụ: `?pin Nội dung của bạn`", delete_after=2)

async def setup(bot):
    await bot.add_cog(PinCommand(bot))
