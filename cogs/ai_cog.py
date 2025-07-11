# ai_cog.py
import discord
from discord.ext import commands
import os
import google.generativeai as genai
import validators
import aiohttp # <-- Quan trọng để gọi API trực tiếp
import io
import json     # <-- Quan trọng để làm việc với JSON
import base64   # <-- Quan trọng để giải mã ảnh

# Cấu hình API key từ biến môi trường
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

# Model tạo ảnh chính xác từ danh sách của bạn
IMAGE_MODEL_NAME = 'gemini-2.0-flash-preview-image-generation'

# Tắt bộ lọc an toàn cho model văn bản
safety_settings = [
    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
]

# Chỉ cấu hình và tạo model nếu có API KEY
if GEMINI_API_KEY:
    try:
        # Chúng ta vẫn dùng thư viện này cho các tác vụ văn bản
        genai.configure(api_key=GEMINI_API_KEY)
    except Exception as e:
        print(f"❌ Lỗi khi cấu hình Google Gemini API: {e}")
        GEMINI_API_KEY = None
else:
    print("⚠️ CẢNH BÁO: GEMINI_API_KEY không được tìm thấy.")

# ---- Các hàm helper không đổi ----
async def fetch_image_from_url(url: str):
    # ... code không đổi ...
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
            self.text_model = genai.GenerativeModel(
                model_name='gemini-2.5-pro',
                safety_settings=safety_settings
            )
            # Chúng ta không cần khởi tạo image_model qua thư viện nữa
            self.image_model_available = True
        else:
            self.text_model = None
            self.image_model_available = False

    # Lệnh !listmodels không đổi
    @commands.command(name='listmodels', hidden=True)
    @commands.is_owner()
    async def list_models(self, ctx: commands.Context):
        # ... code không đổi ...
        await ctx.send("🔍 Đang truy vấn danh sách các model khả dụng từ Google...")
        try:
            model_list = [f"- `{m.name}`" for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
            
            if not model_list:
                await ctx.send("❌ Không tìm thấy model nào khả dụng cho API Key này.")
                return

            description = "\n".join(model_list)
            embed = discord.Embed(title="✅ Các Model Khả Dụng", description=description, color=discord.Color.green())
            await ctx.author.send(embed=embed)
            await ctx.message.add_reaction('✅')
        except Exception as e:
            await ctx.send(f"❌ Đã có lỗi khi truy vấn model: `{e}`")

    # ====> LỆNH GENIMAGE ĐÃ ĐƯỢC VIẾT LẠI HOÀN TOÀN <====
    @commands.command(name='genimage')
    @commands.cooldown(1, 30, commands.BucketType.user)
    async def generate_image(self, ctx: commands.Context, *, prompt: str):
        if not self.image_model_available:
            await ctx.reply("❌ Rất tiếc, tính năng tạo ảnh chưa được cấu hình đúng cách do thiếu API Key.")
            return

        waiting_message = await ctx.reply(f"🎨 Đang vẽ tranh theo yêu cầu của bạn: `{prompt}`...")

        # URL của API, sử dụng phiên bản v1beta
        api_url = f"https://generativelanguage.googleapis.com/v1beta/models/{IMAGE_MODEL_NAME}:generateContent?key={GEMINI_API_KEY}"

        # Dữ liệu gửi đi, định dạng theo đúng yêu cầu của API
        payload = {
            "contents": [{
                "parts": [{"text": prompt}]
            }],
            # Thêm cấu hình này để yêu cầu trả về 1 ảnh
            "generation_config": {
                "candidate_count": 1
            }
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(api_url, json=payload) as response:
                    # Kiểm tra xem API có trả về thành công không
                    if response.status == 200:
                        response_json = await response.json()
                        # Dữ liệu ảnh được mã hóa base64
                        base64_image_data = response_json['candidates'][0]['content']['parts'][0]['inlineData']['data']
                        # Giải mã để lấy dữ liệu bytes
                        image_bytes = base64.b64decode(base64_image_data)

                        # Tạo file và gửi đi như bình thường
                        image_file = discord.File(fp=io.BytesIO(image_bytes), filename="generated_image.png")
                        embed = discord.Embed(title=f"🖼️ Ảnh của {ctx.author.display_name} đây", color=discord.Color.random())
                        embed.set_image(url="attachment://generated_image.png")
                        embed.set_footer(text="Tạo bởi Google Gemini 2.0 Flash", icon_url="https://i.imgur.com/v4vL5V2.png")

                        await waiting_message.delete()
                        await ctx.reply(embed=embed, file=image_file)
                    else:
                        # Nếu API báo lỗi, hiển thị lỗi đó
                        error_text = await response.text()
                        await waiting_message.delete()
                        await ctx.reply(f"❌ Lỗi từ Google API (Code: {response.status}): ```{error_text}```")

        except Exception as e:
            await waiting_message.delete()
            print(f"LỖI CHI TIẾT KHI TẠO ẢNH: {type(e).__name__} - {e}")
            await ctx.reply(f"❌ Rất tiếc, không thể tạo ảnh. Lỗi cục bộ: `{str(e)}`")

    # ---- Các lệnh và hàm xử lý lỗi khác giữ nguyên ----
    @generate_image.error
    # ...
    async def genimage_error(self, ctx: commands.Context, error):
        if isinstance(error, commands.CommandOnCooldown):
            await ctx.reply(f"⏳ Bạn đang thao tác quá nhanh! Vui lòng chờ **{error.retry_after:.1f} giây**.", delete_after=5)
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.reply("⚠️ Bạn quên nhập nội dung để vẽ ảnh rồi! Cú pháp: `!genimage [nội dung bạn muốn vẽ]`", delete_after=7)
        else:
            print(f"Lỗi không xác định trong lệnh genimage: {error}")
            await ctx.reply("Đã xảy ra một lỗi cú pháp hoặc logic trong nội bộ bot.", delete_after=5)

    @commands.command(name='askai')
    # ...
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
    # ...
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
