import discord
from discord.ext import commands

class PinCommand(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def check_permissions(self, ctx):
        return ctx.author.guild_permissions.administrator or \
               discord.utils.get(ctx.guild.roles, name="Supporter") in ctx.author.roles

    @commands.command(name='pin')
    async def pin_message(self, ctx, *, message_content: str):
        try:
            await ctx.message.delete()
        except (discord.NotFound, discord.Forbidden):
            pass

        if not await self.check_permissions(ctx):
            await ctx.send("⚠️ Bạn không có quyền sử dụng lệnh này.", delete_after=3)
            return

        if ctx.channel.id in self.bot.pinned_messages:
            await ctx.send("⚠️ Kênh này đã có tin ghim. Dùng `?stoppin` để gỡ.", delete_after=3)
            return

        # Bước 1: Chỉ cập nhật trạng thái vào bộ nhớ
        formatted_content = f"## 📌Pinned Messege\n\n{message_content}"
        self.bot.pinned_messages[ctx.channel.id] = {
            'content': formatted_content,
            'message_id': None  # Chưa có ID lúc này
        }

        # Bước 2: Gọi hàm trung tâm để thực hiện việc ghim
        await self.bot.update_sticky(ctx.channel)
        
    @pin_message.error
    async def pin_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            try:
                await ctx.message.delete()
            except:
                pass
            await ctx.send("Cú pháp sai. Ví dụ: `?pin Nội dung cần ghim`", delete_after=3)
            
async def setup(bot):
    await bot.add_cog(PinCommand(bot))
