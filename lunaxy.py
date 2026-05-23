"""
╔══════════════════════════════════════════════════════════════════╗
║           🌉 МЕРИДИАН ULTIMATE — ПОЛНАЯ ВЕРСИЯ                   ║
║  60+ команд • 30+ товаров • Карта • Новый Google AI • Aiogram 3.7+ ║
╚══════════════════════════════════════════════════════════════════╝
"""

import asyncio, json, os, random, re, traceback, logging, signal, sys, platform, io, base64, hashlib, math
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple, Union
from collections import defaultdict, Counter
from dataclasses import dataclass, field
from enum import Enum

from aiogram import Bot, Dispatcher, types, F, Router
from aiogram.filters import Command, CommandObject, StateFilter
from aiogram.types import (
    InlineKeyboardMarkup, InlineKeyboardButton,
    ReplyKeyboardMarkup, KeyboardButton, KeyboardButtonRequestLocation,
    BufferedInputFile, BotCommand, BotCommandScopeDefault,
    DefaultBotProperties, InputMediaPhoto, WebAppInfo
)
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder
from aiogram.utils.media_group import MediaGroupBuilder
from aiogram.enums import ParseMode, ChatAction

from google import genai
from google.genai import types as genai_types
import httpx
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance, ImageOps, ImageColor, ImageChops
import aiofiles

# ══════════════════════════════════════════════════════════════════
# 🔑 КЛЮЧИ API И КОНФИГУРАЦИЯ
# ══════════════════════════════════════════════════════════════════
BOT_TOKEN = "8853395386:AAHtdZNkZ1PLMIAnlXq2_Jmd43v7xjn0as8"
GEMINI_API_KEY = "AIzaSyBc-lzSR0htkZJ7DZDWELxYzPyKq8wKRvw"
OPENWEATHER_API_KEY = "c9533271e2a27b86f0abc303b206c6a6"
ADMIN_ID = 8659997773
SUPPORT_USERNAME = "@meridian_support"
BOT_VERSION = "5.0 Ultimate"
DEFAULT_LANGUAGE = "ru"
MAX_QUEST_PHOTOS = 3
COINS_PER_QUEST = 25
XP_PER_QUEST = 50
DIAMONDS_PER_LEVEL = 5
MAX_FRIENDS = 50
MAX_NOTES = 100
MAX_WISHLIST = 50
MAX_EVENTS = 20
STREAK_BONUS_MULTIPLIER = 0.1
VIP_MULTIPLIERS = {1: 1.5, 2: 2.0, 3: 3.0}
CACHE_TIMEOUT = 300

# ══════════════════════════════════════════════════════════════════
# 🤖 AI КЛИЕНТ (google.genai — новая версия)
# ══════════════════════════════════════════════════════════════════
client = genai.Client(api_key=GEMINI_API_KEY)

# ══════════════════════════════════════════════════════════════════
# 🤖 BOT (aiogram 3.7+ fix)
# ══════════════════════════════════════════════════════════════════
bot = Bot(
    token=BOT_TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)
dp = Dispatcher(storage=MemoryStorage())
router = Router()
dp.include_router(router)

# ══════════════════════════════════════════════════════════════════
# 📁 ПАПКИ И ЛОГИРОВАНИЕ
# ══════════════════════════════════════════════════════════════════
for directory in [
    "media", "media/album", "media/collages", "media/avatars", "media/photos",
    "media/thumbnails", "media/stickers", "media/maps", "media/temp", "media/exports",
    "logs", "backups", "temp", "cache"
]:
    Path(directory).mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[
        logging.FileHandler('logs/bot.log', encoding='utf-8'),
        logging.FileHandler('logs/errors.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Отдельные логи для действий
action_logger = logging.getLogger('actions')
action_logger.addHandler(logging.FileHandler('logs/actions.log', encoding='utf-8'))
admin_logger = logging.getLogger('admin')
admin_logger.addHandler(logging.FileHandler('logs/admin.log', encoding='utf-8'))
quest_logger = logging.getLogger('quests')
quest_logger.addHandler(logging.FileHandler('logs/quests.log', encoding='utf-8'))

# ══════════════════════════════════════════════════════════════════
# 🎨 СИСТЕМА ЭМОДЗИ И ИКОНОК
# ══════════════════════════════════════════════════════════════════
class Emoji:
    # Базовые
    sparkles = "✨"; bridge = "🌉"; heart = "💞"; camera = "📸"
    map_marker = "📍"; clock = "⏰"; trophy = "🏆"; star = "⭐"
    fire = "🔥"; gift = "🎁"; album = "📚"; stats_icon = "📊"
    
    # AI и технологии
    brain = "🧠"; robot = "🤖"; eyes = "👀"; magic = "🔮"
    gear = "⚙️"; wrench = "🔧"; shield = "🛡️"; key = "🔑"
    lock = "🔒"; unlock = "🔓"; search = "🔍"; filter_icon = "🔎"
    
    # Погода и природа
    sun = "☀️"; moon = "🌙"; cloud = "☁️"; rain = "🌧️"
    snow = "❄️"; zap = "⚡"; world = "🌍"; globe = "🌐"
    flower = "🌸"; butterfly = "🦋"; rainbow = "🌈"
    
    # Эмоции и отношения
    smile = "😊"; love = "🥰"; party = "🎉"; cool = "😎"
    kiss = "😘"; hug = "🤗"; clap = "👏"; hand = "👋"
    
    # Игровые
    target = "🎯"; dice = "🎲"; puzzle = "🧩"; joystick = "🕹️"
    game = "🎮"; chess = "♟️"; cards = "🃏"; dart = "🎯"
    
    # Магазин и валюта
    shop = "🏪"; cart = "🛒"; coin = "🪙"; money = "💰"
    gem = "💎"; diamond = "💠"; crown = "👑"; medal = "🏅"
    rose = "🌹"; teddy = "🧸"; chocolate = "🍫"; ring = "💍"
    plane = "✈️"; rocket = "🚀"
    
    # Социальное
    users = "👥"; person = "👤"; people = "👨‍👩‍👧‍👦"; family = "👨‍👩‍👧"
    friends = "🤝"; group = "👨‍👩‍👧‍👦"; team = "👥"
    
    # Интерфейс
    check = "✅"; cross = "❌"; warning = "⚠️"; info = "ℹ️"
    question = "❓"; back_arrow = "◀️"; forward = "▶️"; refresh = "🔄"
    save = "💾"; delete = "🗑️"; edit = "✏️"; plus = "➕"; minus = "➖"
    
    # Контент
    letter = "💌"; book = "📖"; pen = "🖊️"; note = "📝"
    calendar = "📅"; chart = "📈"; phone = "📱"; laptop = "💻"
    camera_flash = "📸"; video = "🎥"; music = "🎵"; art = "🎨"
    palette = "🎨"; brush = "🖌️"; frame = "🖼️"
    
    # Специальные
    ghost = "👻"; alien = "👽"; robot_face = "🤖"; monster = "👾"
    unicorn = "🦄"; dragon = "🐉"; phoenix = "🐦‍🔥"; mermaid = "🧜‍♀️"
    wizard = "🧙"; fairy = "🧚"; vampire = "🧛"; genie = "🧞"
    
    # Еда и напитки
    coffee = "☕"; tea = "🍵"; pizza = "🍕"; cake = "🎂"
    cookie = "🍪"; ice_cream = "🍦"; wine = "🍷"; cocktail = "🍸"
    sushi = "🍣"; burger = "🍔"; taco = "🌮"; donut = "🍩"
    
    # Спорт и активность
    run = "🏃"; swim = "🏊"; bike = "🚴"; gym = "🏋️"
    yoga = "🧘"; dance = "💃"; skate = "🛹"; surf = "🏄"
    
    # Транспорт
    car = "🚗"; bus = "🚌"; train = "🚂"; ship = "🚢"
    helicopter = "🚁"; bicycle = "🚲"; scooter = "🛴"
    
    # Здания и места
    home = "🏠"; building = "🏢"; school = "🏫"; hospital = "🏥"
    bank = "🏦"; cinema = "🎦"; theater = "🎭"; museum = "🏛️"
    park = "🏞️"; beach = "🏖️"; mountain = "⛰️"; island = "🏝️"
    
    # Животные
    cat = "🐱"; dog = "🐶"; rabbit = "🐰"; bear = "🐻"
    panda = "🐼"; penguin = "🐧"; owl = "🦉"; fox = "🦊"
    lion = "🦁"; tiger = "🐯"; elephant = "🐘"; giraffe = "🦒"
    dolphin = "🐬"; whale = "🐋"; octopus = "🐙"; butterfly_insect = "🦋"
    
    # Космос
    star2 = "🌟"; planet = "🪐"; comet = "☄️"; satellite = "🛸"
    astronaut = "👨‍🚀"; telescope = "🔭"; milky_way = "🌌"
    
    # Прочее
    hourglass = "⏳"; infinity = "♾️"; yin_yang = "☯️"; peace = "☮️"
    bulb = "💡"; magnet = "🧲"; microscope = "🔬"; pill = "💊"
    syringe = "💉"; dna = "🧬"; gear_icon = "⚙️"; atom = "⚛️"
    radioactive = "☢️"; biohazard = "☣️"; warning_sign = "⚠️"
    no_entry = "⛔"; stop = "🛑"; go = "🟢"; wait = "🟡"
    bell = "🔔"; mute = "🔕"; speaker = "🔊"; megaphone = "📣"

E = Emoji()

# ══════════════════════════════════════════════════════════════════
# 🎨 ASCII ЛОГОТИП И БАННЕРЫ
# ══════════════════════════════════════════════════════════════════
LOGO_FULL = """
╔══════════════════════════════════════════════════════════════════╗
║                                                                  ║
║   ███╗   ███╗███████╗██████╗ ██╗██████╗ ██╗ █████╗ ███╗   ██╗   ║
║   ████╗ ████║██╔════╝██╔══██╗██║██╔══██╗██║██╔══██╗████╗  ██║   ║
║   ██╔████╔██║█████╗  ██████╔╝██║██║  ██║██║███████║██╔██╗ ██║   ║
║   ██║╚██╔╝██║██╔══╝  ██╔══██╗██║██║  ██║██║██╔══██║██║╚██╗██║   ║
║   ██║ ╚═╝ ██║███████╗██║  ██║██║██████╔╝██║██║  ██║██║ ╚████║   ║
║   ╚═╝     ╚═╝╚══════╝╚═╝  ╚═╝╚═╝╚═════╝ ╚═╝╚═╝  ╚═╝╚═╝  ╚═══╝   ║
║                                                                  ║
║                    🌉  U L T I M A T E  🌉                       ║
║              Мосты между городами и сердцами                     ║
║                   v5.0 • 60+ команд                              ║
╚══════════════════════════════════════════════════════════════════╝
"""

LOGO_SMALL = """
╔══════════════════════╗
║  🌉 МЕРИДИАН v5.0  ║
╚══════════════════════╝
"""

# ══════════════════════════════════════════════════════════════════
# 📊 РАНГИ (10 уровней)
# ══════════════════════════════════════════════════════════════════
@dataclass
class Rank:
    name: str
    min_xp: int
    emoji: str
    color: str
    perks: List[str] = field(default_factory=list)

RANKS = [
    Rank("Новичок", 0, "🌱", "#00ff00", ["Базовые квесты"]),
    Rank("Исследователь", 50, "🔍", "#00ccff", ["Квесты сложнее"]),
    Rank("Строитель мостов", 150, "🏗️", "#0099ff", ["Двойные XP за квесты"]),
    Rank("Архитектор", 400, "🏛️", "#0066ff", ["Секретные квесты"]),
    Rank("Мастер", 1000, "👑", "#9900ff", ["+10% монет за квесты"]),
    Rank("Легенда", 2500, "🌟", "#ff00ff", ["Эксклюзивные рамки"]),
    Rank("Полубог", 5000, "💫", "#ff0099", ["Собственные квесты"]),
    Rank("Хранитель", 10000, "🔮", "#ff0066", ["VIP статус"]),
    Rank("Властелин", 25000, "🌌", "#ff0033", ["Безлимитные квесты"]),
    Rank("Божество", 50000, "⚡", "#ff0000", ["ВСЁ!"]),
]

def get_rank(xp: int) -> Rank:
    for rank in reversed(RANKS):
        if xp >= rank.min_xp:
            return rank
    return RANKS[0]

def get_rank_progress(xp: int) -> Tuple[Rank, float, int]:
    rank = get_rank(xp)
    idx = RANKS.index(rank)
    if idx == len(RANKS) - 1:
        return rank, 1.0, 0
    next_rank = RANKS[idx + 1]
    progress = (xp - rank.min_xp) / max(next_rank.min_xp - rank.min_xp, 1)
    return rank, min(progress, 1.0), next_rank.min_xp - xp

# ══════════════════════════════════════════════════════════════════
# 🏆 ДОСТИЖЕНИЯ (30+)
# ══════════════════════════════════════════════════════════════════
@dataclass
class Achievement:
    id: str
    name: str
    description: str
    emoji: str
    xp_reward: int
    coins_reward: int
    diamonds_reward: int = 0
    hidden: bool = False
    category: str = "general"

ACHIEVEMENTS = {
    # Квесты
    "first_quest": Achievement("first_quest", "Первый шаг", "Выполнить первый квест", "🌉", 10, 50, category="quests"),
    "5_quests": Achievement("5_quests", "Начинающий строитель", "Выполнить 5 квестов", "🏗️", 30, 100, category="quests"),
    "10_quests": Achievement("10_quests", "Опытный строитель", "10 квестов", "🏛️", 60, 200, category="quests"),
    "25_quests": Achievement("25_quests", "Градостроитель", "25 квестов", "🏙️", 150, 500, category="quests"),
    "50_quests": Achievement("50_quests", "Инженер", "50 квестов", "👷", 300, 1000, category="quests"),
    "100_quests": Achievement("100_quests", "Архитектор мечты", "100 квестов", "🌟", 1000, 5000, 10, category="quests"),
    
    # Время суток
    "night_owl": Achievement("night_owl", "Ночная сова", "Квест после 23:00", "🦉", 25, 75, category="time"),
    "dawn_patrol": Achievement("dawn_patrol", "Рассветный патруль", "Квест до 7 утра", "🌅", 30, 100, category="time"),
    "morning_person": Achievement("morning_person", "Жаворонок", "3 квеста утром", "☀️", 50, 150, category="time"),
    "sunset_lover": Achievement("sunset_lover", "Любитель закатов", "Квест на закате", "🌇", 35, 100, category="time"),
    
    # Погода
    "rain_dancer": Achievement("rain_dancer", "Дождевик", "Квест в дождь", "🌧️", 20, 50, category="weather"),
    "snow_angel": Achievement("snow_angel", "Снежный ангел", "Квест в снег", "❄️", 25, 75, category="weather"),
    "storm_chaser": Achievement("storm_chaser", "Охотник за грозами", "Квест в грозу", "⛈️", 35, 150, category="weather"),
    "fog_walker": Achievement("fog_walker", "Туманный странник", "Квест в туман", "🌫️", 30, 100, category="weather"),
    
    # Стрики
    "streak_3": Achievement("streak_3", "Три дня", "Стрик 3 дня", "🔥", 25, 100, category="streaks"),
    "streak_7": Achievement("streak_7", "Неделя", "Стрик 7 дней", "🌟", 75, 300, category="streaks"),
    "streak_14": Achievement("streak_14", "Две недели", "Стрик 14 дней", "💫", 200, 750, category="streaks"),
    "streak_30": Achievement("streak_30", "Месяц", "Стрик 30 дней", "👑", 500, 2000, category="streaks"),
    "streak_90": Achievement("streak_90", "Квартал", "Стрик 90 дней", "🏆", 1500, 5000, 25, category="streaks"),
    "streak_365": Achievement("streak_365", "Год вместе", "Стрик 365 дней", "💎", 5000, 20000, 100, category="streaks"),
    
    # Качество
    "perfect_score": Achievement("perfect_score", "Идеал", "Оба фото 10/10", "💎", 50, 250, 5, category="quality"),
    "creative_genius": Achievement("creative_genius", "Гений", "Креативность 10/10", "🎨", 40, 200, category="quality"),
    "ten_perfect": Achievement("ten_perfect", "Мастер фото", "10 идеальных оценок", "📸", 200, 1000, 10, category="quality"),
    
    # Социальное
    "first_surprise": Achievement("first_surprise", "Первый сюрприз", "Отправить сюрприз", "🎁", 15, 50, category="social"),
    "surprise_5": Achievement("surprise_5", "Сюрпризёр", "5 сюрпризов", "🎁", 30, 150, category="social"),
    "surprise_20": Achievement("surprise_20", "Волшебник", "20 сюрпризов", "🧙", 150, 750, category="social"),
    "first_friend": Achievement("first_friend", "Душа компании", "Добавить друга", "🤝", 20, 100, category="social"),
    "5_friends": Achievement("5_friends", "Популярный", "5 друзей", "👥", 50, 250, category="social"),
    
    # Особые
    "secret_finder": Achievement("secret_finder", "Кладоискатель", "Найти секретный квест", "🗝️", 100, 500, 5, category="special"),
    "collector": Achievement("collector", "Коллекционер", "Все типы квестов", "🏅", 200, 1000, 10, category="special"),
    "globetrotter": Achievement("globetrotter", "Путешественник", "Квесты в 5+ городах", "🗺️", 150, 750, category="special"),
    "vip_member": Achievement("vip_member", "VIP Персона", "Купить VIP", "💎", 50, 0, category="special"),
    "generous": Achievement("generous", "Щедрая душа", "Подарить 10 подарков", "🎀", 100, 500, 5, category="special"),
    "love_birds": Achievement("love_birds", "Голубки", "100 дней в паре", "💑", 1000, 5000, 50, category="special"),
}

# ══════════════════════════════════════════════════════════════════
# 🏪 МАГАЗИН (30+ товаров)
# ══════════════════════════════════════════════════════════════════
@dataclass
class ShopItem:
    id: str
    name: str
    emoji: str
    description: str
    price_coins: int
    price_diamonds: int
    category: str
    effect_type: str
    effect_value: int
    duration_days: int = 0
    stock: int = -1  # -1 = бесконечно

SHOP_ITEMS = {
    # Подарки партнёру
    "rose": ShopItem("rose", "Красная роза", "🌹", "Романтичный подарок +10 к следующему квесту", 50, 0, "gifts", "quest_boost", 10),
    "bouquet": ShopItem("bouquet", "Букет роз", "💐", "Роскошный букет +30 к квесту", 150, 0, "gifts", "quest_boost", 30),
    "teddy": ShopItem("teddy", "Плюшевый мишка", "🧸", "Мягкий друг +5 XP", 100, 0, "gifts", "xp_bonus", 5),
    "chocolate": ShopItem("chocolate", "Коробка конфет", "🍫", "Сладкий сюрприз +20 монет партнёру", 150, 0, "gifts", "coins_to_partner", 20),
    "ring": ShopItem("ring", "Кольцо", "💍", "Символ любви +50 XP и рамка", 0, 500, "gifts", "xp_and_frame", 50),
    "necklace": ShopItem("necklace", "Ожерелье", "📿", "Драгоценный подарок +100 XP", 0, 1000, "gifts", "xp_bonus", 100),
    "bracelet": ShopItem("bracelet", "Браслет", "💫", "Браслет дружбы +25 XP", 0, 250, "gifts", "xp_bonus", 25),
    "plane_ticket": ShopItem("plane_ticket", "Билет на самолёт", "✈️", "Виртуальное путешествие +100 XP", 0, 1000, "gifts", "xp_bonus", 100),
    
    # VIP статусы
    "vip_day": ShopItem("vip_day", "VIP на день", "⭐", "x1.5 XP на 1 день", 0, 20, "vip", "vip", 1, 1),
    "vip_week": ShopItem("vip_week", "VIP на неделю", "🌟", "x1.5 XP на 7 дней", 0, 100, "vip", "vip", 1, 7),
    "vip_month": ShopItem("vip_month", "VIP на месяц", "💫", "x2.0 XP на 30 дней", 0, 350, "vip", "vip", 2, 30),
    "vip_quarter": ShopItem("vip_quarter", "VIP на 3 месяца", "👑", "x2.5 XP на 90 дней", 0, 900, "vip", "vip", 2, 90),
    "vip_year": ShopItem("vip_year", "VIP на год", "🔮", "x3.0 XP на 365 дней", 0, 3500, "vip", "vip", 3, 365),
    
    # Бустеры
    "xp_booster": ShopItem("xp_booster", "XP Бустер", "⚡", "x2 XP на 1 час", 200, 0, "boosters", "xp_multiplier", 2, 0),
    "coin_booster": ShopItem("coin_booster", "Монетный бустер", "🪙", "x2 монет на 1 час", 150, 0, "boosters", "coin_multiplier", 2, 0),
    "luck_booster": ShopItem("luck_booster", "Бустер удачи", "🍀", "+20% к оценке AI", 100, 10, "boosters", "ai_score_boost", 20, 0),
    
    # Косметика
    "frame_gold": ShopItem("frame_gold", "Золотая рамка", "🖼️", "Рамка для коллажей", 500, 50, "cosmetics", "frame", 0),
    "frame_heart": ShopItem("frame_heart", "Рамка-сердечки", "💕", "Романтичная рамка", 300, 30, "cosmetics", "frame", 0),
    "frame_stars": ShopItem("frame_stars", "Звёздная рамка", "🌟", "Космическая рамка", 400, 40, "cosmetics", "frame", 0),
    "sticker_pack": ShopItem("sticker_pack", "Стикерпак", "🎭", "5 стикеров Меридиана", 250, 0, "cosmetics", "stickers", 5),
    
    # Редкие предметы
    "time_machine": ShopItem("time_machine", "Машина времени", "⏰", "Повтор любимого квеста", 0, 500, "rare", "repeat_quest", 0),
    "love_potion": ShopItem("love_potion", "Любовное зелье", "🧪", "+50 LP", 0, 200, "rare", "lp_bonus", 50),
    "map_expand": ShopItem("map_expand", "Расширение карты", "🗺️", "Новые локации на карте", 0, 300, "rare", "map_expand", 0),
    "lucky_charm": ShopItem("lucky_charm", "Талисман удачи", "🍀", "Шанс двойных наград 24ч", 0, 400, "rare", "double_rewards", 24),
    
    # Ресурсы
    "coins_100": ShopItem("coins_100", "100 монет", "🪙", "Пополнение баланса", 0, 10, "resources", "coins", 100),
    "coins_500": ShopItem("coins_500", "500 монет", "💰", "Большое пополнение", 0, 40, "resources", "coins", 500),
    "coins_1000": ShopItem("coins_1000", "1000 монет", "💎", "Мега пополнение", 0, 70, "resources", "coins", 1000),
    "diamonds_10": ShopItem("diamonds_10", "10 алмазов", "💠", "Премиум валюта", 500, 0, "resources", "diamonds", 10),
    "diamonds_50": ShopItem("diamonds_50", "50 алмазов", "💎", "Много алмазов", 2000, 0, "resources", "diamonds", 50),
}

SHOP_CATEGORIES = {
    "gifts": "🎁 Подарки",
    "vip": "👑 VIP Статусы",
    "boosters": "⚡ Бустеры",
    "cosmetics": "🎨 Косметика",
    "rare": "🔮 Редкие предметы",
    "resources": "💱 Ресурсы",
}

# ══════════════════════════════════════════════════════════════════
# 💾 БАЗА ДАННЫХ С КЭШИРОВАНИЕМ
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
        self.locations_file = Path("locations.json")
        self.inventory_file = Path("inventory.json")
        self.cache = {}
        self.cache_time = None
        self.lock = asyncio.Lock()

    async def load(self) -> dict:
        async with self.lock:
            now = datetime.now()
            if self.cache and self.cache_time and (now - self.cache_time).seconds < CACHE_TIMEOUT:
                return self.cache.copy()
            if self.data_file.exists():
                data = json.loads(self.data_file.read_text(encoding="utf-8"))
            else:
                data = self._default_data()
            self.cache = data.copy()
            self.cache_time = now
            return data

    async def save(self, data: dict):
        async with self.lock:
            self.data_file.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
            self.cache = data.copy()
            self.cache_time = datetime.now()

    def _default_data(self) -> dict:
        return {
            "users": {},
            "quests": [],
            "album": [],
            "stats": {
                "total_bridges": 0,
                "total_quests": 0,
                "total_users": 0,
                "total_surprises": 0,
                "total_gifts": 0,
                "total_photos": 0,
                "started_at": datetime.now().isoformat()
            },
            "streaks": {},
            "leaderboard": {},
            "daily_rewards": {},
            "weather_cache": {},
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

    async def load_locations(self) -> dict:
        if self.locations_file.exists():
            return json.loads(self.locations_file.read_text(encoding="utf-8"))
        return {"locations": {}}

    async def save_locations(self, data: dict):
        self.locations_file.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    async def load_inventory(self) -> dict:
        if self.inventory_file.exists():
            return json.loads(self.inventory_file.read_text(encoding="utf-8"))
        return {"items": {}}

    async def save_inventory(self, data: dict):
        self.inventory_file.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    async def get_user(self, uid: str) -> dict:
        data = await self.load()
        return data["users"].get(uid, {})

    async def update_user(self, uid: str, updates: dict):
        data = await self.load()
        if uid in data["users"]:
            data["users"][uid].update(updates)
            await self.save(data)

db = Database()

# ══════════════════════════════════════════════════════════════════
# 🛠️ ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
# ══════════════════════════════════════════════════════════════════
def get_partner(data: dict, uid: str) -> Optional[dict]:
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
    if last == today:
        return
    elif last == (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d"):
        s["current"] += 1
        s["last_date"] = today
        s["best"] = max(s["best"], s["current"])
    elif last is None:
        s["current"] = 1
        s["last_date"] = today
        s["best"] = 1
    else:
        s["current"] = 1
        s["last_date"] = today

def progress_bar(progress: float, length: int = 15, filled_char: str = "█", empty_char: str = "░") -> str:
    p = min(max(progress, 0), 1)
    filled = int(length * p)
    return filled_char * filled + empty_char * (length - filled)

def star_rating(score: float, max_score: int = 10) -> str:
    s = min(max(int(score), 0), max_score)
    return "⭐" * s + "☆" * (max_score - s)

def is_admin(user_id: int) -> bool:
    return user_id == ADMIN_ID

def get_vip_multiplier(user: dict) -> float:
    vip = user.get("vip")
    if not vip:
        return 1.0
    try:
        end = datetime.fromisoformat(vip.get("end_date", "2000-01-01"))
        if datetime.now() > end:
            user["vip"] = None
            return 1.0
        level = vip.get("level", 1)
        return VIP_MULTIPLIERS.get(level, 1.0)
    except:
        return 1.0

def format_number(num: int) -> str:
    if num >= 1_000_000:
        return f"{num/1_000_000:.1f}M"
    elif num >= 1_000:
        return f"{num/1_000:.1f}K"
    return str(num)

def escape_html(text: str) -> str:
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

def get_time_ago(dt: datetime) -> str:
    delta = datetime.now() - dt
    if delta.days > 365:
        return f"{delta.days // 365} г. назад"
    elif delta.days > 30:
        return f"{delta.days // 30} мес. назад"
    elif delta.days > 0:
        return f"{delta.days} дн. назад"
    elif delta.seconds > 3600:
        return f"{delta.seconds // 3600} ч. назад"
    elif delta.seconds > 60:
        return f"{delta.seconds // 60} мин. назад"
    else:
        return "только что"

def get_fonts() -> dict:
    system = platform.system()
    candidates = []
    if system == "Linux":
        candidates = [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
        ]
    elif system == "Darwin":
        candidates = ["/System/Library/Fonts/Helvetica.ttc", "/Library/Fonts/Arial.ttf"]
    elif system == "Windows":
        candidates = ["C:\\Windows\\Fonts\\arial.ttf", "C:\\Windows\\Fonts\\arialbd.ttf"]
    
    fonts = {"bold": None, "regular": None, "small": None, "title": None}
    for path in candidates:
        if Path(path).exists():
            try:
                fonts["title"] = ImageFont.truetype(path, 36)
                fonts["bold"] = ImageFont.truetype(path, 24)
                fonts["regular"] = ImageFont.truetype(path, 18)
                fonts["small"] = ImageFont.truetype(path, 14)
                return fonts
            except:
                pass
    
    default = ImageFont.load_default()
    for key in fonts:
        fonts[key] = default
    return fonts

FONTS = get_fonts()

# ══════════════════════════════════════════════════════════════════
# ⌨️ КЛАВИАТУРЫ
# ══════════════════════════════════════════════════════════════════
class KeyboardManager:
    @staticmethod
    def main_menu(paired: bool = False, user_id: int = 0) -> InlineKeyboardMarkup:
        rows = []
        
        # Ряд 1: Основное
        rows.append([
            InlineKeyboardButton(text=f"{E.target} Квест", callback_data="quest_start"),
            InlineKeyboardButton(text=f"{E.album} Альбом", callback_data="album_menu"),
            InlineKeyboardButton(text=f"{E.stats_icon} Статистика", callback_data="stats_menu"),
        ])
        
        # Ряд 2: Достижения и прогресс
        rows.append([
            InlineKeyboardButton(text=f"{E.trophy} Достижения", callback_data="achievements_menu"),
            InlineKeyboardButton(text=f"{E.calendar} Ежедневное", callback_data="daily_menu"),
            InlineKeyboardButton(text=f"{E.medal} Рейтинг", callback_data="leaderboard_menu"),
        ])
        
        # Ряд 3: Социальное
        rows.append([
            InlineKeyboardButton(text=f"{E.users} Друзья", callback_data="friends_menu"),
            InlineKeyboardButton(text=f"{E.shop} Магазин", callback_data="shop_menu"),
            InlineKeyboardButton(text=f"{E.cart} Инвентарь", callback_data="inventory_menu"),
        ])
        
        # Ряд 4: Общение
        rows.append([
            InlineKeyboardButton(text=f"{E.letter} Открытка", callback_data="postcard_menu"),
            InlineKeyboardButton(text=f"{E.love} Комплимент", callback_data="compliment_send"),
            InlineKeyboardButton(text=f"{E.gift} Сюрприз", callback_data="surprise_send"),
        ])
        
        # Ряд 5: Инструменты
        rows.append([
            InlineKeyboardButton(text=f"{E.search} Анализ фото", callback_data="analyze_photo"),
            InlineKeyboardButton(text=f"{E.note} Заметки", callback_data="notes_menu"),
            InlineKeyboardButton(text=f"{E.bell} Напоминания", callback_data="reminders_menu"),
        ])
        
        # Ряд 6: Календарь
        rows.append([
            InlineKeyboardButton(text=f"{E.calendar} Календарь", callback_data="calendar_menu"),
            InlineKeyboardButton(text=f"{E.hourglass} Таймер", callback_data="countdown_menu"),
            InlineKeyboardButton(text=f"{E.party} События", callback_data="events_menu"),
        ])
        
        # Ряд 7: Информация
        rows.append([
            InlineKeyboardButton(text=f"{E.sun} Погода", callback_data="weather_menu"),
            InlineKeyboardButton(text=f"{E.globe} Часовые пояса", callback_data="timezone_menu"),
            InlineKeyboardButton(text=f"{E.map_marker} Карта", callback_data="map_menu"),
        ])
        
        # Ряд 8: Настройки и помощь
        rows.append([
            InlineKeyboardButton(text=f"{E.gear} Настройки", callback_data="settings_menu"),
            InlineKeyboardButton(text=f"{E.question} Помощь", callback_data="help_menu"),
            InlineKeyboardButton(text=f"{E.game} Игры", callback_data="games_menu"),
        ])
        
        # Админ-панель
        if is_admin(user_id):
            rows.append([
                InlineKeyboardButton(text=f"{E.crown} Админ-панель", callback_data="admin_panel")
            ])
        
        # Для не-пары
        if not paired:
            rows = [
                [InlineKeyboardButton(text=f"{E.key} 🔐 Ввести код пары", callback_data="pair_enter")],
                [InlineKeyboardButton(text=f"{E.users} ✨ Создать пару", callback_data="pair_create")],
                [InlineKeyboardButton(text=f"{E.question} ℹ️ Помощь", callback_data="help_menu")],
            ]
        
        return InlineKeyboardMarkup(inline_keyboard=rows)

    @staticmethod
    def back(callback: str = "main_menu") -> InlineKeyboardMarkup:
        return InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text=f"{E.back_arrow} Назад", callback_data=callback),
                InlineKeyboardButton(text=f"{E.home} В меню", callback_data="main_menu"),
            ]
        ])

    @staticmethod
    def location_keyboard() -> ReplyKeyboardMarkup:
        return ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text=f"{E.map_marker} 📍 Отправить геолокацию", request_location=True)]],
            resize_keyboard=True,
            one_time_keyboard=True
        )

    @staticmethod
    def confirm_keyboard(action: str) -> InlineKeyboardMarkup:
        return InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text=f"{E.check} Да", callback_data=f"confirm_{action}"),
                InlineKeyboardButton(text=f"{E.cross} Нет", callback_data="main_menu"),
            ]
        ])

    @staticmethod
    def pagination_keyboard(current_page: int, total_pages: int, prefix: str) -> InlineKeyboardMarkup:
        buttons = []
        if current_page > 0:
            buttons.append(InlineKeyboardButton(text=f"{E.back_arrow}", callback_data=f"{prefix}_{current_page-1}"))
        buttons.append(InlineKeyboardButton(text=f"{current_page+1}/{total_pages}", callback_data="noop"))
        if current_page < total_pages - 1:
            buttons.append(InlineKeyboardButton(text=f"{E.forward}", callback_data=f"{prefix}_{current_page+1}"))
        return InlineKeyboardMarkup(inline_keyboard=[buttons, [InlineKeyboardButton(text=f"{E.home} В меню", callback_data="main_menu")]])

K = KeyboardManager()

# ══════════════════════════════════════════════════════════════════
# 🤖 FSM СОСТОЯНИЯ
# ══════════════════════════════════════════════════════════════════
class UserStates(StatesGroup):
    # Пара
    waiting_pair_code = State()
    
    # Заметки
    waiting_note_text = State()
    waiting_note_edit = State()
    
    # Желания
    waiting_wish_text = State()
    
    # Напоминания
    waiting_reminder_text = State()
    waiting_reminder_time = State()
    
    # События
    waiting_event_name = State()
    waiting_event_date = State()
    waiting_event_type = State()
    
    # Таймер
    waiting_countdown_name = State()
    waiting_countdown_date = State()
    
    # Профиль
    waiting_bio = State()
    waiting_partner_bio = State()
    waiting_avatar = State()
    
    # Жалобы
    waiting_report = State()
    
    # Админ
    waiting_broadcast = State()
    waiting_give_coins = State()
    waiting_give_diamonds = State()
    waiting_give_xp = State()
    waiting_ban_user = State()
    
    # Друзья
    waiting_add_friend = State()
    waiting_accept_friend = State()
    
    # Чат с AI
    waiting_chat_message = State()
    
    # Голосование
    waiting_vote = State()
    waiting_suggest = State()
    
    # Поиск
    waiting_search = State()
    
    # Открытка
    waiting_postcard_text = State()

# ══════════════════════════════════════════════════════════════════
# 🤖 AI ФУНКЦИИ
# ══════════════════════════════════════════════════════════════════
async def ai_generate_quest(context: dict) -> dict:
    """Генерация уникального квеста через Gemini"""
    prompt = f"""
Ты — креативный AI для игры "Меридиан". Придумай УНИКАЛЬНОЕ парное фото-задание.

👤 {context.get('user1_name')} в городе {context.get('city1')}
Погода: {context.get('weather1_temp')}°C, {context.get('weather1_desc')}

👤 {context.get('user2_name')} в городе {context.get('city2')}
Погода: {context.get('weather2_temp')}°C, {context.get('weather2_desc')}

🕐 Время суток: {context.get('time_of_day')}
🌸 Сезон: {context.get('season')}
🌉 Номер моста: #{context.get('quest_number')}
📋 Предыдущие темы (НЕ ПОВТОРЯТЬ): {context.get('recent_themes', 'ещё не было')}
🎭 Режим: {context.get('mode', 'classic')}

СОЗДАЙ ЗАДАНИЕ:
1. theme — поэтичное название (3-6 слов)
2. legend — красивая легенда/метафора (2-3 предложения)
3. task1 — КОНКРЕТНОЕ фото-задание для {context.get('user1_name')} с учётом погоды ({context.get('weather1_desc')})
4. task2 — КОНКРЕТНОЕ фото-задание для {context.get('user2_name')} с учётом погоды ({context.get('weather2_desc')})
5. album_title — красивое название для альбома
6. mood — настроение (романтичное/весёлое/загадочное/уютное/энергичное)
7. difficulty — сложность 1-5
8. hint — подсказка если сложно
9. tags — 2-3 тэга (закат, кофе, природа и т.д.)

ОТВЕТЬ ТОЛЬКО JSON БЕЗ MARKDOWN:
{{"theme":"","legend":"","task1":"","task2":"","album_title":"","mood":"","difficulty":1,"hint":"","tags":[]}}"""
    
    try:
        response = await asyncio.to_thread(
            client.models.generate_content,
            model="gemini-2.0-flash",
            contents=prompt,
            config=genai_types.GenerateContentConfig(
                temperature=0.95,
                max_output_tokens=800,
                top_p=0.95
            )
        )
        text = response.text.strip()
        text = re.sub(r'^```(?:json)?\s*\n?', '', text)
        text = re.sub(r'\n?```\s*$', '', text)
        result = json.loads(text)
        return result
    except Exception as e:
        logger.error(f"AI quest generation failed: {e}")
        return {
            "theme": "Мост между мирами",
            "legend": "Два города, два взгляда — одна любовь",
            "task1": f"Сфоткай что-то красивое в твоём городе прямо сейчас",
            "task2": f"Найди и сфоткай что-то необычное вокруг себя",
            "album_title": "Параллельные миры",
            "mood": "романтичное",
            "difficulty": 2,
            "hint": "Оглянись — красота повсюду!",
            "tags": ["город", "любовь", "момент"]
        }

async def ai_analyze_photo(photo_path: str, task: str, user_name: str) -> dict:
    """AI анализирует фото на соответствие заданию"""
    try:
        with open(photo_path, "rb") as f:
            image_data = f.read()
        
        prompt = f"""
Ты — дружелюбный AI-критик в игре для влюблённых. Оцени фото.

📸 Фотограф: {user_name}
🎯 Задание: «{task}»

ОЦЕНИ:
1. match_score (1-10) — насколько фото соответствует заданию
2. creativity (1-10) — креативность исполнения
3. what_i_see — что изображено на фото (кратко)
4. comment — тёплый комментарий (1-2 предложения) на русском
5. mood — настроение фото
6. tips — совет как улучшить (если оценка <8)

ОТВЕТЬ ТОЛЬКО JSON:
{{"match_score":7,"creativity":7,"what_i_see":"","comment":"","mood":"","tips":""}}"""
        
        response = await asyncio.to_thread(
            client.models.generate_content,
            model="gemini-2.0-flash",
            contents=[prompt, genai_types.Part.from_bytes(data=image_data, mime_type="image/jpeg")],
            config=genai_types.GenerateContentConfig(temperature=0.7, max_output_tokens=400)
        )
        text = response.text.strip()
        text = re.sub(r'^```(?:json)?\s*\n?', '', text)
        text = re.sub(r'\n?```\s*$', '', text)
        return json.loads(text)
    except Exception as e:
        logger.error(f"AI photo analysis failed: {e}")
        return {
            "match_score": 7, "creativity": 7,
            "what_i_see": "что-то интересное",
            "comment": f"Отличная работа, {user_name}! Продолжай в том же духе!",
            "mood": "загадочное", "tips": ""
        }

async def ai_generate_compliment(name: str, style: str = "romantic") -> str:
    """Генерация комплимента"""
    prompt = f"Напиши ОДИН {style} комплимент для {name}. Только комплимент, без лишних слов."
    try:
        response = await asyncio.to_thread(
            client.models.generate_content,
            model="gemini-2.0-flash",
            contents=prompt,
            config=genai_types.GenerateContentConfig(temperature=1.0, max_output_tokens=150)
        )
        return response.text.strip()
    except:
        return f"{name}, ты самый замечательный человек в моей жизни! ✨"

async def ai_chat_response(message: str, context: list = None) -> str:
    """Общий AI-чат"""
    try:
        if context is None:
            context = []
        full_context = [
            "Ты — дружелюбный AI-помощник в игре Меридиан для пар на расстоянии.",
            "Отвечай тепло, с эмодзи, но кратко (1-3 предложения).",
            *context[-10:],  # Последние 10 сообщений
            f"Пользователь: {message}"
        ]
        response = await asyncio.to_thread(
            client.models.generate_content,
            model="gemini-2.0-flash",
            contents="\n".join(full_context),
            config=genai_types.GenerateContentConfig(temperature=0.9, max_output_tokens=300)
        )
        return response.text.strip()
    except:
        return "Я немного запутался, но я рядом! 💫"

# ══════════════════════════════════════════════════════════════════
# 🌤️ API ФУНКЦИИ
# ══════════════════════════════════════════════════════════════════
async def fetch_weather(lat: float, lon: float) -> dict:
    """Получение погоды с кэшированием"""
    cache_key = f"{lat:.2f}_{lon:.2f}"
    data = await db.load()
    cache = data.get("weather_cache", {})
    if cache_key in cache:
        cached = cache[cache_key]
        if datetime.now() - datetime.fromisoformat(cached["time"]) < timedelta(minutes=30):
            return cached["data"]
    
    try:
        url = (
            f"https://api.openweathermap.org/data/2.5/weather?"
            f"lat={lat}&lon={lon}&appid={OPENWEATHER_API_KEY}&units=metric&lang=ru"
        )
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(url)
            response.raise_for_status()
            j = response.json()
            result = {
                "temp": round(j["main"]["temp"]),
                "feels_like": round(j["main"]["feels_like"]),
                "desc": j["weather"][0]["description"],
                "icon": j["weather"][0]["icon"],
                "wind": round(j["wind"]["speed"], 1),
                "humidity": j["main"]["humidity"],
                "pressure": j["main"]["pressure"],
                "sunrise": j["sys"]["sunrise"],
                "sunset": j["sys"]["sunset"],
                "city": j.get("name", ""),
                "country": j.get("sys", {}).get("country", "")
            }
            data["weather_cache"][cache_key] = {
                "data": result,
                "time": datetime.now().isoformat()
            }
            await db.save(data)
            return result
    except Exception as e:
        logger.error(f"Weather API error: {e}")
        return {
            "temp": "?", "feels_like": "?", "desc": "неизвестно",
            "icon": "01d", "wind": "?", "humidity": "?", "pressure": "?",
            "sunrise": 0, "sunset": 0, "city": "", "country": ""
        }

async def reverse_geocode(lat: float, lon: float) -> str:
    """Обратное геокодирование"""
    try:
        url = f"https://nominatim.openstreetmap.org/reverse?lat={lat}&lon={lon}&format=json&accept-language=ru"
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(url, headers={"User-Agent": "MeridianBot/5.0"})
            response.raise_for_status()
            addr = response.json().get("address", {})
            return addr.get("city") or addr.get("town") or addr.get("village") or "Неизвестный город"
    except Exception as e:
        logger.error(f"Geocoding error: {e}")
        return "Неизвестный город"

# ══════════════════════════════════════════════════════════════════
# 🎨 КОЛЛАЖИ И ИЗОБРАЖЕНИЯ
# ══════════════════════════════════════════════════════════════════
async def create_collage(
    img1_path: str, img2_path: str,
    theme: str, city1: str, city2: str,
    quest_num: int, review1: dict = None, review2: dict = None,
    frame: str = None
) -> str:
    """Создание красивого коллажа с рамкой и текстом"""
    try:
        # Открываем изображения
        img1 = Image.open(img1_path).convert("RGB")
        img2 = Image.open(img2_path).convert("RGB")
        
        # Размеры
        photo_width, photo_height = 500, 400
        padding = 30
        header_height = 150
        footer_height = 100
        
        # Ресайз с сохранением пропорций
        img1.thumbnail((photo_width, photo_height), Image.LANCZOS)
        img2.thumbnail((photo_width, photo_height), Image.LANCZOS)
        
        # Размеры холста
        total_width = photo_width * 2 + padding * 3
        total_height = header_height + max(img1.height, img2.height) + footer_height + padding * 2
        
        # Создаём фон с градиентом
        bg = Image.new("RGB", (total_width, total_height))
        for y in range(total_height):
            # Градиент от тёмно-синего к тёмно-фиолетовому
            r = int(15 + 20 * y / total_height)
            g = int(10 + 15 * y / total_height)
            b = int(35 + 25 * y / total_height)
            for x in range(0, total_width, 4):
                for dx in range(4):
                    if x + dx < total_width:
                        bg.putpixel((x + dx, y), (r, g, b))
        
        draw = ImageDraw.Draw(bg)
        
        # Позиции фото
        x1, y1 = padding, header_height + padding
        x2 = x1 + photo_width + padding
        
        # Белые подложки с золотой рамкой
        for x, y in [(x1, y1), (x2, y1)]:
            draw.rectangle(
                [x-3, y-3, x+photo_width+3, y+photo_height+3],
                fill="white",
                outline=(255, 215, 0),
                width=2
            )
        
        # Вставляем фото
        bg.paste(img1, (x1, y1))
        bg.paste(img2, (x2, y1))
        
        # Текст заголовка
        draw.text(
            (padding, 20),
            f"Мост #{quest_num}",
            fill=(255, 255, 255),
            font=FONTS["title"]
        )
        draw.text(
            (padding, 70),
            theme[:60],
            fill=(255, 215, 0),
            font=FONTS["bold"]
        )
        
        # Города
        draw.text(
            (x1 + photo_width//2 - 40, y1 + photo_height + 10),
            f"📍 {city1}",
            fill=(200, 200, 200),
            font=FONTS["regular"]
        )
        draw.text(
            (x2 + photo_width//2 - 40, y1 + photo_height + 10),
            f"📍 {city2}",
            fill=(200, 200, 200),
            font=FONTS["regular"]
        )
        
        # AI-комментарии
        if review1 and review1.get("comment"):
            comment1 = review1["comment"][:80]
            draw.text(
                (x1, y1 + photo_height + 35),
                f"💬 {comment1}",
                fill=(255, 215, 0, 180),
                font=FONTS["small"]
            )
        if review2 and review2.get("comment"):
            comment2 = review2["comment"][:80]
            draw.text(
                (x2, y1 + photo_height + 35),
                f"💬 {comment2}",
                fill=(255, 215, 0, 180),
                font=FONTS["small"]
            )
        
        # Дата и время
        date_str = datetime.now().strftime("%d.%m.%Y • %H:%M")
        bbox = draw.textbbox((0, 0), date_str, font=FONTS["regular"])
        date_width = bbox[2] - bbox[0]
        draw.text(
            ((total_width - date_width) // 2, total_height - 50),
            date_str,
            fill=(150, 150, 150),
            font=FONTS["regular"]
        )
        
        # Декоративная линия
        draw.line(
            [(padding, total_height - 30), (total_width - padding, total_height - 30)],
            fill=(255, 215, 0, 80),
            width=1
        )
        
        # Сохраняем
        filename = f"bridge_{quest_num}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
        output_path = f"media/collages/{filename}"
        bg.save(output_path, quality=95)
        
        # Создаём превью
        preview = bg.copy()
        preview.thumbnail((300, 200), Image.LANCZOS)
        preview_path = f"media/thumbnails/{filename}"
        preview.save(preview_path, quality=80)
        
        return output_path
    
    except Exception as e:
        logger.error(f"Collage creation error: {e}")
        # Простой fallback
        img1 = Image.open(img1_path).resize((500, 400))
        img2 = Image.open(img2_path).resize((500, 400))
        combined = Image.new("RGB", (1000, 400))
        combined.paste(img1, (0, 0))
        combined.paste(img2, (500, 0))
        path = f"media/collages/fallback_{quest_num}.jpg"
        combined.save(path)
        return path

# ══════════════════════════════════════════════════════════════════
# 🗺️ КАРТА МЕСТОПОЛОЖЕНИЙ
# ══════════════════════════════════════════════════════════════════
async def save_user_location(uid: str, lat: float, lon: float, city: str, weather: dict):
    """Сохраняет местоположение пользователя"""
    locations = await db.load_locations()
    locations["locations"][uid] = {
        "lat": lat,
        "lon": lon,
        "city": city,
        "weather": weather,
        "updated_at": datetime.now().isoformat()
    }
    await db.save_locations(locations)

async def get_user_location(uid: str) -> Optional[dict]:
    """Получает последнее местоположение пользователя"""
    locations = await db.load_locations()
    return locations.get("locations", {}).get(uid)

async def get_partner_location(data: dict, uid: str) -> Optional[dict]:
    """Получает местоположение партнёра"""
    partner = get_partner(data, uid)
    if not partner:
        return None
    return await get_user_location(partner["id"])

async def generate_map_image(user1_loc: dict, user2_loc: dict) -> str:
    """Генерирует простую карту с двумя точками"""
    try:
        # Создаём изображение карты
        width, height = 800, 600
        img = Image.new("RGB", (width, height), (240, 248, 255))
        draw = ImageDraw.Draw(img)
        
        # Рисуем сетку
        for i in range(0, width, 50):
            draw.line([(i, 0), (i, height)], fill=(220, 230, 240), width=1)
        for i in range(0, height, 50):
            draw.line([(0, i), (width, i)], fill=(220, 230, 240), width=1)
        
        # Вычисляем позиции (упрощённо — центрируем)
        # В реальности нужно конвертировать координаты
        x1, y1 = 200, 250
        x2, y2 = 550, 300
        
        # Рисуем линию между точками (мост)
        draw.line([(x1, y1), (x2, y2)], fill=(255, 100, 100), width=3)
        
        # Рисуем точки
        for x, y, color, name in [
            (x1, y1, (255, 0, 0), user1_loc.get("city", "Ты")),
            (x2, y2, (0, 0, 255), user2_loc.get("city", "Партнёр"))
        ]:
            draw.ellipse([x-10, y-10, x+10, y+10], fill=color, outline="white", width=2)
            draw.text((x+15, y-25), name, fill=color, font=FONTS["bold"])
        
        # Заголовок
        draw.text((width//2 - 100, 30), "🌉 Карта Меридиана", fill=(50, 50, 50), font=FONTS["title"])
        
        # Расстояние
        if user1_loc.get("lat") and user2_loc.get("lat"):
            # Приблизительное расстояние
            lat1, lon1 = user1_loc["lat"], user1_loc["lon"]
            lat2, lon2 = user2_loc["lat"], user2_loc["lon"]
            # Формула гаверсинусов (упрощённо)
            R = 6371
            dlat = math.radians(lat2 - lat1)
            dlon = math.radians(lon2 - lon1)
            a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
            c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
            distance = R * c
            draw.text((width//2 - 80, height - 50), f"Расстояние: ~{distance:.0f} км", fill=(100, 100, 100), font=FONTS["regular"])
        
        path = f"media/maps/map_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
        img.save(path, quality=90)
        return path
    except Exception as e:
        logger.error(f"Map generation error: {e}")
        return None

# ══════════════════════════════════════════════════════════════════
# 👋 КОМАНДА /start
# ══════════════════════════════════════════════════════════════════
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    """Главная команда — приветствие и регистрация"""
    data = await db.load()
    uid = str(message.from_user.id)
    user = data["users"].get(uid)
    
    if not user:
        # Новый пользователь
        welcome_bonus_coins = 100
        welcome_bonus_diamonds = 10
        
        data["users"][uid] = {
            "id": uid,
            "name": message.from_user.first_name,
            "username": message.from_user.username,
            "full_name": message.from_user.full_name,
            "partner": None,
            "pair_code": None,
            "pair_code_created_at": None,
            
            # Статистика
            "quests_done": 0,
            "total_quests": 0,
            "xp": 0,
            "level": 1,
            "coins": welcome_bonus_coins,
            "diamonds": welcome_bonus_diamonds,
            "lp": 0,  # Love Points
            
            # Статус
            "vip": None,
            "booster": None,
            "rank": "Новичок",
            "title": "",
            
            # Профиль
            "avatar": None,
            "bio": "",
            "partner_bio": "",
            "favorite_theme": None,
            "favorite_mood": None,
            
            # Статистика
            "total_photos": 0,
            "perfect_scores": 0,
            "surprises_sent": 0,
            "surprises_received": 0,
            "gifts_sent": 0,
            "gifts_received": 0,
            "secret_done": False,
            "cities_visited": [],
            
            # Активность
            "joined_at": datetime.now().isoformat(),
            "last_active": datetime.now().isoformat(),
            "last_daily": None,
            "total_days_active": 0,
            
            # Социальное
            "referrals": 0,
            "referral_code": f"REF{uid[:6]}",
            
            # Настройки
            "settings": {
                "notifications": True,
                "theme": "dark",
                "language": "ru",
                "show_on_map": True,
                "auto_share_weather": True,
            },
            
            # Достижения
            "achievements": [],
            "favorite_achievement": None,
        }
        
        data["stats"]["total_users"] = data["stats"].get("total_users", 0) + 1
        await db.save(data)
        
        # Приветственное сообщение
        welcome_text = f"""
{LOGO_SMALL}

{E.sparkles} <b>ДОБРО ПОЖАЛОВАТЬ, {message.from_user.first_name.upper()}!</b> {E.sparkles}

{E.robot} Я — <b>Меридиан Ultimate</b> — самый мощный нейро-бот для пар на расстоянии!

{E.bridge} <b>Я превращаю километры в приключения!</b>

{E.star} <b>ВАШИ БОНУСЫ:</b>
• {E.coin} <b>{welcome_bonus_coins} монет</b>
• {E.diamond} <b>{welcome_bonus_diamonds} алмазов</b>

{E.robot} <b>60+ ФУНКЦИЙ:</b>

{E.brain} <b>AI-КВЕСТЫ</b> — нейросеть создаёт уникальные задания
{E.camera} <b>ПРОВЕРКА ФОТО</b> — AI оценивает каждый снимок
{E.album} <b>АЛЬБОМ</b> — красивые коллажи ваших приключений

{E.shop} <b>МАГАЗИН</b> — 30+ товаров: подарки, VIP, бустеры
{E.trophy} <b>ДОСТИЖЕНИЯ</b> — 30+ наград за успехи
{E.users} <b>ДРУЗЬЯ</b> — добавляй других игроков

{E.map_marker} <b>КАРТА</b> — смотри где твой партнёр
{E.calendar} <b>СОБЫТИЯ</b> — годовщины, таймеры, напоминания
{E.game} <b>ИГРЫ</b> — развлечения для двоих

{E.letter} <b>ОТКРЫТКИ</b> — AI пишет послания
{E.love} <b>КОМПЛИМЕНТЫ</b> — тёплые слова
{E.gift} <b>СЮРПРИЗЫ</b> — неожиданные задания

{E.info} <b>ЧТОБЫ НАЧАТЬ:</b>
1️⃣ Создайте пару (кнопка ниже)
2️⃣ Обменяйтесь кодами
3️⃣ Начните первый квест!

{E.robot} <i>Используй кнопки меню или команды /help</i>
"""
        await message.answer(welcome_text, reply_markup=K.main_menu(paired=False, user_id=message.from_user.id))
        
        # Логируем
        action_logger.info(f"New user registered: {uid} ({message.from_user.first_name})")
    
    else:
        # Существующий пользователь
        user["last_active"] = datetime.now().isoformat()
        user["name"] = message.from_user.first_name  # Обновляем имя
        
        # Проверяем стрик
        streaks = data.get("streaks", {})
        if uid in streaks:
            last_date = streaks[uid].get("last_date")
            if last_date:
                days_passed = (datetime.now() - datetime.strptime(last_date, "%Y-%m-%d")).days
                if days_passed > 1:
                    streaks[uid]["current"] = 0
                    await db.save(data)
        
        await db.save(data)
        
        paired = get_partner(data, uid) is not None
        rank = get_rank(user.get("xp", 0))
        streak = data.get("streaks", {}).get(uid, {}).get("current", 0)
        vip_mult = get_vip_multiplier(user)
        
        if paired:
            partner = get_partner(data, uid)
            partner_rank = get_rank(partner.get("xp", 0))
            
            # Получаем локации
            my_loc = await get_user_location(uid)
            partner_loc = await get_user_location(partner["id"])
            
            location_text = ""
            if my_loc and partner_loc:
                # Вычисляем примерное расстояние
                if my_loc.get("lat") and partner_loc.get("lat"):
                    lat1, lon1 = my_loc["lat"], my_loc["lon"]
                    lat2, lon2 = partner_loc["lat"], partner_loc["lon"]
                    R = 6371
                    dlat = math.radians(lat2 - lat1)
                    dlon = math.radians(lon2 - lon1)
                    a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
                    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
                    distance = R * c
                    location_text = f"\n{E.map_marker} <b>Расстояние:</b> ~{distance:.0f} км"
            
            welcome_back = f"""
{LOGO_SMALL}

{E.heart} <b>С ВОЗВРАЩЕНИЕМ!</b>

{E.person} <b>{user['name']}</b> {E.heart} <b>{partner.get('name', '...')}</b>

{E.star} <b>СТАТИСТИКА:</b>
{rank.emoji} <b>Ранг:</b> {rank.name}
{E.star} <b>XP:</b> {format_number(user.get('xp', 0))}
{E.coin} <b>Монет:</b> {format_number(user.get('coins', 0))}
{E.gem} <b>Алмазов:</b> {format_number(user.get('diamonds', 0))}
{E.fire} <b>Стрик:</b> {streak} дн. (лучший: {data.get('streaks', {}).get(uid, {}).get('best', 0)})
{E.target} <b>Квестов:</b> {user.get('quests_done', 0)}
{E.album} <b>Мостов:</b> {len(data['album'])}
{location_text}
{E.crown} <b>VIP:</b> {'x' + str(vip_mult) if vip_mult > 1 else 'Нет'}

{E.info} <i>Выбери действие в меню ↓</i>
"""
        else:
            welcome_back = f"""
{E.hand} <b>С возвращением, {user['name']}!</b>

{E.warning} <b>Ты ещё не в паре.</b>
Создай пару или введи код, чтобы начать игру!

{E.star} XP: {format_number(user.get('xp', 0))}
{E.coin} Монет: {format_number(user.get('coins', 0))}
"""
        
        await message.answer(welcome_back, reply_markup=K.main_menu(paired=paired, user_id=message.from_user.id))

# ══════════════════════════════════════════════════════════════════
# 🔙 ГЛАВНОЕ МЕНЮ (callback)
# ══════════════════════════════════════════════════════════════════
@dp.callback_query(F.data == "main_menu")
async def callback_main_menu(callback: types.CallbackQuery):
    """Возврат в главное меню"""
    data = await db.load()
    uid = str(callback.from_user.id)
    user = data["users"].get(uid, {})
    paired = get_partner(data, uid) is not None
    
    await callback.message.edit_text(
        f"{LOGO_SMALL}\n{E.robot} <b>Главное меню</b>\n{E.info} Выбери действие:",
        reply_markup=K.main_menu(paired=paired, user_id=callback.from_user.id)
    )
    await callback.answer()

# ══════════════════════════════════════════════════════════════════
# ℹ️ ПОМОЩЬ
# ══════════════════════════════════════════════════════════════════
@dp.message(Command("help"))
@dp.callback_query(F.data == "help_menu")
async def cmd_help(event: Union[types.Message, types.CallbackQuery]):
    """Показывает справку"""
    is_callback = isinstance(event, types.CallbackQuery)
    message = event.message if is_callback else event
    
    help_text = f"""
{E.info} <b>ПОМОЩЬ ПО МЕРИДИАНУ v{BOT_VERSION}</b>

{E.book} <b>ОСНОВНЫЕ КОМАНДЫ:</b>
/start — главное меню
/help — эта справка
/quest — начать квест
/album — альбом мостов
/stats — статистика
/profile — твой профиль
/partner — профиль партнёра

{E.letter} <b>ОБЩЕНИЕ:</b>
/postcard — отправить открытку
/compliment — отправить комплимент
/surprise — отправить сюрприз
/gift — подарить подарок

{E.shop} <b>МАГАЗИН И ПРОГРЕСС:</b>
/shop — магазин (30+ товаров)
/inventory — твой инвентарь
/achievements — достижения (30+)
/daily — ежедневная награда
/leaderboard — рейтинг игроков

{E.users} <b>СОЦИАЛЬНОЕ:</b>
/friends — список друзей
/addfriend — добавить друга
/accept — принять заявку

{E.map_marker} <b>ИНСТРУМЕНТЫ:</b>
/weather — погода
/timezone — часовые пояса
/map — карта (местоположение)
/notes — заметки
/reminder — напоминания
/wishlist — список желаний
/countdown — таймер обратного отсчёта
/calendar — календарь событий
/anniversary — установить годовщину
/birthday — установить день рождения

{E.game} <b>РАЗВЛЕЧЕНИЯ:</b>
/game — игры
/chat — поговорить с AI
/analyze — анализ фото
/vote — голосование за квесты
/suggest — предложить идею

{E.gear} <b>ПРОЧЕЕ:</b>
/settings — настройки
/setbio — описание профиля
/partnerbio — описание партнёра
/timeline — хронология отношений
/report — пожаловаться
/support — поддержка
/faq — частые вопросы
/privacy — конфиденциальность
/logout — разорвать пару
/deleteaccount — удалить аккаунт

{E.info} <i>Все функции также доступны через кнопки в меню!</i>
"""
    
    if is_callback:
        await message.edit_text(help_text, reply_markup=K.back())
        await event.answer()
    else:
        await message.answer(help_text)

# ══════════════════════════════════════════════════════════════════
# 👤 ПРОФИЛЬ
# ══════════════════════════════════════════════════════════════════
@dp.message(Command("profile"))
@dp.callback_query(F.data == "profile_menu")
async def cmd_profile(event: Union[types.Message, types.CallbackQuery]):
    """Показывает профиль пользователя"""
    is_callback = isinstance(event, types.CallbackQuery)
    message = event.message if is_callback else event
    uid = str(event.from_user.id)
    
    data = await db.load()
    user = data["users"].get(uid, {})
    
    if not user:
        text = "Профиль не найден. Используй /start"
        if is_callback:
            await message.edit_text(text)
            await event.answer()
        else:
            await message.answer(text)
        return
    
    rank, progress, xp_left = get_rank_progress(user.get("xp", 0))
    streak = data.get("streaks", {}).get(uid, {}).get("current", 0)
    best_streak = data.get("streaks", {}).get(uid, {}).get("best", 0)
    vip = user.get("vip", {})
    
    vip_text = "Нет"
    if vip:
        try:
            end_date = datetime.fromisoformat(vip.get("end_date", "2000-01-01"))
            if datetime.now() < end_date:
                days_left = (end_date - datetime.now()).days
                vip_text = f"VIP {vip.get('level', 1)} (ещё {days_left} дн.)"
        except:
            pass
    
    profile_text = f"""
{E.sparkles} <b>ПРОФИЛЬ: {user.get('name', 'Неизвестный').upper()}</b> {E.sparkles}

{E.person} <b>Основное:</b>
{E.star} <b>Ранг:</b> {rank.emoji} {rank.name}
{E.star} <b>XP:</b> {format_number(user.get('xp', 0))}
{E.coin} <b>Монет:</b> {format_number(user.get('coins', 0))}
{E.gem} <b>Алмазов:</b> {format_number(user.get('diamonds', 0))}
{E.heart} <b>LP:</b> {format_number(user.get('lp', 0))}

{E.target} <b>Активность:</b>
{E.target} <b>Квестов:</b> {user.get('quests_done', 0)}
{E.camera} <b>Фото:</b> {user.get('total_photos', 0)}
{E.fire} <b>Стрик:</b> {streak} дн. (рекорд: {best_streak})
{E.clock} <b>В игре:</b> с {user.get('joined_at', '?')[:10]}

{E.crown} <b>Статус:</b>
{E.crown} <b>VIP:</b> {vip_text}
{E.users} <b>Друзей:</b> {len([f for f in (await db.load_friends()).get('friendships', []) if f['user1'] == uid or f['user2'] == uid])}

{E.chart} <b>Прогресс:</b>
{progress_bar(progress)} {int(progress*100)}%
До {RANKS[min(RANKS.index(rank)+1, len(RANKS)-1)].name}: {xp_left} XP

{E.pen} <b>О себе:</b>
<i>{user.get('bio', 'Не заполнено')}</i>

{E.info} <i>/setbio чтобы изменить описание</i>
"""
    
    if is_callback:
        await message.edit_text(profile_text, reply_markup=K.back())
        await event.answer()
    else:
        await message.answer(profile_text)

# ══════════════════════════════════════════════════════════════════
# 🗺️ КАРТА
# ══════════════════════════════════════════════════════════════════
@dp.message(Command("map"))
@dp.callback_query(F.data == "map_menu")
async def cmd_map(event: Union[types.Message, types.CallbackQuery]):
    """Показывает карту с местоположением"""
    is_callback = isinstance(event, types.CallbackQuery)
    message = event.message if is_callback else event
    uid = str(event.from_user.id)
    
    data = await db.load()
    user = data["users"].get(uid, {})
    partner = get_partner(data, uid)
    
    if not partner:
        text = f"{E.warning} Нужна пара для просмотра карты!"
        if is_callback:
            await message.edit_text(text, reply_markup=K.back())
            await event.answer()
        else:
            await message.answer(text)
        return
    
    my_loc = await get_user_location(uid)
    partner_loc = await get_user_location(partner["id"])
    
    if not my_loc:
        text = f"{E.warning} Твоё местоположение не найдено. Отправь геолокацию через квест!"
        if is_callback:
            await message.edit_text(text, reply_markup=K.back())
            await event.answer()
        else:
            await message.answer(text)
        return
    
    if not partner_loc:
        text = f"{E.warning} Местоположение партнёра не найдено. Попроси партнёра отправить геолокацию!"
        if is_callback:
            await message.edit_text(text, reply_markup=K.back())
            await event.answer()
        else:
            await message.answer(text)
        return
    
    await message.answer(f"{E.map_marker} <b>Генерирую карту...</b>")
    
    map_path = await generate_map_image(my_loc, partner_loc)
    
    if map_path:
        with open(map_path, "rb") as f:
            photo = BufferedInputFile(f.read(), filename="map.jpg")
        
        # Расстояние
        lat1, lon1 = my_loc["lat"], my_loc["lon"]
        lat2, lon2 = partner_loc["lat"], partner_loc["lon"]
        R = 6371
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        distance = R * c
        
        caption = f"""
{E.map_marker} <b>КАРТА МЕРИДИАНА</b>

{E.person} <b>{user.get('name')}:</b> {my_loc.get('city', 'Неизвестно')}
{E.sun} {my_loc.get('weather', {}).get('temp', '?')}°C

{E.person} <b>{partner.get('name')}:</b> {partner_loc.get('city', 'Неизвестно')}
{E.sun} {partner_loc.get('weather', {}).get('temp', '?')}°C

{E.bridge} <b>Расстояние:</b> ~{distance:.0f} км
"""
        
        if is_callback:
            await message.answer_photo(photo, caption=caption)
            await event.answer("Карта готова!")
        else:
            await message.answer_photo(photo, caption=caption)
    else:
        text = f"{E.cross} Не удалось создать карту."
        if is_callback:
            await message.edit_text(text, reply_markup=K.back())
            await event.answer()
        else:
            await message.answer(text)

# ══════════════════════════════════════════════════════════════════
# 🔗 СОЗДАНИЕ ПАРЫ
# ══════════════════════════════════════════════════════════════════
@dp.message(Command("pair"))
@dp.callback_query(F.data == "pair_create")
async def cmd_pair_create(event: Union[types.Message, types.CallbackQuery]):
    """Создание кода пары"""
    is_callback = isinstance(event, types.CallbackQuery)
    message = event.message if is_callback else event
    uid = str(event.from_user.id)
    
    data = await db.load()
    code = str(random.randint(100000, 999999))
    data["users"][uid]["pair_code"] = code
    data["users"][uid]["pair_code_created_at"] = datetime.now().isoformat()
    await db.save(data)
    
    text = f"""
{E.key} <b>КОД ПАРЫ СОЗДАН!</b>

<code>{code}</code>

{E.info} <b>Инструкция:</b>
1️⃣ Отправь этот код своему партнёру
2️⃣ Партнёр вводит команду /accept {code}
3️⃣ Или нажимает кнопку «Ввести код пары»

{E.hourglass} <b>Код действителен 24 часа!</b>
"""
    
    if is_callback:
        await message.edit_text(text, reply_markup=K.back())
        await event.answer("Код создан!")
    else:
        await message.answer(text)

@dp.callback_query(F.data == "pair_enter")
async def callback_pair_enter(callback: types.CallbackQuery, state: FSMContext):
    """Запрос ввода кода пары"""
    await callback.message.answer(f"{E.lock} <b>Введи 6-значный код от партнёра:</b>")
    await state.set_state(UserStates.waiting_pair_code)
    await callback.answer()

@dp.message(Command("accept"))
@dp.message(UserStates.waiting_pair_code)
async def cmd_accept_pair(message: types.Message, state: FSMContext):
    """Принятие кода пары"""
    data = await db.load()
    uid = str(message.from_user.id)
    
    # Получаем код из команды или сообщения
    text = message.text.strip()
    if text.startswith("/accept"):
        parts = text.split()
        code = parts[1] if len(parts) > 1 else ""
    else:
        code = text
    
    if not code.isdigit() or len(code) != 6:
        await message.answer(f"{E.warning} Нужен 6-значный код. Попробуй ещё раз:")
        return
    
    # Ищем партнёра с таким кодом
    partner_id = None
    for pid, pdata in data["users"].items():
        if pdata.get("pair_code") == code and pid != uid:
            # Проверяем срок действия
            created_at = pdata.get("pair_code_created_at")
            if created_at:
                created = datetime.fromisoformat(created_at)
                if datetime.now() - created > timedelta(hours=24):
                    await message.answer(
                        f"{E.cross} <b>Код просрочен!</b>\nПопроси партнёра создать новый код.",
                        reply_markup=K.back()
                    )
                    await state.clear()
                    return
            partner_id = pid
            break
    
    if not partner_id:
        await message.answer(
            f"{E.cross} <b>Код не найден!</b>\nПроверь правильность кода.",
            reply_markup=K.back()
        )
        await state.clear()
        return
    
    # Связываем пару
    data["users"][uid]["partner"] = partner_id
    data["users"][partner_id]["partner"] = uid
    
    # Очищаем коды
    data["users"][uid]["pair_code"] = None
    data["users"][partner_id]["pair_code"] = None
    data["users"][uid]["pair_code_created_at"] = None
    data["users"][partner_id]["pair_code_created_at"] = None
    
    # Даём бонус за создание пары
    data["users"][uid]["xp"] = data["users"][uid].get("xp", 0) + 100
    data["users"][partner_id]["xp"] = data["users"][partner_id].get("xp", 0) + 100
    data["users"][uid]["coins"] = data["users"][uid].get("coins", 0) + 50
    data["users"][partner_id]["coins"] = data["users"][partner_id].get("coins", 0) + 50
    
    await db.save(data)
    
    name1 = data["users"][uid]["name"]
    name2 = data["users"][partner_id]["name"]
    
    success_text = f"""
{E.party}{E.party}{E.party} <b>ПАРА СОЗДАНА!</b> {E.party}{E.party}{E.party}

{E.heart} <b>{name1}</b> 💞 <b>{name2}</b>

{E.gift} <b>БОНУСЫ:</b>
{E.star} +100 XP каждому
{E.coin} +50 монет каждому

{E.target} <b>Что дальше?</b>
• Нажмите {E.target} <b>Квест</b> чтобы начать приключение!
• Отправьте друг другу {E.letter} <b>открытку</b>
• Исследуйте {E.shop} <b>магазин</b>

{E.info} <i>Удачи в построении мостов!</i>
"""
    
    await message.answer(success_text, reply_markup=K.main_menu(paired=True, user_id=message.from_user.id))
    
    # Уведомляем партнёра
    try:
        await bot.send_message(
            int(partner_id),
            success_text,
            reply_markup=K.main_menu(paired=True, user_id=int(partner_id))
        )
    except Exception as e:
        logger.warning(f"Failed to notify partner {partner_id}: {e}")
        await message.answer(f"{E.warning} Партнёр ещё не запускал бота. Попроси его написать /start")
    
    await state.clear()

# ══════════════════════════════════════════════════════════════════
# 🎯 КВЕСТЫ
# ══════════════════════════════════════════════════════════════════
@dp.message(Command("quest"))
@dp.callback_query(F.data == "quest_start")
async def cmd_quest_start(event: Union[types.Message, types.CallbackQuery]):
    """Начать новый квест"""
    is_callback = isinstance(event, types.CallbackQuery)
    message = event.message if is_callback else event
    uid = str(event.from_user.id)
    
    data = await db.load()
    user = data["users"].get(uid, {})
    partner = get_partner(data, uid)
    
    if not partner:
        text = f"{E.warning} Сначала создайте пару!"
        if is_callback:
            await message.edit_text(text, reply_markup=K.back())
            await event.answer()
        else:
            await message.answer(text)
        return
    
    # Проверяем, нет ли активного квеста
    for q in reversed(data["quests"]):
        if not q.get("done") and (q["user1_id"] == uid or q["user2_id"] == uid):
            text = f"""
{E.warning} <b>У вас уже есть активный квест!</b>

{E.bridge} <b>Мост #{q['id']}</b>
<i>{q.get('theme', '...')}</i>

{E.info} Завершите его — отправьте фото!
"""
            if is_callback:
                await message.edit_text(text, reply_markup=K.back())
                await event.answer()
            else:
                await message.answer(text)
            return
    
    text = f"""
{E.map_marker} <b>НОВЫЙ КВЕСТ!</b>

{E.info} Отправь свою геолокацию.
Партнёр тоже получит запрос.
Когда оба отправят — AI создаст уникальное задание!

{E.brain} <i>Нейросеть учитывает погоду, время суток и вашу историю</i>
"""
    
    if is_callback:
        await message.edit_text(text)
        await message.answer(
            f"{E.map_marker} <b>Нажми кнопку чтобы отправить геолокацию:</b>",
            reply_markup=K.location_keyboard()
        )
        await event.answer()
    else:
        await message.answer(text, reply_markup=K.location_keyboard())

@dp.message(F.location)
async def handle_location(message: types.Message):
    """Обработчик геолокации"""
    data = await db.load()
    uid = str(message.from_user.id)
    user = data["users"].get(uid)
    
    if not user or not get_partner(data, uid):
        await message.answer(
            f"{E.warning} Сначала создайте пару!",
            reply_markup=types.ReplyKeyboardRemove()
        )
        return
    
    lat = message.location.latitude
    lon = message.location.longitude
    
    # Получаем погоду и город
    weather = await fetch_weather(lat, lon)
    city = await reverse_geocode(lat, lon)
    
    # Сохраняем местоположение
    await save_user_location(uid, lat, lon, city, weather)
    
    # Сохраняем для квеста
    data[f"pending_{uid}"] = {
        "lat": lat,
        "lon": lon,
        "weather": weather,
        "city": city,
        "timestamp": datetime.now().isoformat()
    }
    
    # Добавляем город в список посещённых
    if city not in user.get("cities_visited", []):
        user["cities_visited"] = user.get("cities_visited", []) + [city]
    
    await db.save(data)
    
    partner = get_partner(data, uid)
    weather_emoji = {
        "ясно": E.sun, "облачно": E.cloud, "дождь": E.rain,
        "снег": E.snow, "гроза": E.zap, "туман": "🌫️"
    }.get(weather.get("desc", ""), E.world)
    
    await message.answer(
        f"""
{E.map_marker} <b>{city}</b>
{weather_emoji} <b>{weather['temp']}°C</b>, {weather['desc']}
💨 Ветер: {weather['wind']} м/с
💧 Влажность: {weather['humidity']}%

{E.clock} <b>Ожидаю геолокацию от {partner.get('name', 'партнёра')}...</b>
""",
        reply_markup=types.ReplyKeyboardRemove()
    )
    
    # Уведомляем партнёра
    try:
        await bot.send_message(
            int(partner["id"]),
            f"{E.map_marker} <b>{user['name']} уже на месте!</b>\n"
            f"{E.info} Отправь свою геолокацию для квеста!",
            reply_markup=K.location_keyboard()
        )
    except Exception as e:
        logger.warning(f"Failed to notify partner: {e}")
    
    # Если у партнёра тоже есть ожидающая геолокация — создаём квест
    if f"pending_{partner['id']}" in data:
        await create_quest_from_pending(message, uid, partner["id"], data)

async def create_quest_from_pending(message: types.Message, uid1: str, uid2: str, data: dict):
    """Создание квеста из ожидающих геолокаций"""
    p1 = data.pop(f"pending_{uid1}")
    p2 = data.pop(f"pending_{uid2}")
    
    w1, w2 = p1["weather"], p2["weather"]
    c1, c2 = p1["city"], p2["city"]
    
    u1 = data["users"][uid1]
    u2 = data["users"][uid2]
    
    # Получаем последние темы
    recent_quests = [q.get("theme", "") for q in data["quests"] if q.get("done")][-15:]
    quest_number = len(data["quests"]) + 1
    
    now = datetime.now()
    hour = now.hour
    month = now.month
    
    time_of_day = (
        "ночь 🌙" if 0 <= hour < 6 else
        "рассвет 🌅" if 6 <= hour < 8 else
        "утро ☀️" if 8 <= hour < 12 else
        "день 🌤️" if 12 <= hour < 17 else
        "вечер 🌅" if 17 <= hour < 21 else
        "ночь 🌙"
    )
    
    season = (
        "зима ❄️" if month in [12, 1, 2] else
        "весна 🌸" if month in [3, 4, 5] else
        "лето ☀️" if month in [6, 7, 8] else
        "осень 🍂"
    )
    
    await message.answer(f"{E.brain} <b>AI создаёт уникальный квест...</b>\n{E.magic} Анализирую погоду, время, историю...")
    
    context = {
        "user1_name": u1["name"],
        "user2_name": u2["name"],
        "city1": c1,
        "city2": c2,
        "weather1_temp": w1["temp"],
        "weather2_temp": w2["temp"],
        "weather1_desc": w1["desc"],
        "weather2_desc": w2["desc"],
        "time_of_day": time_of_day,
        "season": season,
        "quest_number": quest_number,
        "recent_themes": ", ".join(recent_quests) if recent_quests else "ещё не было квестов",
        "mode": "classic"
    }
    
    quest_data = await ai_generate_quest(context)
    
    # Создаём квест
    quest = {
        "id": quest_number,
        "date": now.isoformat(),
        "user1_id": uid1,
        "user2_id": uid2,
        "theme": quest_data.get("theme", "Мост"),
        "legend": quest_data.get("legend", ""),
        "task1": quest_data.get("task1", ""),
        "task2": quest_data.get("task2", ""),
        "album_title": quest_data.get("album_title", "Мост"),
        "mood": quest_data.get("mood", "романтичное"),
        "difficulty": quest_data.get("difficulty", 2),
        "tags": quest_data.get("tags", []),
        "hint": quest_data.get("hint", ""),
        "city1": c1,
        "city2": c2,
        "weather1": f"{w1['temp']}°C, {w1['desc']}",
        "weather2": f"{w2['temp']}°C, {w2['desc']}",
        "photo1": None,
        "photo2": None,
        "ai_review1": None,
        "ai_review2": None,
        "completing": False,
        "done": False
    }
    
    data["quests"].append(quest)
    data["stats"]["total_quests"] = data["stats"].get("total_quests", 0) + 1
    await db.save(data)
    
    # Отправляем задания
    for u_id, task, city, weather, uname in [
        (uid1, quest["task1"], c1, quest["weather1"], u1["name"]),
        (uid2, quest["task2"], c2, quest["weather2"], u2["name"])
    ]:
        quest_text = f"""
{E.bridge}{E.bridge}{E.bridge} <b>МОСТ #{quest_number}</b> {E.bridge}{E.bridge}{E.bridge}

{E.star} <i>«{quest['theme']}»</i>

{E.book} <b>Легенда:</b>
{quest['legend']}

{E.target} <b>ТВОЁ ЗАДАНИЕ, {uname}:</b>
{task}

{E.map_marker} <b>{city}</b>
{E.sun} <b>Погода:</b> {weather}
{E.magic} <b>Подсказка:</b> {quest['hint']}

{E.camera} <b>СДЕЛАЙ ФОТО И ОТПРАВЬ МНЕ!</b>
{E.robot} <i>AI проверит твой снимок и поставит оценку</i>
"""
        try:
            if u_id == uid1:
                await message.answer(quest_text)
            else:
                await bot.send_message(int(u_id), quest_text)
        except Exception as e:
            logger.error(f"Failed to send quest to {u_id}: {e}")

# ══════════════════════════════════════════════════════════════════
# 📸 ПРИЁМ ФОТО ДЛЯ КВЕСТА
# ══════════════════════════════════════════════════════════════════
@dp.message(F.photo)
async def handle_quest_photo(message: types.Message):
    """Обработчик фото для квеста"""
    data = await db.load()
    uid = str(message.from_user.id)
    
    # Ищем активный квест
    active_quest = None
    for q in reversed(data["quests"]):
        if not q.get("done") and (q["user1_id"] == uid or q["user2_id"] == uid):
            active_quest = q
            break
    
    if not active_quest:
        # Может быть, это фото для анализа?
        await message.answer(
            f"{E.warning} <b>Нет активного квеста!</b>\n"
            f"Используй /quest чтобы начать новый квест.\n"
            f"Или /analyze для анализа фото."
        )
        return
    
    # Проверяем, не завершается ли квест
    if active_quest.get("completing"):
        await message.answer(f"{E.clock} Квест уже завершается, подожди секунду...")
        return
    
    is_user1 = uid == active_quest["user1_id"]
    photo_field = "photo1" if is_user1 else "photo2"
    review_field = "ai_review1" if is_user1 else "ai_review2"
    task = active_quest["task1"] if is_user1 else active_quest["task2"]
    
    # Проверяем, не отправлял ли уже фото
    if active_quest.get(photo_field):
        await message.answer(f"{E.warning} Ты уже отправил фото для этого квеста! Ждём партнёра...")
        return
    
    try:
        # Сохраняем фото
        photo = message.photo[-1]
        file = await bot.get_file(photo.file_id)
        photo_path = f"media/photos/quest_{active_quest['id']}_user_{uid}.jpg"
        await bot.download_file(file.file_path, photo_path)
        
        active_quest[photo_field] = photo_path
        
        # Обновляем счётчик фото
        user_name = data["users"][uid]["name"]
        data["users"][uid]["total_photos"] = data["users"][uid].get("total_photos", 0) + 1
        
        # AI анализ
        await message.answer(f"{E.robot} <b>AI анализирует фото...</b>\n{E.eyes} Проверяю соответствие заданию...")
        
        review = await ai_analyze_photo(photo_path, task, user_name)
        active_quest[review_field] = review
        
        # Показываем результат
        score = review.get("match_score", 7)
        creativity = review.get("creativity", 7)
        
        review_text = f"""
{E.robot} <b>AI-РЕВЬЮ ДЛЯ {user_name.upper()}</b>

{E.eyes} <b>Что я вижу:</b>
{review.get('what_i_see', 'Что-то интересное')}

{E.target} <b>Соответствие заданию:</b> {score}/10
{star_rating(score)}

{E.palette} <b>Креативность:</b> {creativity}/10
{star_rating(creativity)}

{E.speech} <b>Комментарий AI:</b>
<i>«{review.get('comment', 'Отлично!')}»</i>

{E.art} <b>Настроение:</b> {review.get('mood', 'Загадочное')}
"""
        
        if review.get("tips"):
            review_text += f"\n{E.bulb} <b>Совет:</b> {review['tips']}"
        
        await message.answer(review_text)
        await db.save(data)
        
        # Проверяем, есть ли фото от партнёра
        other_photo = "photo2" if is_user1 else "photo1"
        if active_quest.get(other_photo) and not active_quest.get("completing"):
            await finalize_quest(data, active_quest, message)
        else:
            partner = get_partner(data, uid)
            await message.answer(
                f"{E.clock} <b>Ждём фото от {partner.get('name', 'партнёра')}...</b>\n"
                f"{E.info} Я сообщу когда квест будет завершён!"
            )
    
    except Exception as e:
        logger.error(f"Photo handling error: {e}")
        traceback.print_exc()
        await message.answer(f"{E.cross} <b>Ошибка обработки фото.</b>\nПопробуй ещё раз!")

async def finalize_quest(data: dict, quest: dict, message: types.Message):
    """Завершение квеста и создание коллажа"""
    if quest.get("completing"):
        return
    
    quest["completing"] = True
    await db.save(data)
    
    try:
        uid1, uid2 = quest["user1_id"], quest["user2_id"]
        user1 = data["users"][uid1]
        user2 = data["users"][uid2]
        
        review1 = quest.get("ai_review1") or {}
        review2 = quest.get("ai_review2") or {}
        
        # Создаём коллаж
        await message.answer(f"{E.brush} <b>Создаю коллаж...</b>")
        
        collage_path = await create_collage(
            quest["photo1"], quest["photo2"],
            quest["theme"],
            quest.get("city1", ""), quest.get("city2", ""),
            quest["id"],
            review1, review2
        )
        
        # Обновляем данные
        quest["done"] = True
        quest["collage"] = collage_path
        
        # Начисляем награды
        for uid, review in [(uid1, review1), (uid2, review2)]:
            if uid in data["users"]:
                user = data["users"][uid]
                
                # Базовые награды
                vip_mult = get_vip_multiplier(user)
                match_score = review.get("match_score", 7)
                creativity = review.get("creativity", 7)
                
                xp_earned = int((match_score + creativity) / 2 * 15 * vip_mult)
                coins_earned = int((match_score + creativity) / 2 * 5 * vip_mult)
                
                user["quests_done"] = user.get("quests_done", 0) + 1
                user["xp"] = user.get("xp", 0) + xp_earned
                user["coins"] = user.get("coins", 0) + coins_earned
                
                # Бонус за идеальное фото
                if match_score == 10:
                    user["perfect_scores"] = user.get("perfect_scores", 0) + 1
                    user["diamonds"] = user.get("diamonds", 0) + 1
        
        # Добавляем в альбом
        data["album"].append({
            "id": quest["id"],
            "date": quest["date"],
            "theme": quest["theme"],
            "album_title": quest["album_title"],
            "collage": collage_path,
            "ai_reviews": {"user1": review1, "user2": review2},
            "tags": quest.get("tags", []),
            "mood": quest.get("mood", "")
        })
        
        data["stats"]["total_bridges"] = len(data["album"])
        
        # Обновляем стрики
        streaks = data.setdefault("streaks", {})
        for uid in [uid1, uid2]:
            update_streak(streaks, uid)
        
        await db.save(data)
        
        # Проверяем достижения
        for uid in [uid1, uid2]:
            await check_user_achievements(data, uid, quest)
        
        # Отправляем коллаж
        with open(collage_path, "rb") as f:
            photo_bytes = f.read()
        
        avg_score = (review1.get("match_score", 7) + review2.get("match_score", 7)) / 2
        
        caption = f"""
{E.party}{E.party}{E.party} <b>МОСТ #{quest['id']} ПОСТРОЕН!</b> {E.party}{E.party}{E.party}

{E.frame} <i>«{quest['album_title']}»</i>

{E.star} <b>Оценка AI:</b> {avg_score:.1f}/10 {star_rating(int(avg_score))}

{E.album} <b>Мостов в альбоме:</b> {len(data['album'])}
{E.fire} <b>Стрик:</b> {streaks.get(uid1, {}).get('current', 0)} дней

{E.heart} <b>Спасибо за квест!</b>
"""
        
        photo_file = BufferedInputFile(photo_bytes, filename="collage.jpg")
        
        # Отправляем обоим
        for uid in [uid1, uid2]:
            try:
                await bot.send_photo(int(uid), photo_file, caption=caption)
            except Exception as e:
                logger.error(f"Failed to send collage to {uid}: {e}")
                try:
                    await bot.send_message(int(uid), caption)
                except:
                    pass
        
        quest_logger.info(f"Quest #{quest['id']} completed: {user1['name']} & {user2['name']}")
    
    except Exception as e:
        logger.error(f"Quest finalization error: {e}")
        traceback.print_exc()
        quest["completing"] = False
        await db.save(data)
        await message.answer(f"{E.cross} <b>Ошибка при создании коллажа.</b>\nНо ваши фото сохранены!")
        return
    
    quest["completing"] = False
    await db.save(data)

async def check_user_achievements(data: dict, uid: str, quest: dict = None):
    """Проверка и выдача достижений"""
    ach_data = await db.load_ach()
    user_achievements = ach_data.get(uid, [])
    user = data["users"].get(uid, {})
    quests_done = user.get("quests_done", 0)
    new_achievements = []
    
    # Проверяем условия
    checks = {
        "first_quest": quests_done >= 1,
        "5_quests": quests_done >= 5,
        "10_quests": quests_done >= 10,
        "25_quests": quests_done >= 25,
        "50_quests": quests_done >= 50,
        "100_quests": quests_done >= 100,
    }
    
    # Проверяем время
    if quest:
        quest_hour = datetime.fromisoformat(quest["date"]).hour
        checks["night_owl"] = quest_hour >= 23 or quest_hour < 1
        checks["dawn_patrol"] = 5 <= quest_hour < 7
        checks["morning_person"] = 7 <= quest_hour < 10 and user.get("morning_quests", 0) >= 3
    
    # Проверяем погоду
    if quest:
        weather_text = quest.get("weather1", "") + quest.get("weather2", "")
        checks["rain_dancer"] = "дождь" in weather_text
        checks["snow_angel"] = "снег" in weather_text
        checks["storm_chaser"] = "гроза" in weather_text
    
    # Стрики
    streak = data.get("streaks", {}).get(uid, {}).get("current", 0)
    checks["streak_3"] = streak >= 3
    checks["streak_7"] = streak >= 7
    checks["streak_14"] = streak >= 14
    checks["streak_30"] = streak >= 30
    
    # Качество
    if quest:
        review1 = quest.get("ai_review1") or {}
        review2 = quest.get("ai_review2") or {}
        checks["perfect_score"] = review1.get("match_score") == 10 and review2.get("match_score") == 10
        checks["creative_genius"] = review1.get("creativity") == 10 or review2.get("creativity") == 10
    
    # Социальное
    checks["first_surprise"] = user.get("surprises_sent", 0) >= 1
    checks["surprise_5"] = user.get("surprises_sent", 0) >= 5
    checks["surprise_20"] = user.get("surprises_sent", 0) >= 20
    checks["secret_finder"] = user.get("secret_done", False)
    
    # Друзья
    friends_data = await db.load_friends()
    friends_count = len([f for f in friends_data.get("friendships", []) if f["user1"] == uid or f["user2"] == uid])
    checks["first_friend"] = friends_count >= 1
    checks["5_friends"] = friends_count >= 5
    
    # Выдаём достижения
    for ach_id, condition in checks.items():
        if condition and ach_id not in user_achievements and ach_id in ACHIEVEMENTS:
            user_achievements.append(ach_id)
            new_achievements.append(ach_id)
    
    if new_achievements:
        ach_data[uid] = user_achievements
        await db.save_ach(ach_data)
        
        # Начисляем награды
        for ach_id in new_achievements:
            achievement = ACHIEVEMENTS[ach_id]
            user["xp"] = user.get("xp", 0) + achievement.xp_reward
            user["coins"] = user.get("coins", 0) + achievement.coins_reward
            if achievement.diamonds_reward:
                user["diamonds"] = user.get("diamonds", 0) + achievement.diamonds_reward
        
        await db.save(data)
        
        # Уведомляем о достижениях
        try:
            for ach_id in new_achievements:
                achievement = ACHIEVEMENTS[ach_id]
                await bot.send_message(
                    int(uid),
                    f"{E.trophy} <b>НОВОЕ ДОСТИЖЕНИЕ!</b>\n\n"
                    f"{achievement.emoji} <b>{achievement.name}</b>\n"
                    f"{achievement.description}\n\n"
                    f"{E.star} +{achievement.xp_reward} XP\n"
                    f"{E.coin} +{achievement.coins_reward} монет"
                    + (f"\n{E.gem} +{achievement.diamonds_reward} алмазов" if achievement.diamonds_reward else "")
                )
        except:
            pass

# ══════════════════════════════════════════════════════════════════
# 🏪 МАГАЗИН
# ══════════════════════════════════════════════════════════════════
@dp.message(Command("shop"))
@dp.callback_query(F.data == "shop_menu")
async def cmd_shop(event: Union[types.Message, types.CallbackQuery]):
    """Магазин товаров"""
    is_callback = isinstance(event, types.CallbackQuery)
    message = event.message if is_callback else event
    uid = str(event.from_user.id)
    
    data = await db.load()
    user = data["users"].get(uid, {})
    
    # Группируем по категориям
    builder = InlineKeyboardBuilder()
    
    for cat_id, cat_name in SHOP_CATEGORIES.items():
        builder.button(text=cat_name, callback_data=f"shop_cat_{cat_id}")
    
    builder.button(text=f"{E.cart} Инвентарь", callback_data="inventory_menu")
    builder.button(text=f"{E.back_arrow} Назад", callback_data="main_menu")
    builder.adjust(2)
    
    shop_text = f"""
{E.shop} <b>МАГАЗИН МЕРИДИАНА</b>

{E.coin} <b>Твой баланс:</b> {format_number(user.get('coins', 0))} монет
{E.gem} <b>Алмазов:</b> {format_number(user.get('diamonds', 0))}

{E.info} <b>Выбери категорию:</b>
"""
    
    if is_callback:
        await message.edit_text(shop_text, reply_markup=builder.as_markup())
        await event.answer()
    else:
        await message.answer(shop_text, reply_markup=builder.as_markup())

@dp.callback_query(F.data.startswith("shop_cat_"))
async def shop_category(callback: types.CallbackQuery):
    """Показывает товары категории"""
    cat_id = callback.data.replace("shop_cat_", "")
    cat_name = SHOP_CATEGORIES.get(cat_id, "Товары")
    
    data = await db.load()
    uid = str(callback.from_user.id)
    user = data["users"].get(uid, {})
    
    # Фильтруем товары
    items = {k: v for k, v in SHOP_ITEMS.items() if v.category == cat_id}
    
    builder = InlineKeyboardBuilder()
    
    for item_id, item in list(items.items())[:10]:  # Максимум 10 на страницу
        price_text = ""
        if item.price_coins > 0:
            price_text += f"{item.price_coins}🪙"
        if item.price_diamonds > 0:
            if price_text:
                price_text += " / "
            price_text += f"{item.price_diamonds}💎"
        
        builder.button(
            text=f"{item.emoji} {item.name} ({price_text})",
            callback_data=f"buy_{item_id}"
        )
    
    builder.button(text=f"{E.back_arrow} Назад", callback_data="shop_menu")
    builder.adjust(1)
    
    text = f"""
{E.shop} <b>{cat_name}</b>

{E.coin} Баланс: {format_number(user.get('coins', 0))} 🪙
{E.gem} Алмазов: {format_number(user.get('diamonds', 0))} 💎

{E.info} <i>Выбери товар для покупки:</i>
"""
    
    await callback.message.edit_text(text, reply_markup=builder.as_markup())
    await callback.answer()

@dp.callback_query(F.data.startswith("buy_"))
async def shop_buy_item(callback: types.CallbackQuery):
    """Покупка товара"""
    data = await db.load()
    uid = str(callback.from_user.id)
    user = data["users"].get(uid, {})
    
    item_id = callback.data.replace("buy_", "")
    item = SHOP_ITEMS.get(item_id)
    
    if not item:
        await callback.answer("Товар не найден!", show_alert=True)
        return
    
    # Проверяем баланс
    if item.price_coins > 0 and user.get("coins", 0) < item.price_coins:
        await callback.answer(f"Недостаточно монет! Нужно {item.price_coins}", show_alert=True)
        return
    
    if item.price_diamonds > 0 and user.get("diamonds", 0) < item.price_diamonds:
        await callback.answer(f"Недостаточно алмазов! Нужно {item.price_diamonds}", show_alert=True)
        return
    
    # Списываем валюту
    user["coins"] = user.get("coins", 0) - item.price_coins
    user["diamonds"] = user.get("diamonds", 0) - item.price_diamonds
    
    # Применяем эффект
    effect_applied = await apply_item_effect(data, uid, item)
    
    # Добавляем в инвентарь
    inventory = await db.load_inventory()
    if uid not in inventory["items"]:
        inventory["items"][uid] = []
    inventory["items"][uid].append({
        "item_id": item_id,
        "name": item.name,
        "emoji": item.emoji,
        "purchased_at": datetime.now().isoformat(),
        "used": False
    })
    await db.save_inventory(inventory)
    
    await db.save(data)
    
    # Отправляем подарок партнёру если это подарок
    partner = get_partner(data, uid)
    if partner and item.category == "gifts":
        gifts = await db.load_gifts()
        gifts["gifts_sent"].append({
            "from": uid,
            "to": partner["id"],
            "item": item_id,
            "date": datetime.now().isoformat()
        })
        await db.save_gifts(gifts)
        
        try:
            await bot.send_message(
                int(partner["id"]),
                f"{E.gift} <b>ТЫ ПОЛУЧИЛ ПОДАРОК!</b>\n\n"
                f"{item.emoji} <b>{item.name}</b>\n"
                f"От: {user['name']}\n\n"
                f"{item.description}"
            )
        except:
            pass
    
    await callback.answer(f"Куплено: {item.name}!", show_alert=True)
    
    # Обновляем магазин
    await shop_category(callback)

async def apply_item_effect(data: dict, uid: str, item: ShopItem) -> bool:
    """Применяет эффект купленного предмета"""
    user = data["users"].get(uid, {})
    
    if item.effect_type == "xp_bonus":
        user["xp"] = user.get("xp", 0) + item.effect_value
        return True
    
    elif item.effect_type == "coins_to_partner":
        partner = get_partner(data, uid)
        if partner:
            data["users"][partner["id"]]["coins"] = data["users"][partner["id"]].get("coins", 0) + item.effect_value
        return True
    
    elif item.effect_type == "coins":
        user["coins"] = user.get("coins", 0) + item.effect_value
        return True
    
    elif item.effect_type == "diamonds":
        user["diamonds"] = user.get("diamonds", 0) + item.effect_value
        return True
    
    elif item.effect_type == "lp_bonus":
        user["lp"] = user.get("lp", 0) + item.effect_value
        return True
    
    elif item.effect_type == "vip":
        end_date = datetime.now() + timedelta(days=item.duration_days)
        user["vip"] = {
            "level": item.effect_value,
            "end_date": end_date.isoformat(),
            "purchased_at": datetime.now().isoformat()
        }
        return True
    
    return True

# ══════════════════════════════════════════════════════════════════
# 📚 АЛЬБОМ
# ══════════════════════════════════════════════════════════════════
@dp.message(Command("album"))
@dp.callback_query(F.data == "album_menu")
async def cmd_album(event: Union[types.Message, types.CallbackQuery]):
    """Просмотр альбома"""
    is_callback = isinstance(event, types.CallbackQuery)
    message = event.message if is_callback else event
    
    data = await db.load()
    album = data.get("album", [])
    
    if not album:
        text = f"""
{E.album} <b>АЛЬБОМ ПУСТ</b>

{E.info} Выполните первый квест — и здесь появятся ваши мосты!

{E.target} /quest — начать квест
"""
        if is_callback:
            await message.edit_text(text, reply_markup=K.back())
            await event.answer()
        else:
            await message.answer(text)
        return
    
    # Показываем последние 5 коллажей
    recent = album[-5:]
    
    for entry in reversed(recent):
        collage_path = entry.get("collage", "")
        if collage_path and Path(collage_path).exists():
            with open(collage_path, "rb") as f:
                photo = BufferedInputFile(f.read(), filename="album.jpg")
            
            caption = f"""
{E.bridge} <b>Мост #{entry['id']}</b>
{E.frame} <i>{entry.get('album_title', '')}</i>
{E.clock} {entry.get('date', '')[:10]}
{E.art} Настроение: {entry.get('mood', '?')}
"""
            try:
                if is_callback:
                    await message.answer_photo(photo, caption=caption)
                else:
                    await message.answer_photo(photo, caption=caption)
            except:
                pass
    
    summary = f"""
{E.album} <b>АЛЬБОМ МОСТОВ</b>

{E.bridge} <b>Всего мостов:</b> {len(album)}
{E.clock} <b>Первый:</b> {album[0]['date'][:10]}
{E.star} <b>Последний:</b> {album[-1]['date'][:10]}

{E.info} <i>Показаны последние 5 мостов</i>
"""
    
    if is_callback:
        await message.answer(summary, reply_markup=K.back())
        await event.answer()
    else:
        await message.answer(summary)

# ══════════════════════════════════════════════════════════════════
# 📊 СТАТИСТИКА
# ══════════════════════════════════════════════════════════════════
@dp.message(Command("stats"))
@dp.callback_query(F.data == "stats_menu")
async def cmd_stats(event: Union[types.Message, types.CallbackQuery]):
    """Подробная статистика"""
    is_callback = isinstance(event, types.CallbackQuery)
    message = event.message if is_callback else event
    uid = str(event.from_user.id)
    
    data = await db.load()
    user = data["users"].get(uid, {})
    partner = get_partner(data, uid)
    
    if not partner:
        text = f"{E.warning} Нужна пара для статистики!"
        if is_callback:
            await message.edit_text(text, reply_markup=K.back())
            await event.answer()
        else:
            await message.answer(text)
        return
    
    rank, progress, xp_left = get_rank_progress(user.get("xp", 0))
    partner_rank, _, _ = get_rank_progress(partner.get("xp", 0))
    
    streak = data.get("streaks", {}).get(uid, {}).get("current", 0)
    partner_streak = data.get("streaks", {}).get(partner["id"], {}).get("current", 0)
    
    # Сравнение
    my_quests = user.get("quests_done", 0)
    partner_quests = partner.get("quests_done", 0)
    total_quests = my_quests + partner_quests
    
    quest_comparison = ""
    if my_quests > partner_quests:
        quest_comparison = f"Ты лидируешь на {my_quests - partner_quests} квестов!"
    elif partner_quests > my_quests:
        quest_comparison = f"Партнёр лидирует на {partner_quests - my_quests} квестов!"
    else:
        quest_comparison = "У вас равенство!"
    
    stats_text = f"""
{E.stats_icon} <b>СТАТИСТИКА ПАРЫ</b>

{E.heart} <b>{user['name']}</b> & <b>{partner.get('name', '?')}</b>

{E.chart} <b>СРАВНЕНИЕ:</b>
{E.person} <b>Ты:</b> {rank.emoji} {rank.name} ({format_number(user.get('xp', 0))} XP)
{E.person} <b>Партнёр:</b> {partner_rank.emoji} {partner_rank.name} ({format_number(partner.get('xp', 0))} XP)

{E.target} <b>Квесты:</b>
• Ты: {my_quests}
• Партнёр: {partner_quests}
• Всего: {total_quests}
{E.info} {quest_comparison}

{E.fire} <b>Стрики:</b>
• Твой: {streak} дн. (рекорд: {data.get('streaks', {}).get(uid, {}).get('best', 0)})
• Партнёра: {partner_streak} дн.

{E.album} <b>Мостов в альбоме:</b> {len(data['album'])}
{E.camera} <b>Всего фото:</b> {user.get('total_photos', 0)} + {partner.get('total_photos', 0)}

{E.coin} <b>Монет:</b> {format_number(user.get('coins', 0))} | {format_number(partner.get('coins', 0))}
{E.gem} <b>Алмазов:</b> {format_number(user.get('diamonds', 0))} | {format_number(partner.get('diamonds', 0))}

{E.chart} <b>ПРОГРЕСС:</b>
{progress_bar(progress)} {int(progress*100)}%
До {RANKS[min(RANKS.index(rank)+1, len(RANKS)-1)].name}: {xp_left} XP
"""
    
    if is_callback:
        await message.edit_text(stats_text, reply_markup=K.back())
        await event.answer()
    else:
        await message.answer(stats_text)

# ══════════════════════════════════════════════════════════════════
# 🚀 ЗАПУСК БОТА
# ══════════════════════════════════════════════════════════════════
async def main():
    """Главная функция запуска"""
    print(LOGO_FULL)
    print(f"🚀 Меридиан Ultimate v{BOT_VERSION} запускается...")
    print(f"📋 60+ команд • 30+ товаров • Карта • Новый Google AI")
    print(f"👑 Админ: {ADMIN_ID}")
    print(f"📂 Папки созданы")
    print(f"📊 30+ достижений")
    print(f"🏪 30+ товаров в магазине")
    print(f"🗺️ Система карт активна")
    print(f"{'='*60}")
    
    # Устанавливаем команды бота
    await bot.set_my_commands([
        BotCommand(command="start", description="🏠 Главное меню"),
        BotCommand(command="help", description="❓ Помощь по боту"),
        BotCommand(command="quest", description="🎯 Новый квест"),
        BotCommand(command="album", description="📸 Альбом мостов"),
        BotCommand(command="stats", description="📊 Статистика"),
        BotCommand(command="profile", description="👤 Мой профиль"),
        BotCommand(command="partner", description="💑 Профиль партнёра"),
        BotCommand(command="shop", description="🏪 Магазин"),
        BotCommand(command="map", description="🗺️ Карта"),
        BotCommand(command="friends", description="👥 Друзья"),
        BotCommand(command="notes", description="📝 Заметки"),
        BotCommand(command="weather", description="🌤️ Погода"),
        BotCommand(command="compliment", description="💖 Комплимент"),
        BotCommand(command="surprise", description="🎁 Сюрприз"),
        BotCommand(command="postcard", description="💌 Открытка"),
        BotCommand(command="daily", description="📅 Ежедневная награда"),
        BotCommand(command="leaderboard", description="🏆 Рейтинг"),
        BotCommand(command="achievements", description="🎖️ Достижения"),
        BotCommand(command="game", description="🎮 Игры"),
        BotCommand(command="chat", description="💬 Чат с AI"),
        BotCommand(command="settings", description="⚙️ Настройки"),
        BotCommand(command="support", description="🆘 Поддержка"),
    ])
    
    # Graceful shutdown
    def signal_handler(sig, frame):
        print(f"\n{E.cross} Завершение работы...")
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        logger.info("Bot started successfully!")
        await dp.start_polling(bot, skip_updates=True)
    except Exception as e:
        logger.critical(f"Bot crashed: {e}")
        traceback.print_exc()
    finally:
        await bot.session.close()
        logger.info("Bot stopped.")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print(f"\n{E.hand} До свидания!")
    except Exception as e:
        print(f"Fatal error: {e}")
        traceback.print_exc()