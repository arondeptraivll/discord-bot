import discord
from discord.ext import commands

# --- Hàm kiểm tra quyền ---
# (Bạn có thể tách hàm này ra 1 file riêng nếu có nhiều Cogs cùng sử dụng)
def is_admin_or_supporter():
    async def predicate(ctx):
        if ctx.author.guild_permissions.administrator:
            return True
        supporter_role = discord.utils.get(ctx.guild.roles, name="Supporter")
        return supporter_role is not None and supporter_role in ctx.author.roles
    return commands.check(predicate)

class UtilityCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='deletebotmsg')
    @is_admin_or_supporter()
    async def delete_bot_message(self, ctx: commands.Context, message_id: int):
        """Xóa một tin nhắn cụ thể do bot này gửi."""
        
        # Xóa tin nhắn lệnh của người dùng ngay lập tức
        await ctx.message.delete()
        
        try:
            # Lấy tin nhắn từ ID trong kênh hiện tại
            msg_to_delete = await ctx.channel.fetch_message(message_id)

            # Kiểm tra xem tin nhắn có phải do bot này gửi không
            if msg_to_delete.author.id == self.bot.user.id:
                await msg_to_delete.delete()
                # Gửi thông báo thành công và xóa sau 2 giây
                await ctx.send("✅ Đã xóa tin nhắn thành công.", delete_after=2)
            else:
                # Gửi thông báo lỗi và xóa sau 2 giây
                await ctx.send("🚫 Lỗi: Tôi chỉ có thể xóa tin nhắn do chính tôi gửi.", delete_after=2)

        except discord.NotFound:
            # Nếu không tìm thấy ID tin nhắn
            await ctx.send("⚠️ Không tìm thấy tin nhắn với ID này trong kênh hiện tại.", delete_after=2)
        except discord.Forbidden:
            # Nếu bot không có quyền xóa tin nhắn
            await ctx.send("🚫 Lỗi: Tôi không có quyền để xóa tin nhắn trong kênh này.", delete_after=2)
        except Exception as e:
            # Các lỗi khác
            print(f"Error deleting message: {e}")
            await ctx.send("Có lỗi xảy ra, vui lòng thử lại.", delete_after=2)
            
    # Xử lý lỗi riêng cho lệnh này
    @delete_bot_message.error
    async def deletebotmsg_error(self, ctx, error):
        if isinstance(error, commands.CheckFailure):
            await ctx.send("🚫 Bạn không có quyền sử dụng lệnh này.", delete_after=2)
            await ctx.message.delete(delay=2)
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send("⚠️ Vui lòng nhập ID của tin nhắn. Cú pháp: `?deletebotmsg [ID tin nhắn]`", delete_after=5)
            await ctx.message.delete(delay=5)
        elif isinstance(error, commands.BadArgument):
            await ctx.send("⚠️ ID tin nhắn phải là một con số.", delete_after=3)
            await ctx.message.delete(delay=3)


# Hàm setup để bot có thể load Cog này
async def setup(bot):
    await bot.add_cog(UtilityCog(bot))
