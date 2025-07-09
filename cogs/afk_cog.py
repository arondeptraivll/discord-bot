import discord
from discord.ext import commands
import datetime

afk_users = {}

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

    async def _clear_afk_status(self, user_id: int):
        if user_id in self.afk_users:
            afk_data = self.afk_users.pop(user_id)
            try:
                channel = self.bot.get_channel(afk_data['channel_id'])
                if channel:
                    original_afk_message = await channel.fetch_message(afk_data['message_id'])
                    await original_afk_message.delete()
            except (discord.NotFound, discord.Forbidden):
                pass
            return afk_data
        return None

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot or not message.guild:
            return

        # <<< SỬA LỖI TẬN GỐC TẠI ĐÂY >>>
        # Lấy context của tin nhắn. Đây là cách chuẩn để biết tin nhắn có phải là lệnh không.
        ctx = await self.bot.get_context(message)
        # Nếu `ctx.valid` là True, có nghĩa đây là một lệnh hợp lệ (!afk, !help, etc.)
        # => Dừng ngay listener này và để cho hệ thống lệnh tự xử lý.
        if ctx.valid:
            return

        # Từ đây code chỉ chạy với tin nhắn THÔNG THƯỜNG (không phải lệnh).
        
        # Tự động gỡ AFK
        if message.author.id in self.afk_users:
            afk_data = await self._clear_afk_status(message.author.id)
            if afk_data:
                start_time = afk_data['start_time']
                duration = datetime.datetime.now(datetime.timezone.utc) - start_time
                embed = discord.Embed(
                    description=f"👋 **{message.author.display_name}** đã quay trở lại sau khi AFK **{format_duration(duration.total_seconds())}**.",
                    color=discord.Color.green()
                )
                await message.channel.send(embed=embed, delete_after=5)

        # Kiểm tra mention người đang AFK
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
                        await message.reply(embed=log_embed, delete_after=6, silent=True)
                        await message.delete()
                    except discord.Forbidden:
                        await message.reply("Lỗi: Bot cần quyền `Manage Messages`.", delete_after=5)
                    break
        # Dòng `process_commands` đã được xóa hoàn toàn.

    @commands.command(name='afk')
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def set_afk(self, ctx: commands.Context, *, reason: str = "Không có lí do cụ thể"):
        """Đặt trạng thái AFK cho bản thân."""
        await ctx.message.delete()
        
        # Thêm một lớp kiểm tra an toàn nữa
        if ctx.author.id in self.afk_users:
            await ctx.send("⚠️ Bạn đã ở trong trạng thái AFK rồi.", delete_after=5)
            return

        embed = discord.Embed(
            title=f"💤 {ctx.author.display_name} Đang AFK!",
            description=f"**Lí do:** {reason}\n_Gõ một tin nhắn bất kỳ để trở lại._",
            color=discord.Color.orange()
        )
        embed.set_thumbnail(url=ctx.author.avatar)
        afk_message = await ctx.send(embed=embed)
        
        # Chỉ thêm vào danh sách SAU KHI đã gửi tin nhắn
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
            
        afk_data = await self._clear_afk_status(ctx.author.id)
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
            try:
                await ctx.message.delete()
            except discord.HTTPException: pass
            await ctx.send(f"⏳ Vui lòng chờ {error.retry_after:.1f} giây.", delete_after=5)

async def setup(bot):
    await bot.add_cog(AfkCog(bot))
