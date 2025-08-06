import discord
from discord.ext import commands
import asyncio

class BypassView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        
        button = discord.ui.Button(
            label="Lấy Token 🔑",
            style=discord.ButtonStyle.green,
            url="https://tuanhaideptraivcl.vercel.app/Bypass%20Funlink/index.html"
        )
        self.add_item(button)

class AutoMessage(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.excluded_role_id = 1391751822867435631
        self.target_channel_id = 1392067603530256445
        self.recent_messages = set()  # Lưu trữ message ID đã xử lý

    @commands.Cog.listener()
    async def on_message(self, message):
        # Bỏ qua tin nhắn từ bot
        if message.author.bot:
            return
        
        # Kiểm tra duplicate processing
        if message.id in self.recent_messages:
            return
            
        # Bỏ qua tin nhắn không có nội dung
        if not message.content:
            return
            
        # Kiểm tra xem tin nhắn có chứa "funlink" không (không phân biệt hoa thường)
        if "funlink" not in message.content.lower():
            return
            
        # Thêm message ID vào set để tránh duplicate
        self.recent_messages.add(message.id)
        
        # Xóa message ID sau 10 giây để tránh memory leak
        asyncio.create_task(self.cleanup_message_id(message.id))
            
        # Kiểm tra xem người gửi có phải admin không
        if message.author.guild_permissions.administrator:
            return
            
        # Kiểm tra xem người gửi có role được loại trừ không
        user_role_ids = [role.id for role in message.author.roles]
        if self.excluded_role_id in user_role_ids:
            return
            
        # Tạo embed màu đỏ
        embed = discord.Embed(
            title="Bypass Funlink ở đây",
            description=f"Vui lòng sử dụng kênh <#{self.target_channel_id}>",
            color=discord.Color.red()
        )
        
        # Tạo view với button
        view = BypassView()
        
        # Gửi embed với mention người dùng và button
        try:
            await message.channel.send(
                content=f"{message.author.mention}",
                embed=embed,
                view=view
            )
            print(f"Sent funlink response to {message.author.name} in {message.channel.name}")
        except discord.errors.Forbidden:
            print(f"Bot không có quyền gửi tin nhắn trong kênh {message.channel.name}")
        except Exception as e:
            print(f"Lỗi khi gửi tin nhắn tự động: {e}")
    
    async def cleanup_message_id(self, message_id):
        """Xóa message ID sau 10 giây để tránh memory leak"""
        await asyncio.sleep(10)
        self.recent_messages.discard(message_id)

# Hàm setup để load cog
async def setup(bot):
    await bot.add_cog(AutoMessage(bot))
