# ./cogs/suggestion_cog.py
import discord
from discord.ext import commands

# --- CẤU HÌNH NGHIÊM TÚC ---
SUGGESTION_CHANNEL_ID = 1393423014670106778
# -----------------------------

class SuggestionCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # --- LỆNH GÓP Ý CÔNG KHAI (Không thay đổi) ---
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

        embed = discord.Embed(
            title=f"📝 {ctx.author.display_name} đã góp ý!",
            description=content, color=discord.Color.gold(), timestamp=ctx.message.created_at
        )
        embed.set_author(name=ctx.author.name, icon_url=ctx.author.avatar)
        embed.set_footer(text=f"Từ server: {ctx.guild.name}")
        
        await suggestion_channel.send(embed=embed)
        await ctx.send(f"✅ Cảm ơn {ctx.author.mention}, góp ý của bạn đã được gửi đi!", delete_after=5)
    
    # --- LỆNH GÓP Ý BÍ MẬT - PHIÊN BẢN TÀNG HÌNH ---
    @commands.command(name='suggest_secret')
    @commands.cooldown(1, 200, commands.BucketType.user)
    async def suggest_secret(self, ctx: commands.Context, *, content: str):
        """Gửi góp ý ẩn danh với độ bảo mật tối đa."""
        # TUYỆT CHIÊU 1: XÓA DẤU VẾT NGAY LẬP TỨC
        try: await ctx.message.delete()
        except: pass # Bỏ qua nếu không có quyền hoặc tin nhắn đã biến mất

        suggestion_channel = self.bot.get_channel(SUGGESTION_CHANNEL_ID)
        if not suggestion_channel:
            # Lỗi hệ thống thì vẫn phải thông báo, nhưng cũng ẩn danh
            print(f"LỖI: Không tìm thấy kênh góp ý ID {SUGGESTION_CHANNEL_ID}")
            await ctx.send("❌ Hệ thống góp ý ẩn danh đang gặp sự cố.", delete_after=5)
            return

        embed = discord.Embed(
            title="🤫 Một Góp Ý Ẩn Danh",
            description=content, color=discord.Color.dark_grey(), timestamp=ctx.message.created_at
        )
        embed.set_footer(text="Gửi từ chế độ ẩn danh")

        await suggestion_channel.send(embed=embed)
        # Gửi lời cảm ơn ẩn danh và tự hủy
        await ctx.send("✅ Góp ý ẩn danh của bạn đã được gửi đi an toàn.", delete_after=3)

    # --- BỘ XỬ LÝ LỖI RIÊNG BIỆT ---

    @suggest.error
    async def suggest_error(self, ctx: commands.Context, error: commands.CommandError):
        """Xử lý lỗi cho lệnh !suggest CÔNG KHAI."""
        # Lỗi công khai thì cứ mention cho người dùng biết
        if isinstance(error, commands.CommandOnCooldown):
            await ctx.send(f"⏳ {ctx.author.mention}, bạn cần chờ **{error.retry_after:.1f} giây** nữa.", delete_after=5)
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f"⚠️ {ctx.author.mention}, bạn quên nhập nội dung góp ý rồi!", delete_after=7)

    @suggest_secret.error
    async def suggest_secret_error(self, ctx: commands.Context, error: commands.CommandError):
        """
        Xử lý lỗi cho lệnh !suggest_secret BÍ MẬT.
        TUYỆT ĐỐI KHÔNG MENTION NGƯỜI DÙNG.
        """
        # Đảm bảo tin nhắn gốc đã bị xóa dù có lỗi gì xảy ra
        try: await ctx.message.delete()
        except: pass

        # TUYỆT CHIÊU 2: PHẢN HỒI "TÀNG HÌNH"
        if isinstance(error, commands.CommandOnCooldown):
            # Không mention, chỉ thông báo chung chung và tự hủy sau 3 giây
            await ctx.send(f"⏳ Lệnh ẩn danh đang trong thời gian hồi. Vui lòng chờ thêm **{error.retry_after:.1f} giây**.", delete_after=3)
        elif isinstance(error, commands.MissingRequiredArgument):
            # Không mention, chỉ báo lỗi và tự hủy
            await ctx.send("⚠️ Lệnh ẩn danh yêu cầu phải có nội dung.", delete_after=5)
        else:
            # Bất kỳ lỗi lạ nào khác, chỉ log ra console cho admin xem
            print(f"Lỗi không xác định trong lệnh suggest_secret: {error}")
            # Và gửi một thông báo chung chung, tự hủy
            await ctx.send("🤖 Đã có lỗi xảy ra với lệnh ẩn danh.", delete_after=3)

async def setup(bot: commands.Bot):
    await bot.add_cog(SuggestionCog(bot))
