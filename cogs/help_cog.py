import discord
from discord.ext import commands
from discord.ui import View, Button

# --- Định nghĩa Lớp View chứa Button ---
# Lớp này sẽ tạo ra hàng nút bấm bên dưới tin nhắn
class HelpView(View):
    def __init__(self, author: discord.User, **kwargs):
        # Thiết lập timeout cho button, sau 5 phút button sẽ bị vô hiệu hóa
        super().__init__(timeout=300, **kwargs)
        self.author = author

    # Hàm này sẽ được gọi mỗi khi có ai đó tương tác với button trong View này
    # Nó chạy TRƯỚC khi callback của button được gọi
    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        # Kiểm tra xem người tương tác có phải là người đã gọi lệnh hay không
        if interaction.user.id == self.author.id:
            return True  # Cho phép tương tác
        else:
            # Gửi một tin nhắn ẩn (chỉ người bấm thấy) để thông báo họ không có quyền
            await interaction.response.send_message("🚫 Bạn không phải người đã yêu cầu trợ giúp này.", ephemeral=True)
            return False # Không cho phép tương tác

    # Định nghĩa một button
    @discord.ui.button(label="🗑️ Xóa tin nhắn", style=discord.ButtonStyle.danger)
    async def delete_button(self, interaction: discord.Interaction, button: Button):
        # Khi button được bấm (và đã qua được interaction_check), tin nhắn sẽ được xóa
        await interaction.message.delete()


# --- Định nghĩa Cog chứa lệnh Help ---
class HelpCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name='help')
    # Lệnh help thường không cần giới hạn quyền
    async def help_command(self, ctx: commands.Context):
        # Xóa tin nhắn "?help" của người dùng để giữ kênh chat sạch sẽ
        await ctx.message.delete()
        
        # Nội dung của tin nhắn trợ giúp, sử dụng Markdown của Discord để định dạng
        help_text = (
            "**CÁC LỆNH HIỆN TẠI (MUỐN CÓ THÊM LỆNH GÌ NHẮN ADMIN)**\n"
            "_ _\n"
            "```\n"
            "?embed [tiêu đề]\n"
            "[nội dung]\n"
            "```\n"
            "➡️ **Chức năng:** Tạo ra một embed đẹp với tiêu đề và nội dung.\n"
            "_ _\n"
            "```\n"
            "?deletebotmsg [message id]\n"
            "```\n"
            "➡️ **Chức năng:** Xóa tin nhắn do bot gửi (nếu lỡ nhập sai hoặc muốn dọn dẹp).\n"
            "_ _\n"
            "*Anh em có thể test ngay tại đây luôn nhé.*\n"
            "*Làm sao để lấy ID tin nhắn? Vào `Cài đặt > Nâng cao > Bật Chế độ nhà phát triển`. Sau đó chuột phải vào tin nhắn bất kỳ và chọn `Copy Message ID`.*"
        )
        
        # Tạo một đối tượng View với nút bấm và truyền vào tác giả của lệnh
        view = HelpView(author=ctx.author)
        
        # Gửi tin nhắn trợ giúp kèm theo View (nút bấm)
        await ctx.send(help_text, view=view)


# Hàm setup để bot có thể load Cog này từ file main.py
async def setup(bot):
    await bot.add_cog(HelpCog(bot))
