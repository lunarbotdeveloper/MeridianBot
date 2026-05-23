cat > meridian_final.py << 'EOF'
#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════╗
║         🌉 МЕРИДИАН — ПОЛНАЯ АДМИНСКАЯ ВЕРСИЯ               ║
║     Админ-панель | Ротация API | Отдельная БД | Статистика  ║
╚══════════════════════════════════════════════════════════════╝
"""

import asyncio
import json
import os
import random
import re
import sqlite3
import traceback
import platform
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Dict, Any, List
from contextlib import asynccontextmanager

from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import (
    InlineKeyboardMarkup, InlineKeyboardButton,
    ReplyKeyboardMarkup, KeyboardButton,
    BufferedInputFile, BotCommand,
    CallbackQuery, Message
)
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.storage.memory import MemoryStorage

import httpx
from PIL import Image, ImageDraw, ImageFont

# ══════════════════════════════════════════════════════════════
# 🔧 КОНФИГУРАЦИЯ
# ══════════════════════════════════════════════════════════════

# API ключи Gemini (можно добавлять сколько угодно)
GEMINI_KEYS = [
    "AIzaSyBc-lzSR0htkZJ7DZDWELxYzPyKq8wKRvw",
    # Добавляйте новые ключи сюда:
    # "AIzaSyВторойКлюч",
    # "AIzaSyТретийКлюч",
]

# API ключи погоды (можно добавлять сколько угодно)
WEATHER_KEYS = [
    "c9533271e2a27b86f0abc303b206c6a6",
    # "второй_ключ_погоды",
]

# Токен бота
BOT_TOKEN = "8853395386:AAHtdZNkZ1PLMIAnlXq2_Jmd43v7xjn0as8"

# ID администраторов (можно добавлять много)
ADMIN_IDS = [8659997773]

# ══════════════════════════════════════════════════════════════
# 🗄️ БАЗА ДАННЫХ (SQLite)
# ══════════════════════════════════════════════════════════════

DATABASE_FILE = "meridian.db"

class Database:
    def __init__(self, db_file: str = DATABASE_FILE):
        self.db_file = db_file
        self._init_db()

    def _init_db(self):
        """Инициализация всех таблиц"""
        with sqlite3.connect(self.db_file) as conn:
            cursor = conn.cursor()
            
            # Таблица пользователей
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY,
                    name TEXT,
                    username TEXT,
                    partner_id INTEGER,
                    pair_code TEXT,
                    pair_code_created_at TEXT,
                    quests_done INTEGER DEFAULT 0,
                    xp INTEGER DEFAULT 0,
                    lp INTEGER DEFAULT 0,
                    perfect_photos INTEGER DEFAULT 0,
                    surprises_sent INTEGER DEFAULT 0,
                    secret_done INTEGER DEFAULT 0,
                    city TEXT,
                    weather TEXT,
                    temp TEXT,
                    last_location_at TEXT,
                    joined_at TEXT,
                    last_active TEXT
                )
            """)
            
            # Таблица квестов
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS quests (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    quest_id INTEGER,
                    user1_id INTEGER,
                    user2_id INTEGER,
                    theme TEXT,
                    legend TEXT,
                    task1 TEXT,
                    task2 TEXT,
                    album_title TEXT,
                    city1 TEXT,
                    city2 TEXT,
                    weather1 TEXT,
                    weather2 TEXT,
                    photo1 TEXT,
                    photo2 TEXT,
                    ai_review1 TEXT,
                    ai_review2 TEXT,
                    score1 INTEGER,
                    score2 INTEGER,
                    creativity1 INTEGER,
                    creativity2 INTEGER,
                    date TEXT,
                    done INTEGER DEFAULT 0,
                    completing INTEGER DEFAULT 0,
                    collage TEXT
                )
            """)
            
            # Таблица альбома
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS album (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    quest_id INTEGER,
                    user1_id INTEGER,
                    user2_id INTEGER,
                    theme TEXT,
                    album_title TEXT,
                    collage TEXT,
                    date TEXT,
                    avg_score REAL
                )
            """)
            
            # Таблица достижений пользователей
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS user_achievements (
                    user_id INTEGER,
                    achievement_id TEXT,
                    unlocked_at TEXT,
                    PRIMARY KEY (user_id, achievement_id)
                )
            """)
            
            # Таблица стриков
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS streaks (
                    user_id INTEGER PRIMARY KEY,
                    current INTEGER DEFAULT 0,
                    best INTEGER DEFAULT 0,
                    last_date TEXT
                )
            """)
            
            # Таблица API ключей (для админ-панели)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS api_keys (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    service TEXT,
                    key TEXT,
                    is_active INTEGER DEFAULT 1,
                    usage_count INTEGER DEFAULT 0,
                    last_used TEXT,
                    added_at TEXT
                )
            """)
            
            # Таблица использования API
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS api_usage (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    service TEXT,
                    key TEXT,
                    success INTEGER,
                    response_time REAL,
                    error TEXT,
                    timestamp TEXT
                )
            """)
            
            # Таблица логов админов
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS admin_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    admin_id INTEGER,
                    action TEXT,
                    target_id INTEGER,
                    details TEXT,
                    timestamp TEXT
                )
            """)
            
            # Таблица статистики бота
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS bot_stats (
                    key TEXT PRIMARY KEY,
                    value TEXT,
                    updated_at TEXT
                )
            """)
            
            # Таблица рассылок
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS broadcasts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    admin_id INTEGER,
                    message TEXT,
                    recipients INTEGER,
                    sent_at TEXT
                )
            """)
            
            # Таблица жалоб
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS reports (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    reporter_id INTEGER,
                    reported_id INTEGER,
                    reason TEXT,
                    status TEXT DEFAULT 'pending',
                    created_at TEXT
                )
            """)
            
            # Заполняем API ключи
            for key in GEMINI_KEYS:
                if key:
                    cursor.execute("""
                        INSERT OR IGNORE INTO api_keys (service, key, added_at)
                        VALUES (?, ?, ?)
                    """, ("gemini", key, datetime.now().isoformat()))
            
            for key in WEATHER_KEYS:
                if key:
                    cursor.execute("""
                        INSERT OR IGNORE INTO api_keys (service, key, added_at)
                        VALUES (?, ?, ?)
                    """, ("weather", key, datetime.now().isoformat()))
            
            # Инициализируем статистику
            stats = {
                "total_users": "0",
                "total_quests": "0",
                "total_photos": "0",
                "total_collages": "0",
                "total_xp": "0",
                "bot_started_at": datetime.now().isoformat(),
                "api_requests_today": "0",
                "api_failures_today": "0",
                "last_daily_reset": datetime.now().isoformat()
            }
            for key, value in stats.items():
                cursor.execute("""
                    INSERT OR IGNORE INTO bot_stats (key, value, updated_at)
                    VALUES (?, ?, ?)
                """, (key, value, datetime.now().isoformat()))
            
            conn.commit()
    
    async def execute(self, query: str, params: tuple = ()):
        """Выполнить запрос"""
        with sqlite3.connect(self.db_file) as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            conn.commit()
            return cursor.lastrowid
    
    async def fetch_all(self, query: str, params: tuple = ()) -> List[dict]:
        """Получить все строки"""
        with sqlite3.connect(self.db_file) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]
    
    async def fetch_one(self, query: str, params: tuple = ()) -> Optional[dict]:
        """Получить одну строку"""
        with sqlite3.connect(self.db_file) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(query, params)
            row = cursor.fetchone()
            return dict(row) if row else None

db = Database()

# ══════════════════════════════════════════════════════════════
# 🔄 API РОТАЦИЯ
# ══════════════════════════════════════════════════════════════

class APIRotator:
    def __init__(self, service: str):
        self.service = service
        self.failed_keys = {}
    
    async def get_active_key(self) -> Optional[str]:
        """Получить активный ключ"""
        keys = await db.fetch_all(
            "SELECT key, usage_count FROM api_keys WHERE service = ? AND is_active = 1",
            (self.service,)
        )
        if not keys:
            return None
        
        # Сортируем по использованию
        keys.sort(key=lambda x: x['usage_count'])
        
        for key_data in keys:
            key = key_data['key']
            if key in self.failed_keys:
                failed_time = self.failed_keys[key]
                if datetime.now() - failed_time < timedelta(minutes=5):
                    continue
                else:
                    del self.failed_keys[key]
            return key
        return keys[0]['key'] if keys else None
    
    async def report_success(self, key: str):
        """Сообщить об успехе"""
        await db.execute(
            "UPDATE api_keys SET usage_count = usage_count + 1, last_used = ? WHERE key = ?",
            (datetime.now().isoformat(), key)
        )
        await db.execute(
            "INSERT INTO api_usage (service, key, success, response_time, timestamp) VALUES (?, ?, ?, ?, ?)",
            (self.service, key, 1, 0, datetime.now().isoformat())
        )
    
    async def report_failure(self, key: str, error: str = None):
        """Сообщить об ошибке"""
        self.failed_keys[key] = datetime.now()
        await db.execute(
            "UPDATE api_keys SET is_active = 0 WHERE key = ?",
            (key,)
        )
        await db.execute(
            "INSERT INTO api_usage (service, key, success, error, timestamp) VALUES (?, ?, ?, ?, ?)",
            (self.service, key, 0, error, datetime.now().isoformat())
        )
        
        # Уведомляем админов
        for admin_id in ADMIN_IDS:
            try:
                await bot.send_message(admin_id, f"⚠️ API ключ {self.service} отключён: {key[:20]}... - {error}")
            except:
                pass
    
    async def add_key(self, key: str):
        """Добавить новый ключ"""
        await db.execute(
            "INSERT INTO api_keys (service, key, is_active, added_at) VALUES (?, ?, 1, ?)",
            (self.service, key, datetime.now().isoformat())
        )
    
    async def remove_key(self, key: str):
        """Удалить ключ"""
        await db.execute("DELETE FROM api_keys WHERE service = ? AND key = ?", (self.service, key))

gemini_rotator = APIRotator("gemini")
weather_rotator = APIRotator("weather")

# ══════════════════════════════════════════════════════════════
# 🧠 ИНИЦИАЛИЗАЦИЯ GEMINI
# ══════════════════════════════════════════════════════════════

try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    print("Warning: google-generativeai not installed")

async def get_gemini_model():
    """Получить модель Gemini с активным ключом"""
    if not GEMINI_AVAILABLE:
        return None
    
    key = await gemini_rotator.get_active_key()
    if key:
        try:
            genai.configure(api_key=key)
            return genai.GenerativeModel("gemini-1.5-flash", generation_config={
                "temperature": 0.95,
                "max_output_tokens": 600
            })
        except Exception as e:
            await gemini_rotator.report_failure(key, str(e))
    return None

async def ai_call(prompt, is_image: bool = False, image_path: str = None):
    """Универсальный вызов AI"""
    model = await get_gemini_model()
    if not model:
        return None
    
    try:
        if is_image and image_path:
            with open(image_path, "rb") as f:
                img_data = f.read()
            img_part = {"mime_type": "image/jpeg", "data": img_data}
            response = await asyncio.to_thread(model.generate_content, [prompt, img_part])
        else:
            response = await asyncio.to_thread(model.generate_content, prompt)
        
        key = await gemini_rotator.get_active_key()
        await gemini_rotator.report_success(key)
        return response.text.strip()
    except Exception as e:
        key = await gemini_rotator.get_active_key()
        if key:
            await gemini_rotator.report_failure(key, str(e))
        return None

# ══════════════════════════════════════════════════════════════
# 🎨 ЭМОДЗИ
# ══════════════════════════════════════════════════════════════

class E:
    sparkles = "✨"
    bridge = "🌉"
    heart = "💞"
    camera = "📸"
    map_emoji = "📍"
    clock = "⏰"
    trophy = "🏆"
    star = "⭐"
    fire = "🔥"
    gift = "🎁"
    album = "📚"
    stats = "📊"
    brain = "🧠"
    world = "🌍"
    rainbow = "🌈"
    palette = "🎨"
    gem = "💎"
    crown = "👑"
    target = "🎯"
    mail = "📨"
    lock = "🔒"
    key = "🔑"
    users = "👥"
    smile = "😊"
    love = "🥰"
    party = "🎉"
    moon = "🌙"
    sun = "☀️"
    cloud = "☁️"
    rain = "🌧️"
    snow = "❄️"
    zap = "⚡"
    magic = "🔮"
    robot = "🤖"
    eyes = "👀"
    check = "✅"
    cross = "❌"
    warning = "⚠️"
    back_emoji = "◀️"
    letter = "💌"
    ghost = "👻"
    clap = "👏"
    flower = "🌸"
    butterfly = "🦋"
    diamond = "💠"
    medal = "🏅"
    rocket = "🚀"
    music = "🎵"
    hand = "👋"
    info = "ℹ️"
    question = "❓"
    gear = "⚙️"
    book = "📖"
    pen = "🖊️"
    speech = "💬"
    thought = "💭"
    compass = "🧭"
    hourglass = "⏳"
    shield = "🛡️"
    wrench = "🔧"
    photo = "🖼️"
    hq = "📷"
    analysis = "🔍"
    admin = "👑"
    database = "🗄️"
    api = "🔌"
    chart = "📈"
    user = "👤"
    broadcast = "📢"
    report = "📋"
    ban = "🚫"
    art = "🎨"

# ══════════════════════════════════════════════════════════════
# 🔤 ШРИФТЫ
# ══════════════════════════════════════════════════════════════

def get_fonts():
    system = platform.system()
    fonts = {"bold": None, "regular": None, "small": None}
    
    if system == "Linux":
        candidates = [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
        ]
    elif system == "Darwin":
        candidates = [
            "/System/Library/Fonts/Helvetica.ttc",
            "/System/Library/Fonts/SFNSText.ttf"
        ]
    elif system == "Windows":
        candidates = [
            "C:\\Windows\\Fonts\\arial.ttf",
            "C:\\Windows\\Fonts\\arialbd.ttf"
        ]
    else:
        candidates = []
    
    for path in candidates:
        if Path(path).exists():
            try:
                fonts["bold"] = ImageFont.truetype(path, 24)
                fonts["regular"] = ImageFont.truetype(path, 16)
                fonts["small"] = ImageFont.truetype(path, 13)
                return fonts
            except:
                pass
    
    fonts["bold"] = ImageFont.load_default()
    fonts["regular"] = ImageFont.load_default()
    fonts["small"] = ImageFont.load_default()
    return fonts

FONTS = get_fonts()

# ══════════════════════════════════════════════════════════════
# 📁 ПАПКИ
# ══════════════════════════════════════════════════════════════

MEDIA = Path("media")
for sub in ["album", "collages", "temp", "backups"]:
    (MEDIA / sub).mkdir(parents=True, exist_ok=True)

# ══════════════════════════════════════════════════════════════
# 🤖 БОТ
# ══════════════════════════════════════════════════════════════

bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
dp = Dispatcher(storage=MemoryStorage())

# ══════════════════════════════════════════════════════════════
# ⌨️ КЛАВИАТУРЫ
# ══════════════════════════════════════════════════════════════

class K:
    @staticmethod
    def main_menu(paired: bool = False, is_admin: bool = False) -> InlineKeyboardMarkup:
        buttons = []
        if paired:
            buttons = [
                [InlineKeyboardButton(text=f"{E.target} Квест", callback_data="quest"),
                 InlineKeyboardButton(text=f"{E.album} Альбом", callback_data="album")],
                [InlineKeyboardButton(text=f"{E.stats} Статистика", callback_data="stats"),
                 InlineKeyboardButton(text=f"{E.trophy} Достижения", callback_data="ach")],
                [InlineKeyboardButton(text=f"{E.gift} Сюрприз", callback_data="surprise"),
                 InlineKeyboardButton(text=f"{E.letter} Открытка", callback_data="postcard")],
                [InlineKeyboardButton(text=f"{E.magic} Дневник", callback_data="diary"),
                 InlineKeyboardButton(text=f"{E.ghost} Секретный квест", callback_data="secret")],
                [InlineKeyboardButton(text=f"{E.analysis} Анализ фото", callback_data="analyze_photo"),
                 InlineKeyboardButton(text=f"{E.heart} Комплимент", callback_data="compliment")],
                [InlineKeyboardButton(text=f"{E.info} Помощь", callback_data="help")]
            ]
        else:
            buttons = [
                [InlineKeyboardButton(text=f"{E.key} 🔐 Ввести код", callback_data="pair_enter")],
                [InlineKeyboardButton(text=f"{E.users} ✨ Создать пару", callback_data="pair_create")],
                [InlineKeyboardButton(text=f"{E.info} ℹ️ Как играть?", callback_data="help")]
            ]
        
        if is_admin:
            buttons.append([InlineKeyboardButton(text=f"{E.admin} 👑 Админ-панель", callback_data="admin_panel")])
        
        return InlineKeyboardMarkup(inline_keyboard=buttons)
    
    @staticmethod
    def back(cb: str = "main_menu") -> InlineKeyboardMarkup:
        return InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=f"{E.back_emoji} Назад", callback_data=cb)]
        ])
    
    @staticmethod
    def location_kb() -> ReplyKeyboardMarkup:
        return ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text=f"{E.map_emoji} 📍 Отправить геолокацию", request_location=True)]],
            resize_keyboard=True,
            one_time_keyboard=True
        )
    
    @staticmethod
    def admin_menu() -> InlineKeyboardMarkup:
        return InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=f"{E.chart} 📊 Статистика бота", callback_data="admin_stats")],
            [InlineKeyboardButton(text=f"{E.users} 👥 Пользователи", callback_data="admin_users")],
            [InlineKeyboardButton(text=f"{E.api} 🔌 API ключи", callback_data="admin_api")],
            [InlineKeyboardButton(text=f"{E.database} 💾 Резервное копирование", callback_data="admin_backup")],
            [InlineKeyboardButton(text=f"{E.broadcast} 📢 Рассылка", callback_data="admin_broadcast")],
            [InlineKeyboardButton(text=f"{E.gear} ⚙️ Настройки", callback_data="admin_settings")],
            [InlineKeyboardButton(text=f"{E.back_emoji} Назад", callback_data="main_menu")]
        ])

# ══════════════════════════════════════════════════════════════
# 🤖 FSM
# ══════════════════════════════════════════════════════════════

class States(StatesGroup):
    pair_code = State()
    waiting_photo_analysis = State()
    admin_add_api = State()
    admin_add_api_service = State()
    admin_broadcast = State()
    admin_broadcast_confirm = State()

# ══════════════════════════════════════════════════════════════
# 👤 ПОЛЬЗОВАТЕЛЬСКИЕ ФУНКЦИИ
# ══════════════════════════════════════════════════════════════

async def get_or_create_user(user_id: int, name: str, username: str = None) -> dict:
    """Получить или создать пользователя"""
    user = await db.fetch_one("SELECT * FROM users WHERE id = ?", (user_id,))
    if not user:
        await db.execute("""
            INSERT INTO users (id, name, username, joined_at, last_active)
            VALUES (?, ?, ?, ?, ?)
        """, (user_id, name, username, datetime.now().isoformat(), datetime.now().isoformat()))
        
        # Обновляем статистику
        total = await db.fetch_one("SELECT value FROM bot_stats WHERE key = 'total_users'")
        if total:
            await db.execute("UPDATE bot_stats SET value = ?, updated_at = ? WHERE key = 'total_users'",
                            (str(int(total['value']) + 1), datetime.now().isoformat()))
        
        user = await db.fetch_one("SELECT * FROM users WHERE id = ?", (user_id,))
    else:
        await db.execute("UPDATE users SET last_active = ? WHERE id = ?", (datetime.now().isoformat(), user_id))
    return user

async def get_partner(user_id: int) -> Optional[dict]:
    """Получить партнёра пользователя"""
    user = await db.fetch_one("SELECT partner_id FROM users WHERE id = ?", (user_id,))
    if user and user.get('partner_id'):
        return await db.fetch_one("SELECT * FROM users WHERE id = ?", (user['partner_id'],))
    return None

async def update_streak(user_id: int) -> int:
    """Обновить стрик пользователя"""
    today = datetime.now().strftime("%Y-%m-%d")
    streak = await db.fetch_one("SELECT * FROM streaks WHERE user_id = ?", (user_id,))
    
    if not streak:
        await db.execute("INSERT INTO streaks (user_id, current, best, last_date) VALUES (?, 1, 1, ?)",
                        (user_id, today))
        return 1
    
    last_date = streak.get('last_date')
    current = streak.get('current', 0)
    best = streak.get('best', 0)
    
    if last_date == today:
        return current
    elif last_date == (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d"):
        current += 1
        best = max(best, current)
        await db.execute("UPDATE streaks SET current = ?, best = ?, last_date = ? WHERE user_id = ?",
                        (current, best, today, user_id))
        return current
    else:
        await db.execute("UPDATE streaks SET current = 1, last_date = ? WHERE user_id = ?",
                        (today, user_id))
        return 1

def get_rank(xp: int) -> tuple:
    """Получить ранг по XP"""
    ranks = [
        ("Новичок", 0, "🌱"),
        ("Исследователь", 50, "🔍"),
        ("Строитель", 150, "🏗️"),
        ("Архитектор", 400, "🏛️"),
        ("Мастер мостов", 1000, "👑"),
        ("Легенда", 2500, "🌟"),
        ("Полубог", 5000, "💫"),
        ("Хранитель Меридиана", 10000, "🔮"),
    ]
    for i in range(len(ranks)-1, -1, -1):
        if xp >= ranks[i][1]:
            return ranks[i]
    return ranks[0]

def get_rank_progress(xp: int):
    """Получить прогресс до следующего ранга"""
    rank = get_rank(xp)
    ranks = [
        ("Новичок", 0, "🌱"),
        ("Исследователь", 50, "🔍"),
        ("Строитель", 150, "🏗️"),
        ("Архитектор", 400, "🏛️"),
        ("Мастер мостов", 1000, "👑"),
        ("Легенда", 2500, "🌟"),
        ("Полубог", 5000, "💫"),
        ("Хранитель Меридиана", 10000, "🔮"),
    ]
    idx = ranks.index(rank)
    next_idx = min(idx + 1, len(ranks) - 1)
    if next_idx == idx:
        return rank, 1.0, 0
    current_xp = ranks[idx][1]
    next_xp = ranks[next_idx][1]
    progress = min((xp - current_xp) / max(next_xp - current_xp, 1), 1.0)
    return rank, progress, next_xp - xp

# ══════════════════════════════════════════════════════════════
# 🏆 ДОСТИЖЕНИЯ
# ══════════════════════════════════════════════════════════════

ACHIEVEMENTS = {
    "first": {"name": "Первый мост", "desc": "Выполнить первый квест", "emoji": "🌉", "xp": 10},
    "five": {"name": "Строитель", "desc": "5 квестов", "emoji": "🏗️", "xp": 30},
    "ten": {"name": "Архитектор", "desc": "10 квестов", "emoji": "🏛️", "xp": 60},
    "twentyfive": {"name": "Градостроитель", "desc": "25 квестов", "emoji": "🏙️", "xp": 150},
    "fifty": {"name": "Инженер", "desc": "50 квестов", "emoji": "👷", "xp": 300},
    "night": {"name": "Ночная сова", "desc": "Квест после 23:00", "emoji": "🦉", "xp": 25},
    "rain": {"name": "Дождевик", "desc": "Квест в дождь", "emoji": "🌧️", "xp": 20},
    "snow": {"name": "Снежный ангел", "desc": "Квест в снег", "emoji": "❄️", "xp": 25},
    "streak3": {"name": "3 дня подряд", "desc": "Стрик 3 дня", "emoji": "🔥", "xp": 25},
    "streak7": {"name": "Недельный марафон", "desc": "Стрик 7 дней", "emoji": "🌟", "xp": 75},
    "streak30": {"name": "Месяц вместе", "desc": "Стрик 30 дней", "emoji": "👑", "xp": 500},
    "perfect": {"name": "Идеальное фото", "desc": "Оба фото 10/10", "emoji": "💎", "xp": 50},
    "creative": {"name": "Творческий гений", "desc": "Креативность 10/10", "emoji": "🎨", "xp": 40},
    "surprise5": {"name": "Сюрпризёр", "desc": "5 сюрпризов", "emoji": "🎁", "xp": 30},
    "secret": {"name": "Кладоискатель", "desc": "Найти секретный квест", "emoji": "🗝️", "xp": 100},
    "photo_king": {"name": "Король фото", "desc": "10 раз получить 10/10", "emoji": "👑📸", "xp": 200},
}

async def check_achievements(user_id: int, quest_data: dict = None) -> List[str]:
    """Проверить и выдать достижения"""
    user = await db.fetch_one("SELECT * FROM users WHERE id = ?", (user_id,))
    if not user:
        return []
    
    qd = user.get('quests_done', 0)
    perfect = user.get('perfect_photos', 0)
    surprises = user.get('surprises_sent', 0)
    secret = user.get('secret_done', 0)
    
    streak_data = await db.fetch_one("SELECT current FROM streaks WHERE user_id = ?", (user_id,))
    streak = streak_data.get('current', 0) if streak_data else 0
    
    achievements = await db.fetch_all("SELECT achievement_id FROM user_achievements WHERE user_id = ?", (user_id,))
    unlocked = {a['achievement_id'] for a in achievements}
    
    checks = {
        "first": qd >= 1,
        "five": qd >= 5,
        "ten": qd >= 10,
        "twentyfive": qd >= 25,
        "fifty": qd >= 50,
        "streak3": streak >= 3,
        "streak7": streak >= 7,
        "streak30": streak >= 30,
        "surprise5": surprises >= 5,
        "secret": secret >= 1,
        "photo_king": perfect >= 10,
    }
    
    if quest_data:
        hour = datetime.fromisoformat(quest_data.get('date', datetime.now().isoformat())).hour
        checks["night"] = hour >= 23
        checks["rain"] = "дождь" in quest_data.get('weather1', '') + quest_data.get('weather2', '')
        checks["snow"] = "снег" in quest_data.get('weather1', '') + quest_data.get('weather2', '')
        checks["perfect"] = quest_data.get('score1', 0) == 10 and quest_data.get('score2', 0) == 10
    
    new_achievements = []
    for aid, cond in checks.items():
        if cond and aid not in unlocked:
            new_achievements.append(aid)
            await db.execute("""
                INSERT INTO user_achievements (user_id, achievement_id, unlocked_at)
                VALUES (?, ?, ?)
            """, (user_id, aid, datetime.now().isoformat()))
            xp_reward = ACHIEVEMENTS[aid]["xp"]
            await db.execute("UPDATE users SET xp = xp + ? WHERE id = ?", (xp_reward, user_id))
            
            # Обновляем общую статистику XP
            total_xp = await db.fetch_one("SELECT value FROM bot_stats WHERE key = 'total_xp'")
            if total_xp:
                await db.execute("UPDATE bot_stats SET value = ?, updated_at = ? WHERE key = 'total_xp'",
                                (str(int(total_xp['value']) + xp_reward), datetime.now().isoformat()))
    
    return new_achievements

# ══════════════════════════════════════════════════════════════
# 🧠 AI ФУНКЦИИ
# ══════════════════════════════════════════════════════════════

async def ai_quest(ctx: dict) -> dict:
    """Создать квест через AI"""
    recent = ctx.get('recent', '')
    if not recent or recent.strip() == '':
        recent = 'ещё не было квестов'
    
    prompt = f"""
Придумай парное фото-задание для влюблённой пары на расстоянии.
💙 {ctx.get('u1')} в {ctx.get('c1')}: {ctx.get('w1temp')}°C, {ctx.get('w1desc')}
💜 {ctx.get('u2')} в {ctx.get('c2')}: {ctx.get('w2temp')}°C, {ctx.get('w2desc')}
🕐 {ctx.get('tod')}, {ctx.get('season')}
📋 Не повторять темы: {recent}

ОТВЕТЬ ТОЛЬКО JSON без markdown:
{{"theme":"название","legend":"легенда 1-2 предложения","task1":"задание для первого","task2":"задание для второго","album_title":"название для альбома","mood":"настроение","difficulty":1-5,"hint":"подсказка"}}"""
    
    response = await ai_call(prompt)
    if response:
        try:
            text = re.sub(r'^```(?:json)?\s*\n?', '', response)
            text = re.sub(r'\n?```\s*$', '', text)
            return json.loads(text)
        except:
            pass
    
    # Fallback
    return {
        "theme": "Мост между городами",
        "legend": "То, что вы видите сейчас — часть общей картины",
        "task1": "Сфоткай что-то красивое прямо сейчас",
        "task2": "Сфоткай что-то необычное вокруг себя",
        "album_title": "Мост",
        "mood": "романтичное",
        "difficulty": 2,
        "hint": "Просто оглянись!"
    }

async def ai_review_photo(path: str, task: str, name: str) -> dict:
    """Оценить фото через AI"""
    prompt = f"""Посмотри на фото от {name}. Задание было: «{task}».
Оцени по-дружески, с теплотой. ОТВЕТЬ ТОЛЬКО JSON:
{{"match_score":1-10,"creativity":1-10,"what_i_see":"что видишь","comment":"тёплый комментарий на русском","mood":"настроение"}}"""
    
    response = await ai_call(prompt, is_image=True, image_path=path)
    if response:
        try:
            text = re.sub(r'^```(?:json)?\s*\n?', '', response)
            text = re.sub(r'\n?```\s*$', '', text)
            return json.loads(text)
        except:
            pass
    
    return {
        "match_score": 7,
        "creativity": 7,
        "what_i_see": "что-то интересное",
        "comment": f"{name}, отличная работа! Продолжай в том же духе!",
        "mood": "загадочное"
    }

async def ai_analyze_photo_deep(path: str, task: str, name: str) -> dict:
    """Глубокий анализ фото"""
    prompt = f"""Проанализируй это фото от {name}. Задание: «{task}».
Ответь ТОЛЬКО JSON:
{{
    "score": 1-10,
    "creativity": 1-10,
    "composition": "оценка композиции",
    "light": "оценка освещения",
    "emotion": "какие эмоции вызывает",
    "what_i_see": "что именно видно на фото",
    "recommendation": "конкретный совет как улучшить",
    "comment": "тёплый комментарий",
    "fun_fact": "интересный факт о фотографии"
}}"""
    
    response = await ai_call(prompt, is_image=True, image_path=path)
    if response:
        try:
            text = re.sub(r'^```(?:json)?\s*\n?', '', response)
            text = re.sub(r'\n?```\s*$', '', text)
            return json.loads(text)
        except:
            pass
    
    return {
        "score": 7,
        "creativity": 7,
        "composition": "хорошая",
        "light": "естественное",
        "emotion": "тёплая",
        "what_i_see": "интересный кадр",
        "recommendation": "Попробуй экспериментировать с ракурсами",
        "comment": f"{name}, отличная работа!",
        "fun_fact": "Лучшие фото получаются спонтанно"
    }

async def ai_compliment(name: str, partner_name: str) -> str:
    """Сгенерировать комплимент"""
    prompt = f"Напиши короткий, милый комплимент для {name} от {partner_name}. 1 предложение, с душой, про отношения на расстоянии."
    response = await ai_call(prompt)
    if response:
        return response
    return f"Твоя улыбка согревает меня даже на расстоянии, {name}! {E.heart}"

async def ai_postcard(to_name: str, from_name: str, mood: str = "романтичное") -> str:
    """Сгенерировать открытку"""
    prompt = f"Напиши {mood} послание от {from_name} для {to_name}. Пара на расстоянии. 2-3 предложения, душевно, без подписи."
    response = await ai_call(prompt)
    if response:
        return response
    return f"{to_name}, каждое мгновение без тебя — это шаг навстречу. Ты в моём сердце. {E.heart}"

async def ai_diary(data: dict, uid: int) -> str:
    """Сгенерировать дневник"""
    user = await db.fetch_one("SELECT * FROM users WHERE id = ?", (uid,))
    partner = await get_partner(uid)
    if not partner:
        return "Нужна пара для дневника."
    
    recent_quests = await db.fetch_all("SELECT theme FROM quests WHERE done = 1 ORDER BY id DESC LIMIT 5")
    recent = [q.get('theme', '') for q in recent_quests]
    if not recent:
        recent = ["первый мост"]
    
    prompt = f"Напиши страницу дневника отношений {user.get('name')} и {partner.get('name')}. Последние темы: {', '.join(recent)}. 3-5 предложений, душевно, с метафорой про мосты."
    response = await ai_call(prompt)
    if response:
        return response
    return f"Каждый день вы строите новый мост. Невидимые нити становятся крепче. Ваша история — особенная. {E.heart}"

# ══════════════════════════════════════════════════════════════
# 🌤️ ПОГОДА
# ══════════════════════════════════════════════════════════════

async def get_weather(lat: float, lon: float) -> dict:
    """Получить погоду с ротацией ключей"""
    key = await weather_rotator.get_active_key()
    if not key:
        return {"temp": "?", "desc": "неизвестно", "icon": "01d", "wind": "?", "humidity": "?"}
    
    try:
        url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={key}&units=metric&lang=ru"
        async with httpx.AsyncClient(timeout=10) as c:
            r = await c.get(url)
            if r.status_code == 200:
                j = r.json()
                await weather_rotator.report_success(key)
                return {
                    "temp": round(j["main"]["temp"]),
                    "desc": j["weather"][0]["description"],
                    "icon": j["weather"][0]["icon"],
                    "wind": round(j["wind"]["speed"], 1),
                    "humidity": j["main"]["humidity"]
                }
            else:
                await weather_rotator.report_failure(key, f"HTTP {r.status_code}")
    except Exception as e:
        await weather_rotator.report_failure(key, str(e))
    
    return {"temp": "?", "desc": "неизвестно", "icon": "01d", "wind": "?", "humidity": "?"}

async def geocode(lat: float, lon: float) -> str:
    """Обратное геокодирование"""
    try:
        url = f"https://nominatim.openstreetmap.org/reverse?lat={lat}&lon={lon}&format=json&accept-language=ru"
        async with httpx.AsyncClient(timeout=10) as c:
            r = await c.get(url, headers={"User-Agent": "MeridianBot/1.0"})
            if r.status_code == 200:
                addr = r.json().get("address", {})
                return addr.get("city") or addr.get("town") or addr.get("village") or "Где-то прекрасном"
    except:
        pass
    return "Неизвестный город"

# ══════════════════════════════════════════════════════════════
# 🎨 КОЛЛАЖ
# ══════════════════════════════════════════════════════════════

async def make_collage(img1: str, img2: str, theme: str, c1: str, c2: str, qnum: int) -> str:
    """Создать коллаж из двух фото"""
    try:
        i1 = Image.open(img1).convert("RGB")
        i2 = Image.open(img2).convert("RGB")
        pw, ph = 500, 400
        i1.thumbnail((pw, ph), Image.LANCZOS)
        i2.thumbnail((pw, ph), Image.LANCZOS)
        pad, hh = 25, 130
        tw = pw * 2 + pad * 3
        th = hh + max(i1.height, i2.height) + 80
        bg = Image.new("RGB", (tw, th), (20, 20, 40))
        draw = ImageDraw.Draw(bg)
        x1, y1 = pad, hh + pad
        x2 = x1 + pw + pad
        draw.rectangle([x1-2, y1-2, x1+pw+2, y1+ph+2], fill="white", outline=(255, 215, 0), width=2)
        draw.rectangle([x2-2, y1-2, x2+pw+2, y1+ph+2], fill="white", outline=(255, 215, 0), width=2)
        bg.paste(i1, (x1, y1))
        bg.paste(i2, (x2, y1))
        draw.text((pad, 20), f"Мост #{qnum}: {theme[:45]}", fill=(255, 255, 255), font=FONTS["bold"])
        draw.text((x1+pw//2-30, y1+ph+5), f"📍 {c1[:20]}", fill=(200, 200, 200), font=FONTS["regular"])
        draw.text((x2+pw//2-30, y1+ph+5), f"📍 {c2[:20]}", fill=(200, 200, 200), font=FONTS["regular"])
        path = MEDIA / "collages" / f"bridge_{qnum}.jpg"
        bg.save(path, quality=92)
        return str(path)
    except Exception as e:
        print(f"Collage error: {e}")
        i1 = Image.open(img1).resize((500, 400))
        i2 = Image.open(img2).resize((500, 400))
        combined = Image.new("RGB", (1000, 400))
        combined.paste(i1, (0, 0))
        combined.paste(i2, (500, 0))
        path = MEDIA / "collages" / f"fallback_{qnum}.jpg"
        combined.save(path)
        return str(path)

# ══════════════════════════════════════════════════════════════
# 🤖 ОСНОВНЫЕ ОБРАБОТЧИКИ
# ══════════════════════════════════════════════════════════════

@dp.message(Command("start"))
async def cmd_start(msg: Message):
    """Обработчик команды /start"""
    user = await get_or_create_user(msg.from_user.id, msg.from_user.first_name, msg.from_user.username)
    paired = await get_partner(msg.from_user.id) is not None
    is_admin = msg.from_user.id in ADMIN_IDS
    xp = user.get('xp', 0)
    rank_name, rank_emoji, _ = get_rank(xp)
    streak = await update_streak(msg.from_user.id)
    
    if paired:
        partner = await get_partner(msg.from_user.id)
        text = (
            f"{E.bridge}{E.bridge}{E.bridge} <b>С ВОЗВРАЩЕНИЕМ!</b> {E.bridge}{E.bridge}{E.bridge}\n\n"
            f"{E.heart} <b>{user['name']} 💞 {partner['name']}</b>\n\n"
            f"{rank_emoji} <b>{rank_name}</b>\n"
            f"{E.star} <b>XP:</b> {xp}\n"
            f"{E.fire} <b>Стрик:</b> {streak} дн.\n"
            f"{E.album} <b>Мостов:</b> {await db.fetch_one('SELECT COUNT(*) as cnt FROM quests WHERE done = 1') or 0}\n\n"
            f"{E.target} <i>Выбери действие в меню ↓</i>"
        )
    else:
        text = (
            f"{E.sparkles}{E.sparkles}{E.sparkles} <b>ДОБРО ПОЖАЛОВАТЬ В МЕРИДИАН!</b> {E.sparkles}{E.sparkles}{E.sparkles}\n\n"
            f"{E.hand} Привет, <b>{user['name']}</b>!\n\n"
            f"{E.bridge} <b>Меридиан</b> — нейро-бот для пар на расстоянии.\n\n"
            f"{E.users} <b>ЧТОБЫ НАЧАТЬ:</b>\n"
            f"1. Создайте пару\n"
            f"2. Обменяйтесь кодами\n"
            f"3. Играйте!\n\n"
            f"{E.info} <i>Все функции доступны в меню ↓</i>"
        )
    
    await msg.answer(text, reply_markup=K.main_menu(paired, is_admin))

@dp.callback_query(F.data == "main_menu")
async def main_menu_callback(cb: CallbackQuery):
    """Главное меню"""
    user_id = cb.from_user.id
    paired = await get_partner(user_id) is not None
    is_admin = user_id in ADMIN_IDS
    user = await db.fetch_one("SELECT * FROM users WHERE id = ?", (user_id,))
    xp = user.get('xp', 0)
    rank_name, rank_emoji, _ = get_rank(xp)
    streak = await update_streak(user_id)
    
    if paired:
        partner = await get_partner(user_id)
        text = (
            f"{E.bridge} <b>М Е Р И Д И А Н</b> {E.bridge}\n"
            f"{user['name']} {E.heart} {partner['name']}\n"
            f"{rank_emoji} {rank_name} | {E.star} {xp} XP\n"
            f"{E.fire} Стрик: {streak} дн."
        )
    else:
        text = f"{E.bridge} <b>М Е Р И Д И А Н</b>\n{E.hand} {user['name']}, создай пару!"
    
    await cb.message.edit_text(text, reply_markup=K.main_menu(paired, is_admin))
    await cb.answer()

@dp.callback_query(F.data == "help")
async def help_show(cb: CallbackQuery):
    """Показать справку"""
    text = (
        f"{E.info} <b>КАК ИГРАТЬ В МЕРИДИАН?</b>\n\n"
        f"<b>1.</b> {E.users} <b>Создайте пару</b>\n"
        f"Один нажимает «Создать пару» и получает код.\n"
        f"Второй вводит этот код — и вы вместе!\n\n"
        f"<b>2.</b> {E.target} <b>Начните квест</b>\n"
        f"Нажмите «Квест» и отправьте геолокацию.\n"
        f"Когда оба скинут — AI создаст уникальное задание!\n\n"
        f"<b>3.</b> {E.camera} <b>Сделайте фото</b>\n"
        f"Выполните задание и отправьте фото боту.\n"
        f"AI проверит снимок и поставит оценку!\n\n"
        f"<b>4.</b> {E.album} <b>Смотрите альбом</b>\n"
        f"Из двух фото создаётся коллаж.\n"
        f"Все мосты хранятся в вашем альбоме.\n\n"
        f"<b>5.</b> {E.trophy} <b>Получайте награды</b>\n"
        f"За квесты вы получаете XP и LP.\n"
        f"Открывайте достижения и повышайте ранг!\n\n"
        f"{E.analysis} <b>НОВЫЕ ФУНКЦИИ:</b>\n"
        f"• Глубокий анализ фото с советами\n"
        f"• AI-комплименты для партнёра\n"
        f"• Дневник отношений\n"
        f"• Секретные квесты"
    )
    await cb.message.edit_text(text, reply_markup=K.back())
    await cb.answer()

@dp.callback_query(F.data == "stats")
async def stats_show(cb: CallbackQuery):
    """Показать статистику пользователя"""
    user_id = cb.from_user.id
    user = await db.fetch_one("SELECT * FROM users WHERE id = ?", (user_id,))
    partner = await get_partner(user_id)
    
    if not partner:
        await cb.answer("Нужна пара!", show_alert=True)
        return
    
    xp = user.get('xp', 0)
    rank_name, rank_emoji, _ = get_rank(xp)
    _, progress, left = get_rank_progress(xp)
    streak = await update_streak(user_id)
    
    total_quests = await db.fetch_one("SELECT COUNT(*) as cnt FROM quests WHERE done = 1")
    total_quests = total_quests['cnt'] if total_quests else 0
    
    bar_len = 12
    filled = int(bar_len * progress)
    bar = "█" * filled + "░" * (bar_len - filled)
    
    text = (
        f"{E.stats} <b>СТАТИСТИКА</b>\n\n"
        f"{E.heart} <b>{user['name']}</b> & <b>{partner['name']}</b>\n\n"
        f"{rank_emoji} {rank_name}\n"
        f"{E.star} XP: <b>{xp}</b> | {partner.get('xp', 0)}\n"
        f"{E.gem} LP: <b>{user.get('lp', 0)}</b> | {partner.get('lp', 0)}\n"
        f"{E.bridge} Квестов: <b>{user.get('quests_done', 0)}</b> | {partner.get('quests_done', 0)}\n"
        f"{E.album} Мостов всего: <b>{total_quests}</b>\n"
        f"{E.fire} Стрик: <b>{streak} дн.</b>\n\n"
        f"Прогресс: [{bar}] {int(progress*100)}%\n"
        f"До нового ранга: {left} XP"
    )
    await cb.message.edit_text(text, reply_markup=K.back())
    await cb.answer()

@dp.callback_query(F.data == "ach")
async def ach_show(cb: CallbackQuery):
    """Показать достижения пользователя"""
    user_id = cb.from_user.id
    achievements = await db.fetch_all("SELECT achievement_id FROM user_achievements WHERE user_id = ?", (user_id,))
    unlocked = {a['achievement_id'] for a in achievements}
    
    text = f"{E.trophy} <b>ДОСТИЖЕНИЯ</b> ({len(unlocked)}/{len(ACHIEVEMENTS)})\n\n"
    for aid, a in ACHIEVEMENTS.items():
        if aid in unlocked:
            text += f"{a['emoji']} <b>{a['name']}</b>\n   {a['desc']}\n   +{a['xp']} XP\n\n"
        else:
            text += f"🔒 <b>???</b>\n   {a['desc'][:30]}...\n\n"
    
    await cb.message.edit_text(text, reply_markup=K.back())
    await cb.answer()

@dp.callback_query(F.data == "pair_create")
async def pair_create(cb: CallbackQuery):
    """Создать код пары"""
    user_id = cb.from_user.id
    code = str(random.randint(100000, 999999))
    await db.execute("UPDATE users SET pair_code = ?, pair_code_created_at = ? WHERE id = ?",
                    (code, datetime.now().isoformat(), user_id))
    text = (
        f"{E.key} <b>КОД ПАРЫ СОЗДАН!</b>\n\n"
        f"<code>{code}</code>\n\n"
        f"1. Отправь этот код партнёру\n"
        f"2. Партнёр нажимает «Ввести код пары»\n"
        f"3. Вводит эти 6 цифр\n\n"
        f"{E.hourglass} Код действителен 24 часа"
    )
    await cb.message.edit_text(text, reply_markup=K.back())
    await cb.answer("Код создан!")

@dp.callback_query(F.data == "pair_enter")
async def pair_enter(cb: CallbackQuery, state: FSMContext):
    """Ввод кода пары"""
    await cb.message.answer(f"{E.lock} Введи 6-значный код от партнёра:")
    await state.set_state(States.pair_code)
    await cb.answer()

@dp.message(States.pair_code)
async def pair_code_handler(msg: Message, state: FSMContext):
    """Обработка ввода кода"""
    code = msg.text.strip()
    
    if not code.isdigit() or len(code) != 6:
        await msg.answer(f"{E.warning} Нужно ровно 6 цифр. Попробуй ещё раз:")
        return
    
    creator = await db.fetch_one(
        "SELECT id, name, pair_code_created_at FROM users WHERE pair_code = ? AND id != ?",
        (code, msg.from_user.id)
    )
    
    if not creator:
        await msg.answer(f"{E.cross} Код не найден.\nПроверь правильность или попроси новый код.", reply_markup=K.back())
        await state.clear()
        return
    
    created_at = creator.get('pair_code_created_at')
    if created_at:
        if datetime.now() - datetime.fromisoformat(created_at) > timedelta(hours=24):
            await msg.answer(f"{E.cross} Код просрочен (более 24 часов).\nПопроси партнёра создать новый код.", reply_markup=K.back())
            await state.clear()
            return
    
    # Создаём пару
    await db.execute("UPDATE users SET partner_id = ? WHERE id = ?", (creator['id'], msg.from_user.id))
    await db.execute("UPDATE users SET partner_id = ? WHERE id = ?", (msg.from_user.id, creator['id']))
    await db.execute("UPDATE users SET pair_code = NULL, pair_code_created_at = NULL WHERE id = ?", (creator['id'],))
    
    user = await db.fetch_one("SELECT name FROM users WHERE id = ?", (msg.from_user.id,))
    success = (
        f"{E.party} <b>ПАРА СОЗДАНА!</b>\n\n"
        f"{user['name']} {E.heart} {creator['name']}\n\n"
        f"Теперь можно играть! Нажми «Квест» чтобы начать."
    )
    
    is_admin = msg.from_user.id in ADMIN_IDS
    await msg.answer(success, reply_markup=K.main_menu(paired=True, is_admin=is_admin))
    
    try:
        await bot.send_message(creator['id'], success, reply_markup=K.main_menu(paired=True, is_admin=creator['id'] in ADMIN_IDS))
    except:
        pass
    
    await state.clear()

@dp.callback_query(F.data == "quest")
async def quest_start(cb: CallbackQuery):
    """Начать новый квест"""
    user_id = cb.from_user.id
    partner = await get_partner(user_id)
    
    if not partner:
        await cb.answer("Сначала создайте пару!", show_alert=True)
        return
    
    # Проверяем активный квест
    active = await db.fetch_one(
        "SELECT * FROM quests WHERE done = 0 AND (user1_id = ? OR user2_id = ?) LIMIT 1",
        (user_id, user_id)
    )
    
    if active:
        await cb.message.edit_text(
            f"{E.warning} У вас уже есть активный квест #{active['quest_id']}!\n"
            f"<i>{active['theme']}</i>\n\n"
            f"Завершите его — отправьте фото.",
            reply_markup=K.back()
        )
        await cb.answer()
        return
    
    await cb.message.edit_text(
        f"{E.map_emoji} <b>НОВЫЙ КВЕСТ!</b>\n\n"
        f"Отправь свою геолокацию кнопкой ниже.\n"
        f"Партнёр тоже получит запрос.\n"
        f"Когда оба отправят — AI создаст задание!"
    )
    await cb.message.answer(
        f"{E.map_emoji} Нажми кнопку чтобы отправить геолокацию:",
        reply_markup=K.location_kb()
    )
    await cb.answer()

@dp.message(F.location)
async def location_handler(msg: Message):
    """Обработка геолокации"""
    user_id = msg.from_user.id
    partner = await get_partner(user_id)
    
    if not partner:
        await msg.answer(f"{E.warning} Сначала создайте пару!", reply_markup=types.ReplyKeyboardRemove())
        return
    
    lat, lon = msg.location.latitude, msg.location.longitude
    weather = await get_weather(lat, lon)
    city = await geocode(lat, lon)
    
    # Сохраняем геолокацию
    await db.execute(
        "UPDATE users SET city = ?, weather = ?, temp = ?, last_location_at = ? WHERE id = ?",
        (city, weather.get('desc'), weather.get('temp'), datetime.now().isoformat(), user_id)
    )
    
    w_emoji = "☀️" if "ясно" in weather['desc'] else "☁️" if "облачно" in weather['desc'] else "🌧️" if "дождь" in weather['desc'] else "❄️" if "снег" in weather['desc'] else "🌍"
    
    await msg.answer(
        f"{E.map_emoji} <b>{city}</b>\n"
        f"{w_emoji} {weather['temp']}°C, {weather['desc']}\n"
        f"💨 {weather['wind']} м/с | 💧 {weather['humidity']}%\n\n"
        f"{E.clock} Жду геолокацию от <b>{partner['name']}</b>...",
        reply_markup=types.ReplyKeyboardRemove()
    )
    
    # Проверяем, отправил ли партнёр
    partner_data = await db.fetch_one("SELECT city, last_location_at FROM users WHERE id = ?", (partner['id'],))
    
    if partner_data and partner_data.get('city'):
        # Оба отправили, создаём квест
        await create_quest(msg, user_id, partner['id'])
    else:
        # Отправляем запрос партнёру
        try:
            await bot.send_message(
                partner['id'],
                f"{E.map_emoji} <b>{msg.from_user.first_name}</b> уже на месте!\nОтправь свою геолокацию:",
                reply_markup=K.location_kb()
            )
        except:
            pass

async def create_quest(msg: Message, uid1: int, uid2: int):
    """Создать квест на основе геолокаций"""
    u1 = await db.fetch_one("SELECT * FROM users WHERE id = ?", (uid1,))
    u2 = await db.fetch_one("SELECT * FROM users WHERE id = ?", (uid2,))
    
    # Получаем погоду из сохранённых данных
    w1 = {"temp": u1.get('temp', '?'), "desc": u1.get('weather', 'неизвестно')}
    w2 = {"temp": u2.get('temp', '?'), "desc": u2.get('weather', 'неизвестно')}
    c1 = u1.get('city', 'Неизвестный город')
    c2 = u2.get('city', 'Неизвестный город')
    
    # История квестов
    recent_quests = await db.fetch_all("SELECT theme FROM quests WHERE done = 1 ORDER BY id DESC LIMIT 10")
    recent = [q['theme'] for q in recent_quests]
    
    # Определяем время суток и сезон
    now = datetime.now()
    hour = now.hour
    month = now.month
    
    if 5 <= hour < 12:
        tod = "утро"
    elif 12 <= hour < 17:
        tod = "день"
    elif 17 <= hour < 22:
        tod = "вечер"
    else:
        tod = "ночь"
    
    if month in [12, 1, 2]:
        season = "зима"
    elif month in [3, 4, 5]:
        season = "весна"
    elif month in [6, 7, 8]:
        season = "лето"
    else:
        season = "осень"
    
    await msg.answer(f"{E.brain} <b>AI создаёт уникальный квест...</b>\n{E.magic} Анализирую погоду, время, историю...")
    
    ctx = {
        "u1": u1['name'], "u2": u2['name'],
        "c1": c1, "c2": c2,
        "w1temp": w1['temp'], "w2temp": w2['temp'],
        "w1desc": w1['desc'], "w2desc": w2['desc'],
        "tod": tod, "season": season,
        "recent": ", ".join(recent) if recent else "ещё не было"
    }
    
    qd = await ai_quest(ctx)
    
    # Получаем следующий ID квеста
    last_quest = await db.fetch_one("SELECT MAX(quest_id) as max_id FROM quests")
    qnum = (last_quest['max_id'] or 0) + 1
    
    quest_id = await db.execute("""
        INSERT INTO quests (
            quest_id, date, user1_id, user2_id,
            theme, legend, task1, task2, album_title,
            city1, city2, weather1, weather2,
            photo1, photo2, ai_review1, ai_review2,
            done
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        qnum, now.isoformat(), uid1, uid2,
        qd.get("theme", "Мост"), qd.get("legend", ""),
        qd.get("task1", ""), qd.get("task2", ""),
        qd.get("album_title", "Мост"),
        c1, c2, f"{w1['temp']}°C, {w1['desc']}", f"{w2['temp']}°C, {w2['desc']}",
        None, None, None, None, 0
    ))
    
    # Отправляем задания
    for u_id, task, city, weather, uname in [
        (uid1, qd.get("task1", ""), c1, f"{w1['temp']}°C, {w1['desc']}", u1['name']),
        (uid2, qd.get("task2", ""), c2, f"{w2['temp']}°C, {w2['desc']}", u2['name'])
    ]:
        text = (
            f"{E.bridge} <b>МОСТ #{qnum}</b>\n"
            f"<i>{qd.get('theme', 'Мост')}</i>\n\n"
            f"{E.star} <b>Легенда:</b>\n{qd.get('legend', '')}\n\n"
            f"{E.target} <b>Твоё задание, {uname}:</b>\n{task}\n\n"
            f"{E.map_emoji} {city} • {weather}\n"
            f"{E.magic} Подсказка: {qd.get('hint', 'Оглянись вокруг!')}\n\n"
            f"{E.camera} <b>Сделай фото и отправь мне!</b>\n"
            f"{E.robot} AI проверит твой снимок"
        )
        try:
            if u_id == uid1:
                await msg.answer(text)
            else:
                await bot.send_message(u_id, text)
        except Exception as e:
            print(f"Send error: {e}")

@dp.message(F.photo)
async def photo_handler(msg: Message):
    """Обработка фото от пользователя"""
    user_id = msg.from_user.id
    
    # Находим активный квест
    active = await db.fetch_one(
        "SELECT * FROM quests WHERE done = 0 AND (user1_id = ? OR user2_id = ?) LIMIT 1",
        (user_id, user_id)
    )
    
    if not active:
        await msg.answer(f"{E.warning} Нет активного квеста!\nНажми /start и начни новый.", reply_markup=K.main_menu())
        return
    
    # Проверяем, не завершается ли квест
    if active.get('completing'):
        await msg.answer(f"{E.clock} Квест уже завершается, подожди секунду...")
        return
    
    is_u1 = user_id == active['user1_id']
    pf = "photo1" if is_u1 else "photo2"
    rf = "ai_review1" if is_u1 else "ai_review2"
    task = active['task1'] if is_u1 else active['task2']
    
    # Проверяем, не отправлял ли уже фото
    existing_photo = active.get(pf)
    if existing_photo and existing_photo != 'None':
        await msg.answer(f"{E.warning} Ты уже отправил фото! Ждём партнёра...")
        return
    
    try:
        photo = msg.photo[-1]
        file = await bot.get_file(photo.file_id)
        path = MEDIA / "album" / f"quest_{active['quest_id']}_user_{user_id}.jpg"
        await bot.download_file(file.file_path, path)
        
        name = await db.fetch_one("SELECT name FROM users WHERE id = ?", (user_id,))
        name = name['name'] if name else "Пользователь"
        
        await msg.answer(f"{E.robot} <b>AI проверяет фото...</b>\n{E.eyes} Анализирую снимок...")
        review = await ai_review_photo(str(path), task, name)
        
        # Сохраняем review в базу
        review_json = json.dumps(review)
        await db.execute(f"UPDATE quests SET {pf} = ?, {rf} = ? WHERE id = ?", (str(path), review_json, active['id']))
        
        # Сохраняем оценки
        score = review.get('match_score', 7)
        creativity = review.get('creativity', 7)
        if is_u1:
            await db.execute("UPDATE quests SET score1 = ?, creativity1 = ? WHERE id = ?", (score, creativity, active['id']))
        else:
            await db.execute("UPDATE quests SET score2 = ?, creativity2 = ? WHERE id = ?", (score, creativity, active['id']))
        
        stars = "⭐" * min(10, score) + "☆" * (10 - min(10, score))
        
        await msg.answer(
            f"{E.robot} <b>AI-РЕВЬЮ ДЛЯ {name.upper()}:</b>\n\n"
            f"{E.eyes} <b>Вижу:</b> {review.get('what_i_see', 'что-то')}\n"
            f"{E.target} <b>Попадание:</b> {score}/10\n{stars}\n"
            f"{E.palette} <b>Креативность:</b> {creativity}/10\n"
            f"💬 <i>«{review.get('comment', 'Отлично!')}»</i>\n"
            f"{E.butterfly} <b>Настроение:</b> {review.get('mood', 'загадочное')}"
        )
        
        # Проверяем, отправил ли второй пользователь
        other_photo = "photo2" if is_u1 else "photo1"
        other_photo_value = active.get(other_photo)
        
        if other_photo_value and other_photo_value != 'None':
            # Оба фото есть, завершаем квест
            await finalize_quest(active['id'], msg)
        else:
            await msg.answer(f"{E.clock} Ждём фото от партнёра...")
    
    except Exception as e:
        traceback.print_exc()
        await msg.answer(f"{E.cross} Ошибка обработки. Попробуй ещё раз.")

async def finalize_quest(quest_db_id: int, msg: Message):
    """Завершить квест, создать коллаж и отправить обоим"""
    # Блокируем квест
    await db.execute("UPDATE quests SET completing = 1 WHERE id = ?", (quest_db_id,))
    
    try:
        quest = await db.fetch_one("SELECT * FROM quests WHERE id = ?", (quest_db_id,))
        if not quest:
            return
        
        u1 = quest['user1_id']
        u2 = quest['user2_id']
        
        # Получаем данные пользователей
        user1 = await db.fetch_one("SELECT name FROM users WHERE id = ?", (u1,))
        user2 = await db.fetch_one("SELECT name FROM users WHERE id = ?", (u2,))
        
        # Получаем AI ревью
        r1 = json.loads(quest.get('ai_review1', '{}')) if quest.get('ai_review1') else {}
        r2 = json.loads(quest.get('ai_review2', '{}')) if quest.get('ai_review2') else {}
        
        score1 = r1.get('match_score', 7)
        score2 = r2.get('match_score', 7)
        creativity1 = r1.get('creativity', 7)
        creativity2 = r2.get('creativity', 7)
        
        await msg.answer(f"{E.art} <b>Создаю коллаж...</b>")
        
        collage = await make_collage(
            quest['photo1'], quest['photo2'],
            quest['theme'],
            quest.get('city1', ''), quest.get('city2', ''),
            quest['quest_id']
        )
        
        # Обновляем квест
        await db.execute("UPDATE quests SET done = 1, collage = ? WHERE id = ?", (collage, quest_db_id))
        
        # Добавляем в альбом
        avg_score = (score1 + score2) / 2
        await db.execute("""
            INSERT INTO album (quest_id, user1_id, user2_id, theme, album_title, collage, date, avg_score)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (quest['quest_id'], u1, u2, quest['theme'], quest['album_title'], collage, quest['date'], avg_score))
        
        # Обновляем статистику пользователей
        xp1 = int((score1 + creativity1) / 2 * 15)
        xp2 = int((score2 + creativity2) / 2 * 15)
        
        await db.execute("UPDATE users SET quests_done = quests_done + 1, xp = xp + ?, lp = lp + ? WHERE id = ?", (xp1, xp1 // 3, u1))
        await db.execute("UPDATE users SET quests_done = quests_done + 1, xp = xp + ?, lp = lp + ? WHERE id = ?", (xp2, xp2 // 3, u2))
        
        # Обновляем perfect_photos
        if score1 == 10:
            await db.execute("UPDATE users SET perfect_photos = perfect_photos + 1 WHERE id = ?", (u1,))
        if score2 == 10:
            await db.execute("UPDATE users SET perfect_photos = perfect_photos + 1 WHERE id = ?", (u2,))
        
        # Обновляем стрики
        await update_streak(u1)
        await update_streak(u2)
        
        # Проверяем достижения
        quest_data = {
            'date': quest['date'],
            'weather1': quest.get('weather1', ''),
            'weather2': quest.get('weather2', ''),
            'score1': score1,
            'score2': score2
        }
        await check_achievements(u1, quest_data)
        await check_achievements(u2, quest_data)
        
        # Обновляем общую статистику
        total_quests = await db.fetch_one("SELECT value FROM bot_stats WHERE key = 'total_quests'")
        if total_quests:
            await db.execute("UPDATE bot_stats SET value = ?, updated_at = ? WHERE key = 'total_quests'",
                            (str(int(total_quests['value']) + 1), datetime.now().isoformat()))
        
        # Отправляем коллаж обоим пользователям
        with open(collage, "rb") as f:
            pb = f.read()
        
        caption = (
            f"{E.party} <b>МОСТ #{quest['quest_id']} ПОСТРОЕН!</b>\n"
            f"<i>{quest['album_title']}</i>\n\n"
            f"{E.star} AI: {avg_score:.1f}/10 {'⭐' * int(avg_score)}\n"
            f"{E.album} В альбоме: {await db.fetch_one('SELECT COUNT(*) as cnt FROM album') or 0} мостов\n"
            f"{E.star} Ты получил: +{xp1 if u1 == msg.from_user.id else xp2} XP"
        )
        
        photo_file = BufferedInputFile(pb, filename="collage.jpg")
        
        # Отправляем обоим
        for user_id in [u1, u2]:
            try:
                await bot.send_photo(user_id, photo_file, caption=caption)
            except Exception as e:
                print(f"Failed to send to {user_id}: {e}")
                try:
                    await bot.send_message(user_id, caption)
                except:
                    pass
        
        # Разблокируем квест
        await db.execute("UPDATE quests SET completing = 0 WHERE id = ?", (quest_db_id,))
        
    except Exception as e:
        traceback.print_exc()
        await db.execute("UPDATE quests SET completing = 0 WHERE id = ?", (quest_db_id,))
        await msg.answer(f"{E.cross} Ошибка при создании коллажа. Но ваши фото сохранены!")

@dp.callback_query(F.data == "album")
async def album_show(cb: CallbackQuery):
    """Показать альбом"""
    user_id = cb.from_user.id
    
    # Находим квесты пользователя
    album_entries = await db.fetch_all("""
        SELECT * FROM album 
        WHERE user1_id = ? OR user2_id = ? 
        ORDER BY id DESC LIMIT 10
    """, (user_id, user_id))
    
    if not album_entries:
        await cb.message.edit_text(
            f"{E.album} <b>Альбом пока пуст</b>\n\nВыполните первый квест — и здесь появятся ваши мосты!",
            reply_markup=K.back()
        )
        await cb.answer()
        return
    
    for entry in album_entries[:5]:
        if entry.get('collage') and Path(entry['collage']).exists():
            with open(entry['collage'], "rb") as f:
                await cb.message.answer_photo(
                    BufferedInputFile(f.read(), filename="collage.jpg"),
                    caption=f"{E.bridge} <b>Мост #{entry['quest_id']}</b>\n<i>{entry['album_title']}</i>\n{E.star} Оценка: {entry.get('avg_score', 0):.1f}/10"
                )
    
    await cb.message.answer(f"{E.album} Показаны последние 5 из {len(album_entries)} мостов", reply_markup=K.back())
    await cb.answer()

@dp.callback_query(F.data == "diary")
async def diary_show(cb: CallbackQuery):
    """Показать дневник"""
    user_id = cb.from_user.id
    partner = await get_partner(user_id)
    
    if not partner:
        await cb.answer("Нужна пара!", show_alert=True)
        return
    
    await cb.message.edit_text(f"{E.magic} <b>AI пишет дневник...</b>")
    entry = await ai_diary(None, user_id)
    await cb.message.edit_text(f"{E.magic} <b>ДНЕВНИК МЕРИДИАНА</b>\n\n{entry}\n\n{E.butterfly} Новая запись завтра!", reply_markup=K.back())
    await cb.answer()

@dp.callback_query(F.data == "surprise")
async def surprise_send(cb: CallbackQuery):
    """Отправить сюрприз партнёру"""
    user_id = cb.from_user.id
    partner = await get_partner(user_id)
    
    if not partner:
        await cb.answer("Нужна пара!", show_alert=True)
        return
    
    secrets = [
        "Сфоткай свою левую ладонь крупно",
        "Найди число 42 где-нибудь вокруг",
        "Сфоткай движение стоп-кадром",
        "Сфоткай отражение в ложке или другой поверхности",
        "Сфоткай предмет старше тебя",
        "Найди облако, похожее на животное",
        "Сфоткай то, что приятно пахнет",
        "Сфоткай самую старую вещь рядом",
        "Сделай селфи с неожиданным предметом",
        "Сфоткай три предмета одного цвета"
    ]
    task = random.choice(secrets)
    
    try:
        await bot.send_message(
            partner['id'],
            f"{E.gift} <b>СЮРПРИЗ ОТ {await db.fetch_one('SELECT name FROM users WHERE id = ?', (user_id,))}!</b>\n\n{E.target} <b>Задание:</b>\n{task}\n\n{E.camera} Отправь фото!"
        )
        await cb.message.edit_text(f"{E.check} <b>Сюрприз отправлен {partner['name']}!</b>", reply_markup=K.back())
        await db.execute("UPDATE users SET surprises_sent = surprises_sent + 1 WHERE id = ?", (user_id,))
    except Exception as e:
        await cb.message.edit_text(f"{E.cross} Не удалось отправить.", reply_markup=K.back())
    
    await cb.answer()

@dp.callback_query(F.data == "postcard")
async def postcard_menu(cb: CallbackQuery):
    """Меню открыток"""
    partner = await get_partner(cb.from_user.id)
    if not partner:
        await cb.answer("Нужна пара!", show_alert=True)
        return
    
    builder = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💝 Романтичная", callback_data="postcard_romantic")],
        [InlineKeyboardButton(text="😂 Весёлая", callback_data="postcard_funny")],
        [InlineKeyboardButton(text="🌟 Вдохновляющая", callback_data="postcard_inspiring")],
        [InlineKeyboardButton(text="😢 Ностальгическая", callback_data="postcard_nostalgic")],
        [InlineKeyboardButton(text=f"{E.back_emoji} Назад", callback_data="main_menu")],
    ])
    await cb.message.edit_text(f"{E.letter} <b>ОТКРЫТКА</b>\n\nВыбери настроение:", reply_markup=builder)
    await cb.answer()

@dp.callback_query(F.data.startswith("postcard_"))
async def postcard_send(cb: CallbackQuery):
    """Отправить открытку"""
    user_id = cb.from_user.id
    partner = await get_partner(user_id)
    
    if not partner:
        await cb.answer("Нужна пара!", show_alert=True)
        return
    
    mood = cb.data.replace("postcard_", "")
    mood_names = {"romantic": "романтичное", "funny": "весёлое", "inspiring": "вдохновляющее", "nostalgic": "ностальгическое"}
    mood_text = mood_names.get(mood, "романтичное")
    
    user = await db.fetch_one("SELECT name FROM users WHERE id = ?", (user_id,))
    text = await ai_postcard(partner['name'], user['name'], mood_text)
    
    try:
        await bot.send_message(partner['id'], f"{E.letter} <b>Открытка от {user['name']}!</b>\n\n{text}\n\n{E.heart}")
        await cb.message.edit_text(f"{E.check} <b>Отправлено!</b>\n\n{text}", reply_markup=K.back())
    except:
        await cb.message.edit_text(f"{E.cross} Не удалось отправить.", reply_markup=K.back())
    
    await cb.answer()

@dp.callback_query(F.data == "secret")
async def secret_quest(cb: CallbackQuery):
    """Секретный квест"""
    user_id = cb.from_user.id
    partner = await get_partner(user_id)
    
    if not partner:
        await cb.answer("Нужна пара!", show_alert=True)
        return
    
    secrets = [
        "Сфоткай свою тень в необычном ракурсе",
        "Найди и сфоткай что-то в форме сердца",
        "Сфоткай то, что делает тебя счастливым сегодня",
        "Сфоткай место, где ты впервые написал партнёру",
        "Сфоткай предмет, который напоминает о вашей встрече",
        "Сфоткай закат или рассвет",
        "Сфоткай что-то, что ты хочешь показать партнёру лично"
    ]
    task = random.choice(secrets)
    
    user = await db.fetch_one("SELECT secret_done FROM users WHERE id = ?", (user_id,))
    
    if user.get('secret_done'):
        await cb.message.edit_text(
            f"{E.ghost} <b>СЕКРЕТНЫЙ КВЕСТ</b>\n\n"
            f"Ты уже выполнял секретный квест! {E.warning}\n"
            f"Достижение «Кладоискатель» уже твоё!",
            reply_markup=K.back()
        )
    else:
        await db.execute("UPDATE users SET secret_done = 1 WHERE id = ?", (user_id,))
        await cb.message.edit_text(
            f"{E.ghost} <b>СЕКРЕТНЫЙ КВЕСТ!</b>\n\n"
            f"{E.magic} <b>Задание:</b>\n{task}\n\n"
            f"{E.camera} Отправь фото — получишь достижение «Кладоискатель» +100 XP!",
            reply_markup=K.back()
        )
    
    await cb.answer()

@dp.callback_query(F.data == "compliment")
async def compliment_send(cb: CallbackQuery):
    """Отправить комплимент партнёру"""
    user_id = cb.from_user.id
    partner = await get_partner(user_id)
    
    if not partner:
        await cb.answer("Нужна пара!", show_alert=True)
        return
    
    user = await db.fetch_one("SELECT name FROM users WHERE id = ?", (user_id,))
    compliment = await ai_compliment(partner['name'], user['name'])
    
    try:
        await bot.send_message(partner['id'], f"{E.heart} <b>Комплимент от {user['name']}:</b>\n\n{compliment}")
        await cb.message.edit_text(f"{E.check} <b>Комплимент отправлен!</b>\n\n{compliment}", reply_markup=K.back())
    except:
        await cb.message.edit_text(f"{E.cross} Не удалось отправить.", reply_markup=K.back())
    
    await cb.answer()

@dp.callback_query(F.data == "analyze_photo")
async def analyze_photo_request(cb: CallbackQuery, state: FSMContext):
    """Запрос на анализ фото"""
    await cb.message.answer(
        f"{E.analysis} <b>Отправь фото для глубокого анализа</b>\n\n"
        f"AI оценит:\n"
        f"• Композицию и освещение\n"
        f"• Эмоции и настроение\n"
        f"• Детальные советы по улучшению\n"
        f"• Интересные факты о фотографии"
    )
    await state.set_state(States.waiting_photo_analysis)
    await cb.answer()

@dp.message(States.waiting_photo_analysis, F.photo)
async def analyze_photo_handler(msg: Message, state: FSMContext):
    """Обработка фото для анализа"""
    await msg.answer(f"{E.analysis} <b>Анализирую фото...</b>\n{E.hourglass} Это займёт несколько секунд")
    
    try:
        photo = msg.photo[-1]
        file = await bot.get_file(photo.file_id)
        path = MEDIA / "temp" / f"analysis_{msg.from_user.id}.jpg"
        await bot.download_file(file.file_path, path)
        
        analysis = await ai_analyze_photo_deep(str(path), "общее фото", msg.from_user.first_name)
        
        stars = "⭐" * min(10, analysis.get('score', 7)) + "☆" * (10 - min(10, analysis.get('score', 7)))
        
        result = (
            f"{E.analysis} <b>ГЛУБОКИЙ АНАЛИЗ ФОТО</b>\n\n"
            f"{E.star} <b>Общая оценка:</b> {analysis.get('score', 7)}/10 {stars}\n"
            f"{E.palette} <b>Креативность:</b> {analysis.get('creativity', 7)}/10\n"
            f"🎨 <b>Композиция:</b> {analysis.get('composition', 'хорошая')}\n"
            f"☀️ <b>Освещение:</b> {analysis.get('light', 'естественное')}\n"
            f"{E.heart} <b>Эмоции:</b> {analysis.get('emotion', 'тёплые')}\n"
            f"{E.eyes} <b>Что вижу:</b> {analysis.get('what_i_see', 'интересный кадр')}\n\n"
            f"💡 <b>Совет:</b> {analysis.get('recommendation', 'Продолжай экспериментировать!')}\n\n"
            f"💬 <i>«{analysis.get('comment', 'Отличная работа!')}»</i>\n\n"
            f"{E.magic} <b>Факт:</b> {analysis.get('fun_fact', 'Каждое фото — это маленькая история')}"
        )
        
        await msg.answer(result, reply_markup=K.back())
    except Exception as e:
        await msg.answer(f"{E.cross} Ошибка анализа. Попробуй другое фото.", reply_markup=K.back())
    finally:
        await state.clear()

# ══════════════════════════════════════════════════════════════
# 👑 АДМИН-ПАНЕЛЬ
# ══════════════════════════════════════════════════════════════

def is_admin(func):
    """Декоратор для проверки прав администратора"""
    async def wrapper(callback: CallbackQuery, *args, **kwargs):
        if callback.from_user.id not in ADMIN_IDS:
            await callback.answer("⛔ У вас нет прав администратора!", show_alert=True)
            return
        return await func(callback, *args, **kwargs)
    return wrapper

@dp.callback_query(F.data == "admin_panel")
@is_admin
async def admin_panel(cb: CallbackQuery):
    """Главная админ-панель"""
    await cb.message.edit_text(
        f"{E.admin} <b>АДМИН-ПАНЕЛЬ МЕРИДИАН</b>\n\n"
        f"Выберите действие:",
        reply_markup=K.admin_menu()
    )
    await cb.answer()

@dp.callback_query(F.data == "admin_stats")
@is_admin
async def admin_stats(cb: CallbackQuery):
    """Статистика бота для админа"""
    # Собираем статистику
    total_users = await db.fetch_one("SELECT COUNT(*) as cnt FROM users")
    total_users = total_users['cnt'] if total_users else 0
    
    total_quests = await db.fetch_one("SELECT COUNT(*) as cnt FROM quests WHERE done = 1")
    total_quests = total_quests['cnt'] if total_quests else 0
    
    total_pairs = await db.fetch_one("SELECT COUNT(*) as cnt FROM users WHERE partner_id IS NOT NULL")
    total_pairs = total_pairs['cnt'] if total_pairs else 0
    total_pairs = total_pairs // 2
    
    total_photos = await db.fetch_one("SELECT COUNT(*) as cnt FROM quests WHERE photo1 IS NOT NULL AND photo2 IS NOT NULL")
    total_photos = total_photos['cnt'] if total_photos else 0
    
    total_xp = await db.fetch_one("SELECT SUM(xp) as sum FROM users")
    total_xp = total_xp['sum'] if total_xp and total_xp['sum'] else 0
    
    # API статистика
    api_usage = await db.fetch_all("""
        SELECT service, COUNT(*) as cnt, SUM(success) as success
        FROM api_usage 
        WHERE timestamp > datetime('now', '-7 days')
        GROUP BY service
    """)
    
    api_text = ""
    for api in api_usage:
        success_rate = (api['success'] / api['cnt'] * 100) if api['cnt'] > 0 else 0
        api_text += f"\n• {api['service']}: {api['cnt']} запросов, {success_rate:.0f}% успешных"
    
    # Активные ключи
    active_gemini = await db.fetch_all("SELECT COUNT(*) as cnt FROM api_keys WHERE service = 'gemini' AND is_active = 1")
    active_weather = await db.fetch_all("SELECT COUNT(*) as cnt FROM api_keys WHERE service = 'weather' AND is_active = 1")
    
    text = (
        f"{E.chart} <b>СТАТИСТИКА БОТА</b>\n\n"
        f"{E.user} <b>Пользователи:</b> {total_users}\n"
        f"{E.users} <b>Пары:</b> {total_pairs}\n"
        f"{E.bridge} <b>Завершено квестов:</b> {total_quests}\n"
        f"{E.camera} <b>Всего фото:</b> {total_photos * 2}\n"
        f"{E.album} <b>Создано коллажей:</b> {total_quests}\n"
        f"{E.star} <b>Всего XP:</b> {total_xp}\n\n"
        f"{E.api} <b>API статистика (7 дней):</b>{api_text if api_text else ' нет данных'}\n\n"
        f"{E.key} <b>Активные ключи:</b>\n"
        f"• Gemini: {active_gemini[0]['cnt'] if active_gemini else 0}\n"
        f"• Weather: {active_weather[0]['cnt'] if active_weather else 0}\n\n"
        f"{E.clock} <b>Запущен:</b> {await db.fetch_one('SELECT value FROM bot_stats WHERE key = \"bot_started_at\"') or 'неизвестно'}"
    )
    
    await cb.message.edit_text(text, reply_markup=K.admin_menu())
    await cb.answer()

@dp.callback_query(F.data == "admin_users")
@is_admin
async def admin_users(cb: CallbackQuery):
    """Список пользователей"""
    users = await db.fetch_all("""
        SELECT id, name, xp, quests_done, last_active 
        FROM users 
        ORDER BY xp DESC 
        LIMIT 20
    """)
    
    text = f"{E.users} <b>ТОП-20 ПОЛЬЗОВАТЕЛЕЙ</b>\n\n"
    for i, user in enumerate(users, 1):
        rank_name, _, _ = get_rank(user['xp'])
        text += f"{i}. {user['name']} — {user['xp']} XP ({rank_name})\n"
        text += f"   Квестов: {user['quests_done']}\n"
    
    await cb.message.edit_text(text, reply_markup=K.admin_menu())
    await cb.answer()

@dp.callback_query(F.data == "admin_api")
@is_admin
async def admin_api_menu(cb: CallbackQuery):
    """Меню управления API ключами"""
    gemini_keys = await db.fetch_all("SELECT key, is_active, usage_count FROM api_keys WHERE service = 'gemini'")
    weather_keys = await db.fetch_all("SELECT key, is_active, usage_count FROM api_keys WHERE service = 'weather'")
    
    text = (
        f"{E.api} <b>УПРАВЛЕНИЕ API КЛЮЧАМИ</b>\n\n"
        f"<b>Gemini API ({len(gemini_keys)} ключей):</b>\n"
    )
    
    for k in gemini_keys:
        status = "✅" if k['is_active'] else "❌"
        text += f"{status} `{k['key'][:20]}...` ({k['usage_count']} запросов)\n"
    
    text += f"\n<b>Weather API ({len(weather_keys)} ключей):</b>\n"
    for k in weather_keys:
        status = "✅" if k['is_active'] else "❌"
        text += f"{status} `{k['key'][:20]}...` ({k['usage_count']} запросов)\n"
    
    text += f"\n📌 Чтобы добавить ключ, отправьте команду:\n<code>/addkey gemini|weather API_КЛЮЧ</code>"
    
    await cb.message.edit_text(text, reply_markup=K.admin_menu())
    await cb.answer()

@dp.message(Command("addkey"))
async def add_api_key(msg: Message):
    """Добавить API ключ (только для админов)"""
    if msg.from_user.id not in ADMIN_IDS:
        await msg.answer("⛔ У вас нет прав!")
        return
    
    parts = msg.text.split()
    if len(parts) != 3:
        await msg.answer("Использование: /addkey gemini|weather API_КЛЮЧ")
        return
    
    service = parts[1].lower()
    key = parts[2]
    
    if service not in ["gemini", "weather"]:
        await msg.answer("Сервис должен быть 'gemini' или 'weather'")
        return
    
    await db.execute("INSERT INTO api_keys (service, key, is_active, added_at) VALUES (?, ?, 1, ?)",
                    (service, key, datetime.now().isoformat()))
    
    if service == "gemini":
        GEMINI_KEYS.append(key)
    else:
        WEATHER_KEYS.append(key)
    
    await msg.answer(f"✅ API ключ для {service} добавлен!")

@dp.callback_query(F.data == "admin_backup")
@is_admin
async def admin_backup(cb: CallbackQuery):
    """Создать резервную копию БД"""
    backup_name = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
    backup_path = MEDIA / "backups" / backup_name
    
    # Копируем БД
    import shutil
    shutil.copy2(DATABASE_FILE, backup_path)
    
    # Отправляем админу
    with open(backup_path, "rb") as f:
        await cb.message.answer_document(
            BufferedInputFile(f.read(), filename=backup_name),
            caption=f"{E.database} <b>Резервная копия создана!</b>\nДата: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )
    
    await cb.message.edit_text("✅ Резервная копия создана и отправлена!", reply_markup=K.admin_menu())
    await cb.answer()

@dp.callback_query(F.data == "admin_broadcast")
@is_admin
async def admin_broadcast(cb: CallbackQuery, state: FSMContext):
    """Начать рассылку"""
    await cb.message.answer(
        f"{E.broadcast} <b>РАССЫЛКА</b>\n\n"
        f"Введите текст сообщения для рассылки всем пользователям.\n"
        f"Можно использовать HTML-разметку.\n\n"
        f"Для отмены отправьте /cancel"
    )
    await state.set_state(States.admin_broadcast)
    await cb.answer()

@dp.message(States.admin_broadcast)
async def admin_broadcast_text(msg: Message, state: FSMContext):
    """Отправить рассылку"""
    if msg.from_user.id not in ADMIN_IDS:
        return
    
    text = msg.text
    
    if text == "/cancel":
        await msg.answer("Рассылка отменена.")
        await state.clear()
        return
    
    await msg.answer(f"{E.broadcast} <b>Начинаю рассылку...</b>\n\nЭто может занять некоторое время.")
    
    # Получаем всех пользователей
    users = await db.fetch_all("SELECT id FROM users")
    sent = 0
    failed = 0
    
    for user in users:
        try:
            await bot.send_message(user['id'], text)
            sent += 1
            await asyncio.sleep(0.05)  # Чтобы не превысить лимиты
        except:
            failed += 1
    
    await msg.answer(f"✅ Рассылка завершена!\n📨 Отправлено: {sent}\n❌ Не доставлено: {failed}")
    
    # Логируем
    await db.execute("""
        INSERT INTO admin_logs (admin_id, action, details, timestamp)
        VALUES (?, ?, ?, ?)
    """, (msg.from_user.id, "broadcast", f"sent to {sent} users", datetime.now().isoformat()))
    
    await state.clear()

@dp.callback_query(F.data == "admin_settings")
@is_admin
async def admin_settings(cb: CallbackQuery):
    """Настройки бота"""
    # Получаем текущие настройки
    stats = await db.fetch_all("SELECT key, value FROM bot_stats")
    stats_dict = {s['key']: s['value'] for s in stats}
    
    text = (
        f"{E.gear} <b>НАСТРОЙКИ БОТА</b>\n\n"
        f"<b>Основные:</b>\n"
        f"• Всего пользователей: {stats_dict.get('total_users', 0)}\n"
        f"• Всего квестов: {stats_dict.get('total_quests', 0)}\n"
        f"• API запросов сегодня: {stats_dict.get('api_requests_today', 0)}\n"
        f"• Ошибок API сегодня: {stats_dict.get('api_failures_today', 0)}\n\n"
        f"<b>Доступные команды:</b>\n"
        f"• /addkey — добавить API ключ\n"
        f"• /stats — статистика бота\n"
        f"• /backup — создать бэкап БД\n\n"
        f"<b>ID администраторов:</b> {', '.join(map(str, ADMIN_IDS))}\n"
        f"(можно добавить в файл конфигурации)"
    )
    
    await cb.message.edit_text(text, reply_markup=K.admin_menu())
    await cb.answer()

# ══════════════════════════════════════════════════════════════
# 💬 ТЕКСТОВЫЕ СООБЩЕНИЯ
# ══════════════════════════════════════════════════════════════

@dp.message(F.text)
async def text_handler(msg: Message):
    """Обработка обычных текстовых сообщений"""
    text = msg.text.lower()
    
    if any(w in text for w in ["привет", "здарова", "хай", "ку", "hi", "hello"]):
        await msg.answer(
            f"{E.smile} Привет! Я бот Меридиан.\n"
            f"Нажми /start чтобы открыть меню!"
        )
    elif any(w in text for w in ["спасибо", "красава", "круто", "спс", "thanks"]):
        await msg.answer(f"{E.love} Пожалуйста! Рад помочь! {E.sparkles}")
    elif "как дела" in text or "how are you" in text:
        await msg.answer(f"{E.robot} У меня всё отлично! А как ваши мосты строятся? {E.bridge}")
    elif "помощь" in text or "help" in text:
        await msg.answer(
            f"{E.info} <b>Доступные команды:</b>\n\n"
            f"• /start — Главное меню\n"
            f"• /quest — Новый квест\n"
            f"• /stats — Статистика\n"
            f"• /album — Альбом\n\n"
            f"Или просто нажимай на кнопки в меню!",
            parse_mode="HTML"
        )
    elif random.random() < 0.03:
        eggs = [
            f"{E.butterfly} Редкая бабочка пролетела мимо!",
            f"{E.rocket} 🚀 Кто-то запустил ракету!",
            f"{E.diamond} 💎 Ты нашёл скрытый кристалл!",
            f"{E.ghost} 👻 Призрак мостов шепчет: «Стройте дальше!»",
            f"{E.magic} 🔮 Магический шар говорит: «Сделайте фото заката!»",
            f"{E.compass} 🧭 Компас показывает направление к новому квесту!"
        ]
        await msg.answer(random.choice(eggs))
    else:
        await msg.answer(
            f"{E.robot} Я понимаю команды и фото.\n"
            f"Нажми /start для меню или отправь фото для квеста!"
        )

# ══════════════════════════════════════════════════════════════
# 🚀 ЗАПУСК
# ══════════════════════════════════════════════════════════════

async def main():
    print("╔══════════════════════════════════════════════════════════════╗")
    print("║            🌉 МЕРИДИАН — АДМИНСКАЯ ВЕРСИЯ ЗАПУЩЕНА         ║")
    print("║        Админ-панель | Ротация API | Отдельная БД            ║")
    print("╚══════════════════════════════════════════════════════════════╝")
    print(f"\n✅ Бот запущен!")
    print(f"👑 Администраторы: {', '.join(map(str, ADMIN_IDS))}")
    print(f"🗄️ База данных: {DATABASE_FILE}")
    print(f"📁 Папка медиа: {MEDIA}")
    print(f"\n🤖 API Gemini: {len([k for k in GEMINI_KEYS if k])} ключей")
    print(f"🌤️ API Weather: {len([k for k in WEATHER_KEYS if k])} ключей")
    print("\n" + "=" * 60)
    
    await bot.set_my_commands([
        BotCommand(command="start", description="🏠 Главное меню"),
        BotCommand(command="quest", description="🎯 Новый квест"),
        BotCommand(command="stats", description="📊 Статистика"),
        BotCommand(command="album", description="📸 Альбом"),
    ])
    
    try:
        await dp.start_polling(bot)
    except Exception as e:
        traceback.print_exc()
        print(f"\n❌ Ошибка: {e}")

if __name__ == "__main__":
    asyncio.run(main())
EOF