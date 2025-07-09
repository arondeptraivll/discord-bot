import discord
from discord.ext import commands
import datetime

# Dùng dictionary để lưu trữ người dùng AFK: {user_id: {'reason': str, 'start_time': datetime}}
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
    if seconds > 0 or not parts:
        parts.append(f"{seconds} giây")
    
    return ", ".join(parts) if parts else "0 giây"

class AfkCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.afk_users = afk_users 

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot or not message.guild:
            return

        # <--- SỬA LỖI TẠI ĐÂY (PHẦN 1) ---
        # 1. Tự động gỡ AFK khi người dùng chat lại
        #    Thêm điều kiện: CHỈ gỡ AFK nếu người dùng có trong danh sách
        #    VÀ tin nhắn của họ KHÔNG phải là lệnh `!afk`
        if (message.author.id in self.afk_users and
            not message.content.lower().startswith(f'{self.bot.command_prefix}afk')):
            
            afk_data = self.afk_users.pop(message.author.id)
            start_time = afk_data['start_time']
            duration = datetime.datetime.now(datetime.timezone.utc) - start_time
            
            embed = discord.Embed(
                title=f"👋 {message.author.display_name} Đã Quay Trở Lại!",
                description=f"Chào mừng bạn đã quay lại sau khi AFK **{format_duration(duration.total_seconds())}**.",
                color=discord.Color.green()
            )
            try:
                await message.channel.send(embed=embed, delete_after=10)
            except discord.Forbidden:
                pass

        # 2. Kiểm tra nếu có mention người đang AFK
        if message.mentions:
            for user in message.mentions:
                if user.id in self.afk_users:
                    afk_data = self.afk_users[user.id]
                    reason = afk_data['reason']
                    start_time = afk_data['start_time']
                    afk_timestamp = f"<t:{int(start_time.timestamp())}:R>"
                    
                    log_embed = discord.Embed(
                        description=f"💤 **{user.display_name}** đang AFK {afk_timestamp} với lí do: `{reason}`",
                        color=discord.Color.light_grey()
                    )
                    try:
                        await message.reply(embed=log_embed, delete_after=15, silent=True)
                    except discord.Forbidden:
                        pass
                    break

        # <--- SỬA LỖI TẠI ĐÂY (PHẦN 2) ---
        # Phải thêm dòng này vào cuối `on_message` để bot có thể xử lý
        # các lệnh như !afk, !help, !embed...
        await self.bot.process_commands(message)

    @commands.command(name='afk')
    async def set_afk(self, ctx: commands.Context, *, reason: str = "Không có lí do cụ thể"):
        """Đặt trạng thái AFK cho bản thân."""
        if ctx.author.id in self.afk_users:
            await ctx.send("⚠️ Bạn đã ở trong trạng thái AFK rồi.", delete_after=5)
            return

        self.afk_users[ctx.author.id] = {
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
        if ctx.author.id not in self.afk_users:
            await ctx.send("⚠️ Bạn không ở trong trạng thái AFK.", delete_after=5)
            return
            
        afk_data = self.afk_users.pop(ctx.author.id)
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
