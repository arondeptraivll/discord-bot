import discord
from discord.ext import commands

class AutoMessage(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.excluded_role_id = 1391751822867435631
        self.target_channel_id = 1392067603530256445

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
            
        # Tạo embed màu đỏ
        embed = discord.Embed(
            title="Bypass Funlink ở đây",
            description=f"Vui lòng sử dụng kênh <#{self.target_channel_id}>",
            color=discord.Color.red()
        )
        
        # Gửi embed với mention người dùng
        try:
            await message.channel.send(
                content=f"{message.author.mention}",
                embed=embed
            )
        except discord.errors.Forbidden:
            print(f"Bot không có quyền gửi tin nhắn trong kênh {message.channel.name}")
        except Exception as e:
            print(f"Lỗi khi gửi tin nhắn tự động: {e}")

# Hàm setup để load cog
async def setup(bot):
    await bot.add_cog(AutoMessage(bot))
