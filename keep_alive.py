# keep_alive.py
from flask import Flask, render_template, request, jsonify, redirect
import os
import requests
from datetime import datetime, timedelta
import asyncio

app = Flask(__name__)

# Global bot reference
bot_instance = None

def set_bot_instance(bot):
    global bot_instance
    bot_instance = bot

@app.route('/')
def home():
    return "Bot is alive!"

@app.route('/verify')
def verify_page():
    token = request.args.get('token')
    if not token:
        return "Invalid verification link", 400
    
    try:
        user_id, guild_id = token.split('_')
        user_id = int(user_id)
        guild_id = int(guild_id)
        
        # Lấy thông tin guild và user
        if bot_instance:
            guild = bot_instance.get_guild(guild_id)
            if guild:
                guild_icon = guild.icon.url if guild.icon else "https://cdn.discordapp.com/embed/avatars/0.png"
                guild_name = guild.name
            else:
                guild_icon = "https://cdn.discordapp.com/embed/avatars/0.png"
                guild_name = "Discord Server"
        else:
            guild_icon = "https://cdn.discordapp.com/embed/avatars/0.png"
            guild_name = "Discord Server"
        
        site_key = os.getenv('RECAPTCHA_SITE_KEY')
        if not site_key:
            return "reCAPTCHA not configured", 500
            
        return render_template('verify.html', 
                             site_key=site_key, 
                             token=token,
                             guild_icon=guild_icon,
                             guild_name=guild_name)
    except:
        return "Invalid verification link", 400

@app.route('/verify_captcha', methods=['POST'])
def verify_captcha():
    try:
        token = request.form.get('token')
        recaptcha_response = request.form.get('g-recaptcha-response')
        
        if not token or not recaptcha_response:
            return jsonify({'success': False, 'message': 'Missing data'})
        
        # Verify reCAPTCHA
        secret_key = os.getenv('RECAPTCHA_SECRET_KEY')
        if not secret_key:
            return jsonify({'success': False, 'message': 'Server configuration error'})
        
        verify_url = 'https://www.google.com/recaptcha/api/siteverify'
        verify_data = {
            'secret': secret_key,
            'response': recaptcha_response,
            'remoteip': request.remote_addr
        }
        
        verify_result = requests.post(verify_url, data=verify_data)
        result = verify_result.json()
        
        if result.get('success'):
            # reCAPTCHA thành công, complete verification
            try:
                user_id, guild_id = token.split('_')
                user_id = int(user_id)
                guild_id = int(guild_id)
                
                # Gọi hàm complete verification của bot
                if bot_instance:
                    verification_cog = bot_instance.get_cog('VerificationCog')
                    if verification_cog:
                        # Chạy trong background task
                        asyncio.create_task(verification_cog.complete_verification(user_id, guild_id))
                        
                return jsonify({'success': True, 'message': 'Verification completed successfully!'})
            except Exception as e:
                print(f"Error completing verification: {e}")
                return jsonify({'success': False, 'message': 'Verification processing error'})
        else:
            return jsonify({'success': False, 'message': 'reCAPTCHA verification failed'})
            
    except Exception as e:
        print(f"Error in verify_captcha: {e}")
        return jsonify({'success': False, 'message': 'Server error'})

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    from threading import Thread
    t = Thread(target=run)
    t.daemon = True
    t.start()
