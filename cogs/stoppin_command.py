import discord
from discord.ext import commands

class StopPinCommand(commands.Cog):
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

    @commands.command(name='stoppin')
    async def stop_pinning(self, ctx):
        """Dừng ghim tin nhắn trong kênh hiện tại."""
        if not await self.check_permissions(ctx):
            await ctx.send("⚠️ Bạn không có quyền sử dụng lệnh này. Cần quyền Administrator hoặc vai trò 'Supporter'.", ephemeral=True)
            return

        if ctx.channel.id in self.bot.pinned_messages:
            pinned_data = self.bot.pinned_messages[ctx.channel.id]
            try:
                # Tìm và xoá tin nhắn ghim cũ
                old_pinned_msg = await ctx.channel.fetch_message(pinned_data['message_id'])
                await old_pinned_msg.delete()
            except discord.NotFound:
                # Nếu tin nhắn đã bị xoá thủ công, bỏ qua lỗi
                pass
            except discord.Forbidden:
                await ctx.send("⚠️ Bot không có quyền xóa tin nhắn trong kênh này.", ephemeral=True)


            # Xoá thông tin khỏi bộ nhớ
            del self.bot.pinned_messages[ctx.channel.id]
            await ctx.send("✅ Đã dừng ghim và xóa tin nhắn ghim.", ephemeral=True)
        else:
            await ctx.send("⚠️ Không có tin nhắn nào đang được ghim trong kênh này.", ephemeral=True)

async def setup(bot):
    await bot.add_cog(StopPinCommand(bot))
