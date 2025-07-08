import discord
from discord.ext import commands

# --- Hàm kiểm tra quyền ---
# Kiểm tra xem người dùng có phải là Admin hoặc có Role "Supporter" hay không
def is_admin_or_supporter():
    async def predicate(ctx):
        # Kiểm tra nếu có quyền administrator
        if ctx.author.guild_permissions.administrator:
            return True
        # Kiểm tra nếu có role "Supporter"
        supporter_role = discord.utils.get(ctx.guild.roles, name="Supporter")
        return supporter_role is not None and supporter_role in ctx.author.roles
    return commands.check(predicate)

class EmbedCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # --- LOGIC ĐÃ ĐƯỢC CẬP NHẬT ---
    @commands.command(name='embed')
    @is_admin_or_supporter()
    async def create_embed(self, ctx: commands.Context, *, title: str):
        """
        Tạo embed với tiêu đề ở dòng đầu tiên và nội dung ở các dòng tiếp theo.
        Cú pháp:
        ?embed [Tiêu đề của bạn ở đây]
        [Nội dung của bạn bắt đầu từ dòng này]
        [Có thể có nhiều dòng nội dung]
        """
        
        # Xóa tin nhắn lệnh gốc của người dùng
        await ctx.message.delete()

        # Tách nội dung tin nhắn gốc thành các dòng
        lines = ctx.message.content.split('\n')
        
        # Kiểm tra xem có nội dung ở các dòng tiếp theo hay không
        # Nếu chỉ có 1 dòng (dòng lệnh) thì không có nội dung -> báo lỗi
        if len(lines) < 2:
            await ctx.send(
                "⚠️ **Lỗi:** Bạn cần cung cấp nội dung cho embed ở dòng thứ hai.\n\n"
                "**Cú pháp đúng:**\n"
                "```\n"
                "?embed Tiêu đề của embed\n"
                "Nội dung của embed được viết ở đây.\n"
                "```", 
                delete_after=10)
            return # Dừng hàm tại đây
        
        # Lấy nội dung từ dòng thứ hai trở đi và ghép lại
        content = '\n'.join(lines[1:])

        # Kiểm tra xem nội dung có rỗng không (phòng trường hợp người dùng chỉ xuống dòng mà không nhập gì)
        if not content.strip():
            await ctx.send("⚠️ **Lỗi:** Phần nội dung của embed không được để trống.", delete_after=5)
            return

        # Tạo và gửi embed
        embed = discord.Embed(
            title=title,
            description=content,
            color=discord.Color.green() # Đổi màu cho mới lạ
        )
        embed.set_footer(text=f"Tạo bởi: {ctx.author.display_name}", icon_url=ctx.author.avatar)

        await ctx.send(embed=embed)

    # Xử lý lỗi riêng cho Cog này
    @create_embed.error
    async def embed_error(self, ctx, error):
        # Lỗi không có quyền
        if isinstance(error, commands.CheckFailure):
            msg = await ctx.send("🚫 Bạn không có quyền sử dụng lệnh này.", delete_after=3)
            await ctx.message.delete(delay=3)
            
        # Lỗi khi người dùng chỉ gõ "?embed" mà không có tiêu đề
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.message.delete()
            await ctx.send(
                "⚠️ **Lỗi:** Bạn cần nhập tiêu đề cho embed.\n\n"
                "**Cú pháp đúng:**\n"
                "```\n"
                "?embed Tiêu đề của embed\n"
                "Nội dung của embed được viết ở đây.\n"
                "```", 
                delete_after=10)


# Hàm setup để bot có thể load Cog này
async def setup(bot):
    await bot.add_cog(EmbedCog(bot))
