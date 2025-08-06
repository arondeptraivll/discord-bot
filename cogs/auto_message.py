import discord
from discord.ext import commands
import time

class BypassView(discord.ui.View):
    def __init__(self, original_user_id):
        super().__init__(timeout=300)  # 5 phút timeout cho button
        self.original_user_id = original_user_id
        
        # Button lấy token (xanh lá)
        token_button = discord.ui.Button(
            label="Lấy Token 🔑",
            style=discord.ButtonStyle.green,
            url="https://tuanhaideptraivcl.vercel.app/Bypass%20Funlink/index.html"
        )
        self.add_item(token_button)
        
        # Button không quan tâm (đỏ)
        ignore_button = discord.ui.Button(
            label="Không quan tâm ❌",
            style=discord.ButtonStyle.red,
            custom_id="ignore_button"
        )
        ignore_button.callback = self.ignore_callback
        self.add_item(ignore_button)
    
    async def ignore_callback(self, interaction: discord.Interaction):
        # Kiểm tra xem người tương tác có phải là người gốc không
        if interaction.user.id != self.original_user_id:
            await interaction.response.send_message(
                "Bạn không phải là người tương tác button này!", 
                ephemeral=True
            )
            return
        
        # Thêm user vào danh sách ignore trong 15 phút
        AutoMessage.ignored_users[self.original_user_id] = time.time() + 900  # 15 phút = 900 giây
        
        # Xóa tin nhắn embed
        try:
            await interaction.response.defer()
            await interaction.delete_original_response()
        except:
            try:
                await interaction.message.delete()
            except:
                pass

class AutoMessage(commands.Cog):
    # Class variables để track ignored users và cooldown
    ignored_users = {}  # {user_id: timestamp_until_ignored}
    last_embed_time = 0  # Timestamp của lần gửi embed cuối
    
    def __init__(self, bot):
        self.bot = bot
        self.excluded_role_id = 1391751822867435631
        self.target_channel_id = 1392067603530256445

    def cleanup_ignored_users(self):
        """Xóa các user đã hết thời gian ignore"""
        current_time = time.time()
        expired_users = [user_id for user_id, expire_time in self.ignored_users.items() 
                        if current_time > expire_time]
        for user_id in expired_users:
            del self.ignored_users[user_id]

    @commands.Cog.listener()
    async def on_message(self, message):
        # Bỏ qua tin nhắn từ bot
        if message.author.bot:
            return
        
        # Bỏ qua tin nhắn không có nội dung
        if not message.content:
            return
            
        # Kiểm tra xem tin nhắn có chứa "funlink" không (không phân biệt hoa thường)
        if "funlink" not in message.content.lower():
            return
            
        # Kiểm tra xem người gửi có phải admin không
        if message.author.guild_permissions.administrator:
            return
            
        # Kiểm tra xem người gửi có role được loại trừ không
        user_role_ids = [role.id for role in message.author.roles]
        if self.excluded_role_id in user_role_ids:
            return
        
        # Cleanup expired ignored users
        self.cleanup_ignored_users()
        
        # Kiểm tra xem user có đang bị ignore không
        if message.author.id in self.ignored_users:
            return
            
        # Kiểm tra cooldown 30 giây
        current_time = time.time()
        if current_time - self.last_embed_time < 30:
            return
            
        # Cập nhật thời gian gửi embed cuối
        self.last_embed_time = current_time
        
        # Tạo embed màu đỏ
        embed = discord.Embed(
            title="Bypass Funlink ở đây",
            description=f"Vui lòng sử dụng kênh <#{self.target_channel_id}>",
            color=discord.Color.red()
        )
        
        # Tạo view với button (truyền user ID để track)
        view = BypassView(message.author.id)
        
        # Gửi embed với mention người dùng và button
        try:
            await message.channel.send(
                content=f"{message.author.mention}",
                embed=embed,
                view=view
            )
        except discord.errors.Forbidden:
            print(f"Bot không có quyền gửi tin nhắn trong kênh {message.channel.name}")
        except Exception as e:
            print(f"Lỗi khi gửi tin nhắn tự động: {e}")

# Hàm setup để load cog
async def setup(bot):
    await bot.add_cog(AutoMessage(bot))
