# ./cogs/suggestion_cog.py
import discord
from discord.ext import commands
import re # Thêm thư viện re để xử lý chuỗi tốt hơn

# --- CẤU HÌNH NGHIÊM TÚC ---
SUGGESTION_CHANNEL_ID = 1393423014670106778
# -----------------------------

class SuggestionCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        # Tạo 2 bộ lọc cooldown riêng biệt: một cho thường, một cho "điệp viên"
        self._normal_cooldown = commands.CooldownMapping.from_cooldown(1, 60, commands.BucketType.user)
        self._secret_cooldown = commands.CooldownMapping.from_cooldown(1, 200, commands.BucketType.user)

    # Xóa decorator cooldown cũ vì chúng ta cần xử lý động
    @commands.command(name='suggest')
    async def suggest_command(self, ctx: commands.Context, *, full_input: str):
        """
        Lệnh cho phép người dùng gửi góp ý, có tùy chọn ẩn danh.
        Cú pháp: !suggest [nội dung]
        Cú pháp ẩn danh: !suggest [nội dung] secret
        """
        # --- BỘ NÃO CỦA LỆNH: Xử lý input ---
        content = full_input.strip()
        is_secret = False

        # Kiểm tra xem người dùng có muốn làm "điệp viên" không
        # Dùng re.sub để thay thế 'secret' (không phân biệt hoa thường) ở cuối chuỗi
        new_content, num_subs = re.sub(r'\bsecret\s*$', '', content, flags=re.IGNORECASE)
        if num_subs > 0:
            is_secret = True
            content = new_content.strip()

        # Nếu nội dung rỗng sau khi bỏ 'secret' (hoặc ban đầu đã rỗng) -> báo lỗi
        if not content:
            await ctx.send(f"⚠️ {ctx.author.mention}, bạn quên nhập nội dung góp ý rồi! Cú pháp: `!suggest [nội dung]`", delete_after=7)
            return

        # --- BỘ LỌC CHỐNG SPAM PHIÊN BẢN PRO ---
        bucket = self._secret_cooldown.get_bucket(ctx.message) if is_secret else self._normal_cooldown.get_bucket(ctx.message)
        retry_after = bucket.update_rate_limit()
        if retry_after:
            # Nếu bị cooldown, gửi cảnh báo và thoát
            await ctx.send(f"⏳ Bạn đang thao tác quá nhanh! Vui lòng chờ thêm **{retry_after:.1f} giây** nữa.", delete_after=5)
            return
            
        # Xóa tin nhắn lệnh gốc của người dùng
        try:
            await ctx.message.delete()
        except (discord.Forbidden, discord.NotFound):
            pass 

        suggestion_channel = self.bot.get_channel(SUGGESTION_CHANNEL_ID)
        if not suggestion_channel:
            print(f"LỖI NGHIÊM TRỌNG: Không tìm thấy kênh góp ý với ID {SUGGESTION_CHANNEL_ID}")
            await ctx.send("❌ Hệ thống góp ý đang gặp sự cố, vui lòng báo Admin!", delete_after=10)
            return

        # --- TẠO EMBED TÙY BIẾN ---
        if is_secret:
            # Embed phiên bản "điệp viên"
            embed = discord.Embed(
                title="🤫 Một Góp Ý Ẩn Danh",
                description=content,
                color=discord.Color.dark_grey(), # Màu xám bí ẩn
                timestamp=ctx.message.created_at
            )
            embed.set_footer(text="Chế độ ẩn danh")
        else:
            # Embed phiên bản "người thường"
            embed = discord.Embed(
                title=f"📝 {ctx.author.display_name} đã góp ý!",
                description=content,
                color=discord.Color.gold(),
                timestamp=ctx.message.created_at
            )
            embed.set_author(name=ctx.author.name, icon_url=ctx.author.avatar)
            embed.set_footer(text=f"Từ server: {ctx.guild.name}")

        try:
            await suggestion_channel.send(embed=embed)
            await ctx.send(f"✅ Cảm ơn {ctx.author.mention}, góp ý của bạn đã được gửi đi thành công!", delete_after=5)
        except discord.Forbidden:
            print(f"LỖI NGHIÊM TRỌNG: Bot không có quyền gửi tin nhắn trong kênh ID {SUGGESTION_CHANNEL_ID}")
            await ctx.send("❌ Hệ thống góp ý đang gặp lỗi quyền, báo Admin ngay!", delete_after=10)

    # Error handler này giờ chỉ để bắt các lỗi không lường trước
    @suggest_command.error
    async def suggest_error(self, ctx: commands.Context, error):
        # Lỗi cooldown và thiếu nội dung đã được xử lý bên trong lệnh
        # Chúng ta chỉ in ra các lỗi khác để debug
        if not isinstance(error, (commands.CommandOnCooldown, commands.MissingRequiredArgument)):
            print(f"Lỗi không xác định trong lệnh suggest: {error}")
            await ctx.send("🤖 Oups, có lỗi gì đó bất ngờ xảy ra rồi!", delete_after=5)

async def setup(bot: commands.Bot):
    await bot.add_cog(SuggestionCog(bot))
