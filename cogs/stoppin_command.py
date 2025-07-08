import discord
from discord.ext import commands

class StopPinCommand(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def check_permissions(self, ctx):
        if ctx.author.guild_permissions.administrator:
            return True
        supporter_role = discord.utils.get(ctx.guild.roles, name="Supporter")
        return supporter_role and supporter_role in ctx.author.roles

    @commands.command(name='stoppin')
    async def stop_pinning(self, ctx):
        try:
            # SỬA Ở ĐÂY: Thêm 'discord.NotFound' vào khối try-except
            await ctx.message.delete()
        except (discord.Forbidden, discord.NotFound):
            # Nếu không có quyền hoặc tin nhắn đã bị xóa, thì bỏ qua và tiếp tục
            pass
            
        if not await self.check_permissions(ctx):
            await ctx.send("⚠️ Bạn không có quyền sử dụng lệnh này.", delete_after=2)
            return

        if ctx.channel.id in self.bot.pinned_messages:
            pinned_data = self.bot.pinned_messages.pop(ctx.channel.id) 
            try:
                old_msg = await ctx.channel.fetch_message(pinned_data['message_id'])
                await old_msg.delete()
            except (discord.NotFound, discord.Forbidden):
                # Cũng nên thêm xử lý lỗi ở đây cho chắc chắn
                pass

            await ctx.send("✅ Đã dừng ghim và xóa tin nhắn ghim.", delete_after=2)
        else:
            await ctx.send("⚠️ Không có tin nhắn nào đang được ghim trong kênh này.", delete_after=2)

async def setup(bot):
    await bot.add_cog(StopPinCommand(bot))
