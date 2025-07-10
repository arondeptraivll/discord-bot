# cogs/captcha_cog.py
import discord
from discord.ext import commands
from discord.ui import View, Button
import os
import secrets
import datetime
import asyncio

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

    async def verification_timeout_task(self, token: str, delay: int):
        await asyncio.sleep(delay)
        session = self.verification_sessions.pop(token, None)
        if session:
            print(f"Verification session for token {token} has expired.")
            guild = self.bot.get_guild(session['guild_id'])
            if not guild: return
            
            channel = guild.get_channel(session['channel_id'])
            if not channel: return
            
            try:
                message = await channel.fetch_message(session['message_id'])
                expired_embed = discord.Embed(
                    title="⌛ Hết hạn xác minh",
                    description=f"Phiên xác minh cho <@{session['user_id']}> đã hết hạn.",
                    color=discord.Color.red()
                )
                await message.edit(embed=expired_embed, view=None)
            except (discord.NotFound, discord.Forbidden):
                pass

    @commands.command(name='captcha')
    @is_admin_or_supporter()
    @commands.has_permissions(manage_roles=True)
    @commands.bot_has_permissions(manage_roles=True)
    async def captcha_command(self, ctx: commands.Context, member: discord.Member):
        await ctx.message.delete()
        
        unverify_role = discord.utils.get(ctx.guild.roles, name="Unverify")
        if not unverify_role:
            await ctx.send("⚠️ **Lỗi Cấu hình:** Role `Unverify` không tồn tại.", delete_after=10)
            return

        target_channel_id = 1392702105021710527
        target_channel = self.bot.get_channel(target_channel_id)
        if not target_channel:
            await ctx.send(f"⚠️ **Lỗi Cấu hình:** Không tìm thấy kênh ID `{target_channel_id}`.", delete_after=10)
            return
            
        render_url = os.getenv('RENDER_APP_URL')
        if not render_url:
            await ctx.send("⚠️ **Lỗi Cấu hình:** `RENDER_APP_URL` chưa được thiết lập.", delete_after=10)
            return

        try:
            await member.add_roles(unverify_role, reason=f"Yêu cầu xác minh bởi {ctx.author.name}")

            token = secrets.token_urlsafe(16)
            verification_link = f"{render_url}/verify/{token}"

            embed = discord.Embed(
                title="🔒 Bạn chưa được xác minh!",
                description=f"Chào {member.mention}, hãy chứng minh rằng bạn không phải robot để có thể truy cập các kênh khác.",
                color=discord.Color.red()
            )
            embed.set_footer(text="Bạn có 10 phút để hoàn thành xác minh.")

            view = View(timeout=None)
            view.add_item(Button(label="Bắt đầu xác minh", style=discord.ButtonStyle.link, url=verification_link))
            
            sent_message = await target_channel.send(embed=embed, view=view)
            
            expires_at = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(minutes=10)
            self.verification_sessions[token] = {
                'user_id': member.id,
                'guild_id': ctx.guild.id,
                'message_id': sent_message.id,
                'channel_id': target_channel.id,
                'expires_at': expires_at
            }
            
            self.bot.loop.create_task(self.verification_timeout_task(token, 600))
            
            await ctx.send(f"✅ Đã gửi yêu cầu xác minh tới {member.mention} trong {target_channel.mention}.", delete_after=5)

        except discord.Forbidden:
            await ctx.send("🚫 **Lỗi Quyền:** Bot không có quyền để thêm role `Unverify`.", delete_after=10)
        except Exception as e:
            await ctx.send(f"Có lỗi không xác định xảy ra: {e}", delete_after=10)
            print(f"Error in captcha command: {e}")

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
