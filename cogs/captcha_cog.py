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

    # <<< THAY ĐỔI 1: Hàm helper giờ đây nhận các tham số cho embed >>>
    async def _send_verification_message(self, member: discord.Member, title: str, description: str, color: discord.Color):
        """Tạo và gửi tin nhắn xác minh với nội dung tùy chỉnh."""
        channel = self.bot.get_channel(self.VERIFICATION_CHANNEL_ID)
        if not channel:
            print(f"LỖI: Không tìm thấy kênh xác minh với ID {self.VERIFICATION_CHANNEL_ID}")
            return

        render_url = os.getenv('RENDER_APP_URL')
        if not render_url:
            print("LỖI: Biến môi trường RENDER_APP_URL chưa được thiết lập.")
            return

        token = secrets.token_urlsafe(20)
        verification_link = f"{render_url}/verify/{token}"

        # Tạo Embed từ các tham số được truyền vào
        embed = discord.Embed(title=title, description=description, color=color)
        embed.set_footer(text="Nhấn nút bên dưới để bắt đầu.")

        view = View(timeout=None)
        view.add_item(Button(label="Bắt đầu xác minh", style=discord.ButtonStyle.link, url=verification_link))
        
        sent_message = await channel.send(embed=embed, view=view)
        
        self.verification_sessions[token] = {
            'user_id': member.id,
            'guild_id': member.guild.id,
            'message_id': sent_message.id,
            'channel_id': channel.id,
        }
        print(f"Đã tạo phiên xác minh cho {member.name} với token: {token}")

    # <<< THAY ĐỔI 2: Sự kiện on_member_join gọi hàm helper với nội dung "Chào mừng" >>>
    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        print(f"Thành viên mới tham gia: {member.name} ({member.id})")
        if member.bot:
            return

        unverify_role = discord.utils.get(member.guild.roles, name="Unverify")
        if not unverify_role:
            print(f"LỖI: Role 'Unverify' không tồn tại trên server {member.guild.name}.")
            return

        try:
            await member.add_roles(unverify_role, reason="Thành viên mới tham gia")
            print(f"Đã gán role 'Unverify' cho {member.name}")

            # Chuẩn bị nội dung cho embed chào mừng
            welcome_title = "👋 Chào mừng bạn đến với Server!"
            welcome_description = f"Chào {member.mention}, để có thể truy cập các kênh khác, vui lòng xác minh rằng bạn không phải là robot."
            welcome_color = discord.Color.gold()

            # Gửi yêu cầu xác minh với nội dung chào mừng
            await self._send_verification_message(
                member=member,
                title=welcome_title,
                description=welcome_description,
                color=welcome_color
            )
        except discord.Forbidden:
            print(f"LỖI: Bot không có quyền để gán role 'Unverify' cho {member.name}.")
        except Exception as e:
            print(f"Đã xảy ra lỗi khi xử lý thành viên mới {member.name}: {e}")

    # <<< THAY ĐỔI 3: Lệnh !captcha gọi hàm helper với nội dung "Nghi ngờ" >>>
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
            await member.add_roles(unverify_role, reason=f"Yêu cầu xác minh lại bởi {ctx.author.name}")

            # Chuẩn bị nội dung cho embed nghi ngờ
            suspicious_title = "Bạn bị nghi ngờ là Bot!"
            suspicious_description = f"Hãy xác minh bạn không phải là robot ở dưới, {member.mention}!"
            suspicious_color = discord.Color.red()
            
            # Gửi yêu cầu xác minh với nội dung nghi ngờ
            await self._send_verification_message(
                member=member,
                title=suspicious_title,
                description=suspicious_description,
                color=suspicious_color
            )
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
