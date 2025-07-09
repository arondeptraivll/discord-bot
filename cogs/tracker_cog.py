# cogs/tracker_cog.py
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
            print("⚠️  CẢNH BÁO: Biến môi trường BASE_URL chưa được thiết lập trong file .env!")
            print("⚠️  Chức năng IP Tracker sẽ không hoạt động chính xác.")


    @commands.command(name='iptracker')
    @commands.cooldown(1, 10, commands.BucketType.user)
    @commands.dm_only() # Lệnh này chỉ nên dùng trong DM để đảm bảo riêng tư
    async def create_tracker(self, ctx: commands.Context, *, url: str):
        """Tạo một link theo dõi IP và thông tin trình duyệt."""
        
        # Kiểm tra xem BASE_URL đã được cấu hình chưa
        if not BASE_URL:
            await ctx.send("🚫 Lỗi hệ thống: Admin chưa cấu hình `BASE_URL`. Vui lòng liên hệ Admin.")
            return

        # Kiểm tra xem người dùng đã có link nào chưa
        if db.get_tracker_by_creator(ctx.author.id):
            embed = discord.Embed(
                title="🚫 Lỗi: Bạn đã có một link theo dõi đang hoạt động",
                description="Mỗi người chỉ được tạo một link theo dõi tại một thời điểm.\n"
                            "Hãy dùng `!stopiptracker` để xóa link cũ trước khi tạo link mới.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return

        # Kiểm tra định dạng URL
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
            
        if not validators.url(url):
            embed = discord.Embed(
                title="🚫 Lỗi: URL không hợp lệ",
                description="Vui lòng cung cấp một URL hợp lệ. Ví dụ:\n"
                            "`!iptracker google.com`\n"
                            "`!iptracker https://youtube.com/watch?v=dQw4w9WgXcQ`",
                color=discord.Color.orange()
            )
            await ctx.send(embed=embed)
            return
            
        # Tạo tracker trong database
        try:
            tracker_id = db.add_tracker(ctx.author.id, url)
            tracking_url = f"{BASE_URL}/track/{tracker_id}"
            
            embed = discord.Embed(
                title="✅ Link theo dõi đã được tạo thành công!",
                description="Gửi link này cho 'nạn nhân'. Mỗi khi có người truy cập, tôi sẽ gửi thông báo chi tiết vào DM này cho bạn.",
                color=discord.Color.blue()
            )
            embed.add_field(name="🔗 Link theo dõi của bạn", value=f"```{tracking_url}```", inline=False)
            embed.add_field(name="🎯 Link đích (sẽ chuyển hướng đến)", value=url, inline=False)
            embed.set_footer(text="Dùng lệnh !stopiptracker để xóa link này.")
            await ctx.send(embed=embed)
            
        except Exception as e:
            print(f"Lỗi khi tạo tracker: {e}")
            await ctx.send("🚫 Đã có lỗi xảy ra phía server, vui lòng thử lại sau.")

    @commands.command(name='stopiptracker')
    @commands.cooldown(1, 5, commands.BucketType.user)
    @commands.dm_only()
    async def stop_tracker(self, ctx: commands.Context):
        """Dừng và xóa link theo dõi đang hoạt động của bạn."""
        if db.remove_tracker(ctx.author.id):
            embed = discord.Embed(
                title="✅ Đã dừng thành công",
                description="Link theo dõi của bạn đã được xóa khỏi hệ thống. Bạn có thể tạo một link mới.",
                color=discord.Color.green()
            )
            await ctx.send(embed=embed)
        else:
            embed = discord.Embed(
                title="ℹ️ Thông tin",
                description="Bạn không có link theo dõi nào đang hoạt động.",
                color=discord.Color.light_grey()
            )
            await ctx.send(embed=embed)

    @create_tracker.error
    @stop_tracker.error
    async def tracker_error(self, ctx, error):
        if isinstance(error, commands.CommandOnCooldown):
            await ctx.send(f"⏳ Vui lòng chờ {error.retry_after:.1f} giây trước khi dùng lệnh này lần nữa.")
        elif isinstance(error, commands.PrivateMessageOnly):
             await ctx.send("🚫 Lệnh này chỉ có thể được sử dụng trong tin nhắn riêng (DM) với bot để đảm bảo sự riêng tư.", delete_after=10)
             await ctx.message.delete(delay=10)
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send("⚠️ Cú pháp sai! Vui lòng nhập URL. Ví dụ: `!iptracker google.com`")
        else:
            print(f"Lỗi không xác định trong TrackerCog: {error}")

async def setup(bot):
    await bot.add_cog(TrackerCog(bot))
