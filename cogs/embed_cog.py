import discord
from discord.ext import commands

# --- Hàm kiểm tra quyền ---
def is_admin_or_supporter():
    async def predicate(ctx):
        if ctx.author.guild_permissions.administrator:
            return True
        supporter_role = discord.utils.get(ctx.guild.roles, name="Supporter")
        return supporter_role is not None and supporter_role in ctx.author.roles
    return commands.check(predicate)

class EmbedCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # --- LOGIC ĐƯỢC THIẾT KẾ LẠI HOÀN TOÀN ---
    # Lệnh không còn tự động nhận tham số, chúng ta sẽ tự xử lý
    @commands.command(name='embed')
    @is_admin_or_supporter()
    async def create_embed(self, ctx: commands.Context):
        """
        Tạo embed với tiêu đề ở dòng đầu tiên và nội dung ở các dòng tiếp theo.
        Cú pháp:
        ?embed [Tiêu đề của bạn]
        [Nội dung của bạn]
        """
        
        # Xóa tin nhắn lệnh gốc của người dùng ngay lập tức
        await ctx.message.delete()

        # Lấy phần nội dung người dùng nhập sau tên lệnh (ví dụ: "?embed ")
        # Lấy độ dài của "?embed " để cắt chuỗi cho chính xác
        # ctx.invoked_with sẽ lấy đúng tên lệnh được gõ (kể cả khi dùng alias)
        command_prefix_len = len(ctx.prefix) + len(ctx.invoked_with)
        raw_input = ctx.message.content[command_prefix_len:].strip()

        # TRƯỜNG HỢP 1: Người dùng chỉ gõ "?embed"
        if not raw_input:
            await ctx.send(
                "⚠️ **Lỗi:** Bạn cần cung cấp tiêu đề và nội dung.\n\n"
                "**Cú pháp đúng:**\n"
                "```\n"
                "?embed Tiêu đề của embed\n"
                "Nội dung của embed được viết ở đây.\n"
                "```", 
                delete_after=10)
            return

        # Tách chuỗi tại ký tự xuống dòng đầu tiên
        # Nó sẽ tạo ra một list có tối đa 2 phần tử: [tiêu đề, phần còn lại]
        parts = raw_input.split('\n', 1)
        
        title = parts[0] # Tiêu đề luôn là phần tử đầu tiên

        # TRƯỜNG HỢP 2: Người dùng chỉ cung cấp tiêu đề mà không có nội dung
        # (Không có ký tự xuống dòng, hoặc phần sau đó rỗng)
        if len(parts) < 2 or not parts[1].strip():
            await ctx.send(
                "⚠️ **Lỗi:** Bạn cần cung cấp nội dung cho embed ở dòng thứ hai.\n\n"
                "**Cú pháp đúng:**\n"
                "```\n"
                "?embed Tiêu đề của embed\n"
                "Nội dung của embed được viết ở đây.\n"
                "```", 
                delete_after=10)
            return

        content = parts[1] # Nội dung là tất cả phần còn lại

        # Tạo và gửi embed
        embed = discord.Embed(
            title=title,
            description=content,
            color=discord.Color.blue()
        )
        embed.set_footer(text=f"Tạo bởi: {ctx.author.display_name}", icon_url=ctx.author.avatar)

        await ctx.send(embed=embed)

    # Xử lý lỗi cho lệnh này
    # Chúng ta chỉ cần xử lý lỗi không có quyền, vì các lỗi cú pháp đã được xử lý bên trong lệnh
    @create_embed.error
    async def embed_error(self, ctx, error):
        if isinstance(error, commands.CheckFailure):
            msg = await ctx.send("🚫 Bạn không có quyền sử dụng lệnh này.", delete_after=3)
            # Không cần xóa tin nhắn gốc ở đây vì nó đã được xóa ở đầu lệnh
        else:
            # Ghi lại các lỗi không mong muốn khác để debug
            print(f"An unexpected error occurred in 'embed' command: {error}")


# Hàm setup để bot có thể load Cog này
async def setup(bot):
    await bot.add_cog(EmbedCog(bot))
