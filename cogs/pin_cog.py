import discord
from discord.ext import commands
from discord.utils import get

# Hàm kiểm tra quyền: Phải là Admin hoặc có role "Supporter"
# Bạn có thể đổi tên "Supporter" thành bất cứ tên gì bạn muốn
def is_admin_or_supporter():
    async def predicate(ctx):
        # Kiểm tra nếu người dùng là admin
        if ctx.author.guild_permissions.administrator:
            return True
        # Kiểm tra nếu người dùng có role "Supporter"
        supporter_role = get(ctx.guild.roles, name="Supporter")
        if supporter_role and supporter_role in ctx.author.roles:
            return True
        return False
    return commands.check(predicate)

class PinCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # Dictionary để lưu trữ tin nhắn đang được ghim
        # Key: channel_id, Value: {'message_id': ..., 'content': ...}
        self.pinned_messages = {}

    def format_pinned_message(self, content):
        return f"## 📌 Pinned Message\n\n{content}"

    @commands.Cog.listener()
    async def on_message(self, message):
        # Bỏ qua tin nhắn từ chính bot để tránh vòng lặp vô hạn
        if message.author == self.bot.user:
            return

        # Kiểm tra xem kênh này có tin nhắn đang được ghim không
        if message.channel.id in self.pinned_messages:
            pin_data = self.pinned_messages[message.channel.id]

            # 1. Xóa tin nhắn ghim cũ
            try:
                old_pinned_msg = await message.channel.fetch_message(pin_data['message_id'])
                await old_pinned_msg.delete()
            except discord.NotFound:
                # Tin nhắn có thể đã bị xóa thủ công, không sao cả
                print(f"Tin nhắn ghim cũ trong kênh {message.channel.id} không tìm thấy.")
            except discord.Forbidden:
                print(f"Không có quyền xóa tin nhắn trong kênh {message.channel.name}")
                # Có thể gửi thông báo lỗi cho admin ở đây nếu cần

            # 2. Gửi lại tin nhắn ghim mới
            try:
                new_pinned_msg = await message.channel.send(self.format_pinned_message(pin_data['content']))
                # 3. Cập nhật ID tin nhắn mới vào bộ nhớ
                self.pinned_messages[message.channel.id]['message_id'] = new_pinned_msg.id
            except discord.Forbidden:
                 print(f"Không có quyền gửi tin nhắn trong kênh {message.channel.name}")


    @commands.command(name='pin')
    @is_admin_or_supporter()
    async def pin_message(self, ctx, *, message_content: str):
        """Ghim một tin nhắn và giữ nó ở cuối kênh."""
        # Kiểm tra xem kênh này đã có tin nhắn được ghim chưa
        if ctx.channel.id in self.pinned_messages:
            await ctx.send("Kênh này đã có một tin nhắn được ghim. Vui lòng dùng `?stoppin` trước.", ephemeral=True, delete_after=10)
            return

        # Xóa tin nhắn lệnh của người dùng
        try:
            await ctx.message.delete()
        except discord.Forbidden:
            print("Không có quyền xóa tin nhắn lệnh.")

        # Gửi tin nhắn ghim và lưu thông tin
        pinned_msg = await ctx.send(self.format_pinned_message(message_content))
        self.pinned_messages[ctx.channel.id] = {
            'message_id': pinned_msg.id,
            'content': message_content
        }
        print(f"Đã ghim tin nhắn trong kênh #{ctx.channel.name}")

    @commands.command(name='stoppin')
    @is_admin_or_supporter()
    async def stop_pinning(self, ctx):
        """Dừng ghim và xóa tin nhắn đang được ghim trong kênh."""
        if ctx.channel.id in self.pinned_messages:
            pin_data = self.pinned_messages.pop(ctx.channel.id) # Lấy và xóa khỏi dict
            try:
                pinned_msg = await ctx.channel.fetch_message(pin_data['message_id'])
                await pinned_msg.delete()
                await ctx.send("Đã dừng ghim và xóa tin nhắn thành công.", ephemeral=True, delete_after=10)
                print(f"Đã dừng ghim trong kênh #{ctx.channel.name}")
            except discord.NotFound:
                await ctx.send("Không tìm thấy tin nhắn ghim để xóa (có thể đã bị xóa thủ công). Đã dừng ghim.", ephemeral=True, delete_after=10)
            except discord.Forbidden:
                await ctx.send("Bot không có quyền xóa tin nhắn trong kênh này.", ephemeral=True, delete_after=10)
        else:
            await ctx.send("Kênh này không có tin nhắn nào đang được ghim.", ephemeral=True, delete_after=10)

    # Xử lý lỗi cho các lệnh trong Cog này
    @pin_message.error
    @stop_pinning.error
    async def on_command_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send("Bạn chưa nhập nội dung tin nhắn để ghim. Cú pháp: `?pin [nội dung]`", ephemeral=True)
        elif isinstance(error, commands.CheckFailure):
            await ctx.send("Bạn không có quyền sử dụng lệnh này.", ephemeral=True)
        else:
            print(f"Đã xảy ra lỗi không xác định: {error}")
            await ctx.send("Đã có lỗi xảy ra khi thực thi lệnh.", ephemeral=True)

async def setup(bot):
    await bot.add_cog(PinCog(bot))
