# cogs/verification_cog.py
import discord
from discord.ext import commands, tasks
import asyncio
import random
import io
from datetime import datetime, timedelta

# Import PIL với fallback
try:
    from PIL import Image, ImageDraw, ImageFont
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    print("⚠️ PIL not available, using text-based captcha")

class VerificationCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.channel_id = 1402467575299834056  # ID kênh chat
        self.role_id = 1402466671544766494     # ID role
        self.verification_message_id = None    # Lưu ID tin nhắn verify
        
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

    # Event khi user rời server
    @commands.Cog.listener()
    async def on_member_remove(self, member):
        # Kiểm tra lại xem có cần xóa tin nhắn verify không
        await asyncio.sleep(1)  # Chờ 1 giây để đảm bảo member đã được remove
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
                # Tài khoản < 7 ngày, cần captcha
                try:
                    if PIL_AVAILABLE:
                        captcha_view = CaptchaView(self.bot, self.role_id, self.cog)
                        captcha_data = await captcha_view.generate_captcha()
                        
                        embed = discord.Embed(
                            title="🤖 Vui Lòng Giải Captcha Dưới",
                            description="Hãy nhập kết quả phép tính trong hình:",
                            color=0xff9900
                        )
                        
                        if captcha_data['image']:
                            file = discord.File(fp=captcha_data['image'], filename="captcha.png")
                            embed.set_image(url="attachment://captcha.png")
                            await interaction.response.send_message(embed=embed, file=file, view=captcha_view, ephemeral=True)
                        else:
                            # Fallback: text-based captcha
                            embed.description = f"Hãy tính: **{captcha_data['question']}**"
                            await interaction.response.send_message(embed=embed, view=captcha_view, ephemeral=True)
                    else:
                        # Text-based captcha khi không có PIL
                        captcha_view = TextCaptchaView(self.bot, self.role_id, self.cog)
                        question, answer = captcha_view.generate_text_captcha()
                        
                        embed = discord.Embed(
                            title="🤖 Vui Lòng Giải Captcha",
                            description=f"Hãy tính: **{question}**",
                            color=0xff9900
                        )
                        await interaction.response.send_message(embed=embed, view=captcha_view, ephemeral=True)
                    
                    print(f"📝 {interaction.user.name} needs captcha (account age: {account_age.days} days)")
                    
                except Exception as captcha_error:
                    print(f"❌ Error generating captcha: {captcha_error}")
                    await interaction.response.send_message("❌ Có lỗi xảy ra khi tạo captcha, vui lòng thử lại!", ephemeral=True)
                
        except Exception as e:
            print(f"❌ Error in verify button: {e}")
            try:
                await interaction.response.send_message("❌ Có lỗi xảy ra, vui lòng thử lại!", ephemeral=True)
            except:
                pass

class CaptchaView(discord.ui.View):
    def __init__(self, bot, role_id, cog):
        super().__init__(timeout=300)  # 5 phút timeout
        self.bot = bot
        self.role_id = role_id
        self.cog = cog
        self.answer = None
        self.question = None

    async def generate_captcha(self):
        """Tạo captcha - ưu tiên hình ảnh, fallback text"""
        try:
            # Tạo phép tính ngẫu nhiên
            num1 = random.randint(10, 30)
            num2 = random.randint(5, 20)
            operation = random.choice(['+', '-'])
            
            if operation == '+':
                self.answer = num1 + num2
                self.question = f"{num1} + {num2}"
            else:
                # Đảm bảo kết quả không âm
                if num1 < num2:
                    num1, num2 = num2, num1
                self.answer = num1 - num2
                self.question = f"{num1} - {num2}"

            if not PIL_AVAILABLE:
                return {
                    'image': None,
                    'question': self.question,
                    'answer': self.answer
                }

            # Tạo hình ảnh đơn giản cho Render
            width, height = 200, 60
            img = Image.new('RGB', (width, height), color=(240, 240, 240))
            draw = ImageDraw.Draw(img)
            
            # Sử dụng font mặc định của PIL
            try:
                font = ImageFont.load_default()
            except:
                font = None
            
            # Text hiển thị
            text = f"{self.question} = ?"
            
            # Vẽ text ở giữa
            if font:
                bbox = draw.textbbox((0, 0), text, font=font)
                text_width = bbox[2] - bbox[0]
                text_height = bbox[3] - bbox[1]
            else:
                # Estimate size if no font
                text_width = len(text) * 6
                text_height = 11
            
            x = (width - text_width) // 2
            y = (height - text_height) // 2
            
            # Vẽ text
            draw.text((x, y), text, font=font, fill=(50, 50, 50))
            
            # Thêm một ít nhiễu đơn giản
            for _ in range(20):
                x_noise = random.randint(0, width)
                y_noise = random.randint(0, height)
                draw.point((x_noise, y_noise), fill=(200, 200, 200))
            
            # Chuyển thành bytes
            img_bytes = io.BytesIO()
            img.save(img_bytes, format='PNG')
            img_bytes.seek(0)
            
            return {
                'image': img_bytes,
                'question': self.question,
                'answer': self.answer
            }
            
        except Exception as e:
            print(f"❌ Error generating image captcha: {e}")
            # Fallback to text
            return {
                'image': None,
                'question': self.question,
                'answer': self.answer
            }

    @discord.ui.button(label='Giải Captcha', style=discord.ButtonStyle.primary, emoji='🔍')
    async def solve_captcha(self, interaction: discord.Interaction, button: discord.ui.Button):
        modal = CaptchaModal(self.bot, self.role_id, self.answer, self.cog)
        await interaction.response.send_modal(modal)

class TextCaptchaView(discord.ui.View):
    """Text-based captcha cho trường hợp không có PIL"""
    def __init__(self, bot, role_id, cog):
        super().__init__(timeout=300)
        self.bot = bot
        self.role_id = role_id
        self.cog = cog
        self.answer = None

    def generate_text_captcha(self):
        """Tạo captcha dạng text"""
        num1 = random.randint(5, 25)
        num2 = random.randint(5, 20)
        operation = random.choice(['+', '-'])
        
        if operation == '+':
            self.answer = num1 + num2
            question = f"{num1} + {num2}"
        else:
            if num1 < num2:
                num1, num2 = num2, num1
            self.answer = num1 - num2
            question = f"{num1} - {num2}"
        
        return question, self.answer

    @discord.ui.button(label='Giải Captcha', style=discord.ButtonStyle.primary, emoji='🔍')
    async def solve_captcha(self, interaction: discord.Interaction, button: discord.ui.Button):
        modal = CaptchaModal(self.bot, self.role_id, self.answer, self.cog)
        await interaction.response.send_modal(modal)

class CaptchaModal(discord.ui.Modal):
    def __init__(self, bot, role_id, correct_answer, cog):
        super().__init__(title="Giải Captcha")
        self.bot = bot
        self.role_id = role_id
        self.correct_answer = correct_answer
        self.cog = cog

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
                
                # Kiểm tra lại xem có cần xóa tin nhắn verify không
                await self.cog.check_and_send_verification(interaction.guild)
                
            else:
                # Sai - thử lại
                embed = discord.Embed(
                    title="❌ Captcha Sai!",
                    description="Kết quả không chính xác. Vui lòng thử lại!",
                    color=0xff0000
                )
                
                # Tạo captcha mới
                if PIL_AVAILABLE:
                    captcha_view = CaptchaView(self.bot, self.role_id, self.cog)
                    captcha_data = await captcha_view.generate_captcha()
                    
                    if captcha_data['image']:
                        file = discord.File(fp=captcha_data['image'], filename="captcha.png")
                        embed.set_image(url="attachment://captcha.png")
                        await interaction.response.send_message(embed=embed, file=file, view=captcha_view, ephemeral=True)
                    else:
                        embed.description += f"\n\nHãy tính: **{captcha_data['question']}**"
                        await interaction.response.send_message(embed=embed, view=captcha_view, ephemeral=True)
                else:
                    captcha_view = TextCaptchaView(self.bot, self.role_id, self.cog)
                    question, answer = captcha_view.generate_text_captcha()
                    embed.description += f"\n\nHãy tính: **{question}**"
                    await interaction.response.send_message(embed=embed, view=captcha_view, ephemeral=True)
                
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
            try:
                await interaction.response.send_message("❌ Có lỗi xảy ra!", ephemeral=True)
            except:
                pass

async def setup(bot):
    await bot.add_cog(VerificationCog(bot))
