import discord
from discord.ext import commands
import os
import google.generativeai as genai

# Cấu hình API key từ biến môi trường
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

# --- THAY ĐỔI LỚN: TẮT HOÀN TOÀN BỘ LỌC AN TOÀN ---
# Bằng cách đặt tất cả các ngưỡng thành "BLOCK_NONE", chúng ta yêu cầu AI không chặn bất kỳ phản hồi nào.
# Cảnh báo: Điều này có thể cho phép AI tạo ra nội dung nhạy cảm.
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
    # In cảnh báo một lần khi bot khởi động nếu không có key
    print("⚠️ CẢNH BÁO: GEMINI_API_KEY không được tìm thấy. Lệnh !askai sẽ không hoạt động.")


class AiCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        # Chỉ khởi tạo model nếu API key hợp lệ
        if GEMINI_API_KEY:
            # Sử dụng safety_settings đã được cấu hình ở trên
            self.model = genai.GenerativeModel('gemini-pro', safety_settings=safety_settings)
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
                # Gửi prompt tới Gemini và nhận phản hồi
                response = await self.model.generate_content_async(prompt)
                
                # Với safety filter đã tắt, việc truy cập response.text sẽ an toàn hơn nhiều
                ai_response_text = response.text

                # Kiểm tra độ dài phản hồi để tránh lỗi của Discord
                if len(ai_response_text) > 4000:
                    ai_response_text = ai_response_text[:4000] + "\n... (Nội dung quá dài đã được cắt bớt)"

                # Tạo embed để gửi lại cho người dùng
                embed = discord.Embed(
                    title=f"💬 Câu trả lời cho {ctx.author.display_name}",
                    description=ai_response_text,
                    color=discord.Color.purple()
                )
                embed.set_footer(text="Cung cấp bởi Google Gemini", icon_url="https://i.imgur.com/v4vL5V2.png")
                
                await ctx.reply(embed=embed)

            except Exception as e:
                # Xử lý các lỗi chung khác (ví dụ: lỗi mạng, API server down...)
                print(f"Lỗi khi gọi Gemini API: {e}")
                error_embed = discord.Embed(
                    title="🤖 Đã có lỗi bất ngờ",
                    description="Không thể xử lý yêu cầu của bạn tại thời điểm này. Vui lòng thử lại sau.",
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
            # Ghi log các lỗi không xác định để debug
            print(f"Lỗi không xác định trong lệnh !askai: {error}")

async def setup(bot):
    # Chỉ thêm Cog nếu API Key tồn tại và hợp lệ
    if GEMINI_API_KEY:
        await bot.add_cog(AiCog(bot))
    else:
        # Cog sẽ không được tải nếu thiếu key, thông báo đã được in ở trên
        pass
