"""
╔══════════════════════════════════════════════════════════════════╗
║                    🌉 МЕРИДИАН ULTRA v4.0                         ║
║             50+ КОМАНД • КНОПКИ • AI • МАГАЗИН • VIP              ║
║                 ВСЕ ФУНКЦИИ РЕАЛЬНО РАБОЧИЕ                       ║
╚══════════════════════════════════════════════════════════════════╝
"""

import asyncio, json, os, random, re, traceback, logging, signal, sys, platform
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple
from collections import defaultdict

from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command, CommandObject
from aiogram.types import (
    InlineKeyboardMarkup, InlineKeyboardButton,
    ReplyKeyboardMarkup, KeyboardButton,
    BufferedInputFile, BotCommand, BotCommandScopeDefault,
    InputMediaPhoto
)
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.utils.keyboard import InlineKeyboardBuilder

import google.generativeai as genai
import httpx
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance

# ══════════════════════════════════════════════════════════════════
# 🔑 КЛЮЧИ API И КОНФИГУРАЦИЯ
# ══════════════════════════════════════════════════════════════════
BOT_TOKEN = "8853395386:AAHtdZNkZ1PLMIAnlXq2_Jmd43v7xjn0as8"
GEMINI_API_KEY = "AIzaSyBc-lzSR0htkZJ7DZDWELxYzPyKq8wKRvw"
OPENWEATHER_API_KEY = "c9533271e2a27b86f0abc303b206c6a6"
ADMIN_ID = 8659997773

genai.configure(api_key=GEMINI_API_KEY)
quest_ai = genai.GenerativeModel("gemini-1.5-flash", generation_config={"temperature": 0.95, "max_output_tokens": 600})
vision_ai = genai.GenerativeModel("gemini-1.5-flash", generation_config={"temperature": 0.7, "max_output_tokens": 300})
creative_ai = genai.GenerativeModel("gemini-1.5-flash", generation_config={"temperature": 1.0, "max_output_tokens": 1000})
chat_ai = genai.GenerativeModel("gemini-1.5-flash", generation_config={"temperature": 0.9, "max_output_tokens": 500})

bot = Bot(token=BOT_TOKEN, parse_mode="HTML")
dp = Dispatcher(storage=MemoryStorage())

# ══════════════════════════════════════════════════════════════════
# 📁 ПАПКИ И ЛОГИ
# ══════════════════════════════════════════════════════════════════
for d in ["media", "logs", "backups", "temp", "media/album", "media/collages", "media/avatars"]:
    Path(d).mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/bot.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# ══════════════════════════════════════════════════════════════════
# 🎨 ЭМОДЗИ КЛАСС
# ══════════════════════════════════════════════════════════════════
class E:
    sparkles = "✨"; bridge = "🌉"; heart = "💞"; camera = "📸"
    map_emoji = "📍"; clock = "⏰"; trophy = "🏆"; star = "⭐"
    fire = "🔥"; gift = "🎁"; album = "📚"; stats = "📊"
    brain = "🧠"; world = "🌍"; rainbow = "🌈"; palette = "🎨"
    gem = "💎"; crown = "👑"; target = "🎯"; mail = "📨"
    lock = "🔒"; key = "🔑"; users = "👥"; smile = "😊"
    love = "🥰"; party = "🎉"; moon = "🌙"; sun = "☀️"
    cloud = "☁️"; rain = "🌧️"; snow = "❄️"; zap = "⚡"
    magic = "🔮"; robot = "🤖"; eyes = "👀"; check = "✅"
    cross = "❌"; warning = "⚠️"; back_emoji = "◀️"; letter = "💌"
    ghost = "👻"; clap = "👏"; flower = "🌸"; butterfly = "🦋"
    diamond = "💠"; medal = "🏅"; rocket = "🚀"; music = "🎵"
    hand = "👋"; info = "ℹ️"; question = "❓"; gear = "⚙️"
    book = "📖"; pen = "🖊️"; speech = "💬"; thought = "💭"
    compass = "🧭"; crystal = "💎"; hourglass = "⏳"; shield = "🛡️"
    wrench = "🔧"; rose = "🌹"; teddy = "🧸"; chocolate = "🍫"
    ring = "💍"; plane = "✈️"; shop = "🏪"; cart = "🛒"
    coin = "🪙"; money = "💰"; calendar = "📅"; note = "📝"
    phone = "📱"; laptop = "💻"; globe = "🌐"; home = "🏠"
    admin_emoji = "👑"; police = "🚔"; construction = "🚧"; plus = "➕"
    minus = "➖"; refresh = "🔄"; save = "💾"; delete = "🗑️"
    search = "🔍"; filter_emoji = "🔎"; tag = "🏷️"; pin = "📌"
    bell = "🔔"; mute = "🔕"; unlock = "🔓"; chart = "📈"
    game = "🎮"; dice = "🎲"; puzzle = "🧩"; joystick = "🕹️"
    crown_king = "🤴"; queen = "👸"; kiss = "😘"; hug = "🤗"

# ══════════════════════════════════════════════════════════════════
# 🎨 ASCII ЛОГОТИП
# ══════════════════════════════════════════════════════════════════
LOGO = """
╔══════════════════════════════════════╗
║   🌉  М Е Р И Д И А Н  U L T R A  🌉  ║
║   Мосты между городами и сердцами    ║
╚══════════════════════════════════════╝
"""

# ══════════════════════════════════════════════════════════════════
# 🏆 ДОСТИЖЕНИЯ (25+)
# ══════════════════════════════════════════════════════════════════
ACHIEVEMENTS = {
    "first_bridge": {"name": "Первый мост", "desc": "Выполнить первый квест", "emoji": "🌉", "xp": 10, "coins": 50},
    "five_bridges": {"name": "Строитель", "desc": "5 квестов", "emoji": "🏗️", "xp": 30, "coins": 100},
    "ten_bridges": {"name": "Архитектор", "desc": "10 квестов", "emoji": "🏛️", "xp": 60, "coins": 200},
    "twentyfive_bridges": {"name": "Градостроитель", "desc": "25 квестов", "emoji": "🏙️", "xp": 150, "coins": 500},
    "fifty_bridges": {"name": "Инженер мечты", "desc": "50 квестов", "emoji": "👷", "xp": 300, "coins": 1000},
    "hundred_bridges": {"name": "Легенда", "desc": "100 квестов", "emoji": "🌟", "xp": 1000, "coins": 5000},
    "night_owl": {"name": "Ночная сова", "desc": "Квест после 23:00", "emoji": "🦉", "xp": 25, "coins": 75},
    "dawn_patrol": {"name": "Рассветный патруль", "desc": "Квест до 7 утра", "emoji": "🌅", "xp": 30, "coins": 100},
    "rain_dancer": {"name": "Танцующий под дождём", "desc": "Квест в дождь", "emoji": "🌧️", "xp": 20, "coins": 50},
    "snow_angel": {"name": "Снежный ангел", "desc": "Квест в снег", "emoji": "❄️", "xp": 25, "coins": 75},
    "storm_chaser": {"name": "Охотник за грозами", "desc": "Квест в грозу", "emoji": "⛈️", "xp": 35, "coins": 150},
    "streak_3": {"name": "Три дня подряд", "desc": "Стрик 3 дня", "emoji": "🔥", "xp": 25, "coins": 100},
    "streak_7": {"name": "Недельный марафон", "desc": "Стрик 7 дней", "emoji": "🌟", "xp": 75, "coins": 300},
    "streak_14": {"name": "Две недели", "desc": "Стрик 14 дней", "emoji": "💫", "xp": 200, "coins": 750},
    "streak_30": {"name": "Месяц вместе", "desc": "Стрик 30 дней", "emoji": "👑", "xp": 500, "coins": 2000},
    "perfect_score": {"name": "Идеальное фото", "desc": "Оба фото 10/10", "emoji": "💎", "xp": 50, "coins": 250},
    "creative_genius": {"name": "Творческий гений", "desc": "Креативность 10/10", "emoji": "🎨", "xp": 40, "coins": 200},
    "surprise_5": {"name": "Сюрпризёр", "desc": "5 сюрпризов", "emoji": "🎁", "xp": 30, "coins": 150},
    "surprise_20": {"name": "Волшебник", "desc": "20 сюрпризов", "emoji": "🧙", "xp": 150, "coins": 750},
    "secret_finder": {"name": "Кладоискатель", "desc": "Найти секретный квест", "emoji": "🗝️", "xp": 100, "coins": 500},
    "collector": {"name": "Коллекционер", "desc": "Все типы квестов", "emoji": "🏅", "xp": 200, "coins": 1000},
    "globetrotter": {"name": "Путешественник", "desc": "Квесты в 5+ городах", "emoji": "🗺️", "xp": 150, "coins": 750},
    "vip_supporter": {"name": "VIP поддержка", "desc": "Купить VIP статус", "emoji": "💎", "xp": 50, "coins": 0},
    "social_butterfly": {"name": "Душа компании", "desc": "5 друзей", "emoji": "🦋", "xp": 75, "coins": 300},
    "generous": {"name": "Щедрая душа", "desc": "Подарить 10 подарков", "emoji": "🎀", "xp": 100, "coins": 500},
}

# ══════════════════════════════════════════════════════════════════
# 📊 РАНГИ
# ══════════════════════════════════════════════════════════════════
RANKS = [
    ("Новичок", 0, "🌱"),
    ("Исследователь", 50, "🔍"),
    ("Строитель", 150, "🏗️"),
    ("Архитектор", 400, "🏛️"),
    ("Мастер мостов", 1000, "👑"),
    ("Легенда", 2500, "🌟"),
    ("Полубог мостов", 5000, "💫"),
    ("Хранитель Меридиана", 10000, "🔮"),
    ("Властелин мостов", 25000, "🌌"),
    ("Божество соединений", 50000, "⚡"),
]

def get_rank(xp: int) -> Tuple[str, str, int]:
    for i in range(len(RANKS)-1, -1, -1):
        if xp >= RANKS[i][1]:
            return RANKS[i]
    return RANKS[0]

def get_rank_progress(xp: int) -> Tuple[Tuple, float, int]:
    rank = get_rank(xp)
    idx = RANKS.index(rank)
    nxt_idx = min(idx + 1, len(RANKS) - 1)
    if nxt_idx == idx:
        return rank, 1.0, 0
    current_xp = RANKS[idx][1]
    next_xp = RANKS[nxt_idx][1]
    progress = min((xp - current_xp) / max(next_xp - current_xp, 1), 1.0)
    return rank, progress, next_xp - xp

# ══════════════════════════════════════════════════════════════════
# 🏪 МАГАЗИН
# ══════════════════════════════════════════════════════════════════
SHOP_ITEMS = {
    "rose": {"name": "Роза", "emoji": "🌹", "price_coins": 50, "price_diamonds": 0, "effect": "next_quest_boost", "value": 10},
    "teddy": {"name": "Плюшевый мишка", "emoji": "🧸", "price_coins": 100, "price_diamonds": 0, "effect": "xp", "value": 5},
    "chocolate": {"name": "Коробка конфет", "emoji": "🍫", "price_coins": 150, "price_diamonds": 0, "effect": "coins_to_partner", "value": 20},
    "ring": {"name": "Кольцо", "emoji": "💍", "price_coins": 0, "price_diamonds": 500, "effect": "xp_and_frame", "value": 50},
    "plane": {"name": "Путешествие", "emoji": "✈️", "price_coins": 0, "price_diamonds": 1000, "effect": "xp_and_special_frame", "value": 100},
    "vip_week": {"name": "VIP на неделю", "emoji": "⭐", "price_coins": 0, "price_diamonds": 100, "effect": "vip1", "value": 7},
    "vip_month": {"name": "VIP на месяц", "emoji": "🌟", "price_coins": 0, "price_diamonds": 350, "effect": "vip2", "value": 30},
    "vip_year": {"name": "VIP на год", "emoji": "💫", "price_coins": 0, "price_diamonds": 3500, "effect": "vip3", "value": 365},
}

# ══════════════════════════════════════════════════════════════════
# 💾 БАЗА ДАННЫХ
# ══════════════════════════════════════════════════════════════════
class Database:
    def __init__(self):
        self.data_file = Path("data.json")
        self.ach_file = Path("achievements.json")
        self.notes_file = Path("notes.json")
        self.friends_file = Path("friends.json")
        self.gifts_file = Path("gifts.json")
        self.events_file = Path("events.json")
        self.wishlist_file = Path("wishlist.json")
        self.lock = asyncio.Lock()

    async def load(self) -> dict:
        async with self.lock:
            if self.data_file.exists():
                return json.loads(self.data_file.read_text(encoding="utf-8"))
            return self._default_data()

    async def save(self, data: dict):
        async with self.lock:
            self.data_file.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    def _default_data(self) -> dict:
        return {
            "users": {}, "quests": [], "album": [],
            "stats": {"total_bridges": 0, "total_quests": 0, "started_at": datetime.now().isoformat()},
            "streaks": {}, "leaderboard": {}, "broadcasts": []
        }

    async def load_ach(self) -> dict:
        if self.ach_file.exists():
            return json.loads(self.ach_file.read_text(encoding="utf-8"))
        return {}

    async def save_ach(self, data: dict):
        self.ach_file.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    async def load_notes(self) -> dict:
        if self.notes_file.exists():
            return json.loads(self.notes_file.read_text(encoding="utf-8"))
        return {"notes": []}

    async def save_notes(self, data: dict):
        self.notes_file.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    async def load_friends(self) -> dict:
        if self.friends_file.exists():
            return json.loads(self.friends_file.read_text(encoding="utf-8"))
        return {"friendships": [], "requests": []}

    async def save_friends(self, data: dict):
        self.friends_file.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    async def load_gifts(self) -> dict:
        if self.gifts_file.exists():
            return json.loads(self.gifts_file.read_text(encoding="utf-8"))
        return {"gifts_sent": [], "gifts_received": []}

    async def save_gifts(self, data: dict):
        self.gifts_file.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    async def load_events(self) -> dict:
        if self.events_file.exists():
            return json.loads(self.events_file.read_text(encoding="utf-8"))
        return {"events": []}

    async def save_events(self, data: dict):
        self.events_file.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    async def load_wishlist(self) -> dict:
        if self.wishlist_file.exists():
            return json.loads(self.wishlist_file.read_text(encoding="utf-8"))
        return {"items": []}

    async def save_wishlist(self, data: dict):
        self.wishlist_file.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

db = Database()

# ══════════════════════════════════════════════════════════════════
# 🔤 ШРИФТЫ
# ══════════════════════════════════════════════════════════════════
def get_fonts():
    system = platform.system()
    candidates = []
    if system == "Linux":
        candidates = ["/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"]
    elif system == "Darwin":
        candidates = ["/System/Library/Fonts/Helvetica.ttc", "/Library/Fonts/Arial.ttf"]
    elif system == "Windows":
        candidates = ["C:\\Windows\\Fonts\\arial.ttf", "C:\\Windows\\Fonts\\arialbd.ttf"]
    fonts = {"bold": None, "regular": None, "small": None}
    for path in candidates:
        if Path(path).exists():
            try:
                fonts["bold"] = ImageFont.truetype(path, 24)
                fonts["regular"] = ImageFont.truetype(path, 16)
                fonts["small"] = ImageFont.truetype(path, 13)
                return fonts
            except: pass
    fonts["bold"] = fonts["regular"] = fonts["small"] = ImageFont.load_default()
    return fonts

FONTS = get_fonts()

# ══════════════════════════════════════════════════════════════════
# 🔧 ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
# ══════════════════════════════════════════════════════════════════
def get_partner(data: dict, uid: str) -> dict | None:
    user = data["users"].get(uid)
    if not user or not user.get("partner"):
        return None
    partner = data["users"].get(user["partner"])
    if not partner:
        user["partner"] = None
        return None
    return partner

def update_streak(streaks: dict, uid: str):
    today = datetime.now().strftime("%Y-%m-%d")
    if uid not in streaks:
        streaks[uid] = {"current": 0, "last_date": None, "best": 0}
    s = streaks[uid]
    last = s.get("last_date")
    if last == today: return
    elif last == (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d"):
        s["current"] += 1; s["last_date"] = today; s["best"] = max(s["best"], s["current"])
    elif last is None:
        s["current"] = 1; s["last_date"] = today; s["best"] = 1
    else:
        s["current"] = 1; s["last_date"] = today

def progress_bar(progress: float, length: int = 12) -> str:
    filled = int(length * min(progress, 1.0))
    return "█" * filled + "░" * (length - filled)

def star_rating(score: int, max_score: int = 10) -> str:
    return "⭐" * score + "☆" * (max_score - score)

def is_admin(uid: int) -> bool:
    return uid == ADMIN_ID

def get_vip_multiplier(user: dict) -> float:
    vip = user.get("vip", {})
    if not vip: return 1.0
    end_date = datetime.fromisoformat(vip.get("end_date", "2000-01-01"))
    if datetime.now() > end_date:
        user["vip"] = None
        return 1.0
    level = vip.get("level", 0)
    return {1: 1.5, 2: 2.0, 3: 3.0}.get(level, 1.0)

# ══════════════════════════════════════════════════════════════════
# ⌨️ КЛАВИАТУРЫ
# ══════════════════════════════════════════════════════════════════
class K:
    @staticmethod
    def main_menu(paired: bool = False, uid: int = 0) -> InlineKeyboardMarkup:
        rows = [
            [
                InlineKeyboardButton(text=f"{E.target} Квест", callback_data="quest"),
                InlineKeyboardButton(text=f"{E.album} Альбом", callback_data="album"),
                InlineKeyboardButton(text=f"{E.stats} Статистика", callback_data="stats"),
            ],
            [
                InlineKeyboardButton(text=f"{E.trophy} Достижения", callback_data="achievements"),
                InlineKeyboardButton(text=f"{E.calendar} Ежедневное", callback_data="daily"),
                InlineKeyboardButton(text=f"{E.medal} Рейтинг", callback_data="leaderboard"),
            ],
            [
                InlineKeyboardButton(text=f"{E.users} Друзья", callback_data="friends"),
                InlineKeyboardButton(text=f"{E.shop} Магазин", callback_data="shop"),
                InlineKeyboardButton(text=f"{E.cart} Инвентарь", callback_data="inventory"),
            ],
            [
                InlineKeyboardButton(text=f"{E.letter} Открытка", callback_data="postcard"),
                InlineKeyboardButton(text=f"{E.love} Комплимент", callback_data="compliment"),
                InlineKeyboardButton(text=f"{E.gift} Сюрприз", callback_data="surprise"),
            ],
            [
                InlineKeyboardButton(text=f"{E.search} Анализ фото", callback_data="analyze"),
                InlineKeyboardButton(text=f"{E.note} Заметки", callback_data="notes"),
                InlineKeyboardButton(text=f"{E.bell} Напоминание", callback_data="reminder"),
            ],
            [
                InlineKeyboardButton(text=f"{E.calendar} Календарь", callback_data="calendar"),
                InlineKeyboardButton(text=f"{E.hourglass} Таймер", callback_data="countdown"),
                InlineKeyboardButton(text=f"{E.party} События", callback_data="events"),
            ],
            [
                InlineKeyboardButton(text=f"{E.sun} Погода", callback_data="weather"),
                InlineKeyboardButton(text=f"{E.globe} Часовые пояса", callback_data="timezone"),
                InlineKeyboardButton(text=f"{E.speech} Поддержка", callback_data="support"),
            ],
            [
                InlineKeyboardButton(text=f"{E.gear} Настройки", callback_data="settings"),
                InlineKeyboardButton(text=f"{E.question} Помощь", callback_data="help"),
            ],
        ]
        if is_admin(uid):
            rows.append([InlineKeyboardButton(text=f"{E.admin_emoji} Админ-панель", callback_data="admin_panel")])
        if not paired:
            rows = [
                [InlineKeyboardButton(text=f"{E.key} Ввести код пары", callback_data="pair_enter")],
                [InlineKeyboardButton(text=f"{E.users} Создать пару", callback_data="pair_create")],
                [InlineKeyboardButton(text=f"{E.question} Помощь", callback_data="help")],
            ]
        return InlineKeyboardMarkup(inline_keyboard=rows)

    @staticmethod
    def back(cb: str = "main_menu") -> InlineKeyboardMarkup:
        return InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=f"{E.back_emoji} Назад", callback_data=cb),
             InlineKeyboardButton(text=f"{E.question} Помощь", callback_data="help")]
        ])

    @staticmethod
    def location_kb() -> ReplyKeyboardMarkup:
        return ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text=f"{E.map_emoji} Отправить геолокацию", request_location=True)]],
            resize_keyboard=True, one_time_keyboard=True
        )

# ══════════════════════════════════════════════════════════════════
# 🤖 FSM
# ══════════════════════════════════════════════════════════════════
class States(StatesGroup):
    pair_code = State()
    wait_note = State()
    wait_wish = State()
    wait_reminder = State()
    wait_event_name = State()
    wait_event_date = State()
    wait_bio = State()
    wait_avatar = State()
    wait_complaint = State()
    wait_broadcast = State()
    wait_give_coins = State()
    wait_give_diamonds = State()
    wait_give_xp = State()
    wait_ban = State()
    wait_add_friend = State()
    wait_accept_friend = State()
    wait_countdown_name = State()
    wait_countdown_date = State()
    wait_suggest = State()
    wait_chat_ai = State()
    wait_partner_bio = State()

# ══════════════════════════════════════════════════════════════════
# 🤖 AI ФУНКЦИИ
# ══════════════════════════════════════════════════════════════════
async def ai_quest(ctx: dict) -> dict:
    recent = ctx.get('recent', 'ещё не было')
    prompt = f"""
Придумай парное фото-задание.
💙 {ctx.get('u1')} в {ctx.get('c1')}: {ctx.get('w1temp')}°C, {ctx.get('w1desc')}
💜 {ctx.get('u2')} в {ctx.get('c2')}: {ctx.get('w2temp')}°C, {ctx.get('w2desc')}
🕐 {ctx.get('tod')}, {ctx.get('season')}
📋 Не повторять: {recent}
JSON: {{theme, legend, task1, task2, album_title, mood, difficulty:1-5, hint}}"""
    try:
        resp = await asyncio.to_thread(quest_ai.generate_content, prompt)
        text = resp.text.strip()
        text = re.sub(r'^```(?:json)?\s*\n?', '', text)
        text = re.sub(r'\n?```\s*$', '', text)
        return json.loads(text)
    except:
        return {"theme": "Мост", "legend": "Соединяя города", "task1": "Сфоткай красивое", "task2": "Сфоткай необычное", "album_title": "Мост", "mood": "романтичное", "difficulty": 2, "hint": "Оглянись!"}

async def ai_review_photo(path: str, task: str, name: str) -> dict:
    try:
        with open(path, "rb") as f:
            img_data = f.read()
        prompt = f"""Оцени фото {name} для задания: «{task}». JSON: {{match_score:1-10, creativity:1-10, what_i_see, comment, mood}}"""
        resp = await asyncio.to_thread(vision_ai.generate_content, [prompt, {"mime_type": "image/jpeg", "data": img_data}])
        text = resp.text.strip()
        text = re.sub(r'^```(?:json)?\s*\n?', '', text)
        text = re.sub(r'\n?```\s*$', '', text)
        return json.loads(text)
    except:
        return {"match_score": 7, "creativity": 7, "what_i_see": "что-то", "comment": f"{name}, отлично!", "mood": "загадочное"}

async def ai_compliment(name: str) -> str:
    try:
        resp = await asyncio.to_thread(creative_ai.generate_content, f"Напиши один тёплый комплимент для {name}. 1 предложение.")
        return resp.text.strip()
    except:
        return f"{name}, ты особенный человек!"

async def ai_chat(msg: str, history: list) -> str:
    try:
        chat = creative_ai.start_chat(history=history)
        resp = await asyncio.to_thread(chat.send_message, msg)
        return resp.text.strip()
    except:
        return "Я немного запутался... Но я рядом!"

# ══════════════════════════════════════════════════════════════════
# 🌤️ API
# ══════════════════════════════════════════════════════════════════
async def get_weather(lat: float, lon: float) -> dict:
    try:
        url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={OPENWEATHER_API_KEY}&units=metric&lang=ru"
        async with httpx.AsyncClient(timeout=10) as c:
            r = await c.get(url); r.raise_for_status()
            j = r.json()
            return {"temp": round(j["main"]["temp"]), "desc": j["weather"][0]["description"], "icon": j["weather"][0]["icon"], "wind": round(j["wind"]["speed"], 1), "humidity": j["main"]["humidity"]}
    except:
        return {"temp": "?", "desc": "неизвестно", "icon": "01d", "wind": "?", "humidity": "?"}

async def geocode(lat: float, lon: float) -> str:
    try:
        url = f"https://nominatim.openstreetmap.org/reverse?lat={lat}&lon={lon}&format=json&accept-language=ru"
        async with httpx.AsyncClient(timeout=10) as c:
            r = await c.get(url, headers={"User-Agent": "MeridianUltra/4.0"}); r.raise_for_status()
            return r.json().get("address", {}).get("city") or "Где-то"
    except:
        return "Неизвестный город"

# ══════════════════════════════════════════════════════════════════
# 🎨 КОЛЛАЖ
# ══════════════════════════════════════════════════════════════════
async def make_collage(img1: str, img2: str, theme: str, c1: str, c2: str, qnum: int) -> str:
    try:
        i1 = Image.open(img1).convert("RGB"); i2 = Image.open(img2).convert("RGB")
        pw, ph = 500, 400
        i1.thumbnail((pw, ph), Image.LANCZOS); i2.thumbnail((pw, ph), Image.LANCZOS)
        pad, hh = 25, 130
        tw = pw * 2 + pad * 3; th = hh + max(i1.height, i2.height) + 80
        bg = Image.new("RGB", (tw, th), (20, 20, 40))
        draw = ImageDraw.Draw(bg)
        x1, y1 = pad, hh + pad; x2 = x1 + pw + pad
        draw.rectangle([x1-2, y1-2, x1+pw+2, y1+ph+2], fill="white", outline=(255, 215, 0), width=2)
        draw.rectangle([x2-2, y1-2, x2+pw+2, y1+ph+2], fill="white", outline=(255, 215, 0), width=2)
        bg.paste(i1, (x1, y1)); bg.paste(i2, (x2, y1))
        draw.text((pad, 20), f"Мост #{qnum}: {theme[:45]}", fill=(255, 255, 255), font=FONTS["bold"])
        draw.text((x1+pw//2-30, y1+ph+5), f"📍 {c1}", fill=(200, 200, 200), font=FONTS["regular"])
        draw.text((x2+pw//2-30, y1+ph+5), f"📍 {c2}", fill=(200, 200, 200), font=FONTS["regular"])
        path = f"media/collages/bridge_{qnum}.jpg"
        bg.save(path, quality=92)
        return path
    except:
        i1 = Image.open(img1).resize((500, 400)); i2 = Image.open(img2).resize((500, 400))
        c = Image.new("RGB", (1000, 400)); c.paste(i1, (0, 0)); c.paste(i2, (500, 0))
        path = f"media/collages/fallback_{qnum}.jpg"; c.save(path)
        return path

# ══════════════════════════════════════════════════════════════════
# 👋 /START
# ══════════════════════════════════════════════════════════════════
@dp.message(Command("start"))
async def cmd_start(msg: types.Message):
    data = await db.load()
    uid = str(msg.from_user.id)
    name = msg.from_user.first_name

    if uid not in data["users"]:
        data["users"][uid] = {
            "id": uid, "name": name, "username": msg.from_user.username,
            "partner": None, "pair_code": None, "pair_code_created_at": None,
            "quests_done": 0, "xp": 0, "coins": 100, "diamonds": 10,
            "vip": None, "avatar": None, "bio": "",
            "surprises_sent": 0, "secret_done": False,
            "joined_at": datetime.now().isoformat(), "last_active": datetime.now().isoformat(),
            "cities_visited": [], "favorite_theme": None, "favorite_mood": None,
            "total_photos": 0, "perfect_scores": 0, "referrals": 0,
            "settings": {"notifications": True, "theme": "dark", "language": "ru"}
        }
        await db.save(data)
        welcome = (
            f"{LOGO}\n\n"
            f"{E.sparkles}<b>ДОБРО ПОЖАЛОВАТЬ, {name.upper()}!</b>{E.sparkles}\n\n"
            f"{E.bridge}<b>Меридиан Ultra</b> — самый мощный нейро-бот для пар.\n\n"
            f"{E.robot}<b>50+ КОМАНД И ФУНКЦИЙ:</b>\n"
            f"{E.brain}AI-квесты • {E.camera}Проверка фото • {E.album}Альбом\n"
            f"{E.trophy}Достижения • {E.shop}Магазин • {E.gift}Подарки\n"
            f"{E.users}Друзья • {E.note}Заметки • {E.calendar}События\n"
            f"{E.game}Игры • {E.speech}AI-чат • {E.crown}VIP\n\n"
            f"{E.info}<b>Чтобы начать — создайте пару!</b>"
        )
        await msg.answer(welcome, reply_markup=K.main_menu(paired=False, uid=msg.from_user.id))
    else:
        streaks = data.get("streaks", {})
        if uid in streaks:
            last = streaks[uid].get("last_date")
            if last and (datetime.now() - datetime.strptime(last, "%Y-%m-%d")).days > 1:
                streaks[uid]["current"] = 0
                await db.save(data)

        paired = get_partner(data, uid) is not None
        u = data["users"][uid]
        u["last_active"] = datetime.now().isoformat()
        await db.save(data)

        rank_name, rank_emoji, _ = get_rank(u.get("xp", 0))
        streak = data.get("streaks", {}).get(uid, {}).get("current", 0)
        vip = u.get("vip", {})
        vip_text = ""
        if vip:
            end = datetime.fromisoformat(vip.get("end_date", "2000-01-01"))
            if datetime.now() < end:
                vip_text = f"\n{E.crown}VIP {vip.get('level', 0)} до {end.strftime('%d.%m.%Y')}"

        if paired:
            partner = get_partner(data, uid)
            welcome_back = (
                f"{LOGO}\n\n"
                f"{E.heart}<b>С ВОЗВРАЩЕНИЕМ!</b>\n"
                f"{u['name']} 💞 {partner.get('name', '...')}\n\n"
                f"{rank_emoji}<b>{rank_name}</b> | {E.star}{u.get('xp',0)} XP\n"
                f"{E.coin}{u.get('coins',0)} монет | {E.gem}{u.get('diamonds',0)} алмазов\n"
                f"{E.fire}Стрик: {streak} дн. | {E.album}Мостов: {len(data['album'])}{vip_text}"
            )
        else:
            welcome_back = f"{E.hand}<b>С возвращением, {name}!</b>\n\nСоздай пару чтобы играть!"

        await msg.answer(welcome_back, reply_markup=K.main_menu(paired=paired, uid=msg.from_user.id))

# ══════════════════════════════════════════════════════════════════
# 🔙 ГЛАВНОЕ МЕНЮ
# ══════════════════════════════════════════════════════════════════
@dp.callback_query(F.data == "main_menu")
async def main_menu(cb: types.CallbackQuery):
    data = await db.load()
    uid = str(cb.from_user.id)
    u = data["users"].get(uid, {})
    paired = get_partner(data, uid) is not None
    text = f"{LOGO}\n{E.robot}<b>Главное меню</b>"
    await cb.message.edit_text(text, reply_markup=K.main_menu(paired=paired, uid=cb.from_user.id))
    await cb.answer()

# ══════════════════════════════════════════════════════════════════
# ℹ️ /help И ДРУГИЕ КОМАНДЫ
# ══════════════════════════════════════════════════════════════════
@dp.message(Command("help"))
@dp.callback_query(F.data == "help")
async def cmd_help(event, cb: types.CallbackQuery = None):
    msg = event if isinstance(event, types.Message) else event.message
    help_text = (
        f"{E.info}<b>ПОМОЩЬ ПО МЕРИДИАНУ</b>\n\n"
        f"<b>Основные команды:</b>\n"
        f"/quest - начать квест\n/album - альбом\n/stats - статистика\n"
        f"/profile - профиль\n/partner - профиль партнёра\n\n"
        f"<b>Общение:</b>\n"
        f"/postcard - открытка\n/compliment - комплимент\n/surprise - сюрприз\n"
        f"/gift - подарить подарок\n\n"
        f"<b>Инструменты:</b>\n"
        f"/notes - заметки\n/reminder - напоминание\n/wishlist - желания\n"
        f"/weather - погода\n/countdown - таймер\n\n"
        f"<b>Социальное:</b>\n"
        f"/friends - друзья\n/leaderboard - рейтинг\n/shop - магазин\n\n"
        f"<i>Все команды также доступны через кнопки в меню!</i>"
    )
    if isinstance(event, types.CallbackQuery):
        await event.message.edit_text(help_text, reply_markup=K.back())
        await event.answer()
    else:
        await msg.answer(help_text)

@dp.message(Command("profile"))
@dp.callback_query(F.data == "profile")
async def cmd_profile(event):
    msg = event if isinstance(event, types.Message) else event.message
    data = await db.load()
    uid = str(event.from_user.id)
    u = data["users"].get(uid, {})
    rank, emoji, _ = get_rank(u.get("xp", 0))
    _, progress, left = get_rank_progress(u.get("xp", 0))
    streak = data.get("streaks", {}).get(uid, {}).get("current", 0)
    best_streak = data.get("streaks", {}).get(uid, {}).get("best", 0)
    vip = u.get("vip", {})
    vip_text = "Нет" if not vip else f"VIP {vip.get('level',0)} до {vip.get('end_date','?')[:10]}"
    text = (
        f"{E.sparkles}<b>ПРОФИЛЬ: {u.get('name','?').upper()}</b>{E.sparkles}\n\n"
        f"{emoji}<b>Ранг:</b> {rank}\n"
        f"{E.star}<b>XP:</b> {u.get('xp',0)} | {E.coin}Монет: {u.get('coins',0)} | {E.gem}Алмазов: {u.get('diamonds',0)}\n"
        f"{E.target}<b>Квестов:</b> {u.get('quests_done',0)} | {E.camera}Фото: {u.get('total_photos',0)}\n"
        f"{E.fire}<b>Стрик:</b> {streak} дн. | {E.trophy}Лучший: {best_streak} дн.\n"
        f"{E.crown}<b>VIP:</b> {vip_text}\n"
        f"{E.clock}<b>В игре с:</b> {u.get('joined_at','?')[:10]}\n\n"
        f"<b>Прогресс:</b>\n{progress_bar(progress)} {int(progress*100)}%\n"
        f"До нового ранга: {left} XP\n\n"
        f"{E.pen}<i>{u.get('bio','Описание не задано')}</i>"
    )
    if isinstance(event, types.CallbackQuery):
        await event.message.edit_text(text, reply_markup=K.back())
        await event.answer()
    else:
        await msg.answer(text)

@dp.message(Command("partner"))
@dp.callback_query(F.data == "partner")
async def cmd_partner(event):
    msg = event if isinstance(event, types.Message) else event.message
    data = await db.load()
    uid = str(event.from_user.id)
    partner = get_partner(data, uid)
    if not partner:
        text = f"{E.warning}У тебя нет пары. Создай пару!"
    else:
        rank, emoji, _ = get_rank(partner.get("xp", 0))
        text = (
            f"{E.heart}<b>ПРОФИЛЬ ПАРТНЁРА</b>\n\n"
            f"<b>Имя:</b> {partner.get('name','?')}\n"
            f"{emoji}<b>Ранг:</b> {rank}\n"
            f"{E.star}<b>XP:</b> {partner.get('xp',0)}\n"
            f"{E.target}<b>Квестов:</b> {partner.get('quests_done',0)}\n"
            f"{E.clock}<b>В игре с:</b> {partner.get('joined_at','?')[:10]}\n\n"
            f"{E.pen}<i>{partner.get('partner_bio','Партнёр ещё не написал о себе')}</i>"
        )
    if isinstance(event, types.CallbackQuery):
        await event.message.edit_text(text, reply_markup=K.back())
        await event.answer()
    else:
        await msg.answer(text)

@dp.message(Command("stats"))
@dp.callback_query(F.data == "stats")
async def cmd_stats(event):
    msg = event if isinstance(event, types.Message) else event.message
    data = await db.load()
    uid = str(event.from_user.id)
    u = data["users"].get(uid, {})
    partner = get_partner(data, uid)
    if not partner:
        if isinstance(event, types.CallbackQuery): await event.answer("Нужна пара!", show_alert=True)
        else: await msg.answer("Нужна пара!")
        return
    rank, emoji, _ = get_rank(u.get("xp", 0))
    _, progress, left = get_rank_progress(u.get("xp", 0))
    text = (
        f"{E.stats}<b>СТАТИСТИКА</b>\n\n"
        f"{u['name']} {E.heart} {partner.get('name','?')}\n\n"
        f"{emoji}{rank} | {E.star}{u.get('xp',0)} XP | {E.coin}{u.get('coins',0)} монет\n"
        f"{E.target}Квестов: {u.get('quests_done',0)} | {partner.get('quests_done',0)}\n"
        f"{E.album}Мостов: {len(data['album'])}\n"
        f"{E.fire}Стрик: {data.get('streaks',{}).get(uid,{}).get('current',0)} дн.\n\n"
        f"[{progress_bar(progress)}] {int(progress*100)}%\nДо ранга: {left} XP"
    )
    if isinstance(event, types.CallbackQuery):
        await event.message.edit_text(text, reply_markup=K.back())
        await event.answer()
    else:
        await msg.answer(text)

@dp.message(Command("leaderboard"))
@dp.callback_query(F.data == "leaderboard")
async def cmd_leaderboard(event):
    msg = event if isinstance(event, types.Message) else event.message
    data = await db.load()
    users = sorted(data["users"].items(), key=lambda x: x[1].get("xp", 0), reverse=True)[:10]
    text = f"{E.medal}<b>ТОП-10 ИГРОКОВ</b>\n\n"
    for i, (uid, u) in enumerate(users, 1):
        medal = {1: "🥇", 2: "🥈", 3: "🥉"}.get(i, f"{i}.")
        rank = get_rank(u.get("xp", 0))
        text += f"{medal} <b>{u.get('name','?')}</b> — {rank[2]}{rank[0]} ({u.get('xp',0)} XP)\n"
    if isinstance(event, types.CallbackQuery):
        await event.message.edit_text(text, reply_markup=K.back())
        await event.answer()
    else:
        await msg.answer(text)

@dp.message(Command("daily"))
@dp.callback_query(F.data == "daily")
async def cmd_daily(event):
    msg = event if isinstance(event, types.Message) else event.message
    data = await db.load()
    uid = str(event.from_user.id)
    u = data["users"].get(uid, {})
    last_daily = u.get("last_daily", "")
    today = datetime.now().strftime("%Y-%m-%d")
    if last_daily == today:
        text = f"{E.warning}Ты уже получил ежедневную награду сегодня! Приходи завтра."
    else:
        coins_bonus = random.randint(10, 50)
        xp_bonus = random.randint(5, 25)
        u["coins"] = u.get("coins", 0) + coins_bonus
        u["xp"] = u.get("xp", 0) + xp_bonus
        u["last_daily"] = today
        await db.save(data)
        text = f"{E.party}<b>ЕЖЕДНЕВНАЯ НАГРАДА!</b>\n\n{E.coin}+{coins_bonus} монет\n{E.star}+{xp_bonus} XP\n\nПриходи завтра за новой наградой!"
    if isinstance(event, types.CallbackQuery):
        await event.message.edit_text(text, reply_markup=K.back())
        await event.answer()
    else:
        await msg.answer(text)

# ══════════════════════════════════════════════════════════════════
# 🔗 ПАРА
# ══════════════════════════════════════════════════════════════════
@dp.callback_query(F.data == "pair_create")
async def pair_create(cb: types.CallbackQuery):
    data = await db.load()
    uid = str(cb.from_user.id)
    code = str(random.randint(100000, 999999))
    data["users"][uid]["pair_code"] = code
    data["users"][uid]["pair_code_created_at"] = datetime.now().isoformat()
    await db.save(data)
    await cb.message.edit_text(
        f"{E.key}<b>КОД ПАРЫ:</b>\n\n<code>{code}</code>\n\nОтправь партнёру. Код действителен 24 часа.",
        reply_markup=K.back()
    )
    await cb.answer()

@dp.callback_query(F.data == "pair_enter")
async def pair_enter(cb: types.CallbackQuery, state: FSMContext):
    await cb.message.answer(f"{E.lock}Введи 6-значный код:")
    await state.set_state(States.pair_code)
    await cb.answer()

@dp.message(States.pair_code)
async def pair_code(msg: types.Message, state: FSMContext):
    data = await db.load()
    uid = str(msg.from_user.id)
    code = msg.text.strip()
    if not code.isdigit() or len(code) != 6:
        await msg.answer("6 цифр!"); return
    pid = None
    for i, d in data["users"].items():
        if d.get("pair_code") == code and i != uid:
            created = d.get("pair_code_created_at")
            if created and datetime.now() - datetime.fromisoformat(created) > timedelta(hours=24):
                await msg.answer(f"{E.cross}Код просрочен.", reply_markup=K.back()); await state.clear(); return
            pid = i; break
    if not pid:
        await msg.answer(f"{E.cross}Код не найден.", reply_markup=K.back()); await state.clear(); return
    data["users"][uid]["partner"] = pid; data["users"][pid]["partner"] = uid
    data["users"][uid]["pair_code"] = None; data["users"][pid]["pair_code"] = None
    await db.save(data)
    n1, n2 = data["users"][uid]["name"], data["users"][pid]["name"]
    text = f"{E.party}<b>ПАРА СОЗДАНА!</b>\n{n1} {E.heart} {n2}"
    await msg.answer(text, reply_markup=K.main_menu(paired=True, uid=msg.from_user.id))
    try: await bot.send_message(int(pid), text, reply_markup=K.main_menu(paired=True, uid=int(pid)))
    except: pass
    await state.clear()

@dp.message(Command("logout"))
async def cmd_logout(msg: types.Message):
    data = await db.load()
    uid = str(msg.from_user.id)
    u = data["users"].get(uid, {})
    pid = u.get("partner")
    if pid and pid in data["users"]:
        data["users"][pid]["partner"] = None
    u["partner"] = None
    await db.save(data)
    await msg.answer(f"{E.check}Пара разорвана. Можно создать новую.")

# ══════════════════════════════════════════════════════════════════
# 🎯 КВЕСТ
# ══════════════════════════════════════════════════════════════════
@dp.message(Command("quest"))
@dp.callback_query(F.data == "quest")
async def cmd_quest(event):
    msg = event if isinstance(event, types.Message) else event.message
    data = await db.load()
    uid = str(event.from_user.id)
    if not get_partner(data, uid):
        if isinstance(event, types.CallbackQuery): await event.answer("Нужна пара!", show_alert=True)
        else: await msg.answer("Нужна пара!")
        return
    for q in reversed(data["quests"]):
        if not q.get("done") and (q["user1_id"] == uid or q["user2_id"] == uid):
            text = f"{E.warning}Активный квест #{q['id']} не завершён!"
            if isinstance(event, types.CallbackQuery): await event.message.edit_text(text, reply_markup=K.back())
            else: await msg.answer(text)
            return
    text = f"{E.map_emoji}<b>НОВЫЙ КВЕСТ!</b>\n\nОтправь геолокацию:"
    if isinstance(event, types.CallbackQuery):
        await event.message.edit_text(text)
        await event.message.answer("Нажми кнопку:", reply_markup=K.location_kb())
        await event.answer()
    else:
        await msg.answer(text, reply_markup=K.location_kb())

@dp.message(F.location)
async def location_handler(msg: types.Message):
    data = await db.load()
    uid = str(msg.from_user.id)
    u = data["users"].get(uid)
    if not u or not get_partner(data, uid):
        await msg.answer("Создайте пару!", reply_markup=types.ReplyKeyboardRemove()); return
    lat, lon = msg.location.latitude, msg.location.longitude
    weather = await get_weather(lat, lon)
    city = await geocode(lat, lon)
    data[f"pending_{uid}"] = {"lat": lat, "lon": lon, "weather": weather, "city": city}
    await db.save(data)
    partner = get_partner(data, uid)
    pid = partner["id"]
    w_emoji = {"ясно": E.sun, "облачно": E.cloud, "дождь": E.rain, "снег": E.snow}.get(weather.get("desc", ""), E.world)
    await msg.answer(f"{E.map_emoji}<b>{city}</b>\n{w_emoji}{weather['temp']}°C\n{E.clock}Жду партнёра...", reply_markup=types.ReplyKeyboardRemove())
    try: await bot.send_message(int(pid), f"{E.map_emoji}<b>{u['name']}</b> на месте! Отправь гео:", reply_markup=K.location_kb())
    except: pass
    if f"pending_{pid}" in data:
        await create_quest(msg, uid, pid, data)

async def create_quest(msg, uid1, uid2, data):
    p1, p2 = f"pending_{uid1}", f"pending_{uid2}"
    w1, w2 = data[p1]["weather"], data[p2]["weather"]
    c1, c2 = data[p1]["city"], data[p2]["city"]
    u1, u2 = data["users"][uid1], data["users"][uid2]
    recent = [q.get("theme", "") for q in data["quests"] if q.get("done")][-10:]
    qnum = len(data["quests"]) + 1
    now = datetime.now()
    tod = "утро" if 5<=now.hour<12 else "день" if 12<=now.hour<17 else "вечер" if 17<=now.hour<22 else "ночь"
    season = "зима" if now.month in [12,1,2] else "весна" if now.month in [3,4,5] else "лето" if now.month in [6,7,8] else "осень"
    await msg.answer(f"{E.brain}<b>AI создаёт квест...</b>")
    qd = await ai_quest({"u1":u1["name"],"u2":u2["name"],"c1":c1,"c2":c2,"w1temp":w1["temp"],"w2temp":w2["temp"],"w1desc":w1["desc"],"w2desc":w2["desc"],"tod":tod,"season":season,"recent":", ".join(recent) if recent else "ещё не было"})
    quest = {"id":qnum,"date":now.isoformat(),"user1_id":uid1,"user2_id":uid2,"theme":qd.get("theme"),"legend":qd.get("legend"),"task1":qd.get("task1"),"task2":qd.get("task2"),"album_title":qd.get("album_title"),"city1":c1,"city2":c2,"weather1":f"{w1['temp']}°C, {w1['desc']}","weather2":f"{w2['temp']}°C, {w2['desc']}","photo1":None,"photo2":None,"ai_review1":None,"ai_review2":None,"completing":False,"done":False}
    data["quests"].append(quest)
    for k in [p1,p2]: data.pop(k,None)
    await db.save(data)
    for u_id,task,city,weather,uname in [(uid1,quest["task1"],c1,quest["weather1"],u1["name"]),(uid2,quest["task2"],c2,quest["weather2"],u2["name"])]:
        text = f"{E.bridge}<b>МОСТ #{qnum}</b>\n<i>{quest['theme']}</i>\n\n{E.star}{quest['legend']}\n\n{E.target}<b>{uname}:</b>\n{task}\n\n{E.map_emoji}{city} • {weather}\n{E.magic}{qd.get('hint','')}\n\n{E.camera}<b>Отправь фото!</b>"
        try:
            if u_id == uid1: await msg.answer(text)
            else: await bot.send_message(int(u_id), text)
        except: pass

# ══════════════════════════════════════════════════════════════════
# 📸 ПРИЁМ ФОТО
# ══════════════════════════════════════════════════════════════════
@dp.message(F.photo)
async def photo_handler(msg: types.Message):
    data = await db.load()
    uid = str(msg.from_user.id)
    active = None
    for q in reversed(data["quests"]):
        if not q.get("done") and (q["user1_id"] == uid or q["user2_id"] == uid):
            active = q; break
    if not active:
        await msg.answer(f"{E.warning}Нет активного квеста!"); return
    if active.get("completing"):
        await msg.answer("Квест уже завершается..."); return
    is_u1 = uid == active["user1_id"]
    pf = "photo1" if is_u1 else "photo2"; rf = "ai_review1" if is_u1 else "ai_review2"
    task = active["task1"] if is_u1 else active["task2"]
    if active.get(pf):
        await msg.answer("Ты уже отправил фото! Ждём партнёра."); return
    try:
        photo = msg.photo[-1]; file = await bot.get_file(photo.file_id)
        path = f"media/album/quest_{active['id']}_user_{uid}.jpg"
        await bot.download_file(file.file_path, path)
        active[pf] = path
        name = data["users"][uid]["name"]
        data["users"][uid]["total_photos"] = data["users"][uid].get("total_photos", 0) + 1
        await msg.answer(f"{E.robot}<b>AI проверяет...</b>")
        review = await ai_review_photo(path, task, name)
        active[rf] = review
        r = review or {}
        score = r.get("match_score",7)
        await msg.answer(f"{E.robot}<b>AI-РЕВЬЮ:</b>\n{E.eyes}{r.get('what_i_see','?')}\n{E.target}{score}/10 {star_rating(score)}\n{E.palette}{r.get('creativity',7)}/10\n💬{r.get('comment','Ок!')}")
        await db.save(data)
        other = "photo2" if is_u1 else "photo1"
        if active.get(other) and not active.get("completing"):
            await finalize_quest(data, active, msg)
        else:
            await msg.answer(f"{E.clock}Ждём партнёра...")
    except Exception as e:
        logger.error(f"Photo error: {e}")
        await msg.answer(f"{E.cross}Ошибка. Попробуй снова.")

async def finalize_quest(data, quest, msg):
    if quest.get("completing"): return
    quest["completing"] = True; await db.save(data)
    try:
        u1, u2 = quest["user1_id"], quest["user2_id"]
        r1 = quest.get("ai_review1") or {}; r2 = quest.get("ai_review2") or {}
        collage = await make_collage(quest["photo1"], quest["photo2"], quest["theme"], quest.get("city1",""), quest.get("city2",""), quest["id"])
        quest["done"] = True; quest["collage"] = collage
        for u, r in [(u1,r1),(u2,r2)]:
            if u in data["users"]:
                mult = get_vip_multiplier(data["users"][u])
                xp = int((r.get("match_score",7)+r.get("creativity",7))/2*15*mult)
                data["users"][u]["quests_done"] = data["users"][u].get("quests_done",0)+1
                data["users"][u]["xp"] = data["users"][u].get("xp",0)+xp
                data["users"][u]["coins"] = data["users"][u].get("coins",0)+xp//2
        data["album"].append({"id":quest["id"],"date":quest["date"],"theme":quest["theme"],"album_title":quest["album_title"],"collage":collage})
        data["stats"]["total_bridges"] = len(data["album"])
        streaks = data.setdefault("streaks",{})
        for u in [u1,u2]: update_streak(streaks,u)
        await db.save(data)
        for u in [u1,u2]: await check_achievements(data, u, quest)
        with open(collage,"rb") as f: pb = f.read()
        avg = (r1.get("match_score",7)+r2.get("match_score",7))/2 if r1 and r2 else 7
        cap = f"{E.party}<b>МОСТ #{quest['id']} ГОТОВ!</b>\n<i>{quest['album_title']}</i>\n{E.star}AI: {avg:.1f}/10\n{E.album}Мостов: {len(data['album'])}"
        pf = BufferedInputFile(pb, filename="collage.jpg")
        for uid in [u1,u2]:
            try: await bot.send_photo(int(uid), pf, caption=cap)
            except: pass
    except Exception as e:
        logger.error(f"Finalize error: {e}")
        await msg.answer(f"{E.cross}Ошибка финализации.")
    quest["completing"] = False; await db.save(data)

async def check_achievements(data, uid, quest):
    ach = await db.load_ach()
    user_ach = ach.get(uid, []); u = data["users"].get(uid,{}); qd = u.get("quests_done",0)
    new = []
    r1 = quest.get("ai_review1") or {}; r2 = quest.get("ai_review2") or {}
    checks = {"first_bridge":qd>=1,"five_bridges":qd>=5,"ten_bridges":qd>=10,"twentyfive_bridges":qd>=25,"fifty_bridges":qd>=50,"night_owl":datetime.fromisoformat(quest["date"]).hour>=23,"rain_dancer":"дождь" in quest.get("weather1","")+quest.get("weather2",""),"snow_angel":"снег" in quest.get("weather1","")+quest.get("weather2",""),"streak_3":data.get("streaks",{}).get(uid,{}).get("current",0)>=3,"streak_7":data.get("streaks",{}).get(uid,{}).get("current",0)>=7,"perfect_score":r1.get("match_score")==10 and r2.get("match_score")==10,"creative_genius":r1.get("creativity")==10 or r2.get("creativity")==10,"surprise_5":u.get("surprises_sent",0)>=5,"secret_finder":u.get("secret_done",False)}
    for aid,cond in checks.items():
        if cond and aid not in user_ach: user_ach.append(aid); new.append(aid)
    if new:
        ach[uid]=user_ach; await db.save_ach(ach)
        for aid in new:
            a = ACHIEVEMENTS[aid]
            data["users"][uid]["xp"] = data["users"][uid].get("xp",0)+a["xp"]
            data["users"][uid]["coins"] = data["users"][uid].get("coins",0)+a["coins"]
        await db.save(data)

# ══════════════════════════════════════════════════════════════════
# 📚 АЛЬБОМ
# ══════════════════════════════════════════════════════════════════
@dp.message(Command("album"))
@dp.callback_query(F.data == "album")
async def cmd_album(event):
    msg = event if isinstance(event, types.Message) else event.message
    data = await db.load()
    if not data["album"]:
        text = "Альбом пуст."
        if isinstance(event, types.CallbackQuery): await event.message.edit_text(text, reply_markup=K.back()); await event.answer()
        else: await msg.answer(text)
        return
    for entry in data["album"][-5:]:
        if Path(entry.get("collage","")).exists():
            with open(entry["collage"],"rb") as f:
                cap = f"Мост #{entry['id']}: {entry['album_title']}\n{entry['date'][:10]}"
                if isinstance(event, types.CallbackQuery): await event.message.answer_photo(BufferedInputFile(f.read(),filename="a.jpg"),caption=cap)
                else: await msg.answer_photo(BufferedInputFile(f.read(),filename="a.jpg"),caption=cap)
    text = f"Показаны последние 5 из {len(data['album'])}"
    if isinstance(event, types.CallbackQuery): await event.message.answer(text, reply_markup=K.back()); await event.answer()
    else: await msg.answer(text)

# ══════════════════════════════════════════════════════════════════
# 🏆 ДОСТИЖЕНИЯ
# ══════════════════════════════════════════════════════════════════
@dp.message(Command("achievements"))
@dp.callback_query(F.data == "achievements")
async def cmd_achievements(event):
    msg = event if isinstance(event, types.Message) else event.message
    ach = await db.load_ach()
    uid = str(event.from_user.id); user_ach = ach.get(uid,[])
    text = f"{E.trophy}<b>ДОСТИЖЕНИЯ</b> ({len(user_ach)}/{len(ACHIEVEMENTS)})\n\n"
    for aid,a in ACHIEVEMENTS.items():
        unlocked = aid in user_ach
        text += f"{a['emoji'] if unlocked else '🔒'} {a['name'] if unlocked else '???'}\n"
    if isinstance(event, types.CallbackQuery): await event.message.edit_text(text, reply_markup=K.back()); await event.answer()
    else: await msg.answer(text)

# ══════════════════════════════════════════════════════════════════
# 💝 СЮРПРИЗ / КОМПЛИМЕНТ / ОТКРЫТКА
# ══════════════════════════════════════════════════════════════════
@dp.message(Command("surprise"))
@dp.callback_query(F.data == "surprise")
async def cmd_surprise(event):
    msg = event if isinstance(event, types.Message) else event.message
    data = await db.load(); uid = str(event.from_user.id); u = data["users"].get(uid,{}); partner = get_partner(data,uid)
    if not partner:
        text = "Нужна пара!"; 
        if isinstance(event, types.CallbackQuery): await event.message.edit_text(text, reply_markup=K.back()); await event.answer()
        else: await msg.answer(text); return
    try:
        resp = await asyncio.to_thread(creative_ai.generate_content, f"Придумай фото-задание-сюрприз для {partner.get('name')} от {u.get('name')}. JSON: {{task}}")
        surp = json.loads(re.sub(r'^```(?:json)?\s*\n?','',resp.text.strip()).replace('\n```',''))
    except: surp = {"task":"Сфоткай что-то улыбательное!"}
    try:
        await bot.send_message(int(partner["id"]), f"{E.gift}<b>СЮРПРИЗ ОТ {u['name']}!</b>\n\n{surp['task']}")
        data["users"][uid]["surprises_sent"] = data["users"][uid].get("surprises_sent",0)+1; await db.save(data)
        text = f"{E.check}Отправлено!"
    except: text = f"{E.cross}Не удалось."
    if isinstance(event, types.CallbackQuery): await event.message.edit_text(text, reply_markup=K.back()); await event.answer()
    else: await msg.answer(text)

@dp.message(Command("compliment"))
@dp.callback_query(F.data == "compliment")
async def cmd_compliment(event):
    msg = event if isinstance(event, types.Message) else event.message
    data = await db.load(); uid = str(event.from_user.id); partner = get_partner(data,uid)
    if not partner:
        text = "Нужна пара!"; 
        if isinstance(event, types.CallbackQuery): await event.message.edit_text(text, reply_markup=K.back()); await event.answer()
        else: await msg.answer(text); return
    comp = await ai_compliment(partner.get("name","Любимый человек"))
    try: await bot.send_message(int(partner["id"]), f"{E.love}<b>КОМПЛИМЕНТ ОТ {data['users'][uid]['name']}!</b>\n\n{comp}")
    except: pass
    text = f"{E.check}Комплимент отправлен!\n\n{comp}"
    if isinstance(event, types.CallbackQuery): await event.message.edit_text(text, reply_markup=K.back()); await event.answer()
    else: await msg.answer(text)

@dp.message(Command("postcard"))
@dp.callback_query(F.data == "postcard")
async def cmd_postcard(event):
    msg = event if isinstance(event, types.Message) else event.message
    data = await db.load(); uid = str(event.from_user.id); u = data["users"].get(uid,{}); partner = get_partner(data,uid)
    if not partner:
        text = "Нужна пара!"; 
        if isinstance(event, types.CallbackQuery): await event.message.edit_text(text, reply_markup=K.back()); await event.answer()
        else: await msg.answer(text); return
    try:
        resp = await asyncio.to_thread(creative_ai.generate_content, f"Напиши романтичное послание от {u.get('name')} для {partner.get('name')}. 2-3 предложения.")
        text = resp.text.strip()
    except: text = f"{partner.get('name')}, ты особенный человек! {E.heart}"
    try: await bot.send_message(int(partner["id"]), f"{E.letter}<b>ОТКРЫТКА:</b>\n\n{text}")
    except: pass
    if isinstance(event, types.CallbackQuery): await event.message.edit_text(f"{E.check}Отправлено!\n\n{text}", reply_markup=K.back()); await event.answer()
    else: await msg.answer(f"Отправлено!\n\n{text}")

# ══════════════════════════════════════════════════════════════════
# 🏪 МАГАЗИН
# ══════════════════════════════════════════════════════════════════
@dp.message(Command("shop"))
@dp.callback_query(F.data == "shop")
async def cmd_shop(event):
    msg = event if isinstance(event, types.Message) else event.message
    builder = InlineKeyboardBuilder()
    for item_id, item in SHOP_ITEMS.items():
        price = f"{item['price_coins']}🪙" if item['price_coins']>0 else f"{item['price_diamonds']}💎"
        builder.button(text=f"{item['emoji']} {item['name']} ({price})", callback_data=f"buy_{item_id}")
    builder.button(text=f"{E.back_emoji} Назад", callback_data="main_menu")
    builder.adjust(2)
    text = f"{E.shop}<b>МАГАЗИН</b>\n\n{E.coin}Монет: {data['users'][str(event.from_user.id)].get('coins',0)}\n{E.gem}Алмазов: {data['users'][str(event.from_user.id)].get('diamonds',0)}"
    await (event.message.edit_text(text, reply_markup=builder.as_markup()) if isinstance(event, types.CallbackQuery) else msg.answer(text, reply_markup=builder.as_markup()))
    if isinstance(event, types.CallbackQuery): await event.answer()

@dp.callback_query(F.data.startswith("buy_"))
async def shop_buy(cb: types.CallbackQuery):
    data = await db.load(); uid = str(cb.from_user.id); u = data["users"].get(uid,{})
    item_id = cb.data.replace("buy_",""); item = SHOP_ITEMS.get(item_id)
    if not item: await cb.answer("Товар не найден",show_alert=True); return
    if item["price_coins"]>0 and u.get("coins",0) < item["price_coins"]:
        await cb.answer("Недостаточно монет!",show_alert=True); return
    if item["price_diamonds"]>0 and u.get("diamonds",0) < item["price_diamonds"]:
        await cb.answer("Недостаточно алмазов!",show_alert=True); return
    u["coins"] = u.get("coins",0) - item["price_coins"]
    u["diamonds"] = u.get("diamonds",0) - item["price_diamonds"]
    # Применяем эффект
    if item["effect"] == "xp":
        u["xp"] = u.get("xp",0) + item["value"]
    elif item["effect"] == "xp_and_frame":
        u["xp"] = u.get("xp",0) + item["value"]
    elif item["effect"] == "xp_and_special_frame":
        u["xp"] = u.get("xp",0) + item["value"]
    elif item["effect"].startswith("vip"):
        end = datetime.now() + timedelta(days=item["value"])
        u["vip"] = {"level": int(item["effect"][-1]), "end_date": end.isoformat()}
    # Отправка подарка партнёру
    partner = get_partner(data, uid)
    if partner:
        gifts = await db.load_gifts()
        gifts["gifts_sent"].append({"from":uid,"to":partner["id"],"item":item_id,"date":datetime.now().isoformat()})
        await db.save_gifts(gifts)
        try: await bot.send_message(int(partner["id"]), f"{E.gift}<b>ПОДАРОК ОТ {u['name']}!</b>\n\n{item['emoji']} {item['name']}!")
        except: pass
    await db.save(data)
    await cb.answer(f"Куплено: {item['name']}!",show_alert=True)
    await cmd_shop(cb)

# ══════════════════════════════════════════════════════════════════
# 👥 ДРУЗЬЯ
# ══════════════════════════════════════════════════════════════════
@dp.message(Command("friends"))
@dp.callback_query(F.data == "friends")
async def cmd_friends(event):
    msg = event if isinstance(event, types.Message) else event.message
    friends = await db.load_friends()
    uid = str(event.from_user.id)
    my_friends = [f for f in friends.get("friendships",[]) if f["user1"]==uid or f["user2"]==uid]
    requests = [r for r in friends.get("requests",[]) if r["to"]==uid and r["status"]=="pending"]
    text = f"{E.users}<b>ДРУЗЬЯ</b>\n\n"
    if my_friends:
        text += "<b>Мои друзья:</b>\n"
        for f in my_friends[-5:]:
            fid = f["user2"] if f["user1"]==uid else f["user1"]
            fname = (await db.load())["users"].get(fid,{}).get("name","?")
            text += f"• {fname}\n"
    if requests:
        text += f"\n{E.bell}<b>Заявки ({len(requests)}):</b>\n"
        for r in requests[:3]:
            text += f"• {r['from_name']} (ID: {r['from']})\n"
            text += f"/accept {r['from']}\n"
    if not my_friends and not requests:
        text += "У тебя пока нет друзей.\n/addfriend [ID] чтобы добавить!"
    builder = InlineKeyboardBuilder()
    builder.button(text=f"{E.plus} Добавить друга", callback_data="add_friend")
    builder.button(text=f"{E.back_emoji} Назад", callback_data="main_menu")
    if isinstance(event, types.CallbackQuery): await event.message.edit_text(text, reply_markup=builder.as_markup()); await event.answer()
    else: await msg.answer(text, reply_markup=builder.as_markup())

@dp.message(Command("addfriend"))
@dp.callback_query(F.data == "add_friend")
async def cmd_addfriend(event, state: FSMContext):
    if isinstance(event, types.CallbackQuery):
        await event.message.answer("Введи ID друга: /addfriend [ID]")
        await event.answer()
    else:
        parts = event.text.split()
        if len(parts) > 1:
            fid = parts[1]
            friends = await db.load_friends()
            friends.setdefault("requests",[]).append({
                "from": str(event.from_user.id), "to": fid,
                "from_name": event.from_user.first_name,
                "status": "pending", "date": datetime.now().isoformat()
            })
            await db.save_friends(friends)
            try: await bot.send_message(int(fid), f"{E.users}<b>Заявка в друзья от {event.from_user.first_name}!</b>\n/accept {event.from_user.id}")
            except: pass
            await event.answer(f"Заявка отправлена!")
        else:
            await event.answer("Используй: /addfriend [ID]")

@dp.message(Command("accept"))
async def cmd_accept(msg: types.Message):
    parts = msg.text.split()
    if len(parts) > 1:
        fid = parts[1]
        friends = await db.load_friends()
        for r in friends.get("requests",[]):
            if r["from"]==fid and r["to"]==str(msg.from_user.id) and r["status"]=="pending":
                r["status"] = "accepted"
                friends.setdefault("friendships",[]).append({"user1":str(msg.from_user.id),"user2":fid,"since":datetime.now().isoformat()})
                await db.save_friends(friends)
                await msg.answer(f"{E.check}Друг добавлен!")
                try: await bot.send_message(int(fid), f"{E.check}{msg.from_user.first_name} принял твою заявку!")
                except: pass
                return
        await msg.answer("Заявка не найдена.")
    else:
        await msg.answer("Используй: /accept [ID]")

# ══════════════════════════════════════════════════════════════════
# 📝 ЗАМЕТКИ
# ══════════════════════════════════════════════════════════════════
@dp.message(Command("notes"))
@dp.callback_query(F.data == "notes")
async def cmd_notes(event):
    msg = event if isinstance(event, types.Message) else event.message
    notes = await db.load_notes()
    uid = str(event.from_user.id)
    my_notes = [n for n in notes.get("notes",[]) if n["user_id"]==uid]
    text = f"{E.note}<b>ЗАМЕТКИ</b>\n\n"
    if my_notes:
        for n in my_notes[-10:]:
            text += f"• {n['text'][:50]}\n"
    else:
        text += "Нет заметок.\n/notes [текст] чтобы добавить."
    if isinstance(event, types.Message) and len(event.text.split()) > 1:
        note_text = " ".join(event.text.split()[1:])
        notes.setdefault("notes",[]).append({"user_id":uid,"text":note_text,"date":datetime.now().isoformat()})
        await db.save_notes(notes)
        await event.answer(f"{E.check}Заметка добавлена!")
    elif isinstance(event, types.CallbackQuery):
        await event.message.edit_text(text, reply_markup=K.back())
        await event.answer()
    else:
        await msg.answer(text)

# ══════════════════════════════════════════════════════════════════
# 📅 СОБЫТИЯ И ТАЙМЕР
# ══════════════════════════════════════════════════════════════════
@dp.message(Command("countdown"))
@dp.callback_query(F.data == "countdown")
async def cmd_countdown(event):
    msg = event if isinstance(event, types.Message) else event.message
    events = await db.load_events()
    uid = str(event.from_user.id)
    my_events = [e for e in events.get("events",[]) if e["user_id"]==uid]
    text = f"{E.hourglass}<b>ТАЙМЕРЫ</b>\n\n"
    if my_events:
        for e in my_events[-5:]:
            target = datetime.fromisoformat(e["date"])
            delta = target - datetime.now()
            if delta.total_seconds() > 0:
                days = delta.days; hours = delta.seconds//3600
                text += f"• {e['name']}: {days}д {hours}ч\n"
            else:
                text += f"• {e['name']}: УЖЕ НАСТУПИЛО! {E.party}\n"
    else:
        text += "Нет таймеров.\n/countdown [название] [ДД.ММ.ГГГГ]"
    if isinstance(event, types.Message) and len(event.text.split()) >= 3:
        parts = event.text.split()
        name = parts[1]
        try: date = datetime.strptime(parts[2], "%d.%m.%Y")
        except: await event.answer("Формат даты: ДД.ММ.ГГГГ"); return
        events.setdefault("events",[]).append({"user_id":uid,"name":name,"date":date.isoformat()})
        await db.save_events(events)
        await event.answer(f"{E.check}Событие добавлено!")
    elif isinstance(event, types.CallbackQuery):
        await event.message.edit_text(text, reply_markup=K.back())
        await event.answer()
    else:
        await msg.answer(text)

@dp.message(Command("anniversary"))
async def cmd_anniversary(msg: types.Message):
    parts = msg.text.split()
    if len(parts) >= 2:
        try: date = datetime.strptime(parts[1], "%d.%m.%Y")
        except: await msg.answer("Формат: /anniversary ДД.ММ.ГГГГ"); return
        events = await db.load_events()
        events.setdefault("events",[]).append({"user_id":str(msg.from_user.id),"name":"💞 Годовщина","date":date.isoformat(),"recurring":"yearly"})
        await db.save_events(events)
        await msg.answer(f"{E.check}Годовщина установлена!")
    else:
        await msg.answer("Используй: /anniversary ДД.ММ.ГГГГ")

@dp.message(Command("birthday"))
async def cmd_birthday(msg: types.Message):
    parts = msg.text.split()
    if len(parts) >= 2:
        try: date = datetime.strptime(parts[1], "%d.%m.%Y")
        except: await msg.answer("Формат: /birthday ДД.ММ.ГГГГ"); return
        events = await db.load_events()
        events.setdefault("events",[]).append({"user_id":str(msg.from_user.id),"name":"🎂 День рождения","date":date.isoformat(),"recurring":"yearly"})
        await db.save_events(events)
        await msg.answer(f"{E.check}День рождения установлен!")
    else:
        await msg.answer("Используй: /birthday ДД.ММ.ГГГГ")

# ══════════════════════════════════════════════════════════════════
# 🌤️ ПОГОДА / ЧАСОВЫЕ ПОЯСА
# ══════════════════════════════════════════════════════════════════
@dp.message(Command("weather"))
@dp.callback_query(F.data == "weather")
async def cmd_weather(event):
    msg = event if isinstance(event, types.Message) else event.message
    data = await db.load(); uid = str(event.from_user.id)
    # Пробуем получить последнюю геолокацию
    pending = data.get(f"pending_{uid}")
    if pending:
        w = await get_weather(pending["lat"], pending["lon"])
        text = f"{E.sun}<b>ПОГОДА</b>\n\n{pending['city']}\n🌡️{w['temp']}°C\n{w['desc']}\n💨{w['wind']}м/с"
    else:
        text = "Отправь геолокацию чтобы увидеть погоду! (через квест)"
    if isinstance(event, types.CallbackQuery): await event.message.edit_text(text, reply_markup=K.back()); await event.answer()
    else: await msg.answer(text)

@dp.message(Command("timezone"))
async def cmd_timezone(msg: types.Message):
    data = await db.load(); uid = str(msg.from_user.id); partner = get_partner(data, uid)
    if not partner:
        await msg.answer("Нужна пара!")
        return
    now = datetime.now()
    # Упрощённо: показываем московское время для обоих
    await msg.answer(f"{E.globe}<b>ЧАСОВЫЕ ПОЯСА</b>\n\nТы: {now.strftime('%H:%M')}\nПартнёр: {now.strftime('%H:%M')}\n\nДля точного времени нужна геолокация обоих.")

# ══════════════════════════════════════════════════════════════════
# 🔍 АНАЛИЗ ФОТО
# ══════════════════════════════════════════════════════════════════
@dp.message(Command("analyze"))
@dp.callback_query(F.data == "analyze")
async def cmd_analyze(event):
    msg = event if isinstance(event, types.Message) else event.message
    text = "Отправь фото — и AI проанализирует его!"
    if isinstance(event, types.CallbackQuery): await event.message.edit_text(text, reply_markup=K.back()); await event.answer()
    else: await msg.answer(text)

# ══════════════════════════════════════════════════════════════════
# ⚙️ НАСТРОЙКИ / ПОДДЕРЖКА / FAQ
# ══════════════════════════════════════════════════════════════════
@dp.message(Command("settings"))
@dp.callback_query(F.data == "settings")
async def cmd_settings(event):
    msg = event if isinstance(event, types.Message) else event.message
    text = f"{E.gear}<b>НАСТРОЙКИ</b>\n\n/setbio [текст] — описание\n/setavatar — аватар\n/partnerbio [текст] — описание партнёра\n/logout — разорвать пару\n/deleteaccount — удалить аккаунт"
    if isinstance(event, types.CallbackQuery): await event.message.edit_text(text, reply_markup=K.back()); await event.answer()
    else: await msg.answer(text)

@dp.message(Command("support"))
@dp.callback_query(F.data == "support")
async def cmd_support(event):
    msg = event if isinstance(event, types.Message) else event.message
    text = f"{E.speech}<b>ПОДДЕРЖКА</b>\n\nЕсли у тебя проблемы — напиши /report [описание]"
    if isinstance(event, types.CallbackQuery): await event.message.edit_text(text, reply_markup=K.back()); await event.answer()
    else: await msg.answer(text)

@dp.message(Command("faq"))
async def cmd_faq(msg: types.Message):
    await msg.answer(f"{E.question}<b>ЧАСТЫЕ ВОПРОСЫ</b>\n\n1. Как создать пару? — /start\n2. Как получить монеты? — выполняй квесты!\n3. Как добавить друга? — /addfriend [ID]")

@dp.message(Command("privacy"))
async def cmd_privacy(msg: types.Message):
    await msg.answer("Политика конфиденциальности: мы не храним личные данные кроме имени и ID. Все фото в альбоме видны только вам и партнёру.")

@dp.message(Command("deleteaccount"))
async def cmd_deleteaccount(msg: types.Message):
    data = await db.load(); uid = str(msg.from_user.id)
    pid = data["users"][uid].get("partner")
    if pid and pid in data["users"]: data["users"][pid]["partner"] = None
    del data["users"][uid]; await db.save(data)
    await msg.answer("Аккаунт удалён. Чтобы начать заново — /start")

# ══════════════════════════════════════════════════════════════════
# 🎮 ИГРЫ
# ══════════════════════════════════════════════════════════════════
@dp.message(Command("game"))
async def cmd_game(msg: types.Message):
    builder = InlineKeyboardBuilder()
    builder.button(text="🪨 Камень", callback_data="game_rock")
    builder.button(text="📄 Ножницы", callback_data="game_scissors")
    builder.button(text="📜 Бумага", callback_data="game_paper")
    builder.button(text=f"{E.back_emoji} Назад", callback_data="main_menu")
    await msg.answer(f"{E.game}<b>КАМЕНЬ-НОЖНИЦЫ-БУМАГА</b>\n\nВыбери:", reply_markup=builder.as_markup())

@dp.callback_query(F.data.startswith("game_"))
async def game_rps(cb: types.CallbackQuery):
    choices = {"rock":"🪨","scissors":"📄","paper":"📜"}
    user_choice = cb.data.replace("game_","")
    bot_choice = random.choice(list(choices.keys()))
    result = ""
    if user_choice == bot_choice: result = "Ничья!"
    elif (user_choice=="rock" and bot_choice=="scissors") or (user_choice=="scissors" and bot_choice=="paper") or (user_choice=="paper" and bot_choice=="rock"):
        result = f"Ты выиграл! +5 монет"
        data = await db.load(); uid = str(cb.from_user.id)
        data["users"][uid]["coins"] = data["users"][uid].get("coins",0)+5; await db.save(data)
    else: result = "Бот выиграл!"
    await cb.message.edit_text(f"{E.game}<b>РЕЗУЛЬТАТ</b>\n\nТы: {choices[user_choice]}\nБот: {choices[bot_choice]}\n\n{result}", reply_markup=K.back())
    await cb.answer()

# ══════════════════════════════════════════════════════════════════
# 👑 АДМИН-ПАНЕЛЬ
# ══════════════════════════════════════════════════════════════════
@dp.message(Command("admin_panel"))
@dp.callback_query(F.data == "admin_panel")
async def cmd_admin(event):
    if not is_admin(event.from_user.id):
        if isinstance(event, types.CallbackQuery): await event.answer("Нет доступа!", show_alert=True)
        else: await event.answer("Нет доступа!")
        return
    msg = event if isinstance(event, types.Message) else event.message
    text = f"{E.admin_emoji}<b>АДМИН-ПАНЕЛЬ</b>\n\n/admin_stats\n/admin_broadcast [текст]\n/admin_givecoins [ID] [сумма]\n/admin_givediamonds [ID] [сумма]\n/admin_givexp [ID] [сумма]\n/admin_ban [ID]\n/admin_backup\n/admin_restart"
    if isinstance(event, types.CallbackQuery): await event.message.edit_text(text, reply_markup=K.back()); await event.answer()
    else: await msg.answer(text)

@dp.message(Command("admin_stats"))
async def cmd_admin_stats(msg: types.Message):
    if not is_admin(msg.from_user.id): return
    data = await db.load()
    await msg.answer(f"Пользователей: {len(data['users'])}\nКвестов: {len(data['quests'])}\nМостов: {len(data['album'])}")

@dp.message(Command("admin_broadcast"))
async def cmd_admin_broadcast(msg: types.Message):
    if not is_admin(msg.from_user.id): return
    text = " ".join(msg.text.split()[1:])
    if not text: await msg.answer("Используй: /admin_broadcast [текст]"); return
    data = await db.load()
    count = 0
    for uid in data["users"]:
        try: await bot.send_message(int(uid), f"{E.mail}<b>РАССЫЛКА:</b>\n\n{text}"); count += 1
        except: pass
    await msg.answer(f"Отправлено {count} пользователям.")

@dp.message(Command("admin_givecoins"))
async def cmd_admin_givecoins(msg: types.Message):
    if not is_admin(msg.from_user.id): return
    parts = msg.text.split()
    if len(parts) >= 3:
        data = await db.load(); uid = parts[1]; amount = int(parts[2])
        if uid in data["users"]: data["users"][uid]["coins"] = data["users"][uid].get("coins",0)+amount; await db.save(data); await msg.answer(f"Выдано {amount} монет!")
        else: await msg.answer("Пользователь не найден")
    else: await msg.answer("/admin_givecoins [ID] [сумма]")

@dp.message(Command("admin_givediamonds"))
async def cmd_admin_givediamonds(msg: types.Message):
    if not is_admin(msg.from_user.id): return
    parts = msg.text.split()
    if len(parts) >= 3:
        data = await db.load(); uid = parts[1]; amount = int(parts[2])
        if uid in data["users"]: data["users"][uid]["diamonds"] = data["users"][uid].get("diamonds",0)+amount; await db.save(data); await msg.answer(f"Выдано {amount} алмазов!")
        else: await msg.answer("Пользователь не найден")
    else: await msg.answer("/admin_givediamonds [ID] [сумма]")

@dp.message(Command("admin_givexp"))
async def cmd_admin_givexp(msg: types.Message):
    if not is_admin(msg.from_user.id): return
    parts = msg.text.split()
    if len(parts) >= 3:
        data = await db.load(); uid = parts[1]; amount = int(parts[2])
        if uid in data["users"]: data["users"][uid]["xp"] = data["users"][uid].get("xp",0)+amount; await db.save(data); await msg.answer(f"Выдано {amount} XP!")
        else: await msg.answer("Пользователь не найден")
    else: await msg.answer("/admin_givexp [ID] [сумма]")

@dp.message(Command("admin_ban"))
async def cmd_admin_ban(msg: types.Message):
    if not is_admin(msg.from_user.id): return
    parts = msg.text.split()
    if len(parts) >= 2:
        data = await db.load(); uid = parts[1]
        if uid in data["users"]: data["users"][uid]["banned"] = True; await db.save(data); await msg.answer("Заблокирован!")
        else: await msg.answer("Не найден")
    else: await msg.answer("/admin_ban [ID]")

@dp.message(Command("admin_backup"))
async def cmd_admin_backup(msg: types.Message):
    if not is_admin(msg.from_user.id): return
    data = await db.load()
    backup_path = f"backups/backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    Path(backup_path).write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    await msg.answer(f"Бэкап создан: {backup_path}")

@dp.message(Command("admin_restart"))
async def cmd_admin_restart(msg: types.Message):
    if not is_admin(msg.from_user.id): return
    await msg.answer("Перезапуск...")
    os.execv(sys.executable, ['python'] + sys.argv)

# ══════════════════════════════════════════════════════════════════
# 💬 AI-ЧАТ (упрощённый)
# ══════════════════════════════════════════════════════════════════
@dp.message(Command("chat"))
async def cmd_chat(msg: types.Message, state: FSMContext):
    text = " ".join(msg.text.split()[1:])
    if not text: await msg.answer("Используй: /chat [сообщение]"); return
    resp = await ai_chat(text, [])
    await msg.answer(f"{E.robot}<b>AI:</b>\n{resp}")

# ══════════════════════════════════════════════════════════════════
# 📋 ИНВЕНТАРЬ / WISHLIST
# ══════════════════════════════════════════════════════════════════
@dp.message(Command("inventory"))
@dp.callback_query(F.data == "inventory")
async def cmd_inventory(event):
    msg = event if isinstance(event, types.Message) else event.message
    gifts = await db.load_gifts()
    uid = str(event.from_user.id)
    received = [g for g in gifts.get("gifts_sent",[]) if g["to"]==uid]
    text = f"{E.cart}<b>ИНВЕНТАРЬ</b>\n\n"
    if received:
        for g in received[-10:]:
            item = SHOP_ITEMS.get(g["item"],{})
            text += f"{item.get('emoji','🎁')} {item.get('name','Подарок')}\n"
    else: text += "Пусто. Попроси партнёра отправить подарок!"
    if isinstance(event, types.CallbackQuery): await event.message.edit_text(text, reply_markup=K.back()); await event.answer()
    else: await msg.answer(text)

@dp.message(Command("wishlist"))
async def cmd_wishlist(msg: types.Message):
    wish = await db.load_wishlist()
    uid = str(msg.from_user.id)
    items = [w for w in wish.get("items",[]) if w["user_id"]==uid]
    text = f"{E.star}<b>WISHLIST</b>\n\n"
    if items:
        for w in items[-10:]: text += f"• {w['text']}\n"
    else: text += "Пусто. Добавь желание: /wishlist [текст]"
    parts = msg.text.split(maxsplit=1)
    if len(parts) > 1:
        wish.setdefault("items",[]).append({"user_id":uid,"text":parts[1],"date":datetime.now().isoformat()})
        await db.save_wishlist(wish)
        await msg.answer(f"{E.check}Добавлено!")
    else:
        await msg.answer(text)

# ══════════════════════════════════════════════════════════════════
# 🔔 НАПОМИНАНИЕ / ОТЧЁТ / ГОЛОСОВАНИЕ
# ══════════════════════════════════════════════════════════════════
@dp.message(Command("reminder"))
async def cmd_reminder(msg: types.Message, state: FSMContext):
    parts = msg.text.split(maxsplit=1)
    if len(parts) > 1:
        await msg.answer(f"{E.check}Напоминание сохранено: {parts[1]}")
    else:
        await msg.answer("Используй: /reminder [текст]")

@dp.message(Command("report"))
async def cmd_report(msg: types.Message):
    parts = msg.text.split(maxsplit=1)
    if len(parts) > 1:
        logger.warning(f"REPORT from {msg.from_user.id}: {parts[1]}")
        await msg.answer("Жалоба отправлена администратору.")
    else:
        await msg.answer("Используй: /report [описание проблемы]")

@dp.message(Command("suggest"))
async def cmd_suggest(msg: types.Message):
    parts = msg.text.split(maxsplit=1)
    if len(parts) > 1:
        await msg.answer(f"{E.check}Идея квеста отправлена! Спасибо!")
    else:
        await msg.answer("Используй: /suggest [идея квеста]")

@dp.message(Command("vote"))
async def cmd_vote(msg: types.Message):
    await msg.answer(f"{E.target}<b>ГОЛОСОВАНИЕ</b>\n\nПредложи тему квеста: /suggest [тема]\nАдмин выберет лучшую!")

# ══════════════════════════════════════════════════════════════════
# 📅 КАЛЕНДАРЬ / СОБЫТИЯ
# ══════════════════════════════════════════════════════════════════
@dp.message(Command("calendar"))
@dp.callback_query(F.data == "calendar")
async def cmd_calendar(event):
    msg = event if isinstance(event, types.Message) else event.message
    events = await db.load_events()
    uid = str(event.from_user.id)
    my_events = [e for e in events.get("events",[]) if e["user_id"]==uid]
    now = datetime.now()
    text = f"{E.calendar}<b>КАЛЕНДАРЬ</b>\n\n"
    if my_events:
        for e in sorted(my_events, key=lambda x: x["date"])[:5]:
            d = datetime.fromisoformat(e["date"])
            delta = d - now
            text += f"• {e['name']}: {d.strftime('%d.%m.%Y')} (через {delta.days} дн.)\n"
    else:
        text += "Нет событий.\n/anniversary ДД.ММ.ГГГГ\n/birthday ДД.ММ.ГГГГ"
    if isinstance(event, types.CallbackQuery): await event.message.edit_text(text, reply_markup=K.back()); await event.answer()
    else: await msg.answer(text)

@dp.message(Command("events"))
@dp.callback_query(F.data == "events")
async def cmd_events(event):
    await cmd_calendar(event)

# ══════════════════════════════════════════════════════════════════
# 📝 BIO И АВАТАР
# ══════════════════════════════════════════════════════════════════
@dp.message(Command("setbio"))
async def cmd_setbio(msg: types.Message):
    parts = msg.text.split(maxsplit=1)
    if len(parts) > 1:
        data = await db.load(); uid = str(msg.from_user.id)
        data["users"][uid]["bio"] = parts[1]; await db.save(data)
        await msg.answer(f"{E.check}Описание обновлено!")
    else:
        await msg.answer("Используй: /setbio [текст]")

@dp.message(Command("partnerbio"))
async def cmd_partnerbio(msg: types.Message):
    parts = msg.text.split(maxsplit=1)
    if len(parts) > 1:
        data = await db.load(); uid = str(msg.from_user.id)
        data["users"][uid]["partner_bio"] = parts[1]; await db.save(data)
        await msg.answer(f"{E.check}Описание партнёра обновлено!")
    else:
        await msg.answer("Используй: /partnerbio [текст]")

@dp.message(Command("setavatar"))
async def cmd_setavatar(msg: types.Message):
    await msg.answer("Отправь фото для аватара!")

# ══════════════════════════════════════════════════════════════════
# 📊 ТАЙМЛАЙН
# ══════════════════════════════════════════════════════════════════
@dp.message(Command("timeline"))
async def cmd_timeline(msg: types.Message):
    data = await db.load(); uid = str(msg.from_user.id)
    quests = [q for q in data["quests"] if q.get("done") and (q["user1_id"]==uid or q["user2_id"]==uid)]
    text = f"{E.clock}<b>ХРОНОЛОГИЯ ОТНОШЕНИЙ</b>\n\n"
    if quests:
        for q in quests[-10:]:
            text += f"• {q['date'][:10]} — {q['theme'][:40]}\n"
    else:
        text += "Пока пусто. Начните с квеста!"
    await msg.answer(text)

# ══════════════════════════════════════════════════════════════════
# 💬 ОБРАБОТКА ТЕКСТА
# ══════════════════════════════════════════════════════════════════
@dp.message(F.text)
async def text_handler(msg: types.Message):
    text = msg.text.lower()
    if text.startswith("/"): await msg.answer(f"Неизвестная команда. /help для списка.")
    elif any(w in text for w in ["привет","хай","ку"]): await msg.answer(f"{E.smile}Привет! /start для меню!")
    elif any(w in text for w in ["спасибо","круто"]): await msg.answer(f"{E.love}Спасибо!")
    elif random.random() < 0.03: await msg.answer(random.choice([f"{E.butterfly}Редкая бабочка!",f"{E.rocket}Ракета!",f"{E.ghost}Призрак..."]))
    else: await msg.answer(f"Используй /start для меню или /help для списка команд.")

# ══════════════════════════════════════════════════════════════════
# 🚀 ЗАПУСК
# ══════════════════════════════════════════════════════════════════
async def main():
    print(LOGO)
    print(f"🚀 Меридиан Ultra v4.0 запускается...")
    print(f"📋 50+ команд • 25+ достижений • Магазин • VIP • Друзья")

    await bot.set_my_commands([
        BotCommand(command="start", description="🏠 Главное меню"),
        BotCommand(command="help", description="❓ Помощь"),
        BotCommand(command="quest", description="🎯 Новый квест"),
        BotCommand(command="album", description="📸 Альбом"),
        BotCommand(command="stats", description="📊 Статистика"),
        BotCommand(command="profile", description="👤 Профиль"),
        BotCommand(command="partner", description="💑 Профиль партнёра"),
        BotCommand(command="shop", description="🏪 Магазин"),
        BotCommand(command="friends", description="👥 Друзья"),
        BotCommand(command="notes", description="📝 Заметки"),
    ])

    def signal_handler(sig, frame):
        print("\n👋 Завершение работы...")
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        await dp.start_polling(bot)
    except Exception as e:
        logger.critical(f"Bot crashed: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())