import discord
from discord.ext import commands

class StopPinCommand(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # Hàm kiểm tra quyền hạn (không đổi)
    async def check_permissions(self, ctx):
        if ctx.author.guild_permissions.administrator:
            return True
        supporter_role = discord.utils.get(ctx.guild.roles, name="Supporter")
        return supporter_role and supporter_role in ctx.author.roles

    @commands.command(name='stoppin')
    async def stop_pinning(self, ctx):
        """Dừng ghim tin nhắn và xóa tin nhắn đang ghim."""
        try:
            # Xóa tin nhắn lệnh của người dùng
            await ctx.message.delete()
        except discord.Forbidden:
            print(f"Lỗi: Không có quyền xóa tin nhắn trong kênh {ctx.channel.name}")
            
        # Kiểm tra quyền hạn
        if not await self.check_permissions(ctx):
            await ctx.send("⚠️ Bạn không có quyền sử dụng lệnh này.", delete_after=2)
            return

        # Kiểm tra xem có tin nhắn đang ghim không
        if ctx.channel.id in self.bot.pinned_messages:
            # Lấy thông tin và xóa khỏi bộ nhớ
            # Dùng .pop() để lấy và xóa trong một bước
            pinned_data = self.bot.pinned_messages.pop(ctx.channel.id) 
            try:
                # Tìm và xóa tin nhắn ghim cũ
                old_msg = await ctx.channel.fetch_message(pinned_data['message_id'])
                await old_msg.delete()
            except discord.NotFound:
                # Nếu tin nhắn đã bị xóa thủ công, bỏ qua
                pass
            except discord.Forbidden:
                # Gửi cảnh báo nếu không xóa được tin ghim
                 await ctx.send("⚠️ Bot không có quyền xóa tin nhắn ghim.", delete_after=2)

            await ctx.send("✅ Đã dừng ghim và xóa tin nhắn ghim.", delete_after=2)
        else:
            await ctx.send("⚠️ Không có tin nhắn nào đang được ghim trong kênh này.", delete_after=2)

async def setup(bot):
    await bot.add_cog(StopPinCommand(bot))
