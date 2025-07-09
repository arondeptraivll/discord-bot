# app/database.py
import psycopg2
from psycopg2.extras import DictCursor
import os
import uuid
import hashlib
from typing import Optional

DATABASE_URL = os.getenv('DATABASE_URL')
if not DATABASE_URL:
    raise Exception("❌ Cấu hình thiếu: Biến môi trường DATABASE_URL chưa được thiết lập.")

def get_db_connection():
    try:
        conn = psycopg2.connect(DATABASE_URL, cursor_factory=DictCursor)
        return conn
    except psycopg2.OperationalError as e:
        print(f"❌ Không thể kết nối đến PostgreSQL Database: {e}")
        raise

def setup_database():
    conn = get_db_connection()
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute('''
                CREATE TABLE IF NOT EXISTS trackers (
                    id TEXT PRIMARY KEY,
                    creator_id BIGINT NOT NULL,
                    target_url TEXT NOT NULL,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT (NOW() AT TIME ZONE 'utc')
                )
                ''')
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
    except psycopg2.Error as e:
        print(f"❌ LỖI DATABASE trong hàm setup_database: {e}")
    finally:
        conn.close()

def add_tracker(creator_id: int, target_url: str) -> str:
    new_id = uuid.uuid4().hex[:10]
    conn = get_db_connection()
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO trackers (id, creator_id, target_url) VALUES (%s, %s, %s)",
                    (new_id, creator_id, target_url)
                )
    except psycopg2.Error as e:
        print(f"❌ LỖI DATABASE trong hàm add_tracker: {e}")
        raise e # Ném lại lỗi để cog có thể xử lý
    finally:
        conn.close()
    return new_id

def get_tracker_by_id(tracker_id: str) -> Optional[dict]:
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM trackers WHERE id = %s", (tracker_id,))
            row = cur.fetchone()
            return dict(row) if row else None
    except psycopg2.Error as e:
        print(f"❌ LỖI DATABASE trong hàm get_tracker_by_id: {e}")
        return None
    finally:
        conn.close()

def get_tracker_by_creator(creator_id: int) -> Optional[dict]:
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM trackers WHERE creator_id = %s", (creator_id,))
            row = cur.fetchone()
            return dict(row) if row else None
    except psycopg2.Error as e:
        print(f"❌ LỖI DATABASE trong hàm get_tracker_by_creator: {e}")
        return None
    finally:
        conn.close()

def remove_tracker(creator_id: int) -> bool:
    """Xóa tracker của một người dùng và trả về True nếu thành công."""
    conn = get_db_connection()
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM trackers WHERE creator_id = %s", (creator_id,))
                # cur.rowcount sẽ > 0 nếu có hàng nào bị xóa
                return cur.rowcount > 0
    except psycopg2.Error as e: # Bắt lỗi cụ thể của database
        print(f"❌ LỖI DATABASE trong hàm remove_tracker: {e}")
        return False # Trả về False khi có lỗi để cog biết đã thất bại
    finally:
        conn.close()

def add_log(tracker_id: str, ip_address: str, fingerprint_data: dict):
    """Lưu lại log truy cập."""
    conn = get_db_connection()
    try:
        fp_hash_part = fingerprint_data.get('visitorId', 'unknown')
        visitor_hash = hashlib.md5(f"{ip}-{fp_hash_part}".encode()).hexdigest()[:12]
        
        fingerprint_str = "\n".join([f"{k}: {v}" for k, v in fingerprint_data.items()])
        if not fingerprint_str:
            fingerprint_str = "Bị chặn hoặc không thể lấy."

        with conn:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO logs (tracker_id, visitor_id, ip_address, fingerprint) VALUES (%s, %s, %s, %s)",
                    (tracker_id, visitor_hash, ip_address, fingerprint_str)
                )
    except psycopg2.Error as e: # Bắt lỗi cụ thể của database
        print(f"❌ LỖI DATABASE trong hàm add_log: {e}")
    finally:
        conn.close()


# Khởi tạo DB khi module được import
setup_database()
