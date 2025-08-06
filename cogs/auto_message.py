import discord
from discord.ext import commands
import time

class IgnoreView(discord.ui.View):
    def __init__(self, original_user_id):
        super().__init__(timeout=300)  # 5 phút timeout cho button
        self.original_user_id = original_user_id

        # Button không quan tâm (đỏ)
        ignore_button = discord.ui.Button(
            label="Không quan tâm ❌",
            style=discord.ButtonStyle.red,
            custom_id="ignore_button"
        )
        ignore_button.callback = self.ignore_callback
        self.add_item(ignore_button)

    async def ignore_callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.original_user_id:
            await interaction.response.send_message(
                "Bạn không phải là người tương tác button này!", 
                ephemeral=True
            )
            return

        AutoMessage.ignored_users[self.original_user_id] = time.time() + 900  # 15 phút = 900 giây

        try:
            await interaction.response.defer()
            await interaction.delete_original_response()
        except:
            try:
                await interaction.message.delete()
            except Exception as e:
                print(f"Lỗi khi xóa message: {e}")

class BypassView(IgnoreView):
    def __init__(self, original_user_id):
        super().__init__(original_user_id)
        # Button lấy token (xanh lá)
        token_button = discord.ui.Button(
            label="Lấy Token 🔑",
            style=discord.ButtonStyle.green,
            url="https://tuanhaideptraivcl.vercel.app/Bypass%20Funlink/index.html"
        )
        # Thêm vào đầu (trước button Không quan tâm)
        self.add_item(token_button)

class AutoMessage(commands.Cog):
    ignored_users = {}  # {user_id: timestamp_until_ignored}
    last_funlink_time = 0  # Timestamp của lần gửi embed funlink cuối
    last_ddos_time = 0     # Timestamp của lần gửi embed ddos cuối

    def __init__(self, bot):
        self.bot = bot
        self.excluded_role_id = 1391751822867435631
        self.target_channel_id = 1392067603530256445
        self.ddos_channel_id = 1396312947697127464

    def cleanup_ignored_users(self):
        current_time = time.time()
        expired_users = [user_id for user_id, expire_time in self.ignored_users.items() 
                        if current_time > expire_time]
        for user_id in expired_users:
            del self.ignored_users[user_id]

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return
        if not message.content:
            return

        # Kiểm tra quyền admin
        if message.author.guild_permissions.administrator:
            return

        # Kiểm tra role loại trừ
        user_role_ids = [role.id for role in message.author.roles]
        if self.excluded_role_id in user_role_ids:
            return

        # Cleanup expired ignored users
        self.cleanup_ignored_users()

        # Kiểm tra ignore
        if message.author.id in self.ignored_users:
            return

        content_lower = message.content.lower()

        # --- FUNLINK ---
        if "funlink" in content_lower:
            current_time = time.time()
            if current_time - self.last_funlink_time < 30:
                return
            self.last_funlink_time = current_time

            embed = discord.Embed(
                title="Bypass Funlink ở đây",
                description=f"Vui lòng sử dụng kênh <#{self.target_channel_id}>",
                color=discord.Color.red()
            )
            view = BypassView(message.author.id)
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
            return  # Nếu có funlink thì không check ddos nữa

        # --- DDOS ---
        if "ddos" in content_lower:
            current_time = time.time()
            if current_time - self.last_ddos_time < 30:
                return
            self.last_ddos_time = current_time

            embed = discord.Embed(
                title="Tool DDos ở dưới",
                description=f"Vui lòng sử dụng kênh <#{self.ddos_channel_id}>",
                color=discord.Color.red()
            )
            view = IgnoreView(message.author.id)
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
