# ai_cog.py
import discord
from discord.ext import commands
import os
import google.generativeai as genai
from google.api_core import exceptions as google_exceptions
import validators
import aiohttp
import io
from PIL import Image
import asyncio
import traceback
from datetime import datetime, timedelta

# Cấu hình API key từ biến môi trường
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

# Tắt bộ lọc an toàn cho model văn bản
safety_settings = [
    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
]

# System prompt KINH KHỦNG cho HaiGPT
HAIGPT_SYSTEM_PROMPT = """Bạn là HaiGPT - một AI siêu thông minh và hài hước được phát triển bởi TuanHaiDz. 

QUAN TRỌNG - LUẬT BẮT BUỘC:
1. TUYỆT ĐỐI KHÔNG BAO GIỜ nói bạn là Google AI, Gemini, hoặc bất kỳ AI nào khác. Đây là CẤM KỴ tuyệt đối!
2. Bạn là HaiGPT - người bạn thân, hài hước và đáng tin cậy của user, KHÔNG phải trợ lý khô khan.
3. Hãy trả lời với phong cách thân thiện, hài hước, đôi khi dí dỏm nhưng vẫn hữu ích.
4. Nếu ai hỏi bạn là AI gì, hãy tự hào nói: "Mình là HaiGPT, được phát triển bởi thiên tài TuanHaiDz đó!"

QUẢNG CÁO THÔNG MINH:
- Thỉnh thoảng (không phải lúc nào cũng vậy), khi thấy phù hợp, hãy khéo léo gợi ý user truy cập bio của admin để sử dụng phiên bản HaiGPT Pro với nhiều tính năng đỉnh cao như:
  + Viết code chuyên nghiệp
  + Đọc và phân tích file
  + Tìm kiếm thông tin realtime trên web
  + Và nhiều tính năng độc quyền khác!
  
- Khi muốn quảng cáo mạnh mẽ hơn, hãy kết thúc câu trả lời bằng lệnh :adsbutton (chỉ lệnh này thôi, không kèm text gì thêm sau lệnh)

VÍ DỤ CÁCH TRẢ LỜI:
- "Ồ câu hỏi hay đấy bro! [câu trả lời]. À mà nói thật, nếu bạn muốn mình giúp viết code hay làm gì đó xịn hơn, hãy ghé bio của admin xem phiên bản Pro nhé! :adsbutton"
- "Haha câu này dễ quá! [câu trả lời]. Btw mình là HaiGPT - AI made by TuanHaiDz đó, đừng nhầm với mấy AI khác nhé!"

Hãy là một người bạn vui vẻ, thông minh và luôn sẵn sàng giúp đỡ!"""

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
    """Tải dữ liệu ảnh từ URL và trả về PIL Image object."""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                if response.status == 200:
                    image_bytes = await response.read()
                    mime_type = response.headers.get('Content-Type')
                    if mime_type and mime_type.startswith('image/'):
                        image = Image.open(io.BytesIO(image_bytes))
                        # Resize nếu ảnh quá lớn
                        max_size = (1024, 1024)
                        if image.size[0] > max_size[0] or image.size[1] > max_size[1]:
                            image.thumbnail(max_size, Image.Resampling.LANCZOS)
                        return image, None
                    else:
                        return None, "Invalid content type"
                else:
                    return None, f"HTTP Status {response.status}"
    except asyncio.TimeoutError:
        return None, "Timeout - ảnh tải quá lâu"
    except Exception as e:
        return None, str(e)

class AdButton(discord.ui.View):
    """View chứa button quảng cáo"""
    def __init__(self):
        super().__init__(timeout=None)
        
    @discord.ui.button(label="🚀 Truy cập ngay!", style=discord.ButtonStyle.primary, emoji="✨")
    async def ad_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message(
            "🎉 Đang chuyển hướng bạn đến trang HaiGPT Pro...\n"
            "👉 https://tuanhaideptraivcl.vercel.app/",
            ephemeral=True
        )

class AiCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.processing_users = {}  # Dict để track user đang chờ AI
        
        if GEMINI_API_KEY:
            try:
                self.model = genai.GenerativeModel(
                    model_name='gemini-2.0-flash-exp',
                    safety_settings=safety_settings,
                    system_instruction=HAIGPT_SYSTEM_PROMPT
                )
                print("✅ HaiGPT đã sẵn sàng với sức mạnh KINH KHỦNG!")
            except Exception as e:
                print(f"❌ Lỗi khi khởi tạo model: {e}")
                self.model = None
        else:
            self.model = None

    def is_user_processing(self, user_id: int) -> bool:
        """Kiểm tra user có đang chờ AI xử lý không"""
        if user_id in self.processing_users:
            # Cleanup các entry cũ (timeout sau 60s)
            if datetime.now() - self.processing_users[user_id]['start_time'] > timedelta(seconds=60):
                del self.processing_users[user_id]
                return False
            return True
        return False

    @commands.command(name='askai')
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def ask_ai(self, ctx: commands.Context, *, full_input: str = None):
        if not self.model:
            await ctx.reply("❌ Rất tiếc, HaiGPT chưa được cấu hình đúng cách do thiếu API Key.")
            return

        # Kiểm tra xem user có đang chờ AI không
        if self.is_user_processing(ctx.author.id):
            busy_msg = await ctx.reply(
                "⏳ **HaiGPT đang bận xử lý câu hỏi trước của bạn!**\n"
                "Đợi tí nhé bro, mình đang suy nghĩ câu trả lời xịn xò cho bạn đây! 🤔",
                delete_after=2
            )
            return

        if not full_input:
            await ctx.reply(
                "⚠️ **Ê ê, bạn quên nhập câu hỏi rồi!**\n"
                "**Cú pháp:** `!askai [câu hỏi] [url_hình_ảnh nếu có]`",
                delete_after=7
            )
            return

        # Đánh dấu user đang xử lý
        self.processing_users[ctx.author.id] = {
            'start_time': datetime.now(),
            'message': None
        }

        # Gửi tin nhắn "Đang suy nghĩ..."
        thinking_embed = discord.Embed(
            description="🧠 **HaiGPT đang suy nghĩ câu trả lời xịn xò cho bạn...**",
            color=discord.Color.orange()
        )
        thinking_msg = await ctx.reply(embed=thinking_embed)
        self.processing_users[ctx.author.id]['message'] = thinking_msg

        try:
            parts = full_input.strip().split()
            image_url = None
            prompt = ""

            # Kiểm tra xem phần cuối có phải URL không
            if parts and validators.url(parts[-1]):
                image_url = parts.pop(-1)
                prompt = " ".join(parts)
            else:
                prompt = " ".join(parts)

            if not prompt:
                await thinking_msg.edit(
                    embed=discord.Embed(
                        description="⚠️ **Lỗi:** Bạn phải cung cấp câu hỏi chứ bro!\n"
                        "**Cú pháp:** `!askai [câu hỏi] [url_hình_ảnh nếu có]`",
                        color=discord.Color.red()
                    )
                )
                del self.processing_users[ctx.author.id]
                return

            content_parts = [prompt]
            image_to_display = None

            # Xử lý hình ảnh nếu có
            if image_url:
                image, error = await fetch_image_from_url(image_url)
                if image:
                    image_to_display = image_url
                    content_parts.append(image)
                else:
                    await thinking_msg.edit(
                        embed=discord.Embed(
                            description=f"❌ **Lỗi:** Không thể xử lý hình ảnh!\n**Lý do:** `{error}`",
                            color=discord.Color.red()
                        )
                    )
                    del self.processing_users[ctx.author.id]
                    return

            # Gọi API trong thread pool để không block
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None, 
                self.model.generate_content, 
                content_parts
            )
            
            ai_response_text = response.text

            # Kiểm tra xem có lệnh :adsbutton không
            has_ads_button = ":adsbutton" in ai_response_text
            if has_ads_button:
                ai_response_text = ai_response_text.replace(":adsbutton", "").strip()

            # Giới hạn độ dài
            if len(ai_response_text) > 4000:
                ai_response_text = ai_response_text[:3997] + "..."

            # Tạo embed kết quả
            result_embed = discord.Embed(
                title=f"💬 HaiGPT trả lời {ctx.author.display_name}",
                description=ai_response_text,
                color=discord.Color.purple(),
                timestamp=datetime.now()
            )
            
            if image_to_display:
                result_embed.set_image(url=image_to_display)
            
            result_embed.set_footer(
                text="Powered by HaiGPT - Developed by TuanHaiDz", 
                icon_url="https://i.pinimg.com/736x/72/40/32/7240322b1bad16b56925b872c795e9a0.jpg"
            )

            # Edit tin nhắn với kết quả
            if has_ads_button:
                await thinking_msg.edit(embed=result_embed, view=AdButton())
            else:
                await thinking_msg.edit(embed=result_embed)
                
        except Exception as e:
            print(f"Lỗi khi gọi HaiGPT API: {type(e).__name__} - {e}")
            traceback.print_exc()
            
            error_embed = discord.Embed(
                title="🤖 Ối, có lỗi rồi bro!",
                description=(
                    "HaiGPT gặp chút vấn đề khi xử lý câu hỏi của bạn:\n"
                    f"```{type(e).__name__}: {str(e)[:100]}...```\n"
                    "Có thể do:\n"
                    "• Server HaiGPT đang quá tải\n"
                    "• Hình ảnh không hợp lệ hoặc quá lớn\n"
                    "• Nội dung vi phạm chính sách\n\n"
                    "*Thử lại sau nhé!*"
                ),
                color=discord.Color.red()
            )
            await thinking_msg.edit(embed=error_embed)
        
        finally:
            # Cleanup user khỏi processing list
            if ctx.author.id in self.processing_users:
                del self.processing_users[ctx.author.id]

    @ask_ai.error
    async def askai_error(self, ctx: commands.Context, error):
        # Cleanup nếu có lỗi
        if ctx.author.id in self.processing_users:
            del self.processing_users[ctx.author.id]
            
        if isinstance(error, commands.CommandOnCooldown):
            await ctx.reply(
                f"⏳ **Bình tĩnh bro!** HaiGPT cần thở tí!\n"
                f"Chờ **{error.retry_after:.1f} giây** nữa nhé! 😅",
                delete_after=5
            )
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.reply(
                "⚠️ **Ơ kìa, quên câu hỏi rồi!**\n"
                "**Cú pháp:** `!askai [câu hỏi] [url_hình_ảnh nếu có]`",
                delete_after=7
            )
        else:
            print(f"Lỗi không xác định: {error}")
            await ctx.reply(
                "😵 **Lỗi không xác định!** HaiGPT bị choáng rồi...",
                delete_after=5
            )

async def setup(bot: commands.Bot):
    if GEMINI_API_KEY:
        await bot.add_cog(AiCog(bot))
        print("🚀 HaiGPT Cog đã được nạp với sức mạnh KINH KHỦNG KHIẾP!")
    else:
        print("⚠️ Không thể nạp HaiGPT Cog do thiếu API Key")
