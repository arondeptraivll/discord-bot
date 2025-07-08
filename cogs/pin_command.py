import discord
from discord.ext import commands

class PinCommand(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
    async def check_permissions(self, ctx):
        if ctx.author.guild_permissions.administrator:
            return True
        supporter_role = discord.utils.get(ctx.guild.roles, name="Supporter")
        return supporter_role and supporter_role in ctx.author.roles

    @commands.command(name='pin')
    async def pin_message(self, ctx, *, message_content: str):
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
            await ctx.send("⚠️ Kênh này đã có một tin nhắn được ghim. Dùng `?stoppin` để gỡ.", delete_after=2)
            return

        formatted_content = f"## 📌Pinned Messege\n\n{message_content}"
        pinned_msg = await ctx.send(formatted_content)
        
        self.bot.pinned_messages[ctx.channel.id] = {
            'message_id': pinned_msg.id, 
            'content': formatted_content
        }
    
    @pin_message.error
    async def pin_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            try:
                await ctx.message.delete()
            except (discord.Forbidden, discord.NotFound):
                pass
            await ctx.send("Vui lòng nhập nội dung tin nhắn. Ví dụ: `?pin Nội dung của bạn`", delete_after=2)

async def setup(bot):
    await bot.add_cog(PinCommand(bot))
