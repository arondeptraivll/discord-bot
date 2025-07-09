# app/database.py
import sqlite3
import uuid
import hashlib
from typing import Optional

DB_FILE = "app_data.sqlite"

def setup_database():
    """Khởi tạo các bảng cần thiết trong database nếu chưa tồn tại."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    # Bảng lưu các link đang hoạt động
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS trackers (
        id TEXT PRIMARY KEY,
        creator_id INTEGER NOT NULL,
        target_url TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    # Bảng lưu log những người đã truy cập
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS logs (
        log_id INTEGER PRIMARY KEY AUTOINCREMENT,
        tracker_id TEXT NOT NULL,
        visitor_id TEXT NOT NULL,
        ip_address TEXT,
        fingerprint TEXT,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (tracker_id) REFERENCES trackers (id)
    )
    ''')
    conn.commit()
    conn.close()

def add_tracker(creator_id: int, target_url: str) -> str:
    """Tạo một tracker mới và trả về ID của nó."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    new_id = uuid.uuid4().hex[:10] # Tạo ID ngắn
    cursor.execute("INSERT INTO trackers (id, creator_id, target_url) VALUES (?, ?, ?)",
                   (new_id, creator_id, target_url))
    conn.commit()
    conn.close()
    return new_id

def get_tracker_by_id(tracker_id: str) -> Optional[dict]:
    """Lấy thông tin tracker bằng ID."""
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM trackers WHERE id = ?", (tracker_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def get_tracker_by_creator(creator_id: int) -> Optional[dict]:
    """Kiểm tra xem một người dùng đã có tracker nào đang hoạt động chưa."""
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM trackers WHERE creator_id = ?", (creator_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def remove_tracker(creator_id: int) -> bool:
    """Xóa tracker của một người dùng và các log liên quan."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    # Tìm tracker ID trước khi xóa
    cursor.execute("SELECT id FROM trackers WHERE creator_id = ?", (creator_id,))
    result = cursor.fetchone()
    if not result:
        conn.close()
        return False
        
    tracker_id = result[0]
    # Xóa tracker và logs
    cursor.execute("DELETE FROM trackers WHERE creator_id = ?", (creator_id,))
    cursor.execute("DELETE FROM logs WHERE tracker_id = ?", (tracker_id,))
    conn.commit()
    conn.close()
    return True

def add_log(tracker_id: str, ip_address: str, fingerprint_data: dict):
    """Lưu lại log truy cập."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    # Tạo visitor ID dựa trên IP và một phần của fingerprint để nhận diện người dùng cũ
    fp_hash_part = fingerprint_data.get('visitorId', 'unknown')
    visitor_hash = hashlib.md5(f"{ip_address}-{fp_hash_part}".encode()).hexdigest()[:12]
    
    fingerprint_str = "\n".join([f"{k}: {v}" for k, v in fingerprint_data.items()])
    if not fingerprint_str:
        fingerprint_str = "Bị chặn hoặc không thể lấy."

    cursor.execute("INSERT INTO logs (tracker_id, visitor_id, ip_address, fingerprint) VALUES (?, ?, ?, ?)",
                   (tracker_id, visitor_hash, ip_address, fingerprint_str))
    conn.commit()
    conn.close()

# Khởi tạo DB khi module được import
setup_database()
