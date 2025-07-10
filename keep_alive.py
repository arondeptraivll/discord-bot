# keep_alive.py (ĐÃ SỬA LỖI)
from flask import Flask, render_template, request
from threading import Thread
import os
import requests
import asyncio
import discord

# Biến toàn cục để lưu bot instance
_bot = None

app = Flask(__name__, template_folder='templates')

# Hàm để chạy coroutine của Discord từ một thread khác (thread của Flask)
def run_discord_task(coro):
    future = asyncio.run_coroutine_threadsafe(coro, _bot.loop)
    try:
        future.result()
    except Exception as e:
        print(f"Error running Discord task from Flask thread: {e}")

# Trang chủ
@app.route('/')
def home():
    return "Bot Verification Server is alive!"

# Trang xác minh
@app.route('/verify/<token>', methods=['GET', 'POST'])
def verify(token):
    session = _bot.verification_sessions.get(token)
    
    if not session:
        return render_template('invalid.html', message="Liên kết xác minh không hợp lệ hoặc đã được sử dụng."), 404

    user_id_to_verify = session['user_id']
    print(f"Attempting verification for user ID: {user_id_to_verify} with token: {token}")

    if request.method == 'POST':
        recaptcha_response = request.form.get('g-recaptcha-response')
        payload = {'secret': os.getenv('RECAPTCHA_SECRET_KEY'), 'response': recaptcha_response}
        response = requests.post('https://www.google.com/recaptcha/api/siteverify', data=payload)
        result = response.json()

        if result.get('success'):
            print(f"User ID {user_id_to_verify} verified successfully via web.")
            run_discord_task(handle_successful_verification(token))
            return render_template('success.html')
        else:
            print(f"User ID {user_id_to_verify} failed verification. Reason: {result.get('error-codes')}")
            return render_template('verify.html', site_key=os.getenv('RECAPTCHA_SITE_KEY'), token=token, error="Xác minh CAPTCHA thất bại. Vui lòng thử lại.")

    return render_template('verify.html', site_key=os.getenv('RECAPTCHA_SITE_KEY'), token=token, error=None)

def run():
  # SỬA LỖI QUAN TRỌNG Ở ĐÂY
  app.run(host='0.0.0.0', port=8080)

def keep_alive(bot_instance):
    global _bot
    _bot = bot_instance
    t = Thread(target=run)
    t.start()

async def handle_successful_verification(token):
    session = _bot.verification_sessions.pop(token, None)
    if not session: return

    guild = _bot.get_guild(session['guild_id'])
    if not guild: return
    
    member = guild.get_member(session['user_id'])
    if not member: return

    unverify_role = discord.utils.get(guild.roles, name="Unverify")

    if unverify_role and unverify_role in member.roles:
        await member.remove_roles(unverify_role, reason="Hoàn thành xác minh Captcha")
        print(f"Đã xóa role 'Unverify' khỏi {member.name}")

    try:
        channel = guild.get_channel(session['channel_id'])
        if channel:
            message = await channel.fetch_message(session['message_id'])
            await message.delete()
            print(f"Đã xóa tin nhắn xác minh của {member.name}")
    except (discord.NotFound, discord.Forbidden):
        pass
