# ai_cog.py
import discord
from discord.ext import commands
import os
import google.generativeai as genai
from google.api_core import exceptions as google_exceptions
import validators
import aiohttp
import io

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
    try:
        genai.configure(api_key=GEMINI_API_KEY)
    except Exception as e:
        print(f"❌ Lỗi khi cấu hình Google Gemini API: {e}")
        GEMINI_API_KEY = None
else:
    print("⚠️ CẢNH BÁO: GEMINI_API_KEY không được tìm thấy. Lệnh !askai sẽ không hoạt động.")

async def fetch_image_from_url(url: str):
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    image_bytes = await response.read()
                    mime_type = response.headers.get('Content-Type')
                    if mime_type and mime_type.startswith('image/'):
                        return image_bytes, mime_type
                    else:
                        return None, "Invalid content type"
                else:
                    return None, f"HTTP Status {response.status}"
    except Exception as e:
        return None, str(e)

class AiCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        if GEMINI_API_KEY:
            # Model cho chat và phân tích
            self.text_model = genai.GenerativeModel(
                model_name='gemini-2.5-pro',
                safety_settings=safety_settings
            )
            # Model tạo ảnh mạnh nhất (sẽ hoạt động sau khi bật Vertex AI API)
            self.image_model = genai.GenerativeModel(
                model_name='models/imagen-4.0-ultra-generate-preview-06-06'
            )
        else:
            self.text_model = None
            self.image_model = None

    @commands.command(name='genimage')
    @commands.cooldown(1, 30, commands.BucketType.user)
    async def generate_image(self, ctx: commands.Context, *, prompt: str):
        if not self.image_model:
            await ctx.reply("❌ Rất tiếc, tính năng tạo ảnh chưa được cấu hình đúng cách do thiếu API Key.")
            return

        waiting_message = await ctx.reply(f"🎨 Đang vẽ tranh **chất lượng cao** theo yêu cầu của bạn: `{prompt}`. Vui lòng đợi một chút...")

        try:
            # Chạy tác vụ blocking trong một luồng riêng để không làm bot bị treo
            def generation_func():
                return self.image_model.generate_content(prompt)

            response = await self.bot.loop.run_in_executor(None, generation_func)
            image_bytes = response.images[0]._image_bytes
            image_file = discord.File(fp=io.BytesIO(image_bytes), filename="generated_image.png")
            
            embed = discord.Embed(
                title=f"🖼️ Ảnh của {ctx.author.display_name} đây",
                color=discord.Color.random()
            )
            embed.set_image(url="attachment://generated_image.png")
            embed.set_footer(text="Tạo bởi Google Imagen 4.0 Ultra", icon_url="https://i.imgur.com/v4vL5V2.png")

            await waiting_message.delete()
            await ctx.reply(embed=embed, file=image_file)

        except Exception as e:
            await waiting_message.delete()
            print(f"LỖI CHI TIẾT KHI TẠO ẢNH: {type(e).__name__} - {e}")
            
            error_type = type(e).__name__
            error_details = str(e)

            # Phân tích lỗi để đưa ra thông báo thân thiện hơn
            user_friendly_error = "Đã có lỗi bất ngờ xảy ra khi tạo ảnh."
            if "permissiondenied" in error_details.lower() or "service has been disabled" in error_details.lower():
                user_friendly_error = "API Key của bạn không có quyền sử dụng model này. Vui lòng kiểm tra và đảm bảo **Vertex AI API** đã được bật trong Google Cloud Project của bạn."
            elif "unsupporteduserlocation" in error_details.lower():
                user_friendly_error = "Rất tiếc, tính năng này không khả dụng tại khu vực của bạn."
            elif "prompt violates the safety policy" in error_details.lower():
                 user_friendly_error = "Yêu cầu của bạn đã vi phạm chính sách an toàn. Vui lòng thử một ý tưởng khác."


            error_embed = discord.Embed(
                title="❌ Tạo ảnh thất bại",
                description=user_friendly_error,
                color=discord.Color.red()
            )
            error_embed.add_field(name="Loại lỗi API", value=f"`{error_type}`", inline=False)
            
            await ctx.reply(embed=error_embed)


    @generate_image.error
    async def genimage_error(self, ctx: commands.Context, error):
        if isinstance(error, commands.CommandOnCooldown):
            await ctx.reply(f"⏳ Bạn đang thao tác quá nhanh! Vui lòng chờ **{error.retry_after:.1f} giây**.", delete_after=5)
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.reply("⚠️ Bạn quên nhập nội dung để vẽ ảnh rồi! Cú pháp: `!genimage [nội dung bạn muốn vẽ]`", delete_after=7)
        else:
            print(f"Lỗi không xác định trong lệnh genimage: {error}")
            await ctx.reply("Đã xảy ra một lỗi cú pháp hoặc logic trong nội bộ bot.", delete_after=5)
            
    # Lệnh !askai không thay đổi
    @commands.command(name='askai')
    @commands.cooldown(1, 15, commands.BucketType.user)
    async def ask_ai(self, ctx: commands.Context, *, full_input: str):
        if not self.text_model:
            await ctx.reply("❌ Rất tiếc, tính năng AI chưa được cấu hình đúng cách do thiếu API Key.")
            return

        async with ctx.typing():
            parts = full_input.strip().split()
            image_url = None
            prompt = ""

            if validators.url(parts[-1]):
                image_url = parts.pop(-1)
                prompt = " ".join(parts)
            else:
                prompt = " ".join(parts)

            if not prompt:
                await ctx.reply(
                    "⚠️ **Lỗi:** Bạn phải cung cấp câu hỏi.\n"
                    "**Cú pháp đúng:** `!askai [câu hỏi bắt buộc] [url_hình_ảnh tùy chọn]`",
                    delete_after=10
                )
                return

            content_parts = []
            image_to_display = None

            if image_url:
                image_bytes, mime_type_or_error = await fetch_image_from_url(image_url)
                if image_bytes:
                    image_to_display = image_url
                    image_part = {"mime_type": mime_type_or_error, "data": image_bytes}
                    content_parts.append(image_part)
                else:
                    await ctx.reply(f"❌ Không thể xử lý hình ảnh từ URL. Lý do: `{mime_type_or_error}`")
                    return
            
            content_parts.append(prompt)

            try:
                response = await self.text_model.generate_content_async(content_parts)
                ai_response_text = response.text

                if len(ai_response_text) > 4000:
                    ai_response_text = ai_response_text[:4000] + "\n... (Nội dung quá dài đã được cắt bớt)"

                embed = discord.Embed(
                    title=f"💬 Câu trả lời cho {ctx.author.display_name}",
                    description=ai_response_text,
                    color=discord.Color.purple()
                )
                
                if image_to_display:
                    embed.set_image(url=image_to_display)
                
                embed.set_footer(text="Cung cấp bởi Google Gemini 2.5 Pro", icon_url="https://i.imgur.com/v4vL5V2.png")
                
                await ctx.reply(embed=embed)
                
            except Exception as e:
                print(f"Lỗi khi gọi Gemini API: {type(e).__name__} - {e}")
                error_embed = discord.Embed(
                    title="🤖 Đã có lỗi bất ngờ",
                    description="Không thể xử lý yêu cầu của bạn. Điều này có thể do:\n- Lỗi từ máy chủ AI.\n- Hình ảnh không được hỗ trợ hoặc quá lớn.\n- Câu hỏi của bạn vi phạm chính sách nội dung của AI.",
                    color=discord.Color.red()
                )
                await ctx.reply(embed=error_embed)
                return 

    @ask_ai.error
    async def askai_error(self, ctx: commands.Context, error):
        if isinstance(error, commands.CommandOnCooldown):
            await ctx.reply(f"⏳ Bạn đang thao tác quá nhanh! Vui lòng chờ **{error.retry_after:.1f} giây**.", delete_after=5)
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.reply(
                "⚠️ **Bạn quên nhập câu hỏi rồi!**\n"
                "**Cú pháp:** `!askai [câu hỏi bắt buộc] [url_hình_ảnh tùy chọn]`", 
                delete_after=7
            )
        else:
            print(f"Lỗi không xác định được xử lý bởi askai_error: {error}")
            await ctx.reply("Đã xảy ra một lỗi không xác định. Vui lòng thử lại.", delete_after=5)

async def setup(bot: commands.Bot):
    if GEMINI_API_KEY:
        await bot.add_cog(AiCog(bot))
    else:
        pass
