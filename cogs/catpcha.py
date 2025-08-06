# cogs/verification_cog.py
import discord
from discord.ext import commands, tasks
import asyncio
import random
import io
from PIL import Image, ImageDraw, ImageFont
import math
from datetime import datetime, timedelta

class VerificationCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.channel_id = 1402467575299834056  # ID kênh chat
        self.role_id = 1402466671544766494     # ID role
        self.verification_check.start()
        self.verification_sent = False
        
    def cog_unload(self):
        self.verification_check.cancel()

    # Event khi user mới vào server
    @commands.Cog.listener()
    async def on_member_join(self, member):
        try:
            role = member.guild.get_role(self.role_id)
            if role:
                await member.add_roles(role)
                print(f"✅ Added verification role to {member.name}")
        except Exception as e:
            print(f"❌ Error adding role to {member.name}: {e}")

    # Task kiểm tra và gửi tin nhắn verify mỗi 30 giây
    @tasks.loop(seconds=30)
    async def verification_check(self):
        try:
            channel = self.bot.get_channel(self.channel_id)
            if not channel:
                return
                
            # Kiểm tra xem có ai có role verification không
            role = channel.guild.get_role(self.role_id)
            if not role:
                return
                
            # Nếu có người có role và chưa gửi tin nhắn verify
            if any(role in member.roles for member in channel.guild.members) and not self.verification_sent:
                embed = discord.Embed(
                    title="🛡️ Xác Thực Tài Khoản",
                    description="Vui lòng click vào button để kiểm tra bạn có phải robot không?",
                    color=0x00ff00
                )
                view = VerifyView(self.bot, self.role_id)
                await channel.send(embed=embed, view=view)
                self.verification_sent = True
                print("✅ Sent verification message")
                
        except Exception as e:
            print(f"❌ Error in verification check: {e}")

    @verification_check.before_loop
    async def before_verification_check(self):
        await self.bot.wait_until_ready()

class VerifyView(discord.ui.View):
    def __init__(self, bot, role_id):
        super().__init__(timeout=None)
        self.bot = bot
        self.role_id = role_id

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
            else:
                # Tài khoản < 7 ngày, cần captcha
                captcha_view = CaptchaView(self.bot, self.role_id)
                captcha_image = await captcha_view.generate_captcha()
                
                embed = discord.Embed(
                    title="🤖 Vui Lòng Giải Captcha Dưới",
                    description="Hãy nhập kết quả phép tính trong hình:",
                    color=0xff9900
                )
                
                file = discord.File(fp=captcha_image, filename="captcha.png")
                embed.set_image(url="attachment://captcha.png")
                
                await interaction.response.send_message(embed=embed, file=file, view=captcha_view, ephemeral=True)
                print(f"📝 {interaction.user.name} needs captcha (account age: {account_age.days} days)")
                
        except Exception as e:
            print(f"❌ Error in verify button: {e}")
            await interaction.response.send_message("❌ Có lỗi xảy ra, vui lòng thử lại!", ephemeral=True)

class CaptchaView(discord.ui.View):
    def __init__(self, bot, role_id):
        super().__init__(timeout=300)  # 5 phút timeout
        self.bot = bot
        self.role_id = role_id
        self.answer = None

    async def generate_captcha(self):
        """Tạo captcha với phép tính cộng/trừ"""
        try:
            # Tạo phép tính ngẫu nhiên
            num1 = random.randint(10, 99)
            num2 = random.randint(10, 99)
            operation = random.choice(['+', '-'])
            
            if operation == '+':
                self.answer = num1 + num2
                text = f"{num1} + {num2} = ?"
            else:
                # Đảm bảo kết quả không âm
                if num1 < num2:
                    num1, num2 = num2, num1
                self.answer = num1 - num2
                text = f"{num1} - {num2} = ?"

            # Tạo hình ảnh với text bị méo
            img = Image.new('RGB', (300, 100), color='white')
            draw = ImageDraw.Draw(img)
            
            # Thêm nhiễu nền
            for _ in range(100):
                x = random.randint(0, 300)
                y = random.randint(0, 100)
                draw.point((x, y), fill=(random.randint(0, 255), random.randint(0, 255), random.randint(0, 255)))
            
            # Vẽ text với font size lớn và rotation
            try:
                font = ImageFont.truetype("arial.ttf", 30)
            except:
                font = ImageFont.load_default()
            
            # Tính toán vị trí text
            bbox = draw.textbbox((0, 0), text, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            x = (300 - text_width) // 2
            y = (100 - text_height) // 2
            
            # Vẽ text với màu ngẫu nhiên
            color = (random.randint(50, 200), random.randint(50, 200), random.randint(50, 200))
            draw.text((x, y), text, font=font, fill=color)
            
            # Thêm đường kẻ nhiễu
            for _ in range(5):
                start = (random.randint(0, 300), random.randint(0, 100))
                end = (random.randint(0, 300), random.randint(0, 100))
                draw.line([start, end], fill=(random.randint(0, 255), random.randint(0, 255), random.randint(0, 255)), width=2)
            
            # Chuyển thành bytes
            img_bytes = io.BytesIO()
            img.save(img_bytes, format='PNG')
            img_bytes.seek(0)
            
            return img_bytes
            
        except Exception as e:
            print(f"❌ Error generating captcha: {e}")
            # Fallback: tạo captcha đơn giản
            self.answer = random.randint(10, 99)
            img = Image.new('RGB', (200, 60), color='lightgray')
            draw = ImageDraw.Draw(img)
            draw.text((50, 20), f"Answer: {self.answer}", fill='black')
            
            img_bytes = io.BytesIO()
            img.save(img_bytes, format='PNG')
            img_bytes.seek(0)
            return img_bytes

    @discord.ui.button(label='Giải Captcha', style=discord.ButtonStyle.primary, emoji='🔍')
    async def solve_captcha(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(CaptchaModal(self.bot, self.role_id, self.answer))

class CaptchaModal(discord.ui.Modal):
    def __init__(self, bot, role_id, correct_answer):
        super().__init__(title="Giải Captcha")
        self.bot = bot
        self.role_id = role_id
        self.correct_answer = correct_answer

    answer = discord.ui.TextInput(
        label='Kết quả phép tính:',
        placeholder='Nhập kết quả...',
        required=True,
        max_length=10
    )

    async def on_submit(self, interaction: discord.Interaction):
        try:
            user_answer = int(self.answer.value.strip())
            
            if user_answer == self.correct_answer:
                # Đúng - gỡ role
                role = interaction.guild.get_role(self.role_id)
                if role and role in interaction.user.roles:
                    await interaction.user.remove_roles(role)
                    
                embed = discord.Embed(
                    title="✅ Captcha Thành Công!",
                    description="Bạn đã giải captcha thành công và được xác thực!",
                    color=0x00ff00
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                print(f"✅ {interaction.user.name} solved captcha correctly")
                
            else:
                # Sai - thử lại
                embed = discord.Embed(
                    title="❌ Captcha Sai!",
                    description="Kết quả không chính xác. Vui lòng thử lại!",
                    color=0xff0000
                )
                
                # Tạo captcha mới
                captcha_view = CaptchaView(self.bot, self.role_id)
                captcha_image = await captcha_view.generate_captcha()
                
                file = discord.File(fp=captcha_image, filename="captcha.png")
                embed.set_image(url="attachment://captcha.png")
                
                await interaction.response.send_message(embed=embed, file=file, view=captcha_view, ephemeral=True)
                print(f"❌ {interaction.user.name} failed captcha")
                
        except ValueError:
            embed = discord.Embed(
                title="❌ Lỗi!",
                description="Vui lòng chỉ nhập số!",
                color=0xff0000
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
        except Exception as e:
            print(f"❌ Error in captcha submit: {e}")
            await interaction.response.send_message("❌ Có lỗi xảy ra!", ephemeral=True)

async def setup(bot):
    await bot.add_cog(VerificationCog(bot))
