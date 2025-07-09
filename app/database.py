# app/database.py
# File này đã được viết lại hoàn toàn để sử dụng PostgreSQL qua DATABASE_URL.

import psycopg2
from psycopg2.extras import DictCursor
import os
import uuid
import hashlib
from typing import Optional

# Lấy URL kết nối từ biến môi trường
DATABASE_URL = os.getenv('DATABASE_URL')
if not DATABASE_URL:
    raise Exception("❌ Cấu hình thiếu: Biến môi trường DATABASE_URL chưa được thiết lập.")

def get_db_connection():
    """Tạo và trả về một kết nối đến database."""
    try:
        # DictCursor giúp chúng ta truy cập các cột bằng tên, giống như dictionary
        conn = psycopg2.connect(DATABASE_URL, cursor_factory=DictCursor)
        return conn
    except psycopg2.OperationalError as e:
        print(f"❌ Không thể kết nối đến PostgreSQL Database: {e}")
        raise

def setup_database():
    """Khởi tạo các bảng cần thiết trong database nếu chưa tồn tại."""
    conn = get_db_connection()
    try:
        # 'with' statement đảm bảo commit hoặc rollback và đóng kết nối tự động
        with conn:
            with conn.cursor() as cur:
                # Bảng lưu các link đang hoạt động
                # BIGINT cho Discord ID, SERIAL/BIGSERIAL cho khóa tự tăng trong PG
                cur.execute('''
                CREATE TABLE IF NOT EXISTS trackers (
                    id TEXT PRIMARY KEY,
                    creator_id BIGINT NOT NULL,
                    target_url TEXT NOT NULL,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT (NOW() AT TIME ZONE 'utc')
                )
                ''')
                # Bảng lưu log những người đã truy cập
                cur.execute('''
                CREATE TABLE IF NOT EXISTS logs (
                    log_id BIGSERIAL PRIMARY KEY,
                    tracker_id TEXT NOT NULL,
                    visitor_id TEXT NOT NULL,
                    ip_address TEXT,
                    fingerprint TEXT,
                    timestamp TIMESTAMP WITH TIME ZONE DEFAULT (NOW() AT TIME ZONE 'utc'),
                    FOREIGN KEY (tracker_id) REFERENCES trackers (id) ON DELETE CASCADE
                )
                ''')
                print("✅ Database tables checked/created successfully.")
    finally:
        conn.close()


def add_tracker(creator_id: int, target_url: str) -> str:
    """Tạo một tracker mới và trả về ID của nó."""
    new_id = uuid.uuid4().hex[:10]
    conn = get_db_connection()
    try:
        with conn:
            with conn.cursor() as cur:
                # PostgreSQL sử dụng %s làm placeholder thay vì ?
                cur.execute(
                    "INSERT INTO trackers (id, creator_id, target_url) VALUES (%s, %s, %s)",
                    (new_id, creator_id, target_url)
                )
    finally:
        conn.close()
    return new_id

def get_tracker_by_id(tracker_id: str) -> Optional[dict]:
    """Lấy thông tin tracker bằng ID."""
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM trackers WHERE id = %s", (tracker_id,))
            row = cur.fetchone()
            return dict(row) if row else None
    finally:
        conn.close()


def get_tracker_by_creator(creator_id: int) -> Optional[dict]:
    """Kiểm tra xem một người dùng đã có tracker nào đang hoạt động chưa."""
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM trackers WHERE creator_id = %s", (creator_id,))
            row = cur.fetchone()
            return dict(row) if row else None
    finally:
        conn.close()


def remove_tracker(creator_id: int) -> bool:
    """Xóa tracker của một người dùng và các log liên quan."""
    conn = get_db_connection()
    try:
        with conn:
            with conn.cursor() as cur:
                # ON DELETE CASCADE trong định nghĩa bảng logs sẽ tự động xóa các log liên quan.
                cur.execute("DELETE FROM trackers WHERE creator_id = %s", (creator_id,))
                # cur.rowcount sẽ > 0 nếu có hàng bị xóa
                return cur.rowcount > 0
    finally:
        conn.close()

def add_log(tracker_id: str, ip_address: str, fingerprint_data: dict):
    """Lưu lại log truy cập."""
    conn = get_db_connection()
    try:
        fp_hash_part = fingerprint_data.get('visitorId', 'unknown')
        visitor_hash = hashlib.md5(f"{ip_address}-{fp_hash_part}".encode()).hexdigest()[:12]
        
        fingerprint_str = "\n".join([f"{k}: {v}" for k, v in fingerprint_data.items()])
        if not fingerprint_str:
            fingerprint_str = "Bị chặn hoặc không thể lấy."

        with conn:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO logs (tracker_id, visitor_id, ip_address, fingerprint) VALUES (%s, %s, %s, %s)",
                    (tracker_id, visitor_hash, ip_address, fingerprint_str)
                )
    finally:
        conn.close()


# Khởi tạo DB khi module được import
setup_database()
