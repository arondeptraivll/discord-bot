# ./cogs/suggestion_cog.py
import discord
from discord.ext import commands

# --- CẤU HÌNH NGHIÊM TÚC ---
# ID của kênh mà bot sẽ gửi các góp ý vào.
# Nhớ thay đổi ID này nếu bạn muốn đổi kênh trong tương lai.
SUGGESTION_CHANNEL_ID = 1393423014670106778 
# -----------------------------

class SuggestionCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name='suggest')
    # Cooldown: 1 lần mỗi 60 giây cho mỗi người dùng. Chống spam hiệu quả!
    @commands.cooldown(1, 60, commands.BucketType.user) 
    async def suggest_command(self, ctx: commands.Context, *, content: str):
        """
        Lệnh cho phép người dùng gửi góp ý tới một kênh được chỉ định.
        """
        # Xóa tin nhắn lệnh gốc của người dùng để giữ kênh chat sạch sẽ
        try:
            await ctx.message.delete()
        except discord.Forbidden:
            print(f"Lỗi: Bot không có quyền 'Manage Messages' để xóa lệnh !suggest của {ctx.author.name}")
        except discord.NotFound:
            pass # Tin nhắn có thể đã bị xóa rồi, bỏ qua

        # Tìm kênh để gửi góp ý dựa trên ID đã cấu hình
        suggestion_channel = self.bot.get_channel(SUGGESTION_CHANNEL_ID)

        # Kiểm tra xem có tìm thấy kênh không
        if not suggestion_channel:
            # Gửi cảnh báo cho người dùng và thông báo trong console
            print(f"LỖI NGHIÊM TRỌNG: Không tìm thấy kênh góp ý với ID {SUGGESTION_CHANNEL_ID}")
            await ctx.send("❌ Đã có lỗi xảy ra với hệ thống góp ý. Vui lòng báo cho Admin.", delete_after=10)
            return

        # Tạo embed xịn sò để gửi đi
        embed = discord.Embed(
            title=f"📝 {ctx.author.display_name} đã góp ý!",
            description=content,
            color=discord.Color.gold(), # Màu vàng cho nó "quý's tộc's"
            timestamp=ctx.message.created_at # Thêm cả thời gian người dùng gửi cho chuẩn
        )
        embed.set_author(name=f"Từ: {ctx.author.name}", icon_url=ctx.author.avatar)
        embed.set_footer(text=f"ID Người Góp Ý: {ctx.author.id}")
        
        # Gửi embed vào kênh góp ý
        try:
            await suggestion_channel.send(embed=embed)
            # Phản hồi cho người dùng biết là đã thành công
            await ctx.send(f"✅ Cảm ơn {ctx.author.mention}, góp ý của bạn đã được gửi đi!", delete_after=5)
        except discord.Forbidden:
            print(f"LỖI NGHIÊM TRỌNG: Bot không có quyền gửi tin nhắn trong kênh ID {SUGGESTION_CHANNEL_ID}")
            await ctx.send("❌ Hệ thống góp ý đang gặp lỗi quyền, báo Admin ngay!", delete_after=10)

    # Xử lý lỗi cho lệnh suggest
    @suggest_command.error
    async def suggest_error(self, ctx: commands.Context, error):
        # Lỗi gõ lệnh quá nhanh (cooldown)
        if isinstance(error, commands.CommandOnCooldown):
            await ctx.send(f"⏳ Chờ chút đã... Bạn cần chờ thêm **{error.retry_after:.1f} giây** nữa để góp ý tiếp.", delete_after=5)
        # Lỗi quên nhập nội dung
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f"⚠️ {ctx.author.mention}, bạn quên nhập nội dung góp ý rồi! Cú pháp: `!suggest [nội dung]`", delete_after=7)
        else:
            # Ghi lại các lỗi không mong muốn khác
            print(f"Lỗi không xác định trong lệnh suggest: {error}")
            await ctx.send("🤖 Oups, có lỗi gì đó xảy ra rồi, thử lại sau nhé!", delete_after=5)

# Hàm setup để bot có thể load cog này
async def setup(bot: commands.Bot):
    await bot.add_cog(SuggestionCog(bot))
