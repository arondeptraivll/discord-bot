import discord
from discord.ext import commands

def is_admin_or_supporter():
    async def predicate(ctx):
        if ctx.author.guild_permissions.administrator: return True
        supporter_role = discord.utils.get(ctx.guild.roles, name="Supporter")
        return supporter_role is not None and supporter_role in ctx.author.roles
    return commands.check(predicate)

class UtilityCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='deletebotmsg')
    @is_admin_or_supporter()
    async def delete_bot_message(self, ctx: commands.Context, message_id: int):
        await ctx.message.delete()
        try:
            msg_to_delete = await ctx.channel.fetch_message(message_id)
            if msg_to_delete.author.id == self.bot.user.id:
                await msg_to_delete.delete()
                await ctx.send("✅ Đã xóa tin nhắn thành công.", delete_after=2)
            else:
                await ctx.send("🚫 Lỗi: Tôi chỉ có thể xóa tin nhắn do chính tôi gửi.", delete_after=2)
        except discord.NotFound:
            await ctx.send("⚠️ Không tìm thấy tin nhắn với ID này trong kênh hiện tại.", delete_after=2)
        except discord.Forbidden:
            await ctx.send("🚫 Lỗi: Tôi không có quyền để xóa tin nhắn trong kênh này.", delete_after=2)
        except Exception as e:
            print(f"Error deleting message: {e}")
            await ctx.send("Có lỗi xảy ra, vui lòng thử lại.", delete_after=2)
            
    @delete_bot_message.error
    async def deletebotmsg_error(self, ctx, error):
        if isinstance(error, commands.CheckFailure):
            await ctx.send("🚫 Bạn không có quyền sử dụng lệnh này.", delete_after=3)
        elif isinstance(error, commands.MissingRequiredArgument):
            # ====> THAY ĐỔI DÒNG DƯỚI ĐÂY <====
            await ctx.send("⚠️ Vui lòng nhập ID của tin nhắn. Cú pháp: `!deletebotmsg [ID tin nhắn]`", delete_after=5) # <-- Đã đổi
        elif isinstance(error, commands.BadArgument):
            await ctx.send("⚠️ ID tin nhắn phải là một con số.", delete_after=3)

async def setup(bot):
    await bot.add_cog(UtilityCog(bot))
