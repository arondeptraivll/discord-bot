import discord
from discord.ext import commands

class StopPinCommand(commands.Cog):
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

    @commands.command(name='stoppin')
    async def stop_pinning(self, ctx):
        """Dừng ghim tin nhắn trong kênh hiện tại."""
        # Xóa tin nhắn lệnh gốc của người dùng để giữ kênh sạch sẽ
        try:
            await ctx.message.delete()
        except discord.Forbidden:
            print(f"Không thể xóa tin nhắn lệnh của người dùng trong kênh {ctx.channel.name}")

        if not await self.check_permissions(ctx):
            await ctx.send("⚠️ Bạn không có quyền sử dụng lệnh này. Cần quyền Administrator hoặc vai trò 'Supporter'.", ephemeral=True, delete_after=10)
            return

        if ctx.channel.id in self.bot.pinned_messages:
            pinned_data = self.bot.pinned_messages[ctx.channel.id]
            try:
                old_pinned_msg = await ctx.channel.fetch_message(pinned_data['message_id'])
                await old_pinned_msg.delete()
            except discord.NotFound:
                pass
            except discord.Forbidden:
                await ctx.send("⚠️ Bot không có quyền xóa tin nhắn trong kênh này.", ephemeral=True, delete_after=10)

            # Xoá thông tin khỏi bộ nhớ
            del self.bot.pinned_messages[ctx.channel.id]
            # Gửi tin nhắn ẩn (ephemeral) xác nhận thành công
            await ctx.send("✅ Đã dừng ghim và xóa tin nhắn ghim.", ephemeral=True, delete_after=10)
        else:
            # Gửi tin nhắn ẩn (ephemeral) báo lỗi
            await ctx.send("⚠️ Không có tin nhắn nào đang được ghim trong kênh này.", ephemeral=True, delete_after=10)

async def setup(bot):
    await bot.add_cog(StopPinCommand(bot))
