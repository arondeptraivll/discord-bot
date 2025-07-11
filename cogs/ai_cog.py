import discord
from discord.ext import commands
import os
import google.generativeai as genai
from google.api_core import exceptions as google_exceptions

# Cấu hình API key từ biến môi trường
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

# Tắt bộ lọc an toàn
safety_settings = [
    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
]

# Chỉ cấu hình và tạo model nếu có API KEY
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
else:
    print("⚠️ CẢNH BÁO: GEMINI_API_KEY không được tìm thấy. Lệnh !askai sẽ không hoạt động.")


class AiCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        if GEMINI_API_KEY:
            # ===> THAY ĐỔI 1: NÂNG CẤP LÊN GEMINI 1.5 FLASH <===
            self.model = genai.GenerativeModel(
                model_name='gemini-1.5-flash-latest', 
                safety_settings=safety_settings
            )
        else:
            self.model = None

    @commands.command(name='askai')
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def ask_ai(self, ctx: commands.Context, *, prompt: str):
        if not self.model:
            await ctx.reply("❌ Rất tiếc, tính năng AI chưa được cấu hình đúng cách do thiếu API Key.")
            return

        async with ctx.typing():
            try:
                response = await self.model.generate_content_async(prompt)
                ai_response_text = response.text

                if len(ai_response_text) > 4000:
                    ai_response_text = ai_response_text[:4000] + "\n... (Nội dung quá dài đã được cắt bớt)"

                embed = discord.Embed(
                    title=f"💬 Câu trả lời cho {ctx.author.display_name}",
                    description=ai_response_text,
                    color=discord.Color.purple()
                )
                embed.set_footer(text="Cung cấp bởi Google Gemini 1.5 Flash", icon_url="https://i.imgur.com/v4vL5V2.png")
                
                await ctx.reply(embed=embed)
                
            # ===> THAY ĐỔI 2: XỬ LÝ LỖI TRIỆT ĐỂ HƠN <===
            except (google_exceptions.GoogleAPICallError, google_exceptions.RetryError, Exception) as e:
                # Bắt tất cả các lỗi tiềm tàng từ API của Google và các lỗi chung khác.
                print(f"Lỗi khi gọi Gemini API với prompt '{prompt}': {type(e).__name__} - {e}")
                
                error_embed = discord.Embed(
                    title="🤖 Đã có lỗi bất ngờ",
                    description="Không thể xử lý yêu cầu của bạn tại thời điểm này. Có thể do lỗi từ máy chủ của AI hoặc câu hỏi quá phức tạp. Vui lòng thử lại sau.",
                    color=discord.Color.red()
                )
                await ctx.reply(embed=error_embed)
                # Dòng "return" này cực kỳ quan trọng. 
                # Nó sẽ ngăn không cho lỗi bị xử lý thêm lần nữa bởi @ask_ai.error.
                return 

    @ask_ai.error
    async def askai_error(self, ctx: commands.Context, error):
        # Bộ xử lý này giờ chỉ còn xử lý các lỗi của discord.py như Cooldown và thiếu tham số.
        # Các lỗi từ API đã được xử lý bên trong lệnh ask_ai.
        if isinstance(error, commands.CommandOnCooldown):
            await ctx.reply(f"⏳ Bạn đang thao tác quá nhanh! Vui lòng chờ **{error.retry_after:.1f} giây**.", delete_after=5)
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.reply("⚠️ Bạn quên nhập câu hỏi rồi! Cú pháp: `!askai [câu hỏi của bạn]`", delete_after=5)
        else:
            # Các lỗi không mong muốn khác vẫn sẽ được in ra console để bạn debug.
            print(f"Lỗi không xác định được xử lý bởi askai_error: {error}")
