import discord
from discord.ext import commands
import os
import google.generativeai as genai

# Cấu hình API key từ biến môi trường
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

# Chỉ cấu hình và tạo model nếu có API KEY
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    # Cài đặt an toàn để tránh các nội dung nhạy cảm, có thể điều chỉnh
    safety_settings = [
        {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
        {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
        {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
        {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
    ]
else:
    print("⚠️ CẢNH BÁO: GEMINI_API_KEY không được tìm thấy. Lệnh !askai sẽ không hoạt động.")


class AiCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        # Chỉ khởi tạo model nếu API key hợp lệ
        if GEMINI_API_KEY:
            self.model = genai.GenerativeModel('gemini-pro', safety_settings=safety_settings)
        else:
            self.model = None

    @commands.command(name='askai')
    @commands.cooldown(1, 10, commands.BucketType.user) # 1 lần mỗi 10 giây cho mỗi người dùng
    async def ask_ai(self, ctx: commands.Context, *, prompt: str):
        if not self.model:
            await ctx.reply("❌ Rất tiếc, tính năng AI chưa được cấu hình đúng cách do thiếu API Key.")
            return

        # Gửi tin nhắn tạm thời và hiển thị "Bot is typing..."
        async with ctx.typing():
            try:
                # Gửi prompt tới Gemini và nhận phản hồi
                response = await self.model.generate_content_async(prompt)
                ai_response_text = response.text

                # Kiểm tra độ dài phản hồi
                if len(ai_response_text) > 4000:
                    ai_response_text = ai_response_text[:4000] + "\n... (Nội dung quá dài đã được cắt bớt)"

                # Tạo embed để gửi lại cho người dùng
                embed = discord.Embed(
                    title=f"💬 Câu trả lời cho {ctx.author.display_name}",
                    description=ai_response_text,
                    color=discord.Color.purple()
                )
                embed.set_footer(text="Cung cấp bởi Google Gemini", icon_url="https://i.imgur.com/v4vL5V2.png")
                
                # Trả lời tin nhắn gốc của người dùng
                await ctx.reply(embed=embed)

            except Exception as e:
                # Xử lý các lỗi có thể xảy ra từ API (ví dụ: nội dung bị chặn)
                print(f"Lỗi khi gọi Gemini API: {e}")
                error_embed = discord.Embed(
                    title="🤖 Đã xảy ra lỗi",
                    description="AI không thể xử lý yêu cầu này. Có thể do nội dung không phù hợp hoặc đã có lỗi từ phía máy chủ của AI. Vui lòng thử lại với một câu hỏi khác.",
                    color=discord.Color.red()
                )
                await ctx.reply(embed=error_embed)

    @ask_ai.error
    async def askai_error(self, ctx: commands.Context, error):
        if isinstance(error, commands.CommandOnCooldown):
            await ctx.reply(f"⏳ Bạn đang thao tác quá nhanh! Vui lòng chờ **{error.retry_after:.1f} giây**.", delete_after=5)
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.reply("⚠️ Bạn quên nhập câu hỏi rồi! Cú pháp: `!askai [câu hỏi của bạn]`", delete_after=5)
        else:
            print(f"Lỗi không xác định trong lệnh !askai: {error}")


async def setup(bot):
    # Chỉ thêm Cog nếu API Key tồn tại
    if GEMINI_API_KEY:
        await bot.add_cog(AiCog(bot))
    else:
        # Bạn có thể bỏ qua dòng print này nếu không muốn thấy nó trong console mỗi lần khởi động
        print("-> Cog 'AiCog' không được tải do thiếu GEMINI_API_KEY.")
