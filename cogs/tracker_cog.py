import discord
from discord.ext import commands
import os
import validators
from app import database as db

BASE_URL = os.getenv("BASE_URL")

class TrackerCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        if not BASE_URL:
            print("⚠️  CẢNH BÁO: Biến môi trường BASE_URL chưa được thiết lập!")

    @commands.command(name='iptracker')
    @commands.cooldown(1, 10, commands.BucketType.user)
    # XÓA @commands.dm_only()
    async def create_tracker(self, ctx: commands.Context, *, url: str):
        """Tạo một link theo dõi IP. Sẽ trả lời vào DM."""
        
        await ctx.message.delete() # Xóa tin nhắn lệnh gốc

        if not BASE_URL:
            await ctx.send("🚫 Lỗi hệ thống: Admin chưa cấu hình `BASE_URL`.", delete_after=10)
            return

        if db.get_tracker_by_creator(ctx.author.id):
            await ctx.send(f"🚫 {ctx.author.mention}, bạn đã có link đang hoạt động. Dùng `!stopiptracker` để xóa link cũ.", delete_after=10)
            return

        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
            
        if not validators.url(url):
            await ctx.send(f"🚫 {ctx.author.mention}, URL không hợp lệ. Vui lòng cung cấp URL đúng. Ví dụ: `!iptracker google.com`", delete_after=10)
            return
            
        try:
            tracker_id = db.add_tracker(ctx.author.id, url)
            tracking_url = f"{BASE_URL}/track/{tracker_id}"
            
            embed = discord.Embed(
                title="✅ Link theo dõi đã được tạo!",
                description="Gửi link này cho 'nạn nhân'. Mỗi khi có người truy cập, tôi sẽ gửi thông báo chi tiết vào DM cho bạn.",
                color=discord.Color.blue()
            )
            embed.add_field(name="🔗 Link theo dõi của bạn", value=f"```{tracking_url}```", inline=False)
            embed.add_field(name="🎯 Link đích (chuyển hướng đến)", value=url, inline=False)
            embed.set_footer(text="Dùng lệnh !stopiptracker để xóa link này.")
            
            # GỬI KẾT QUẢ VÀO DM CỦA NGƯỜI DÙNG
            await ctx.author.send(embed=embed)
            await ctx.send(f"✅ {ctx.author.mention}, tôi đã gửi link theo dõi vào tin nhắn riêng của bạn!", delete_after=5)

        except discord.Forbidden:
             # Xử lý trường hợp người dùng khóa DM
            await ctx.send(f"🚫 {ctx.author.mention}, tôi không thể gửi tin nhắn cho bạn. Vui lòng mở khóa tin nhắn riêng từ thành viên server này.", delete_after=10)
            db.remove_tracker(ctx.author.id) # Xóa link đã tạo vì không gửi được
        except Exception as e:
            print(f"Lỗi khi tạo tracker: {e}")
            await ctx.send("🚫 Đã có lỗi xảy ra phía server, vui lòng thử lại sau.", delete_after=10)

    @commands.command(name='stopiptracker')
    @commands.cooldown(1, 5, commands.BucketType.user)
    # XÓA @commands.dm_only()
    async def stop_tracker(self, ctx: commands.Context):
        """Dừng và xóa link theo dõi đang hoạt động."""
        await ctx.message.delete() # Xóa tin nhắn lệnh gốc
        if db.remove_tracker(ctx.author.id):
            await ctx.send(f"✅ {ctx.author.mention}, link theo dõi của bạn đã được xóa thành công.", delete_after=5)
        else:
            await ctx.send(f"ℹ️ {ctx.author.mention}, bạn không có link theo dõi nào đang hoạt động.", delete_after=5)

    @create_tracker.error
    async def tracker_error(self, ctx, error):
        if isinstance(error, commands.CommandOnCooldown):
            await ctx.message.delete()
            await ctx.send(f"⏳ {ctx.author.mention}, vui lòng chờ {error.retry_after:.1f} giây.", delete_after=5)
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.message.delete()
            await ctx.send("⚠️ Cú pháp sai! Ví dụ: `!iptracker google.com`", delete_after=5)
        else:
            # Không xóa tin nhắn gốc để dễ debug
            print(f"Lỗi không xác định trong TrackerCog: {error}")
            await ctx.send(f"🚫 Đã xảy ra lỗi không xác định. Vui lòng báo cho Admin.\n`{error}`", delete_after=10)

# Phần async def setup(bot) giữ nguyên không đổi

async def setup(bot):
    await bot.add_cog(TrackerCog(bot))
