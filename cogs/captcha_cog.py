# cogs/captcha_cog.py
import discord
from discord.ext import commands
from discord.ui import View, Button
import os
import secrets

# Check quyền Admin/Supporter
def is_admin_or_supporter():
    async def predicate(ctx):
        if ctx.author.guild_permissions.administrator: return True
        supporter_role = discord.utils.get(ctx.guild.roles, name="Supporter")
        return supporter_role is not None and supporter_role in ctx.author.roles
    return commands.check(predicate)

class CaptchaCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.verification_sessions = self.bot.verification_sessions
        self.VERIFICATION_CHANNEL_ID = 1392702105021710527 # ID kênh xác minh

    # --- HÀM NỘI BỘ ĐỂ GỬI YÊU CẦU XÁC MINH ---
    async def _send_verification_message(self, member: discord.Member):
        """Tạo và gửi tin nhắn xác minh cho một thành viên."""
        channel = self.bot.get_channel(self.VERIFICATION_CHANNEL_ID)
        if not channel:
            print(f"LỖI: Không tìm thấy kênh xác minh với ID {self.VERIFICATION_CHANNEL_ID}")
            return

        render_url = os.getenv('RENDER_APP_URL')
        if not render_url:
            print("LỖI: Biến môi trường RENDER_APP_URL chưa được thiết lập.")
            return

        # Tạo token duy nhất và link xác minh
        token = secrets.token_urlsafe(20)
        verification_link = f"{render_url}/verify/{token}"

        # Tạo Embed
        embed = discord.Embed(
            title="👋 Chào mừng bạn đến với Server!",
            description=f"Chào {member.mention}, để có thể truy cập các kênh khác, vui lòng xác minh rằng bạn không phải là robot.",
            color=discord.Color.gold()
        )
        embed.set_footer(text="Nhấn nút bên dưới để bắt đầu.")

        # Tạo Button với link
        view = View(timeout=None) # Timeout=None để button không bao giờ bị vô hiệu hóa
        view.add_item(Button(label="Bắt đầu xác minh", style=discord.ButtonStyle.link, url=verification_link))
        
        # Gửi tin nhắn và lưu thông tin phiên
        sent_message = await channel.send(embed=embed, view=view)
        
        # Lưu session, không có thời gian hết hạn
        self.verification_sessions[token] = {
            'user_id': member.id,
            'guild_id': member.guild.id,
            'message_id': sent_message.id,
            'channel_id': channel.id,
        }
        print(f"Đã tạo phiên xác minh cho {member.name} với token: {token}")

    # --- SỰ KIỆN TỰ ĐỘNG KHI CÓ THÀNH VIÊN MỚI ---
    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        print(f"Thành viên mới tham gia: {member.name} ({member.id})")
        
        # Bỏ qua bot
        if member.bot:
            return

        # Lấy role Unverify
        unverify_role = discord.utils.get(member.guild.roles, name="Unverify")
        if not unverify_role:
            print(f"LỖI: Role 'Unverify' không tồn tại trên server {member.guild.name}.")
            return

        # Gán role và gửi yêu cầu xác minh
        try:
            await member.add_roles(unverify_role, reason="Thành viên mới tham gia")
            print(f"Đã gán role 'Unverify' cho {member.name}")
            await self._send_verification_message(member)
        except discord.Forbidden:
            print(f"LỖI: Bot không có quyền để gán role 'Unverify' cho {member.name}.")
        except Exception as e:
            print(f"Đã xảy ra lỗi khi xử lý thành viên mới {member.name}: {e}")

    # --- LỆNH !captcha DÀNH CHO ADMIN/SUPPORTER ---
    @commands.command(name='captcha')
    @is_admin_or_supporter()
    @commands.has_permissions(manage_roles=True)
    @commands.bot_has_permissions(manage_roles=True)
    async def captcha_command(self, ctx: commands.Context, member: discord.Member):
        """Yêu cầu một thành viên hiện tại phải xác minh lại."""
        await ctx.message.delete()
        
        unverify_role = discord.utils.get(ctx.guild.roles, name="Unverify")
        if not unverify_role:
            await ctx.send("⚠️ **Lỗi Cấu hình:** Role `Unverify` không tồn tại.", delete_after=10)
            return

        try:
            # Gán lại role và gửi yêu cầu xác minh mới
            await member.add_roles(unverify_role, reason=f"Yêu cầu xác minh lại bởi {ctx.author.name}")
            await self._send_verification_message(member)
            await ctx.send(f"✅ Đã gửi lại yêu cầu xác minh tới {member.mention}.", delete_after=5)
        except discord.Forbidden:
            await ctx.send("🚫 **Lỗi Quyền:** Bot không có quyền để gán role cho thành viên này.", delete_after=10)
        except Exception as e:
            await ctx.send(f"Có lỗi không xác định xảy ra: {e}", delete_after=10)
            print(f"Lỗi trong lệnh captcha: {e}")

    @captcha_command.error
    async def captcha_error(self, ctx, error):
        if isinstance(error, commands.CheckFailure):
            await ctx.send("🚫 Bạn không có quyền sử dụng lệnh này.", delete_after=5)
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send("⚠️ Cú pháp: `!captcha @thành_viên`", delete_after=5)
        elif isinstance(error, commands.MemberNotFound):
            await ctx.send(f"⚠️ Không tìm thấy thành viên `{error.argument}`.", delete_after=5)
        elif isinstance(error, commands.BotMissingPermissions):
            await ctx.send("🚫 Bot thiếu quyền `Manage Roles` để hoạt động.", delete_after=5)

async def setup(bot):
    await bot.add_cog(CaptchaCog(bot))
