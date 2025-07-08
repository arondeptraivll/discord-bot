import discord
from discord.ext import commands

class StopPinCommand(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def check_permissions(self, ctx):
        return ctx.author.guild_permissions.administrator or \
               discord.utils.get(ctx.guild.roles, name="Supporter") in ctx.author.roles

    @commands.command(name='stoppin')
    async def stop_pinning(self, ctx):
        try:
            await ctx.message.delete()
        except (discord.NotFound, discord.Forbidden):
            pass

        if not await self.check_permissions(ctx):
            await ctx.send("⚠️ Bạn không có quyền sử dụng lệnh này.", delete_after=3)
            return

        # Lấy và xóa dữ liệu khỏi bộ nhớ
        pinned_data = self.bot.pinned_messages.pop(ctx.channel.id, None)

        if pinned_data and pinned_data.get('message_id'):
            # Xóa tin nhắn ghim cũ lần cuối
            try:
                old_msg = await ctx.channel.fetch_message(pinned_data['message_id'])
                await old_msg.delete()
            except (discord.NotFound, discord.Forbidden):
                pass
            await ctx.send("✅ Đã gỡ ghim thành công.", delete_after=3)
        else:
            await ctx.send("⚠️ Kênh này không có tin nhắn nào đang được ghim.", delete_after=3)

async def setup(bot):
    await bot.add_cog(StopPinCommand(bot))
