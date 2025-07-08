import discord
from discord.ext import commands

def is_admin_or_supporter():
    async def predicate(ctx):
        if ctx.author.guild_permissions.administrator: return True
        supporter_role = discord.utils.get(ctx.guild.roles, name="Supporter")
        return supporter_role is not None and supporter_role in ctx.author.roles
    return commands.check(predicate)

class EmbedCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='embed')
    @is_admin_or_supporter()
    async def create_embed(self, ctx: commands.Context):
        await ctx.message.delete()
        command_prefix_len = len(ctx.prefix) + len(ctx.invoked_with)
        raw_input = ctx.message.content[command_prefix_len:].strip()
        
        # ====> THAY ĐỔI CÁC DÒNG DƯỚI ĐÂY <====
        error_syntax_message = (
            "⚠️ **Lỗi:** Cú pháp không đúng.\n\n"
            "**Cú pháp đúng:**\n"
            "```\n"
            "!embed Tiêu đề của embed\n"  # <-- Đã đổi
            "Nội dung của embed được viết ở đây.\n"
            "```"
        )
        
        if not raw_input:
            await ctx.send(error_syntax_message, delete_after=10)
            return

        parts = raw_input.split('\n', 1)
        title = parts[0]
        
        if len(parts) < 2 or not parts[1].strip():
            await ctx.send(error_syntax_message, delete_after=10)
            return

        content = parts[1]
        embed = discord.Embed(title=title, description=content, color=discord.Color.blue())
        embed.set_footer(text=f"Tạo bởi: {ctx.author.display_name}", icon_url=ctx.author.avatar)
        await ctx.send(embed=embed)

    @create_embed.error
    async def embed_error(self, ctx, error):
        if isinstance(error, commands.CheckFailure):
            await ctx.send("🚫 Bạn không có quyền sử dụng lệnh này.", delete_after=3)
        else:
            print(f"An unexpected error occurred in 'embed' command: {error}")

async def setup(bot):
    await bot.add_cog(EmbedCog(bot))
