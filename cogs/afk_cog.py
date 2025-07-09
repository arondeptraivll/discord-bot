import discord
from discord.ext import commands
import datetime

# Giờ đây dictionary sẽ lưu thêm message_id và channel_id
# {user_id: {'reason': str, 'start_time': dt, 'message_id': int, 'channel_id': int}}
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

    async def _clear_afk_message(self, user_id: int):
        """Helper function to delete the original AFK message."""
        if user_id in self.afk_users:
            afk_data = self.afk_users.pop(user_id)
            try:
                channel = self.bot.get_channel(afk_data['channel_id'])
                if channel:
                    original_afk_message = await channel.fetch_message(afk_data['message_id'])
                    await original_afk_message.delete()
            except (discord.NotFound, discord.Forbidden):
                # Bỏ qua nếu tin nhắn đã bị xóa hoặc bot không có quyền
                pass
            return afk_data
        return None

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot or not message.guild:
            return

        ctx = await self.bot.get_context(message)
        if ctx.valid:
            return
            
        # Tự động gỡ AFK khi người dùng chat
        if message.author.id in self.afk_users:
            afk_data = await self._clear_afk_message(message.author.id)
            if afk_data:
                start_time = afk_data['start_time']
                duration = datetime.datetime.now(datetime.timezone.utc) - start_time
                
                embed = discord.Embed(
                    description=f"👋 **{message.author.display_name}** đã quay trở lại sau khi AFK **{format_duration(duration.total_seconds())}**.",
                    color=discord.Color.green()
                )
                await message.channel.send(embed=embed, delete_after=5)

        # Kiểm tra nếu có mention người đang AFK
        if message.mentions:
            for user in message.mentions:
                if user.id in self.afk_users:
                    afk_data = self.afk_users[user.id]
                    afk_timestamp = f"<t:{int(afk_data['start_time'].timestamp())}:R>"
                    
                    log_embed = discord.Embed(
                        description=f"💤 **{user.display_name}** đang AFK {afk_timestamp}: `{afk_data['reason']}`",
                        color=discord.Color.light_grey()
                    )
                    
                    try:
                        # Gửi tin cảnh báo và xóa tin nhắn mention
                        await message.reply(embed=log_embed, delete_after=6, silent=True)
                        await message.delete() # Xóa tin nhắn có mention
                    except discord.Forbidden:
                        # Bot không có quyền xóa tin nhắn
                        await message.reply("Lỗi: Bot cần quyền `Manage Messages` để xóa tin nhắn này.", delete_after=5)
                    except Exception:
                        pass # Bỏ qua các lỗi khác
                    break

    @commands.command(name='afk')
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def set_afk(self, ctx: commands.Context, *, reason: str = "Không có lí do cụ thể"):
        """Đặt trạng thái AFK cho bản thân."""
        # Xóa tin nhắn lệnh
        await ctx.message.delete()
        
        if ctx.author.id in self.afk_users:
            await ctx.send("⚠️ Bạn đã ở trong trạng thái AFK rồi.", delete_after=5)
            return

        embed = discord.Embed(
            title=f"💤 {ctx.author.display_name} Đang AFK!",
            description=f"**Lí do:** {reason}\n_Gõ một tin nhắn bất kỳ để trở lại._",
            color=discord.Color.orange()
        )
        embed.set_thumbnail(url=ctx.author.avatar)
        # Gửi tin nhắn afk và lưu lại ID
        afk_message = await ctx.send(embed=embed)
        
        self.afk_users[ctx.author.id] = {
            'reason': reason,
            'start_time': datetime.datetime.now(datetime.timezone.utc),
            'message_id': afk_message.id,
            'channel_id': ctx.channel.id
        }

    @commands.command(name='noafk')
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def remove_afk(self, ctx: commands.Context):
        """Gỡ trạng thái AFK của bản thân."""
        await ctx.message.delete()

        if ctx.author.id not in self.afk_users:
            await ctx.send("⚠️ Bạn không ở trong trạng thái AFK.", delete_after=5)
            return
            
        # Xóa tin nhắn AFK cũ và lấy data
        afk_data = await self._clear_afk_message(ctx.author.id)
        if afk_data:
            start_time = afk_data['start_time']
            duration = datetime.datetime.now(datetime.timezone.utc) - start_time

            embed = discord.Embed(
                title=f"👋 {ctx.author.display_name} Đã Quay Trở Lại!",
                description=f"Bạn đã quay trở lại sau khi AFK **{format_duration(duration.total_seconds())}**.",
                color=discord.Color.green()
            )
            await ctx.send(embed=embed, delete_after=5)
        
    @set_afk.error
    @remove_afk.error
    async def afk_error(self, ctx, error):
        if isinstance(error, commands.CommandOnCooldown):
            # Cố gắng xóa tin nhắn lệnh gốc nếu có thể
            try:
                await ctx.message.delete()
            except discord.HTTPException:
                pass
            await ctx.send(f"⏳ Vui lòng chờ {error.retry_after:.1f} giây trước khi dùng lệnh này nữa.", delete_after=5)

async def setup(bot):
    await bot.add_cog(AfkCog(bot))
