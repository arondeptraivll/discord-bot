import discord
from discord.ext import commands

# Hàm kiểm tra quyền
async def is_admin_or_supporter(ctx):
    if ctx.author.guild_permissions.administrator:
        return True
    supporter_role = discord.utils.get(ctx.guild.roles, name="Supporter")
    if supporter_role and supporter_role in ctx.author.roles:
        return True
    return False

class PinCog(commands.Cog):
    def __init__(self, bot, sticky_messages):
        self.bot = bot
        self.sticky_messages = sticky_messages

    @commands.command(name='pin')
    @commands.check(is_admin_or_supporter)
    async def pin_message(self, ctx, *, message_content: str):
        """Ghim một tin nhắn và giữ nó luôn ở dưới cùng kênh chat."""
        try:
            await ctx.message.delete()
        except (discord.Forbidden, discord.NotFound):
            pass

        if ctx.channel.id in self.sticky_messages:
            await ctx.send(
                f"{ctx.author.mention}, kênh này đã có tin nhắn ghim. Dùng `?stoppin` để gỡ.",
                delete_after=15  # Tự xóa sau 15 giây
            )
            return

        # Định dạng nội dung tin nhắn ghim với 3 dòng trống ở giữa
        formatted_content = f"## 📌 Tin Nhắn Được Ghim\n\n\n\n{message_content}"
        
        new_sticky_message = await ctx.send(formatted_content)
        
        self.sticky_messages[ctx.channel.id] = {
            'content': formatted_content,
            'last_message': new_sticky_message
        }
        print(f"Đã ghim tin nhắn mới tại kênh #{ctx.channel.name}")

    @commands.command(name='stoppin')
    @commands.check(is_admin_or_supporter)
    async def stop_pin(self, ctx):
        """Dừng ghim và xóa tin nhắn ghim hiện tại trong kênh."""
        try:
            await ctx.message.delete()
        except (discord.Forbidden, discord.NotFound):
            pass

        if ctx.channel.id in self.sticky_messages:
            sticky_info = self.sticky_messages.pop(ctx.channel.id) # Lấy và xóa khỏi dict
            try:
                await sticky_info['last_message'].delete()
            except (discord.NotFound, discord.Forbidden):
                pass
            
            await ctx.send("✅ Đã bỏ ghim tin nhắn tại kênh này.", delete_after=15)
            print(f"Đã dừng ghim tin nhắn tại kênh #{ctx.channel.name}")
        else:
            await ctx.send("Kênh này không có tin nhắn nào đang được ghim.", delete_after=15)

    # Xử lý lỗi chung (không có quyền)
    async def cog_command_error(self, ctx, error):
        if isinstance(error, commands.CheckFailure):
            try:
                await ctx.message.delete()
            except (discord.Forbidden, discord.NotFound):
                pass
            await ctx.send(
                f"{ctx.author.mention}, bạn không có quyền dùng lệnh này.",
                delete_after=15
            )
        else:
            # In ra các lỗi khác để debug
            print(f"Lỗi xảy ra trong cog Pin: {error}")


async def setup(bot):
    await bot.add_cog(PinCog(bot, bot.sticky_messages))
