import discord
from discord.ext import commands

# Hàm kiểm tra quyền: Chỉ Admin hoặc người có role "Supporter" mới được dùng
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

    # --- SỬA ĐỔI LỆNH ?PIN ---
    # Thêm kiểm tra để ngăn ghim tin nhắn thứ hai
    @commands.command(name='pin')
    @commands.check(is_admin_or_supporter)
    async def pin_message(self, ctx, *, message_content: str):
        """Ghim một tin nhắn và giữ nó luôn ở dưới cùng kênh chat."""
        # Xóa tin nhắn lệnh của người dùng trước tiên
        try:
            await ctx.message.delete()
        except (discord.Forbidden, discord.NotFound):
            pass

        # Kiểm tra xem kênh này đã có tin nhắn ghim chưa
        if ctx.channel.id in self.sticky_messages:
            # Gửi tin nhắn lỗi và tự xóa sau 15 giây
            await ctx.send(
                f"{ctx.author.mention}, kênh này đã có một tin nhắn được ghim. "
                f"Vui lòng dùng lệnh `?stoppin` để gỡ tin nhắn cũ trước.",
                delete_after=15
            )
            return # Dừng thực thi lệnh

        # Định dạng nội dung tin nhắn ghim (với khoảng trống)
        formatted_content = f"## 📌 Tin Nhắn Được Ghim\n\n\n\n{message_content}"

        # Gửi tin nhắn ghim mới
        new_sticky_message = await ctx.send(formatted_content)

        # Lưu thông tin về tin nhắn ghim
        self.sticky_messages[ctx.channel.id] = {
            'content': formatted_content,
            'last_message': new_sticky_message
        }
        print(f"Đã ghim tin nhắn mới tại kênh #{ctx.channel.name}")

    # --- THÊM LỆNH MỚI: ?STOPPIN ---
    @commands.command(name='stoppin')
    @commands.check(is_admin_or_supporter)
    async def stop_pin(self, ctx):
        """Dừng ghim và xóa tin nhắn ghim hiện tại trong kênh."""
        # Xóa tin nhắn lệnh của người dùng
        try:
            await ctx.message.delete()
        except (discord.Forbidden, discord.NotFound):
            pass

        # Kiểm tra xem kênh có tin nhắn ghim để dừng không
        if ctx.channel.id in self.sticky_messages:
            sticky_info = self.sticky_messages[ctx.channel.id]

            # Cố gắng xóa tin nhắn ghim cuối cùng của bot
            try:
                await sticky_info['last_message'].delete()
            except discord.NotFound:
                print(f"Tin nhắn ghim ở kênh #{ctx.channel.name} đã bị xóa thủ công.")
            except discord.Forbidden:
                await ctx.send("Bot không có quyền xóa tin nhắn trong kênh này.", delete_after=10)
                return

            # Xóa thông tin về tin nhắn ghim khỏi bộ nhớ của bot
            del self.sticky_messages[ctx.channel.id]

            await ctx.send("✅ Đã dừng và gỡ bỏ tin nhắn ghim tại kênh này.", delete_after=10)
            print(f"Đã dừng ghim tin nhắn tại kênh #{ctx.channel.name}")
        else:
            # Nếu kênh không có tin nhắn ghim nào
            await ctx.send("Kênh này không có tin nhắn nào đang được ghim.", delete_after=10)

    # Xử lý lỗi chung cho các lệnh trong Cog này
    @pin_message.error
    @stop_pin.error
    async def pin_error(self, ctx, error):
        if isinstance(error, commands.CheckFailure):
            # Xóa tin nhắn lệnh của người dùng
            try:
                await ctx.message.delete()
            except (discord.Forbidden, discord.NotFound):
                pass
            await ctx.send(
                f"{ctx.author.mention}, bạn không có quyền sử dụng lệnh này. Cần quyền Admin hoặc vai trò `Supporter`.",
                delete_after=10
            )

# Hàm setup để load Cog
async def setup(bot):
    await bot.add_cog(PinCog(bot, bot.sticky_messages))
