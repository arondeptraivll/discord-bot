# cogs/verification_cog.py
import discord
from discord.ext import commands
import asyncio
import os
from datetime import datetime, timedelta

class VerificationCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.channel_id = 1402467575299834056  # ID kênh chat
        self.role_id = 1402466671544766494     # ID role
        self.verification_message_id = None    # Lưu ID tin nhắn verify
        self.pending_verifications = {}        # Lưu các verification đang chờ
        
    # Event khi user mới vào server
    @commands.Cog.listener()
    async def on_member_join(self, member):
        try:
            # Gán role cho user mới
            role = member.guild.get_role(self.role_id)
            if role:
                await member.add_roles(role)
                print(f"✅ Added verification role to {member.name}")
            
            # Kiểm tra và gửi tin nhắn verify ngay lập tức
            await self.check_and_send_verification(member.guild)
                
        except Exception as e:
            print(f"❌ Error in on_member_join: {e}")

    async def check_and_send_verification(self, guild):
        """Kiểm tra và gửi tin nhắn verification nếu cần"""
        try:
            channel = guild.get_channel(self.channel_id)
            if not channel:
                print(f"❌ Channel {self.channel_id} not found")
                return
                
            role = guild.get_role(self.role_id)
            if not role:
                print(f"❌ Role {self.role_id} not found")
                return
            
            # Kiểm tra xem có ai có role verification không
            members_with_role = [member for member in guild.members if role in member.roles]
            
            if not members_with_role:
                # Không có ai cần verify, xóa tin nhắn verify nếu có
                if self.verification_message_id:
                    try:
                        message = await channel.fetch_message(self.verification_message_id)
                        await message.delete()
                        self.verification_message_id = None
                        print("🗑️ Deleted verification message (no users need verification)")
                    except:
                        pass
                return
            
            # Kiểm tra xem tin nhắn verify đã tồn tại chưa
            verification_exists = False
            if self.verification_message_id:
                try:
                    await channel.fetch_message(self.verification_message_id)
                    verification_exists = True
                except:
                    self.verification_message_id = None
            
            # Nếu chưa có tin nhắn verify thì gửi mới
            if not verification_exists:
                embed = discord.Embed(
                    title="🛡️ Xác Thực Tài Khoản",
                    description="Vui lòng click vào button để kiểm tra bạn có phải robot không?",
                    color=0x00ff00
                )
                view = VerifyView(self.bot, self.role_id, self)
                message = await channel.send(embed=embed, view=view)
                self.verification_message_id = message.id
                print("✅ Sent verification message")
                
        except Exception as e:
            print(f"❌ Error in check_and_send_verification: {e}")

    async def complete_verification(self, user_id, guild_id):
        """Hoàn thành verification từ web"""
        try:
            guild = self.bot.get_guild(guild_id)
            if not guild:
                return False
                
            member = guild.get_member(user_id)
            if not member:
                return False
                
            role = guild.get_role(self.role_id)
            if not role:
                return False
                
            await member.remove_roles(role)
            print(f"✅ {member.name} completed web verification")
            
            # Kiểm tra lại xem có cần xóa tin nhắn verify không
            await self.check_and_send_verification(guild)
            
            return True
        except Exception as e:
            print(f"❌ Error completing verification: {e}")
            return False

    # Event khi user rời server
    @commands.Cog.listener()
    async def on_member_remove(self, member):
        # Kiểm tra lại xem có cần xóa tin nhắn verify không
        await asyncio.sleep(1)
        await self.check_and_send_verification(member.guild)

class VerifyView(discord.ui.View):
    def __init__(self, bot, role_id, cog):
        super().__init__(timeout=None)
        self.bot = bot
        self.role_id = role_id
        self.cog = cog

    @discord.ui.button(label='Verify', style=discord.ButtonStyle.success, emoji='✅')
    async def verify_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            # Kiểm tra user có role verification không
            role = interaction.guild.get_role(self.role_id)
            if not role or role not in interaction.user.roles:
                await interaction.response.send_message("❌ Bạn không cần xác thực!", ephemeral=True)
                return

            # Kiểm tra tuổi tài khoản
            account_age = datetime.utcnow() - interaction.user.created_at
            
            if account_age >= timedelta(days=7):
                # Tài khoản >= 7 ngày, pass luôn
                await interaction.user.remove_roles(role)
                embed = discord.Embed(
                    title="✅ Xác Thực Thành Công!",
                    description="Tài khoản của bạn đã được xác thực thành công!",
                    color=0x00ff00
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                print(f"✅ {interaction.user.name} passed verification (account age: {account_age.days} days)")
                
                # Kiểm tra lại xem có cần xóa tin nhắn verify không
                await self.cog.check_and_send_verification(interaction.guild)
                
            else:
                # Tài khoản < 7 ngày, cần captcha web
                embed = discord.Embed(
                    title="🤖 Vui lòng giải captcha ở dưới",
                    description="Xác thực bạn không phải robot",
                    color=0xff9900
                )
                
                # Tạo verification token
                verification_token = f"{interaction.user.id}_{interaction.guild.id}"
                self.cog.pending_verifications[verification_token] = {
                    'user_id': interaction.user.id,
                    'guild_id': interaction.guild.id,
                    'timestamp': datetime.utcnow()
                }
                
                # URL tới trang verification
                base_url = os.getenv('WEB_URL', 'https://your-render-app.onrender.com')
                verification_url = f"{base_url}/verify?token={verification_token}"
                
                view = WebCaptchaView(verification_url)
                await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
                print(f"📝 {interaction.user.name} redirected to web captcha")
                
        except Exception as e:
            print(f"❌ Error in verify button: {e}")
            await interaction.response.send_message("❌ Có lỗi xảy ra, vui lòng thử lại!", ephemeral=True)

class WebCaptchaView(discord.ui.View):
    def __init__(self, verification_url):
        super().__init__(timeout=300)
        self.verification_url = verification_url

    @discord.ui.button(label='Xác Thực', style=discord.ButtonStyle.link, url=None, emoji='🔗')
    async def verify_web_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Button này sẽ được setup với URL trong __init__
        pass

    def __post_init__(self):
        # Set URL for the button
        self.verify_web_button.url = self.verification_url

async def setup(bot):
    await bot.add_cog(VerificationCog(bot))
