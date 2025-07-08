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

    @commands.command(name='embed')
    @is_admin_or_supporter()
    async def create_embed(self, ctx: commands.Context, title: str, *, content: str):
        """Tạo một embed đẹp với tiêu đề và nội dung được cung cấp."""
        
        # Xóa tin nhắn lệnh của người dùng để giữ kênh chat sạch sẽ
        await ctx.message.delete()
        
        # Tạo đối tượng Embed
        embed = discord.Embed(
            title=title,
            description=content,
            color=discord.Color.blue() # Bạn có thể đổi màu tại đây
        )
        embed.set_footer(text=f"Tạo bởi: {ctx.author.display_name}", icon_url=ctx.author.avatar)

        # Gửi embed
        await ctx.send(embed=embed)

    # Xử lý lỗi riêng cho Cog này
    @create_embed.error
    async def embed_error(self, ctx, error):
        if isinstance(error, commands.CheckFailure):
            msg = await ctx.send("🚫 Bạn không có quyền sử dụng lệnh này.", delete_after=2)
            await ctx.message.delete(delay=2) # Xóa lệnh gốc
        elif isinstance(error, commands.MissingRequiredArgument):
            msg = await ctx.send("⚠️ Vui lòng nhập đủ các tham số. Cú pháp: `?embed [Tiêu đề] [Nội dung]`", delete_after=5)
            await ctx.message.delete(delay=5)


# Hàm setup để bot có thể load Cog này
async def setup(bot):
    await bot.add_cog(EmbedCog(bot))
