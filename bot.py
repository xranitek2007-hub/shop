"""
FrozenShop Bot — Полнофункциональный магазин игровых товаров
============================================================
Вдохновлён @buypinbot и @Cyber_DonateBot

Функции:
 - Каталог игр прямо в боте (кнопки)
 - Выбор товара → цена в сум и рублях
 - Автоматическая отправка реквизитов
 - Приём чека → уведомление тебе
 - Выбор: написать боту или @frozenld1 лично
 - Ты нажимаешь ✅ → покупатель получает "Выдан!"
 - История заказов для покупателя
 - Бонусы / промокоды
 - Рефералы
 - Рассылка
 - Полная статистика
 - Управление товарами из бота
"""

import asyncio, os, json, uuid, logging
from datetime import datetime, timedelta
from typing import Optional
from collections import defaultdict

from aiogram import Bot, Dispatcher, F
from aiogram.types import (
    Message, CallbackQuery,
    InlineKeyboardMarkup, InlineKeyboardButton,
    ReplyKeyboardMarkup, KeyboardButton,
    ReplyKeyboardRemove
)
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.utils.keyboard import InlineKeyboardBuilder

from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)

# ══════════════════════════════════════════════
#  ⚙️  НАСТРОЙКИ
# ══════════════════════════════════════════════
BOT_TOKEN   = os.getenv("BOT_TOKEN",   "8165503899:AAGlY0wz8vMqtWftiOXIDPTh95Gppk06FPs")
ADMIN_ID    = int(os.getenv("ADMIN_ID", "123456789"))   # ← ЗАМЕНИ свой TG ID
ADMIN_USER  = "frozenld1"                               # ← твой @username (без @)
BOT_USER    = "frozenld_bot"                            # ← username бота (без @)
WEBHOOK_URL = os.getenv("WEBHOOK_URL", "https://YOUR-APP.railway.app")
SITE_URL    = os.getenv("SITE_URL",    "https://YOUR-SITE.vercel.app")
PORT        = int(os.getenv("PORT", 8000))
RUB_RATE    = 150   # 1 сум = 1/150 руб → price_rub = price_sum / 150

CARDS = [
    {"bank": "HUMO", "num": "9860 1606 3787 3359", "raw": "9860160637873359", "owner": "Бухарбаев Бердах"},
    {"bank": "HUMO", "num": "9860 3501 4482 3951", "raw": "9860350144823951", "owner": "Бухарбаев Бердах"},
]
# ══════════════════════════════════════════════

bot  = Bot(token=BOT_TOKEN, parse_mode="HTML")
dp   = Dispatcher(storage=MemoryStorage())
app  = FastAPI(title="FrozenShop")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# ── In-memory DB ──────────────────────────────
orders:      dict[str, dict] = {}
users:       dict[int, dict] = {}   # uid → {name, username, joined, orders[], ref_by}
bonuses:     list[dict]      = []
referrals:   dict[int, list] = defaultdict(list)   # referrer_uid → [referred_uids]
# ──────────────────────────────────────────────

# ══════════════════════════════════════════════
#  📦 КАТАЛОГ ТОВАРОВ
# ══════════════════════════════════════════════
GAMES = [
    {"id": "mlbb",    "name": "Mobile Legends",     "emoji": "⚔️",  "sub": "Bang Bang"},
    {"id": "roblox",  "name": "Roblox",              "emoji": "🔴",  "sub": "Robux"},
    {"id": "genshin", "name": "Genshin Impact",      "emoji": "✨",  "sub": "Примогемы"},
    {"id": "pubg",    "name": "PUBG Mobile",         "emoji": "🪖",  "sub": "UC"},
    {"id": "ff",      "name": "Free Fire",           "emoji": "🔥",  "sub": "Diamonds"},
    {"id": "hsr",     "name": "Honkai: Star Rail",   "emoji": "🌟",  "sub": "Сущности"},
    {"id": "zzz",     "name": "Zenless Zone Zero",   "emoji": "⚡",  "sub": "Монохромы"},
    {"id": "hok",     "name": "Honor of Kings",      "emoji": "👑",  "sub": "Tokens"},
    {"id": "s2",      "name": "Standoff 2",          "emoji": "🔫",  "sub": "Голда"},
    {"id": "tgprem",  "name": "Telegram Premium",    "emoji": "💎",  "sub": "Подписка"},
    {"id": "jutsu",   "name": "Jutsu+",              "emoji": "🥷",  "sub": "Подписка"},
    {"id": "tggift",  "name": "Подарки Telegram",    "emoji": "🎁",  "sub": "Любому"},
    {"id": "stars",   "name": "Telegram Stars",      "emoji": "⭐",  "sub": "270 сум / ⭐"},
]

CATALOG = {
    "mlbb": [
        {"id":"m01","name":"11 💎",       "price":2500},
        {"id":"m02","name":"55 💎",       "price":13000},
        {"id":"m03","name":"110 💎",      "price":27000},
        {"id":"m04","name":"165 💎",      "price":35000},
        {"id":"m05","name":"275 💎",      "price":54000},
        {"id":"m06","name":"385 💎",      "price":75000},
        {"id":"m07","name":"514 💎",      "price":98000},
        {"id":"m08","name":"620 💎",      "price":120000},
        {"id":"m09","name":"792 💎",      "price":150000},
        {"id":"m10","name":"1036 💎",     "price":200000},
        {"id":"m11","name":"1584 💎",     "price":300000},
        {"id":"m12","name":"2195 💎",     "price":400000},
        {"id":"m13","name":"3688 💎",     "price":640000},
        {"id":"m14","name":"9288 💎",     "price":1590000},
        {"id":"mp1","name":"📅 Недельник",          "price":20000,  "desc":"Weekly Diamond Pass"},
        {"id":"mp2","name":"🌅 Сумеречный пропуск", "price":110000, "desc":"Twilight Pass"},
        {"id":"mp3","name":"🌙 Эпик набор (месяц)", "price":56000,  "desc":"275 алм + 180 авроры"},
        {"id":"md1","name":"50+50 💎 (двойные)",    "price":12000},
        {"id":"md2","name":"250+250 💎 (двойные)",  "price":53000},
    ],
    "roblox": [
        {"id":"r01","name":"50 Robux",   "price":11000, "desc":"5-7 дней · логин"},
        {"id":"r02","name":"100 Robux",  "price":19000, "desc":"5-7 дней · логин"},
        {"id":"r03","name":"200 Robux",  "price":35000, "desc":"5-7 дней · логин"},
        {"id":"r04","name":"400 Robux",  "price":60000, "desc":"5-7 дней · логин"},
        {"id":"r05","name":"800 Robux",  "price":115000,"desc":"Моментально · логин"},
        {"id":"r06","name":"1700 Robux", "price":280000,"desc":"Моментально · логин"},
        {"id":"r07","name":"4500 Robux", "price":680000,"desc":"Моментально · логин"},
        {"id":"r08","name":"100 Robux (промокод)","price":68000,"desc":"Без логина"},
        {"id":"r09","name":"800 Robux (промокод)","price":170000,"desc":"Без логина"},
    ],
    "genshin": [
        {"id":"g01","name":"60 🌙 камней",  "price":13000},
        {"id":"g02","name":"330 🌙 камней", "price":60000},
        {"id":"g03","name":"1090 🌙 камней","price":160000},
        {"id":"g04","name":"2240 🌙 камней","price":330000},
        {"id":"g05","name":"3880 🌙 камней","price":510000},
        {"id":"g06","name":"🌙 Луна (Welkin)","price":50000,"desc":"90 примогем/день × 30"},
        {"id":"g07","name":"📖 Battle Pass","price":125000},
    ],
    "pubg": [
        {"id":"p01","name":"325 UC",   "price":64000},
        {"id":"p02","name":"660 UC",   "price":120000},
        {"id":"p03","name":"985 UC",   "price":190000},
        {"id":"p04","name":"1320 UC",  "price":250000},
        {"id":"p05","name":"2460 UC",  "price":450000},
        {"id":"p06","name":"5650 UC",  "price":900000},
        {"id":"p07","name":"16200 UC", "price":2300000},
    ],
    "ff": [
        {"id":"f01","name":"100 💎",  "price":26000},
        {"id":"f02","name":"200 💎",  "price":50000},
        {"id":"f03","name":"500 💎",  "price":90000},
        {"id":"f04","name":"1000 💎", "price":165000},
        {"id":"f05","name":"3000 💎", "price":400000},
    ],
    "hsr": [
        {"id":"h01","name":"60 ✨",   "price":13000},
        {"id":"h02","name":"330 ✨",  "price":60000},
        {"id":"h03","name":"1090 ✨", "price":160000},
        {"id":"h04","name":"2240 ✨", "price":330000},
        {"id":"h05","name":"3880 ✨", "price":510000},
        {"id":"h06","name":"📦 Supply Pass","price":50000,"desc":"Express Supply Pass"},
    ],
    "zzz": [
        {"id":"z01","name":"60 ⚡",   "price":13000},
        {"id":"z02","name":"330 ⚡",  "price":59000},
        {"id":"z03","name":"1090 ⚡", "price":180000},
        {"id":"z04","name":"2240 ⚡", "price":370000},
        {"id":"z05","name":"3880 ⚡", "price":590000},
    ],
    "hok": [
        {"id":"k01","name":"80 Tokens",   "price":15000},
        {"id":"k02","name":"400 Tokens",  "price":70000},
        {"id":"k03","name":"830 Tokens",  "price":130000},
        {"id":"k04","name":"2508 Tokens", "price":355000},
        {"id":"k05","name":"8360 Tokens", "price":1200000},
    ],
    "s2": [
        {"id":"s01","name":"100 🪙",  "price":26000},
        {"id":"s02","name":"300 🪙",  "price":76000},
        {"id":"s03","name":"500 🪙",  "price":90000},
        {"id":"s04","name":"1000 🪙", "price":165000},
        {"id":"s05","name":"3000 🪙", "price":400000},
    ],
    "tgprem": [
        {"id":"tp1","name":"1 мес Premium (с входом)",  "price":38000},
        {"id":"tp2","name":"3 мес Premium (подарок)",   "price":170000},
        {"id":"tp3","name":"6 мес Premium (подарок)",   "price":225000},
        {"id":"tp4","name":"12 мес Premium (с входом)", "price":280000},
        {"id":"tp5","name":"12 мес Premium (подарок)",  "price":400000},
    ],
    "jutsu": [
        {"id":"j01","name":"1 месяц Jutsu+",  "price":15000},
        {"id":"j02","name":"6 месяцев Jutsu+","price":85000},
    ],
    "tggift": [
        {"id":"tg1","name":"🌹 Роза (1 подарок)",         "price":6500},
        {"id":"tg2","name":"🎂🌹🚀 Набор (5 подарков)",   "price":12000},
        {"id":"tg3","name":"🏆💍💎 Премиум (3 подарка)",  "price":23500},
    ],
    "stars": [
        {"id":"st1","name":"50 ⭐",      "price":13500},
        {"id":"st2","name":"100 ⭐",     "price":27000},
        {"id":"st3","name":"250 ⭐",     "price":67500},
        {"id":"st4","name":"500 ⭐",     "price":130950, "desc":"-3% бонус"},
        {"id":"st5","name":"1000 ⭐",    "price":261900, "desc":"-3% бонус"},
        {"id":"st6","name":"5000 ⭐",    "price":1309500,"desc":"-3% бонус"},
        {"id":"st7","name":"10000 ⭐",   "price":2619000,"desc":"-3% бонус"},
    ],
}


# ══════════════════════════════════════════════
#  FSM States
# ══════════════════════════════════════════════
class OrderState(StatesGroup):
    game_id   = State()
    item_id   = State()
    game_data = State()   # ID игры, ник и т.д.

class BonusAdd(StatesGroup):
    title = State(); desc = State(); code = State()

class Broadcast(StatesGroup):
    text = State()

class AddProduct(StatesGroup):
    game = State(); name = State(); price = State(); desc = State()


# ══════════════════════════════════════════════
#  UTILS
# ══════════════════════════════════════════════
def fmt(n: int) -> str:
    return f"{int(n):,}".replace(",", "\u202f")

def rub(s: int) -> str:
    return fmt(max(1, round(int(s) / RUB_RATE)))

def now_str() -> str:
    return datetime.now().isoformat()

def short_id(oid: str) -> str:
    return oid[:8].upper()

def get_game(gid: str) -> dict:
    return next((g for g in GAMES if g["id"] == gid), {"name": gid, "emoji": "🎮"})

def get_item(gid: str, iid: str) -> Optional[dict]:
    return next((i for i in CATALOG.get(gid, []) if i["id"] == iid), None)

def ensure_user(u) -> dict:
    if u.id not in users:
        users[u.id] = {
            "id": u.id, "name": u.full_name,
            "username": u.username or "",
            "joined": now_str(), "orders": [],
            "ref_by": None, "ref_count": 0,
        }
    return users[u.id]

def price_line(price: int) -> str:
    return f"<b>{fmt(price)} сум</b>  (~{rub(price)} ₽)"

def cards_text(price: int = 0) -> str:
    lines = ["💳 <b>Реквизиты для оплаты:</b>\n"]
    if price:
        lines.append(f"💰 Переведите ровно <b>{fmt(price)} сум</b>\n")
    for c in CARDS:
        lines += [f"<b>{c['bank']}</b>", f"<code>{c['num']}</code>", f"👤 {c['owner']}", ""]
    lines.append("📸 После оплаты выберите куда отправить скриншот 👇")
    return "\n".join(lines)

def receipt_choice_kb(order_id: str) -> InlineKeyboardMarkup:
    """Кнопки выбора куда отправить чек"""
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text=f"🤖 Отправить боту @{BOT_USER}",
                             callback_data=f"receipt_here:{order_id}"),
    ],[
        InlineKeyboardButton(text=f"👤 Написать лично @{ADMIN_USER}",
                             url=f"https://t.me/{ADMIN_USER}"),
    ]])

def order_admin_kb(order_id: str, buyer_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="✅ Выдан",    callback_data=f"done:{order_id}"),
        InlineKeyboardButton(text="❌ Отклонён", callback_data=f"reject:{order_id}"),
    ],[
        InlineKeyboardButton(text="💬 Написать покупателю", url=f"tg://user?id={buyer_id}"),
    ]])

def format_order_admin(o: dict) -> str:
    g = get_game(o.get("gid",""))
    ts = datetime.fromisoformat(o["date"]).strftime("%d.%m.%Y %H:%M")
    st = {"pending":"⏳","done":"✅","rejected":"❌"}.get(o["status"],"⏳")
    uname = ("@" + o["buyer_username"]) if o.get("buyer_username") else "—"
    return (
        f"🛒 <b>ЗАКАЗ #{short_id(o['id'])}</b>  {st}\n\n"
        f"{g['emoji']} <b>{g['name']}</b>  •  {o.get('name','—')}\n"
        f"💰 {price_line(o.get('price',0))}\n\n"
        f"👤 {o.get('buyer_name','?')}  {uname}\n"
        f"🆔 <code>{o.get('buyer_id','?')}</code>  •  🕐 {ts}"
        + (f"\n📝 <i>{o['game_data']}</i>" if o.get("game_data") else "")
    )

def format_order_buyer(o: dict) -> str:
    g = get_game(o.get("gid",""))
    st = {"pending":"⏳ Ожидает","done":"✅ Выдан!","rejected":"❌ Отклонён"}.get(o["status"],"⏳")
    return (
        f"{g['emoji']} <b>{o.get('name','—')}</b>\n"
        f"💰 {fmt(o.get('price',0))} сум  •  Статус: {st}\n"
        f"📋 ID: <code>{short_id(o['id'])}</code>"
    )


# ══════════════════════════════════════════════
#  KEYBOARDS
# ══════════════════════════════════════════════
def main_kb(is_admin: bool = False) -> ReplyKeyboardMarkup:
    if is_admin:
        return ReplyKeyboardMarkup(keyboard=[
            [KeyboardButton(text="📋 Заказы"),      KeyboardButton(text="⏳ Ожидающие")],
            [KeyboardButton(text="📊 Статистика"),  KeyboardButton(text="👥 Пользователи")],
            [KeyboardButton(text="🎁 Бонусы"),      KeyboardButton(text="📢 Рассылка")],
            [KeyboardButton(text="➕ Добавить товар")],
        ], resize_keyboard=True)
    return ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text="🛒 Каталог"),       KeyboardButton(text="📦 Мои заказы")],
        [KeyboardButton(text="🎁 Бонусы"),        KeyboardButton(text="👥 Рефералы")],
        [KeyboardButton(text="💬 Поддержка"),     KeyboardButton(text="🌐 Сайт")],
        [KeyboardButton(text="ℹ️ О магазине")],
    ], resize_keyboard=True)

def games_kb() -> InlineKeyboardMarkup:
    bld = InlineKeyboardBuilder()
    for g in GAMES:
        bld.button(text=f"{g['emoji']} {g['name']}", callback_data=f"game:{g['id']}")
    bld.adjust(2)
    return bld.as_markup()

def items_kb(gid: str, page: int = 0) -> InlineKeyboardMarkup:
    items = CATALOG.get(gid, [])
    per_page = 8
    start = page * per_page
    chunk = items[start:start + per_page]
    bld = InlineKeyboardBuilder()
    for item in chunk:
        price_txt = f"{fmt(item['price'])} сум"
        bld.button(
            text=f"{item['name']}  —  {price_txt}",
            callback_data=f"item:{gid}:{item['id']}"
        )
    bld.adjust(1)
    # Pagination
    nav = []
    if page > 0:
        nav.append(InlineKeyboardButton(text="⬅️ Назад", callback_data=f"page:{gid}:{page-1}"))
    if start + per_page < len(items):
        nav.append(InlineKeyboardButton(text="Ещё ➡️", callback_data=f"page:{gid}:{page+1}"))
    if nav:
        bld.row(*nav)
    bld.row(InlineKeyboardButton(text="🔙 К играм", callback_data="catalog"))
    return bld.as_markup()

def confirm_kb(gid: str, iid: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="✅ Подтвердить заказ", callback_data=f"confirm:{gid}:{iid}"),
        InlineKeyboardButton(text="❌ Отмена", callback_data=f"game:{gid}"),
    ]])


# ══════════════════════════════════════════════
#  /start  — с реферальной ссылкой
# ══════════════════════════════════════════════
@dp.message(CommandStart())
async def cmd_start(msg: Message, state: FSMContext):
    await state.clear()
    u = ensure_user(msg.from_user)

    # Реферал через /start ref_ID
    args = msg.text.split(maxsplit=1)
    if len(args) > 1 and u.get("ref_by") is None:
        try:
            ref_id = int(args[1].replace("ref_", ""))
            if ref_id != msg.from_user.id and ref_id in users:
                u["ref_by"] = ref_id
                users[ref_id]["ref_count"] = users[ref_id].get("ref_count", 0) + 1
                referrals[ref_id].append(msg.from_user.id)
                try:
                    await bot.send_message(ref_id,
                        f"🎉 По вашей реферальной ссылке зарегистрировался новый пользователь!\n"
                        f"👤 {msg.from_user.full_name}")
                except: pass
        except: pass

    is_admin = msg.from_user.id == ADMIN_ID

    if is_admin:
        await msg.answer(
            "👋 <b>FrozenShop Admin Panel</b>\n\n"
            f"🤖 Бот: @{BOT_USER}\n"
            "📦 Заказы с сайта и бота приходят сюда автоматически.\n\n"
            "Используй кнопки ниже 👇",
            reply_markup=main_kb(True)
        )
    else:
        await msg.answer(
            f"👋 <b>Добро пожаловать в FrozenShop!</b>\n\n"
            f"🎮 Алмазы, валюта, пропуска — всё для ваших игр\n"
            f"⚡ Доставка от 5 минут • 24/7\n"
            f"💎 Лучшие цены в Узбекистане\n\n"
            f"Выберите действие 👇",
            reply_markup=main_kb()
        )


# ══════════════════════════════════════════════
#  КАТАЛОГ
# ══════════════════════════════════════════════
@dp.message(F.text == "🛒 Каталог")
async def catalog_menu(msg: Message):
    ensure_user(msg.from_user)
    await msg.answer("🎮 <b>Выберите игру:</b>", reply_markup=games_kb())


@dp.callback_query(F.data == "catalog")
async def cb_catalog(cb: CallbackQuery):
    await cb.message.edit_text("🎮 <b>Выберите игру:</b>", reply_markup=games_kb())
    await cb.answer()


@dp.callback_query(F.data.startswith("game:"))
async def cb_game(cb: CallbackQuery, state: FSMContext):
    gid = cb.data.split(":", 1)[1]
    g = get_game(gid)
    items = CATALOG.get(gid, [])
    if not items:
        await cb.answer("Товары временно недоступны", show_alert=True)
        return
    await state.update_data(game_id=gid)
    await cb.message.edit_text(
        f"{g['emoji']} <b>{g['name']}</b> — {g['sub']}\n\n"
        f"Выберите товар:",
        reply_markup=items_kb(gid)
    )
    await cb.answer()


@dp.callback_query(F.data.startswith("page:"))
async def cb_page(cb: CallbackQuery):
    _, gid, page_str = cb.data.split(":", 2)
    g = get_game(gid)
    await cb.message.edit_text(
        f"{g['emoji']} <b>{g['name']}</b>\n\nВыберите товар:",
        reply_markup=items_kb(gid, int(page_str))
    )
    await cb.answer()


@dp.callback_query(F.data.startswith("item:"))
async def cb_item(cb: CallbackQuery, state: FSMContext):
    _, gid, iid = cb.data.split(":", 2)
    item = get_item(gid, iid)
    g = get_game(gid)
    if not item:
        await cb.answer("Товар не найден", show_alert=True)
        return

    await state.update_data(game_id=gid, item_id=iid)
    price = item["price"]
    desc_line = f"\n📝 {item['desc']}" if item.get("desc") else ""

    await cb.message.edit_text(
        f"{g['emoji']} <b>{g['name']}</b>\n"
        f"📦 <b>{item['name']}</b>{desc_line}\n\n"
        f"💰 {price_line(price)}\n\n"
        f"Подтвердить заказ?",
        reply_markup=confirm_kb(gid, iid)
    )
    await cb.answer()


@dp.callback_query(F.data.startswith("confirm:"))
async def cb_confirm(cb: CallbackQuery, state: FSMContext):
    _, gid, iid = cb.data.split(":", 2)
    item = get_item(gid, iid)
    g = get_game(gid)
    if not item:
        await cb.answer("Товар не найден", show_alert=True)
        return

    await state.update_data(game_id=gid, item_id=iid)
    await state.set_state(OrderState.game_data)

    # Подсказка какие данные нужны
    hints = {
        "mlbb":    "Введи <b>ID и сервер</b>\nПример: <code>1510395929 (16321)</code>",
        "roblox":  "Введи <b>логин и пароль</b> аккаунта Roblox",
        "genshin": "Введи <b>UID и сервер</b> (найти в профиле игры)",
        "pubg":    "Введи <b>ID персонажа</b> (в профиле PUBG)",
        "ff":      "Введи <b>ID аккаунта</b> Free Fire",
        "hsr":     "Введи <b>UID</b> (в профиле игры)",
        "zzz":     "Введи <b>UID</b> (в профиле игры)",
        "hok":     "Введи <b>ID</b> Honor of Kings",
        "s2":      "Введи <b>ID</b> Standoff 2",
        "tgprem":  "Введи <b>@username или номер</b> аккаунта для Premium",
        "jutsu":   "Введи <b>@username</b> аккаунта Jutsu+",
        "tggift":  "Введи <b>@username или номер</b> получателя подарка",
        "stars":   "Введи <b>@username</b> Telegram для отправки звёзд",
    }
    hint = hints.get(gid, "Введи необходимые данные для заказа")

    await cb.message.edit_text(
        f"📋 <b>Данные для заказа</b>\n\n"
        f"{hint}\n\n"
        f"<i>Или напиши /skip если данные не нужны</i>"
    )
    await cb.answer()


@dp.message(OrderState.game_data)
async def order_data_received(msg: Message, state: FSMContext):
    data = await state.get_data()
    gid = data.get("game_id")
    iid = data.get("item_id")
    game_data = msg.text if msg.text != "/skip" else None

    await _place_order(msg, state, gid, iid, game_data)


@dp.message(Command("skip"))
async def cmd_skip(msg: Message, state: FSMContext):
    current = await state.get_state()
    if current == OrderState.game_data:
        data = await state.get_data()
        await _place_order(msg, state, data.get("game_id"), data.get("item_id"), None)


async def _place_order(msg: Message, state: FSMContext, gid: str, iid: str, game_data: Optional[str]):
    await state.clear()
    item = get_item(gid, iid)
    g = get_game(gid)
    if not item:
        await msg.answer("Ошибка: товар не найден.")
        return

    u = ensure_user(msg.from_user)
    order_id = str(uuid.uuid4())
    price = item["price"]

    o = {
        "id": order_id, "gid": gid, "iid": iid,
        "name": item["name"], "price": price,
        "status": "pending", "date": now_str(),
        "buyer_id": msg.from_user.id,
        "buyer_name": msg.from_user.full_name,
        "buyer_username": msg.from_user.username or "",
        "game_data": game_data,
        "source": "bot",
    }
    orders[order_id] = o
    u["orders"].append(order_id)

    # ── Уведомление тебе ──
    try:
        await bot.send_message(
            ADMIN_ID,
            f"🔔 <b>НОВЫЙ ЗАКАЗ (бот)</b>\n\n{format_order_admin(o)}",
            reply_markup=order_admin_kb(order_id, msg.from_user.id)
        )
    except Exception as e:
        log.error(f"admin notify: {e}")

    # ── Подтверждение покупателю ──
    await msg.answer(
        f"✅ <b>Заказ оформлен!</b>\n\n"
        f"{g['emoji']} {item['name']}\n"
        f"💰 {price_line(price)}\n"
        f"📋 ID: <code>{short_id(order_id)}</code>\n\n"
        f"Теперь оплатите и пришлите скриншот 👇",
        reply_markup=main_kb()
    )

    # ── Реквизиты ──
    await msg.answer(
        cards_text(price),
        reply_markup=receipt_choice_kb(order_id)
    )


# ══════════════════════════════════════════════
#  RECEIPT CHOICE — куда отправить чек
# ══════════════════════════════════════════════
@dp.callback_query(F.data.startswith("receipt_here:"))
async def cb_receipt_here(cb: CallbackQuery):
    order_id = cb.data.split(":", 1)[1]
    await cb.message.edit_reply_markup(reply_markup=None)
    await cb.message.answer(
        "📸 <b>Отправь скриншот чека прямо сюда</b>\n\n"
        "Прикрепи фото оплаты — мы проверим и выдадим товар ⚡"
    )
    await cb.answer()


# ══════════════════════════════════════════════
#  ПРИЁМ СКРИНШОТА / ЧЕКА
# ══════════════════════════════════════════════
@dp.message(F.photo | F.document)
async def receive_receipt(msg: Message):
    if msg.from_user.id == ADMIN_ID:
        return  # Игнорируем фото от себя

    u = ensure_user(msg.from_user)
    # Найти последний pending заказ этого пользователя
    pending = [orders[oid] for oid in reversed(u.get("orders", []))
               if orders.get(oid, {}).get("status") == "pending"]

    uname = f"@{msg.from_user.username}" if msg.from_user.username else msg.from_user.full_name
    header = f"📸 <b>ЧЕК от {uname}</b> (<code>{msg.from_user.id}</code>)"
    if pending:
        o = pending[0]
        header += f"\n\n{format_order_admin(o)}"

    try:
        await bot.send_message(ADMIN_ID, header)
        await bot.forward_message(ADMIN_ID, msg.chat.id, msg.message_id)
        if pending:
            await bot.send_message(
                ADMIN_ID,
                "Подтвердить выдачу?",
                reply_markup=order_admin_kb(pending[0]["id"], msg.from_user.id)
            )
    except Exception as e:
        log.error(f"receipt forward: {e}")

    await msg.answer(
        "✅ <b>Чек получен!</b>\n\n"
        "Проверяем оплату — выдадим товар в течение 5 минут ⚡\n\n"
        "Если нет ответа — напишите <b>@frozenld1</b> напрямую."
    )


# ══════════════════════════════════════════════
#  CALLBACKS — ✅ Выдан / ❌ Отклонён
# ══════════════════════════════════════════════
@dp.callback_query(F.data.startswith("done:"))
async def cb_done(cb: CallbackQuery):
    if cb.from_user.id != ADMIN_ID:
        await cb.answer("Нет доступа"); return
    oid = cb.data.split(":", 1)[1]
    o = orders.get(oid)
    if not o: await cb.answer("Не найден"); return
    o["status"] = "done"
    await cb.message.edit_text(format_order_admin(o) + "\n\n✅ <b>ВЫДАН</b>")
    await cb.answer("✅ Выдан!")

    bid = o.get("buyer_id")
    if bid:
        try:
            g = get_game(o.get("gid",""))
            await bot.send_message(
                bid,
                f"🎉 <b>Ваш заказ выдан!</b>\n\n"
                f"{g['emoji']} <b>{o.get('name','—')}</b>\n"
                f"💰 {fmt(o.get('price',0))} сум\n\n"
                f"Спасибо за покупку в <b>FrozenShop</b>! 🛒\n"
                f"Есть вопросы? @{ADMIN_USER}",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[[
                    InlineKeyboardButton(text="🛒 Купить ещё", callback_data="catalog"),
                    InlineKeyboardButton(text="⭐ Оценить",    callback_data=f"rate:{oid}"),
                ]])
            )
        except Exception as e:
            await cb.message.answer(f"⚠️ Не удалось уведомить покупателя: {e}")


@dp.callback_query(F.data.startswith("reject:"))
async def cb_reject(cb: CallbackQuery):
    if cb.from_user.id != ADMIN_ID:
        await cb.answer("Нет доступа"); return
    oid = cb.data.split(":", 1)[1]
    o = orders.get(oid)
    if not o: await cb.answer("Не найден"); return
    o["status"] = "rejected"
    await cb.message.edit_text(format_order_admin(o) + "\n\n❌ <b>ОТКЛОНЁН</b>")
    await cb.answer("❌ Отклонён")
    bid = o.get("buyer_id")
    if bid:
        try:
            await bot.send_message(
                bid,
                f"❌ <b>Заказ отклонён</b>\n\n"
                f"{format_order_buyer(o)}\n\n"
                f"Есть вопросы? Пишите @{ADMIN_USER}"
            )
        except: pass


@dp.callback_query(F.data.startswith("rate:"))
async def cb_rate(cb: CallbackQuery):
    await cb.message.answer(
        "⭐ Спасибо! Оставьте отзыв:\n\n"
        "Просто напишите что думаете о нашем магазине 👇\n"
        f"<i>Или поделитесь ссылкой: t.me/{BOT_USER}</i>"
    )
    await cb.answer()


# ══════════════════════════════════════════════
#  МОИ ЗАКАЗЫ
# ══════════════════════════════════════════════
@dp.message(F.text == "📦 Мои заказы")
async def my_orders(msg: Message):
    u = ensure_user(msg.from_user)
    order_ids = u.get("orders", [])
    if not order_ids:
        await msg.answer(
            "У вас пока нет заказов 😊\n\n"
            "Нажмите 🛒 Каталог чтобы выбрать товар!",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[[
                InlineKeyboardButton(text="🛒 Открыть каталог", callback_data="catalog")
            ]])
        )
        return

    await msg.answer(f"📦 <b>Ваши заказы ({len(order_ids)}):</b>")
    for oid in reversed(order_ids[-8:]):
        o = orders.get(oid)
        if not o: continue
        st = o.get("status","pending")
        kb = None
        if st == "pending":
            kb = InlineKeyboardMarkup(inline_keyboard=[[
                InlineKeyboardButton(text="💳 Оплатить", callback_data=f"pay_again:{oid}"),
                InlineKeyboardButton(text="🔄 Статус",   callback_data=f"chk:{oid}"),
            ]])
        await msg.answer(format_order_buyer(o), reply_markup=kb)


@dp.callback_query(F.data.startswith("pay_again:"))
async def cb_pay_again(cb: CallbackQuery):
    oid = cb.data.split(":", 1)[1]
    o = orders.get(oid)
    if not o or o["status"] != "pending":
        await cb.answer("Заказ уже обработан", show_alert=True); return
    await cb.message.answer(cards_text(o.get("price", 0)),
                            reply_markup=receipt_choice_kb(oid))
    await cb.answer()


@dp.callback_query(F.data.startswith("chk:"))
async def cb_chk(cb: CallbackQuery):
    oid = cb.data.split(":", 1)[1]
    o = orders.get(oid)
    if not o: await cb.answer("Не найден", show_alert=True); return
    st = {"pending":"⏳ Ожидает подтверждения","done":"✅ Выдан!","rejected":"❌ Отклонён"}.get(o["status"],"⏳")
    await cb.answer(st, show_alert=True)


# ══════════════════════════════════════════════
#  РЕФЕРАЛЫ
# ══════════════════════════════════════════════
@dp.message(F.text == "👥 Рефералы")
async def referral_menu(msg: Message):
    u = ensure_user(msg.from_user)
    count = u.get("ref_count", 0)
    link = f"https://t.me/{BOT_USER}?start=ref_{msg.from_user.id}"
    await msg.answer(
        f"👥 <b>Реферальная программа</b>\n\n"
        f"Приглашай друзей и получай бонусы!\n\n"
        f"🔗 Твоя ссылка:\n<code>{link}</code>\n\n"
        f"👤 Приглашено: <b>{count}</b> чел.\n\n"
        f"<i>За каждого нового покупателя — скидка на следующий заказ!\n"
        f"(спроси у @{ADMIN_USER} о деталях)</i>",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[[
            InlineKeyboardButton(text="📤 Поделиться ссылкой",
                                 url=f"https://t.me/share/url?url={link}&text=FrozenShop%20—%20игровые%20товары%20быстро%20и%20выгодно!")
        ]])
    )


# ══════════════════════════════════════════════
#  БОНУСЫ
# ══════════════════════════════════════════════
@dp.message(F.text == "🎁 Бонусы")
async def bonuses_menu(msg: Message):
    if msg.from_user.id == ADMIN_ID:
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="➕ Добавить бонус",  callback_data="bn:add")],
            [InlineKeyboardButton(text="📋 Все бонусы",     callback_data="bn:list")],
            [InlineKeyboardButton(text="🗑 Удалить бонус",  callback_data="bn:del")],
        ])
        await msg.answer("🎁 <b>Управление бонусами</b>", reply_markup=kb)
        return

    if not bonuses:
        await msg.answer(
            "🎁 <b>Бонусы и спецпредложения</b>\n\n"
            "Скоро появятся акции и скидки!\n"
            "Следи за обновлениями 👀\n\n"
            f"<i>Подпишись на уведомления — напиши @{ADMIN_USER}</i>"
        ); return

    text = "🎁 <b>Активные бонусы:</b>\n\n"
    for b in bonuses:
        text += f"🔸 <b>{b['title']}</b>\n{b['desc']}\n"
        if b.get("code"):
            text += f"Промокод: <code>{b['code']}</code>\n"
        text += "\n"
    await msg.answer(text)


@dp.callback_query(F.data.startswith("bn:"))
async def cb_bn(cb: CallbackQuery, state: FSMContext):
    if cb.from_user.id != ADMIN_ID: return
    action = cb.data.split(":", 1)[1]
    if action == "list":
        if not bonuses:
            await cb.answer("Бонусов нет", show_alert=True); return
        text = "📋 <b>Бонусы:</b>\n\n"
        for i, b in enumerate(bonuses):
            text += f"{i+1}. {b['title']} — {b['desc']}"
            if b.get("code"): text += f" [{b['code']}]"
            text += "\n"
        await cb.message.answer(text); await cb.answer()
    elif action == "add":
        await state.set_state(BonusAdd.title)
        await cb.message.answer("Название бонуса (напр: 🔥 -10% на MLBB):"); await cb.answer()
    elif action == "del":
        if not bonuses:
            await cb.answer("Бонусов нет", show_alert=True); return
        bld = InlineKeyboardBuilder()
        for b in bonuses:
            bld.button(text=f"🗑 {b['title']}", callback_data=f"bn_del:{b['id']}")
        bld.adjust(1)
        await cb.message.answer("Какой бонус удалить?", reply_markup=bld.as_markup())
        await cb.answer()


@dp.callback_query(F.data.startswith("bn_del:"))
async def cb_bn_del(cb: CallbackQuery):
    if cb.from_user.id != ADMIN_ID: return
    bid = cb.data.split(":", 1)[1]
    global bonuses
    bonuses = [b for b in bonuses if b["id"] != bid]
    await cb.answer("🗑 Удалён", show_alert=True)
    await cb.message.delete()


@dp.message(BonusAdd.title)
async def bn_title(msg: Message, state: FSMContext):
    await state.update_data(title=msg.text)
    await state.set_state(BonusAdd.desc)
    await msg.answer("Описание бонуса:")

@dp.message(BonusAdd.desc)
async def bn_desc(msg: Message, state: FSMContext):
    await state.update_data(desc=msg.text)
    await state.set_state(BonusAdd.code)
    await msg.answer("Промокод (или напиши 'нет'):")

@dp.message(BonusAdd.code)
async def bn_code(msg: Message, state: FSMContext):
    d = await state.get_data(); await state.clear()
    b = {"id": str(uuid.uuid4())[:6], "title": d["title"], "desc": d["desc"],
         "code": None if msg.text.lower() in ("нет","no","-") else msg.text}
    bonuses.append(b)
    await msg.answer(f"✅ Бонус добавлен!\n\n<b>{b['title']}</b>\n{b['desc']}")


# ══════════════════════════════════════════════
#  ПОДДЕРЖКА
# ══════════════════════════════════════════════
@dp.message(F.text == "💬 Поддержка")
async def support_menu(msg: Message):
    await msg.answer(
        "💬 <b>Поддержка FrozenShop</b>\n\n"
        "Если есть проблема с заказом — выберите удобный способ:\n\n"
        "🤖 <b>Боту</b> — пришли скриншот чека прямо сюда\n"
        f"👤 <b>Лично</b> — напиши @{ADMIN_USER} напрямую\n\n"
        "Мы отвечаем в течение 5–15 минут ⚡",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=f"🤖 Написать боту @{BOT_USER}",
                                  url=f"https://t.me/{BOT_USER}")],
            [InlineKeyboardButton(text=f"👤 Написать @{ADMIN_USER} лично",
                                  url=f"https://t.me/{ADMIN_USER}")],
        ])
    )


# ══════════════════════════════════════════════
#  САЙТ
# ══════════════════════════════════════════════
@dp.message(F.text == "🌐 Сайт")
async def open_site(msg: Message):
    await msg.answer(
        "🌐 <b>FrozenShop</b>\n\nПолный каталог и история заказов на сайте:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[[
            InlineKeyboardButton(text="🛒 Открыть FrozenShop", url=SITE_URL)
        ]])
    )


# ══════════════════════════════════════════════
#  О МАГАЗИНЕ
# ══════════════════════════════════════════════
@dp.message(F.text == "ℹ️ О магазине")
async def about(msg: Message):
    total_done = sum(1 for o in orders.values() if o.get("status") == "done")
    await msg.answer(
        f"🏪 <b>FrozenShop</b>\n\n"
        f"Магазин игровых товаров в Узбекистане\n\n"
        f"✅ Выполнено заказов: <b>{total_done}+</b>\n"
        f"⚡ Доставка: от 5 минут\n"
        f"💰 Оплата: HUMO\n"
        f"🕐 Работаем: 24/7\n\n"
        f"🎮 Игры: MLBB, PUBG, Genshin, Roblox, FF и другие\n\n"
        f"🔗 Сайт: {SITE_URL}\n"
        f"👤 Контакт: @{ADMIN_USER}"
    )


# ══════════════════════════════════════════════
#  ADMIN — Статистика
# ══════════════════════════════════════════════
@dp.message(F.text == "📊 Статистика")
async def admin_stats(msg: Message):
    if msg.from_user.id != ADMIN_ID: return
    total = len(orders)
    done_orders = [o for o in orders.values() if o.get("status") == "done"]
    pending_c = sum(1 for o in orders.values() if o.get("status") == "pending")
    revenue = sum(o.get("price", 0) for o in done_orders)
    today = datetime.now().date().isoformat()
    today_orders = sum(1 for o in orders.values() if o.get("date","")[:10] == today)
    # Топ игр
    game_counts: dict[str, int] = defaultdict(int)
    for o in done_orders:
        game_counts[o.get("gid","?")] += 1
    top_games = sorted(game_counts.items(), key=lambda x: -x[1])[:3]
    top_str = ""
    for gid, cnt in top_games:
        g = get_game(gid)
        top_str += f"  {g['emoji']} {g['name']}: {cnt}\n"

    await msg.answer(
        f"📊 <b>Статистика FrozenShop</b>\n\n"
        f"📅 Сегодня заказов: <b>{today_orders}</b>\n"
        f"📦 Всего заказов: <b>{total}</b>\n"
        f"⏳ Ожидают: <b>{pending_c}</b>\n"
        f"✅ Выдано: <b>{len(done_orders)}</b>\n\n"
        f"💰 Выручка: <b>{fmt(revenue)} сум</b>\n"
        f"   ≈ <b>{rub(revenue)} ₽</b>\n\n"
        f"👥 Пользователей: <b>{len(users)}</b>\n\n"
        f"🏆 Топ игры:\n{top_str or '  —'}"
    )


@dp.message(F.text == "👥 Пользователи")
async def admin_users(msg: Message):
    if msg.from_user.id != ADMIN_ID: return
    total = len(users)
    week_ago = (datetime.now() - timedelta(days=7)).isoformat()
    new_week = sum(1 for u in users.values() if u.get("joined","") > week_ago)
    await msg.answer(
        f"👥 <b>Пользователи</b>\n\n"
        f"Всего: <b>{total}</b>\n"
        f"За 7 дней: <b>{new_week}</b>\n\n"
        f"Последние 5:\n" +
        "\n".join(f"• {u['name']} (@{u.get('username','—')})" 
                  for u in list(users.values())[-5:])
    )


@dp.message(F.text == "📋 Заказы")
async def admin_all_orders(msg: Message):
    if msg.from_user.id != ADMIN_ID: return
    if not orders:
        await msg.answer("Заказов пока нет."); return
    recent = sorted(orders.values(), key=lambda x: x.get("date",""), reverse=True)[:8]
    for o in recent:
        kb = order_admin_kb(o["id"], o.get("buyer_id",0)) if o["status"]=="pending" else None
        await msg.answer(format_order_admin(o), reply_markup=kb)


@dp.message(F.text == "⏳ Ожидающие")
async def admin_pending(msg: Message):
    if msg.from_user.id != ADMIN_ID: return
    p = [o for o in orders.values() if o.get("status") == "pending"]
    if not p:
        await msg.answer("✅ Нет ожидающих заказов!"); return
    await msg.answer(f"⏳ <b>Ожидают: {len(p)}</b>")
    for o in sorted(p, key=lambda x: x.get("date",""))[:10]:
        await msg.answer(format_order_admin(o),
                         reply_markup=order_admin_kb(o["id"], o.get("buyer_id",0)))


@dp.message(F.text == "📢 Рассылка")
async def broadcast_start(msg: Message, state: FSMContext):
    if msg.from_user.id != ADMIN_ID: return
    await state.set_state(Broadcast.text)
    await msg.answer(
        f"📢 <b>Рассылка</b>\n\nНапиши сообщение — уйдёт всем {len(users)} пользователям.\n"
        "/cancel — отменить"
    )


@dp.message(Broadcast.text)
async def broadcast_send(msg: Message, state: FSMContext):
    if msg.from_user.id != ADMIN_ID: return
    await state.clear()
    sent = fail = 0
    for uid in users:
        if uid == ADMIN_ID: continue
        try:
            await bot.send_message(uid, msg.html_text or msg.text or "")
            sent += 1; await asyncio.sleep(0.05)
        except: fail += 1
    await msg.answer(f"📢 Готово!\n✅ Отправлено: {sent}\n❌ Не доставлено: {fail}")


# ══════════════════════════════════════════════
#  ADMIN — Добавить товар
# ══════════════════════════════════════════════
@dp.message(F.text == "➕ Добавить товар")
async def add_product_start(msg: Message, state: FSMContext):
    if msg.from_user.id != ADMIN_ID: return
    bld = InlineKeyboardBuilder()
    for g in GAMES:
        bld.button(text=f"{g['emoji']} {g['name']}", callback_data=f"addprod:{g['id']}")
    bld.adjust(2)
    await msg.answer("Выбери игру для нового товара:", reply_markup=bld.as_markup())


@dp.callback_query(F.data.startswith("addprod:"))
async def cb_addprod(cb: CallbackQuery, state: FSMContext):
    if cb.from_user.id != ADMIN_ID: return
    gid = cb.data.split(":", 1)[1]
    await state.update_data(game=gid)
    await state.set_state(AddProduct.name)
    await cb.message.answer(f"Название товара (напр: 500 💎):")
    await cb.answer()

@dp.message(AddProduct.name)
async def ap_name(msg: Message, state: FSMContext):
    if msg.from_user.id != ADMIN_ID: return
    await state.update_data(name=msg.text)
    await state.set_state(AddProduct.price)
    await msg.answer("Цена в сумах:")

@dp.message(AddProduct.price)
async def ap_price(msg: Message, state: FSMContext):
    if msg.from_user.id != ADMIN_ID: return
    try: price = int(msg.text.replace(" ","").replace(",",""))
    except: await msg.answer("Введи число!"); return
    await state.update_data(price=price)
    await state.set_state(AddProduct.desc)
    await msg.answer("Описание (или 'нет'):")

@dp.message(AddProduct.desc)
async def ap_desc(msg: Message, state: FSMContext):
    if msg.from_user.id != ADMIN_ID: return
    d = await state.get_data(); await state.clear()
    gid = d["game"]
    new_item = {
        "id": f"custom_{str(uuid.uuid4())[:6]}",
        "name": d["name"],
        "price": d["price"],
        "desc": None if msg.text.lower() in ("нет","no","-") else msg.text
    }
    CATALOG.setdefault(gid, []).append(new_item)
    g = get_game(gid)
    await msg.answer(
        f"✅ Товар добавлен!\n\n{g['emoji']} {g['name']}\n"
        f"📦 {new_item['name']}\n💰 {fmt(new_item['price'])} сум"
    )


@dp.message(Command("cancel"))
async def cmd_cancel(msg: Message, state: FSMContext):
    await state.clear()
    await msg.answer("Отменено.", reply_markup=main_kb(msg.from_user.id == ADMIN_ID))


# ══════════════════════════════════════════════
#  🤖 АВТО-ОТВЕТЫ — спецслова
# ══════════════════════════════════════════════
# Формат: ты пишешь в ЛЮБОЙ чат /f ключ текст ответа
# Примеры:
#   /f привет    Привет! Чем могу помочь? 😊
#   /f цена      Актуальные цены смотри на сайте...
#   /f готово    Ваш заказ готов! Проверяйте игру 🎉
#
# Или заранее задай в AUTO_REPLIES ниже.
# Префикс по умолчанию: !  (пишешь покупателю  !привет  → бот пишет ответ)
# Можно изменить PREFIX на любой символ.

AUTO_REPLY_PREFIX = "!"   # префикс для быстрых ответов из любого чата

# Встроенные авто-ответы (ключ → текст)
# Ты можешь добавлять новые через команду /f прямо в боте
auto_replies: dict[str, str] = {
    "привет":     "👋 Привет! Добро пожаловать в FrozenShop!\nЧем могу помочь? Напиши что ищешь или выбери в меню 👇",
    "цена":       "💰 Актуальные цены на все товары:\n🌐 " + SITE_URL + "\n\nИли нажми 🛒 Каталог в меню.",
    "доставка":   "⚡ Доставка от <b>5 минут</b> после оплаты.\nРаботаем 24/7 — без выходных!",
    "оплата":     "💳 Оплата переводом на карту HUMO:\n<code>9860 1606 3787 3359</code>\nБухарбаев Бердах\n\nПосле оплаты пришли скриншот сюда.",
    "готово":     "✅ <b>Ваш заказ выдан!</b>\n\nПроверяйте игру 🎮\nСпасибо за покупку в FrozenShop!\n\nЕсть вопросы? Пишите — помогу 😊",
    "ждите":      "⏳ Ваш заказ обрабатывается.\nОбычно это занимает 5–15 минут.\nМы уведомим как только всё будет готово!",
    "проблема":   "😔 Понял, разберёмся!\nОпишите проблему подробнее — что именно не работает?\nЯ помогу решить в кратчайшие сроки.",
    "спасибо":    "🙏 Спасибо за покупку!\nБудем рады видеть вас снова.\nПоделитесь отзывом — это очень важно для нас 💙",
    "mlbb":       "⚔️ <b>Mobile Legends — алмазы</b>\n\nВсе пакеты и цены:\n🌐 " + SITE_URL + "\n\nДля заказа нужен ID и сервер.\nПример: <code>1510395929 (16321)</code>",
    "робукс":     "🔴 <b>Robux для Roblox</b>\n\nЕсть два варианта:\n• С логином (5-7 дней) — дешевле\n• Моментально (нужен логин)\n• Промокод (без логина)\n\nЦены: " + SITE_URL,
    "pubg":       "🪖 <b>PUBG Mobile — UC</b>\n\nДля заказа нужен ID персонажа.\nНайти: Профиль → Настройки → ID\n\nЦены: " + SITE_URL,
    "старс":      "⭐ <b>Telegram Stars</b>\n\nЦена: 270 сум за ⭐\nСкидка 3% от 500 звёзд!\n\nЦены: " + SITE_URL,
    "премиум":    "💎 <b>Telegram Premium</b>\n\n• 1 месяц с входом — 38 000 сум\n• 3 мес подарок — 170 000 сум\n• 6 мес подарок — 225 000 сум\n• 12 мес подарок — 400 000 сум",
    "гарантия":   "🔒 <b>Гарантия FrozenShop</b>\n\nЕсли возникли проблемы — пишите @frozenld1\nМы всегда решаем спорные ситуации в пользу покупателя.\nРаботаем честно с 2023 года 💙",
    "акция":      "🎁 <b>Актуальные акции:</b>\n\n⭐ Скидка 3% на 500+ Telegram Stars\n💎 Двойные алмазы MLBB по спецценам\n\nСледи за обновлениями в боте!",
}

# Команда /f для добавления нового авто-ответа
# Использование: /f ключ Текст ответа
@dp.message(Command("f"))
async def cmd_add_autoreply(msg: Message):
    if msg.from_user.id != ADMIN_ID: return
    parts = msg.text.split(maxsplit=2)
    if len(parts) < 3:
        keys = "\n".join(f"• <code>{k}</code>" for k in auto_replies)
        await msg.answer(
            "📝 <b>Авто-ответы</b>\n\n"
            "Добавить: <code>/f ключ Текст ответа</code>\n"
            "Пример: <code>/f старс 270 сум за звезду ✨</code>\n\n"
            f"Текущие ключи:\n{keys or '—'}\n\n"
            f"<b>Быстрый ответ покупателю:</b>\n"
            f"Напиши <code>!ключ</code> в любом сообщении и бот ответит тем пользователем"
        )
        return
    key = parts[1].lower().strip()
    text = parts[2].strip()
    auto_replies[key] = text
    await msg.answer(f"✅ Авто-ответ добавлен!\n\nКлюч: <code>{key}</code>\nТекст: {text}")

# Команда /del для удаления авто-ответа
@dp.message(Command("del"))
async def cmd_del_autoreply(msg: Message):
    if msg.from_user.id != ADMIN_ID: return
    parts = msg.text.split(maxsplit=1)
    if len(parts) < 2:
        await msg.answer("Использование: <code>/del ключ</code>"); return
    key = parts[1].lower().strip()
    if key in auto_replies:
        del auto_replies[key]
        await msg.answer(f"🗑 Авто-ответ <code>{key}</code> удалён.")
    else:
        await msg.answer(f"Ключ <code>{key}</code> не найден.")

# Команда /list — показать все авто-ответы
@dp.message(Command("list"))
async def cmd_list_autoreplies(msg: Message):
    if msg.from_user.id != ADMIN_ID: return
    if not auto_replies:
        await msg.answer("Авто-ответов нет. Добавь через /f"); return
    text = "📋 <b>Все авто-ответы:</b>\n\n"
    for k, v in auto_replies.items():
        short = v[:60] + "..." if len(v) > 60 else v
        text += f"<code>!{k}</code> → {short}\n"
    await msg.answer(text)

# Команда /help — справка по командам
@dp.message(Command("help"))
async def cmd_help(msg: Message):
    if msg.from_user.id == ADMIN_ID:
        await msg.answer(
            "🛠 <b>Команды администратора:</b>\n\n"
            "<code>/f ключ текст</code> — добавить авто-ответ\n"
            "<code>/del ключ</code> — удалить авто-ответ\n"
            "<code>/list</code> — список авто-ответов\n"
            "<code>/send ID текст</code> — написать пользователю\n"
            "<code>/cancel</code> — отменить текущее действие\n\n"
            "<b>Быстрые ответы покупателям:</b>\n"
            f"Напиши <code>!ключ</code> — бот ответит последнему активному покупателю\n"
            f"Или: <code>!ключ ID_пользователя</code> — конкретному пользователю\n\n"
            "<b>Примеры:</b>\n"
            "<code>!готово</code> — отправить «заказ готов» последнему\n"
            "<code>!привет 123456789</code> — написать конкретному ID"
        )
    else:
        await msg.answer(
            "ℹ️ <b>Помощь FrozenShop</b>\n\n"
            "🛒 Каталог — выбрать товар\n"
            "📦 Мои заказы — история и статус\n"
            "💬 Поддержка — связь с продавцом\n"
            "🎁 Бонусы — акции и скидки\n"
            "👥 Рефералы — пригласить друзей\n\n"
            f"По любым вопросам: @{ADMIN_USER}"
        )

# Команда /send — написать конкретному пользователю
@dp.message(Command("send"))
async def cmd_send(msg: Message):
    if msg.from_user.id != ADMIN_ID: return
    parts = msg.text.split(maxsplit=2)
    if len(parts) < 3:
        await msg.answer("Использование: <code>/send TG_ID текст сообщения</code>"); return
    try:
        target_id = int(parts[1])
        text = parts[2]
        await bot.send_message(target_id, text)
        await msg.answer(f"✅ Сообщение отправлено пользователю <code>{target_id}</code>")
    except ValueError:
        await msg.answer("❌ Неверный ID пользователя")
    except Exception as e:
        await msg.answer(f"❌ Ошибка: {e}")

# ── Обработчик входящих сообщений с префиксом ! ──
# Ты пишешь !ключ → бот автоматически отвечает последнему активному пользователю
# Или !ключ 123456 → конкретному пользователю по ID

last_active_buyer: dict = {}   # хранит последнего написавшего покупателя

@dp.message(F.text.startswith(AUTO_REPLY_PREFIX), F.from_user.func(lambda u: True))
async def quick_reply_trigger(msg: Message):
    # Если это ты — отправить ответ покупателю
    if msg.from_user.id == ADMIN_ID:
        raw = msg.text[len(AUTO_REPLY_PREFIX):].strip()
        parts = raw.split(maxsplit=1)
        key = parts[0].lower()
        # Опциональный target_id в конце: !привет 123456789
        target_id = None
        if len(parts) > 1 and parts[1].isdigit():
            target_id = int(parts[1])
        elif last_active_buyer:
            # Последний активный покупатель
            target_id = list(last_active_buyer.keys())[-1]

        reply_text = auto_replies.get(key)
        if not reply_text:
            await msg.answer(
                f"❓ Ключ <code>{key}</code> не найден.\n"
                f"Добавь через <code>/f {key} текст ответа</code>\n"
                f"Список: /list"
            )
            return

        if not target_id:
            await msg.answer("❓ Нет активных покупателей. Укажи ID: <code>!{key} 123456789</code>")
            return

        try:
            await bot.send_message(target_id, reply_text)
            buyer_name = last_active_buyer.get(target_id, {}).get("name", str(target_id))
            await msg.answer(f"✅ Ответ отправлен: {buyer_name} (<code>{target_id}</code>)\n\n<i>{reply_text[:100]}</i>")
        except Exception as e:
            await msg.answer(f"❌ Не удалось отправить: {e}")
        return

    # Если это покупатель пишет !что-то — ищем ответ в авто-ответах
    raw = msg.text[len(AUTO_REPLY_PREFIX):].strip().lower()
    reply_text = auto_replies.get(raw)
    if reply_text:
        await msg.answer(reply_text)
    # Не нашли — просто игнорируем (не мешаем другим хендлерам)


# ── Трекинг активных покупателей (любое сообщение) ──
@dp.message(F.from_user.func(lambda u: True))
async def track_active_buyer(msg: Message):
    """Запоминаем последнего написавшего покупателя для быстрых ответов"""
    if msg.from_user.id != ADMIN_ID:
        last_active_buyer[msg.from_user.id] = {
            "name": msg.from_user.full_name,
            "username": msg.from_user.username or "",
            "last_msg": msg.text or "[медиа]",
        }


# ══════════════════════════════════════════════
#  REST API (для сайта)
# ══════════════════════════════════════════════
@app.post("/api/order")
async def api_order(request: Request):
    try:
        data = await request.json()
    except:
        raise HTTPException(400, "bad json")

    oid = data.get("id") or str(uuid.uuid4())
    data.update({"id": oid, "status": "pending",
                 "date": data.get("date") or now_str(), "source": "site"})
    orders[oid] = data

    bid = data.get("buyer_id")
    if bid:
        u = users.setdefault(int(bid), {
            "id": int(bid), "name": data.get("buyer_name","?"),
            "username": data.get("buyer_username",""),
            "joined": now_str(), "orders": [], "ref_by": None, "ref_count": 0
        })
        u["orders"].append(oid)

    try:
        await bot.send_message(
            ADMIN_ID, f"🌐 <b>ЗАКАЗ С САЙТА</b>\n\n{format_order_admin(data)}",
            reply_markup=order_admin_kb(oid, bid)
        )
    except Exception as e:
        log.error(f"api order admin: {e}")

    if bid:
        try:
            await bot.send_message(
                bid,
                f"✅ <b>Заказ принят!</b>\n\n{format_order_buyer(data)}\n\n"
                f"Оплатите и пришлите скриншот 👇",
            )
            await bot.send_message(bid, cards_text(data.get("price",0)),
                                   reply_markup=receipt_choice_kb(oid))
        except: pass

    return {"ok": True, "order_id": oid}


@app.post("/api/status")
async def api_status(request: Request):
    d = await request.json()
    o = orders.get(d.get("id",""))
    return {"status": o["status"] if o else "not_found"}


@app.get("/api/orders/{buyer_id}")
async def api_buyer_orders(buyer_id: str):
    u = users.get(int(buyer_id) if buyer_id.isdigit() else 0, {})
    ids = u.get("orders", [])
    return {"orders": [orders[i] for i in ids if i in orders]}


@app.post("/webhook")
async def tg_webhook(request: Request):
    from aiogram.types import Update
    update = Update.model_validate(await request.json())
    await dp.feed_update(bot, update)
    return {"ok": True}


@app.get("/health")
async def health():
    return {"ok": True, "orders": len(orders), "users": len(users)}


# ══════════════════════════════════════════════
#  STARTUP
# ══════════════════════════════════════════════
async def on_startup():
    await bot.set_webhook(f"{WEBHOOK_URL}/webhook")
    log.info(f"Webhook set: {WEBHOOK_URL}/webhook")
    try:
        await bot.send_message(ADMIN_ID,
            f"🚀 <b>FrozenShop Bot запущен!</b>\n\n"
            f"🤖 @{BOT_USER}\n"
            f"🌐 {SITE_URL}\n\n"
            "Жду заказов 📦",
            reply_markup=main_kb(True))
    except Exception as e:
        log.warning(f"startup msg: {e}")

async def on_shutdown():
    await bot.delete_webhook()

app.add_event_handler("startup",  on_startup)
app.add_event_handler("shutdown", on_shutdown)

if __name__ == "__main__":
    uvicorn.run("bot:app", host="0.0.0.0", port=PORT)
