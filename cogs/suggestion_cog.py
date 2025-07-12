# ./cogs/suggestion_cog.py
import discord
from discord.ext import commands

# --- CẤU HÌNH NGHIÊM TÚC ---
SUGGESTION_CHANNEL_ID = 1393423014670106778
# -----------------------------

class SuggestionCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # --- LỆNH GÓP Ý CÔNG KHAI ---
    @commands.command(name='suggest')
    @commands.cooldown(1, 60, commands.BucketType.user)
    async def suggest(self, ctx: commands.Context, *, content: str):
        """Gửi góp ý công khai."""
        try: await ctx.message.delete()
        except: pass

        suggestion_channel = self.bot.get_channel(SUGGESTION_CHANNEL_ID)
        if not suggestion_channel:
            print(f"LỖI: Không tìm thấy kênh góp ý ID {SUGGESTION_CHANNEL_ID}")
            await ctx.send("❌ Hệ thống góp ý đang gặp sự cố, vui lòng báo Admin!", delete_after=10)
            return

        # Embed công khai, đầy đủ thông tin
        embed = discord.Embed(
            title=f"📝 {ctx.author.display_name} đã góp ý!",
            description=content,
            color=discord.Color.gold(),
            timestamp=ctx.message.created_at
        )
        embed.set_author(name=ctx.author.name, icon_url=ctx.author.avatar)
        embed.set_footer(text=f"Từ server: {ctx.guild.name}")
        
        await suggestion_channel.send(embed=embed)
        await ctx.send(f"✅ Cảm ơn {ctx.author.mention}, góp ý của bạn đã được gửi đi!", delete_after=5)

    # --- LỆNH GÓP Ý BÍ MẬT (SECRET) ---
    @commands.command(name='suggest_secret')
    @commands.cooldown(1, 200, commands.BucketType.user)
    async def suggest_secret(self, ctx: commands.Context, *, content: str):
        """Gửi góp ý ẩn danh."""
        try: await ctx.message.delete()
        except: pass

        suggestion_channel = self.bot.get_channel(SUGGESTION_CHANNEL_ID)
        if not suggestion_channel:
            print(f"LỖI: Không tìm thấy kênh góp ý ID {SUGGESTION_CHANNEL_ID}")
            await ctx.send("❌ Hệ thống góp ý đang gặp sự cố, vui lòng báo Admin!", delete_after=10)
            return

        # Embed ẩn danh, không lộ danh tính
        embed = discord.Embed(
            title="🤫 Một Góp Ý Ẩn Danh",
            description=content,
            color=discord.Color.dark_grey(),
            timestamp=ctx.message.created_at
        )
        embed.set_footer(text="Gửi từ chế độ ẩn danh")

        await suggestion_channel.send(embed=embed)
        await ctx.send(f"✅ Cảm ơn {ctx.author.mention}, góp ý ẩn danh của bạn đã được gửi đi an toàn!", delete_after=5)

    # --- BỘ XỬ LÝ LỖI CHUNG ---
    async def cog_command_error(self, ctx: commands.Context, error: commands.CommandError):
        """Bắt lỗi chung cho cả 2 lệnh trong cog này."""
        if isinstance(error, commands.CommandOnCooldown):
            await ctx.send(f"⏳ Bạn đang thao tác quá nhanh! Vui lòng chờ thêm **{error.retry_after:.1f} giây**.", delete_after=5)
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f"⚠️ {ctx.author.mention}, bạn quên nhập nội dung góp ý rồi!", delete_after=7)
        else:
            print(f"Lỗi không xác định trong SuggestionCog: {error}")
            await ctx.send("🤖 Oups, có lỗi gì đó bất ngờ xảy ra rồi!", delete_after=5)

# Hàm setup để bot có thể load cog này
async def setup(bot: commands.Bot):
    await bot.add_cog(SuggestionCog(bot))
