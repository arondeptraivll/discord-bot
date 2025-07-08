import discord
from discord.ext import commands
from discord.ui import View, Button

class HelpView(View):
    def __init__(self, author: discord.User, **kwargs):
        super().__init__(timeout=300, **kwargs)
        self.author = author

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id == self.author.id:
            return True
        else:
            await interaction.response.send_message("🚫 Bạn không phải người đã yêu cầu trợ giúp này.", ephemeral=True)
            return False

    @discord.ui.button(label="🗑️ Xóa tin nhắn", style=discord.ButtonStyle.danger)
    async def delete_button(self, interaction: discord.Interaction, button: Button):
        await interaction.message.delete()

class HelpCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name='help')
    async def help_command(self, ctx: commands.Context):
        await ctx.message.delete()
        
        # ====> THAY ĐỔI CÁC DÒNG DƯỚI ĐÂY <====
        help_text = (
            "**CÁC LỆNH HIỆN TẠI (MUỐN CÓ THÊM LỆNH GÌ NHẮN ADMIN)**\n"
            "_ _\n"
            "```\n"
            "!embed [tiêu đề]\n"  # <-- Đã đổi
            "[nội dung]\n"
            "```\n"
            "➡️ **Chức năng:** Tạo ra một embed đẹp với tiêu đề và nội dung.\n"
            "_ _\n"
            "```\n"
            "!deletebotmsg [message id]\n"  # <-- Đã đổi
            "```\n"
            "➡️ **Chức năng:** Xóa tin nhắn do bot gửi (nếu lỡ nhập sai hoặc muốn dọn dẹp).\n"
            "_ _\n"
            
            "*Làm sao để lấy ID tin nhắn? Vào `Cài đặt > Nâng cao > Bật Chế độ nhà phát triển`. Sau đó chuột phải vào tin nhắn bất kỳ và chọn `Copy Message ID`.*"
        )
        
        view = HelpView(author=ctx.author)
        await ctx.send(help_text, view=view)

async def setup(bot):
    await bot.add_cog(HelpCog(bot))
