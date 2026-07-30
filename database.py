import sqlite3
from datetime import datetime, timedelta

DB_NAME = "sushi_game.db"

def init_db():
    """Створює базу даних та таблиці, якщо їх ще немає"""
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        
        # Таблиця користувачів
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                phone_number TEXT,
                last_spin DATETIME
            )
        """)
        
        # Таблиця промокодів
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS promocodes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                prize_name TEXT,
                code TEXT UNIQUE,
                is_used BOOLEAN DEFAULT 0,
                expires_at DATETIME
            )
        """)
        conn.commit()

def register_user(user_id: int, username: str, phone: str):
    """Зберігає або оновлює дані користувача"""
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO users (user_id, username, phone_number)
            VALUES (?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET phone_number=excluded.phone_number
        """, (user_id, username, phone))
        conn.commit()

def can_spin(user_id: int) -> bool:
    """Перевіряє, чи пройшло 24 години з останнього спіну"""
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT last_spin FROM users WHERE user_id = ?", (user_id,))
        row = cursor.fetchone()
        
        if not row or not row[0]:
            return True  # Ще не крутив або новий юзер
        
        last_spin_time = datetime.fromisoformat(row[0])
        return datetime.now() >= last_spin_time + timedelta(hours=24)

def update_spin_time(user_id: int):
    """Оновлює час останнього спіну на поточний"""
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET last_spin = ? WHERE user_id = ?", 
                       (datetime.now().isoformat(), user_id))
        conn.commit()

def is_user_registered(user_id: int) -> bool:
    """Перевіряє, чи є користувач у базі та чи залишив він номер телефону"""
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT phone_number FROM users WHERE user_id = ?", (user_id,))
        row = cursor.fetchone()
        return bool(row and row[0])

import string
import random

def generate_promo_code() -> str:
    """Генерує випадковий код вигляду SUSHI-X8K2"""
    chars = string.ascii_uppercase + string.digits
    code_suffix = ''.join(random.choices(chars, k=4))
    return f"SUSHI-{code_suffix}"

def save_promocode(user_id: int, prize_name: str) -> tuple[str, str]:
    """Створює промокод, зберігає його в БД та повертає (code, expires_at_str)"""
    code = generate_promo_code()
    expires_at = datetime.now() + timedelta(hours=24)  # ⏰ Змінено на 24 години
    expires_str = expires_at.strftime("%d.%m.%Y о %H:%M")
    
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO promocodes (user_id, prize_name, code, expires_at)
            VALUES (?, ?, ?, ?)
        """, (user_id, prize_name, code, expires_at.isoformat()))
        conn.commit()
        
    return code, expires_str