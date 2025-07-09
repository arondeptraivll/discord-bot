import discord
from discord.ext import commands
import datetime

# Dùng dictionary để lưu trữ người dùng AFK: {user_id: {'reason': str, 'start_time': datetime}}
# Đây là biến global cho cog này, lưu trữ trạng thái giữa các lệnh
afk_users = {}

# Hàm helper để định dạng thời gian cho dễ đọc
def format_duration(seconds: float) -> str:
    seconds = int(seconds)
    days, seconds = divmod(seconds, 86400)
    hours, seconds = divmod(seconds, 3600)
    minutes, seconds = divmod(seconds, 60)
    
    parts = []
    if days > 0: parts.append(f"{days} ngày")
    if hours > 0: parts.append(f"{hours} giờ")
    if minutes > 0: parts.append(f"{minutes} phút")
    # Luôn hiển thị giây nếu thời gian AFK < 1 phút
    if seconds > 0 or not parts:
        parts.append(f"{seconds} giây")
    
    return ", ".join(parts)

class AfkCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        # Sử dụng self.afk_users để cog có thể truy cập dictionary
        self.afk_users = afk_users 

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        # Bỏ qua nếu tin nhắn từ bot hoặc trong tin nhắn riêng
        if message.author.bot or not message.guild:
            return

        # 1. Tự động gỡ AFK khi người dùng chat lại
        if message.author.id in self.afk_users:
            afk_data = self.afk_users.pop(message.author.id)
            start_time = afk_data['start_time']
            duration = datetime.datetime.now(datetime.timezone.utc) - start_time
            
            embed = discord.Embed(
                title=f"👋 {message.author.display_name} Đã Quay Trở Lại!",
                description=f"Chào mừng bạn đã quay lại sau khi AFK **{format_duration(duration.total_seconds())}**.",
                color=discord.Color.green()
            )
            try:
                # Gửi tin nhắn và tự xóa sau 10 giây để đỡ làm phiền
                await message.channel.send(embed=embed, delete_after=10)
            except discord.Forbidden:
                pass # Bỏ qua nếu không có quyền gửi tin nhắn

        # 2. Kiểm tra nếu có mention người đang AFK
        if not message.mentions:
            return

        for user in message.mentions:
            if user.id in self.afk_users:
                afk_data = self.afk_users[user.id]
                reason = afk_data['reason']
                start_time = afk_data['start_time']
                
                # Sử dụng timestamp của Discord để hiển thị thời gian tương đối (vd: "cách đây 5 phút")
                afk_timestamp = f"<t:{int(start_time.timestamp())}:R>"
                
                # Tạo embed thông báo
                log_embed = discord.Embed(
                    description=f"💤 **{user.display_name}** đang AFK {afk_timestamp} với lí do: `{reason}`",
                    color=discord.Color.light_grey()
                )
                try:
                    # Dùng reply để người gửi biết họ đang mention ai, tự xóa sau 15 giây
                    await message.reply(embed=log_embed, delete_after=15, silent=True)
                except discord.Forbidden:
                    pass
                # Chỉ cần thông báo một lần cho mỗi tin nhắn, nên break sau khi tìm thấy
                break

    @commands.command(name='afk')
    async def set_afk(self, ctx: commands.Context, *, reason: str = "Không có lí do cụ thể"):
        """Đặt trạng thái AFK cho bản thân."""
        user_id = ctx.author.id
        
        if user_id in self.afk_users:
            await ctx.send("⚠️ Bạn đã ở trong trạng thái AFK rồi.", delete_after=5)
            return

        # Lưu thông tin AFK
        self.afk_users[user_id] = {
            'reason': reason,
            'start_time': datetime.datetime.now(datetime.timezone.utc)
        }
        
        embed = discord.Embed(
            title=f"💤 {ctx.author.display_name} Đang AFK!",
            description=f"Bạn đã AFK với lí do: `{reason}`\n_Gõ một tin nhắn bất kỳ để trở lại._",
            color=discord.Color.orange()
        )
        embed.set_thumbnail(url=ctx.author.avatar)
        
        await ctx.reply(embed=embed)

    @commands.command(name='noafk')
    async def remove_afk(self, ctx: commands.Context):
        """Gỡ trạng thái AFK của bản thân."""
        user_id = ctx.author.id

        if user_id not in self.afk_users:
            await ctx.send("⚠️ Bạn không ở trong trạng thái AFK.", delete_after=5)
            return
            
        afk_data = self.afk_users.pop(user_id)
        start_time = afk_data['start_time']
        duration = datetime.datetime.now(datetime.timezone.utc) - start_time

        embed = discord.Embed(
            title=f"👋 {ctx.author.display_name} Đã Quay Trở Lại!",
            description=f"Bạn đã quay trở lại sau khi AFK **{format_duration(duration.total_seconds())}**.",
            color=discord.Color.green()
        )
        embed.set_thumbnail(url=ctx.author.avatar)

        await ctx.reply(embed=embed)


async def setup(bot):
    await bot.add_cog(AfkCog(bot))
