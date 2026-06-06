"""
FrozenShop Telegram Bot — aiogram 3.x
Full ordering flow + admin commands
"""
import asyncio
import uuid
import re

from aiogram import Bot, Dispatcher, F, Router
from aiogram.filters import Command
from aiogram.types import (
    Message, CallbackQuery,
    InlineKeyboardMarkup, InlineKeyboardButton
)
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage

from config import (
    BOT_TOKEN, ADMIN_ID, PRODUCTS, GAME_NAMES,
    GAME_EMOJI, CARDS, MLBB_COMBOS, GAME_KEYS, MANUAL_GAMES
)
from db import (
    get_order, all_orders, save_order, set_status,
    get_wallet, wallet_add, wallet_sub,
    receipt_seen, sid, now, fmt
)
from buypin import fulfill, sync_products, bp_validate, bp_balance

bot = Bot(token=BOT_TOKEN, parse_mode="HTML")
dp  = Dispatcher(storage=MemoryStorage())
r   = Router()
dp.include_router(r)

# ── FSM States ────────────────────────────────────────────────
class Order(StatesGroup):
    game    = State()
    product = State()
    uid     = State()
    server  = State()
    confirm = State()
    card    = State()
    amount  = State()

# ── Pending orders (user_id → order dict) ─────────────────────
_pending: dict[int, dict] = {}

# ── Public send function (used by api.py) ─────────────────────
async def send(chat_id, text: str):
    try:
        await bot.send_message(chat_id, text)
    except Exception as e:
        print(f"send {chat_id}: {e}")

# ── Keyboard builders ─────────────────────────────────────────
def ik(*rows):
    return InlineKeyboardMarkup(inline_keyboard=list(rows))

def btn(text: str, data: str = None, url: str = None):
    return InlineKeyboardButton(text=text, callback_data=data, url=url)

def games_kb():
    keys = list(PRODUCTS.keys())
    rows = []
    for i in range(0, len(keys), 2):
        row = []
        for g in keys[i:i+2]:
            e = GAME_EMOJI.get(g, "🎮")
            n = GAME_NAMES.get(g, g)
            row.append(btn(f"{e} {n}", f"g:{g}"))
        rows.append(row)
    rows.append([btn("❌ Отмена", "cancel")])
    return InlineKeyboardMarkup(inline_keyboard=rows)

def products_kb(gid: str):
    items = PRODUCTS.get(gid, [])
    rows  = []
    for p in items:
        price = f"{fmt(p['price'])} сум" if p["price"] else "Договорная"
        tag   = " 🔥" if p.get("tag") == "hot" else " ⭐" if p.get("tag") == "new" else ""
        cat_prefix = {
            "robux_slow":  "🕐 ",
            "robux_fast":  "⚡ ",
            "gems_uid":    "💠 ",
            "gems_login":  "🔐 ",
        }.get(p.get("cat", ""), "")
        rows.append([btn(
            f"{cat_prefix}{p['name']}{tag} — {price}",
            f"p:{gid}:{p['id']}"
        )])
    rows.append([btn("◀️ Назад к играм", "back_games")])
    return InlineKeyboardMarkup(inline_keyboard=rows)

def confirm_kb(oid: str):
    return ik(
        [btn("💳 Оплатил картой",    f"paycard:{oid}")],
        [btn("🪙 Оплатить FrozenCoins", f"paycoins:{oid}")],
        [btn("❌ Отменить",           "cancel")],
    )

def cards_kb(oid: str):
    rows = []
    for last4, num in CARDS.items():
        bank = "HUMO" if num.startswith("9860") else "UzCard"
        rows.append([btn(f"💳 {num} ({bank})", f"card:{oid}:{last4}")])
    rows.append([btn("◀️ Назад", f"backconfirm:{oid}")])
    return InlineKeyboardMarkup(inline_keyboard=rows)

def menu_kb():
    return ik(
        [btn("🛍 Сделать заказ",    "shop")],
        [btn("💰 Кошелёк",          "wallet"),
         btn("📋 Мои заказы",       "myorders")],
        [btn("❓ Помощь",           "help")],
    )

# ── UID hints per game ────────────────────────────────────────
UID_HINTS = {
    "mlbb":    "Профиль → под ником\nПример: <code>1510395929</code>",
    "genshin": "Меню → Аккаунт → UID",
    "hsr":     "Меню → Аккаунт → UID",
    "zzz":     "Профиль → UID",
    "pubg":    "Инвентарь → ID персонажа",
    "ff":      "Главный экран → под именем",
    "hok":     "Профиль → UID",
    "s2":      "Профиль → ID",
    "roblox":  "Профиль → URL (числа в конце)",
    "brawl":   "Профиль → тег",
}

# Games that also need server/zone input
NEEDS_SERVER = {"mlbb"}

# Games that need login credentials (no UID)
NEEDS_LOGIN = {"steam", "tgprem", "jutsu"}


# ════════════════════════════════════════════════════════════
#  /start
# ════════════════════════════════════════════════════════════
@r.message(Command("start"))
async def cmd_start(msg: Message, state: FSMContext):
    await state.clear()
    _pending.pop(msg.from_user.id, None)
    await msg.answer(
        f"👋 Привет, <b>{msg.from_user.first_name}</b>!\n"
        f"Добро пожаловать в <b>FrozenShop</b> ❄️\n\n"
        f"🎮 <b>Продаём:</b>\n"
        f"• ⚔️ Mobile Legends — 60+ пакетов алмазов\n"
        f"• 🌸 Genshin · 🚂 HSR · ⚡ ZZZ — камни/гранулы\n"
        f"• 🎯 PUBG · 🔥 Free Fire · 👑 Honor of Kings\n"
        f"• 🎮 Roblox (трейд 5-7 дней + моментально)\n"
        f"• 💥 Brawl Stars · ⭐ Telegram Premium · Steam\n\n"
        f"📦 Выдача 1–5 мин · 🕐 24/7 · 💬 @frozenld1",
        reply_markup=menu_kb()
    )


# ── Main menu callback ─────────────────────────────────────────
@r.callback_query(F.data == "main_menu")
async def cb_menu(cb: CallbackQuery, state: FSMContext):
    await state.clear()
    _pending.pop(cb.from_user.id, None)
    await cb.message.edit_text(
        "🏠 <b>FrozenShop ❄️</b>",
        reply_markup=menu_kb()
    )
    await cb.answer()


# ════════════════════════════════════════════════════════════
#  Help
# ════════════════════════════════════════════════════════════
@r.message(Command("help"))
@r.callback_query(F.data == "help")
async def cmd_help(event, **_):
    text = (
        "🆘 <b>Помощь — FrozenShop</b>\n\n"
        "<b>Как заказать:</b>\n"
        "1️⃣ Нажми «Сделать заказ»\n"
        "2️⃣ Выбери игру и пакет\n"
        "3️⃣ Введи свой игровой ID\n"
        "4️⃣ Переведи деньги на карту\n"
        "5️⃣ Нажми «Оплатил картой» и введи сумму\n"
        "6️⃣ Получи товар автоматически!\n\n"
        "<b>Частые вопросы:</b>\n"
        "❓ Где ID в MLBB? → Профиль → под ником\n"
        "❓ Когда придут алмазы? → 1–5 минут\n"
        "❓ Не получил? → @frozenld1\n\n"
        "💳 <b>Карты для оплаты:</b>\n"
        + "\n".join(
            f"  <code>{num}</code>"
            for num in CARDS.values()
        )
    )
    back = ik([btn("🛍 Заказать", "shop")], [btn("◀️ Меню", "main_menu")])
    if isinstance(event, Message):
        await event.answer(text, reply_markup=back)
    else:
        await event.message.edit_text(text, reply_markup=back)
        await event.answer()


# ════════════════════════════════════════════════════════════
#  Shop — game selection
# ════════════════════════════════════════════════════════════
@r.callback_query(F.data.in_({"shop", "back_games"}))
async def cb_shop(cb: CallbackQuery, state: FSMContext):
    await state.set_state(Order.game)
    await cb.message.edit_text(
        "🎮 <b>Выбери игру:</b>",
        reply_markup=games_kb()
    )
    await cb.answer()


@r.callback_query(F.data.startswith("g:"))
async def cb_game(cb: CallbackQuery, state: FSMContext):
    gid = cb.data[2:]
    await state.update_data(gid=gid)
    await state.set_state(Order.product)

    name  = GAME_NAMES.get(gid, gid)
    emoji = GAME_EMOJI.get(gid, "🎮")
    await cb.message.edit_text(
        f"{emoji} <b>{name}</b>\n\nВыбери пакет:",
        reply_markup=products_kb(gid)
    )
    await cb.answer()


# ── Product selection ─────────────────────────────────────────
@r.callback_query(F.data.startswith("p:"))
async def cb_product(cb: CallbackQuery, state: FSMContext):
    _, gid, pid = cb.data.split(":")
    items = PRODUCTS.get(gid, [])
    prod  = next((p for p in items if p["id"] == pid), None)
    if not prod:
        await cb.answer("Товар не найден", show_alert=True)
        return

    await state.update_data(gid=gid, pid=pid, prod=prod)

    # Games needing no UID
    if gid in NEEDS_LOGIN:
        await _make_order(cb.message, state, uid="", server="", edit=True)
        await cb.answer()
        return

    # Show UID input prompt
    hint = UID_HINTS.get(gid, "ID из профиля игры")
    await state.set_state(Order.uid)
    await cb.message.edit_text(
        f"📝 <b>Введи игровой ID</b>\n\n"
        f"📌 Где найти:\n{hint}\n\n"
        f"⬇️ Напиши ниже:",
        reply_markup=ik([btn("◀️ Назад", f"g:{gid}")])
    )
    await cb.answer()


@r.message(Order.uid)
async def msg_uid(msg: Message, state: FSMContext):
    uid = (msg.text or "").strip()
    if not uid:
        await msg.answer("❌ Введи корректный ID")
        return

    data = await state.get_data()
    gid  = data.get("gid", "")
    await state.update_data(bp_uid=uid)

    # MLBB needs server
    if gid in NEEDS_SERVER:
        await state.set_state(Order.server)
        await msg.answer(
            f"✅ ID: <code>{uid}</code>\n\n"
            f"Теперь введи <b>номер сервера</b>\n"
            f"(в скобках рядом с ID в игре)\n\n"
            f"Пример: <code>16321</code>",
            reply_markup=ik([btn("⏭ Пропустить", "skip_server")])
        )
        return

    await state.update_data(bp_server="")
    await _make_order(msg, state)


@r.message(Order.server)
async def msg_server(msg: Message, state: FSMContext):
    server = (msg.text or "").strip().strip("()")
    await state.update_data(bp_server=server)
    await _make_order(msg, state)


@r.callback_query(F.data == "skip_server")
async def cb_skip_server(cb: CallbackQuery, state: FSMContext):
    await state.update_data(bp_server="")
    await _make_order(cb.message, state, edit=True)
    await cb.answer()


# ── Build order + show summary ────────────────────────────────
async def _make_order(event, state: FSMContext, uid=None, server=None, edit=False):
    data   = await state.get_data()
    gid    = data["gid"]
    pid    = data["pid"]
    prod   = data["prod"]
    bp_uid = uid if uid is not None else data.get("bp_uid", "")
    bp_srv = server if server is not None else data.get("bp_server", "")

    # Get user info
    if hasattr(event, "from_user"):
        user = event.from_user
    elif hasattr(event, "chat"):
        user = None
    else:
        user = None

    uid_int  = user.id if user else (event.chat.id if hasattr(event, "chat") else 0)
    name_str = ""
    if user:
        name_str = f"{user.first_name or ''} {user.last_name or ''}".strip() or "Покупатель"

    # Validate player via Buypin if possible
    bp_username = ""
    if bp_uid and gid in GAME_KEYS:
        try:
            result = await bp_validate(GAME_KEYS[gid], bp_uid, bp_srv)
            if result.get("ok"):
                bp_username = result.get("username", "")
        except Exception:
            pass

    # Extract diamonds for MLBB
    diamonds = None
    m = re.match(r"^(\d+)", str(prod.get("name", "")))
    if m and gid == "mlbb":
        diamonds = int(m.group(1))

    oid = uuid.uuid4().hex[:16]
    order = {
        "id":             oid,
        "pid":            pid,
        "gid":            gid,
        "name":           prod["name"],
        "price":          prod["price"],
        "diamonds":       diamonds,
        "buyer_tg_id":    uid_int,
        "buyer_name":     name_str or "Покупатель",
        "buyer_username": getattr(user, "username", None),
        "bp_username":    bp_username,
        "cred_fields":    (
            [{"label": "Игровой ID", "value": bp_uid}]
            + ([{"label": "Сервер", "value": bp_srv}] if bp_srv else [])
        ) if bp_uid else [],
        "bp_uid":         bp_uid or None,
        "bp_server":      bp_srv or None,
        "bp_order_ids":   [],
        "status":         "pending",
        "created_at":     now(),
        "updated_at":     now(),
        "error":          None,
    }

    _pending[uid_int] = order
    await state.update_data(oid=oid)
    await state.set_state(Order.confirm)
    await _show_summary(event, order, edit=edit)


async def _show_summary(event, order: dict, edit=False):
    gname = GAME_NAMES.get(order["gid"], order["gid"])
    price = order.get("price", 0)

    # Credentials info
    creds = ""
    if order.get("bp_uid"):
        creds = f"\n🎮 ID: <code>{order['bp_uid']}</code>"
        if order.get("bp_server"):
            creds += f"\n📍 Сервер: {order['bp_server']}"
        if order.get("bp_username"):
            creds += f"\n👤 Ник: <b>{order['bp_username']}</b> ✅"

    # Cards list
    cards_txt = "\n💳 <b>Карты для оплаты:</b>\n"
    for last4, num in CARDS.items():
        bank = "HUMO" if num.startswith("9860") else "UzCard"
        cards_txt += f"  <code>{num}</code> ({bank})\n"

    # FrozenCoins balance
    w   = get_wallet(order["buyer_tg_id"])
    bal = w.get("balance", 0)
    coins_line = f"\n🪙 Твои монеты: <b>{fmt(bal)} FC</b>" if bal > 0 else ""

    # Special notice for fast roblox
    fast_note = ""
    if order["gid"] == "roblox":
        items = PRODUCTS.get("roblox", [])
        p = next((x for x in items if x["id"] == order["pid"]), None)
        if p and p.get("cat") == "robux_fast":
            fast_note = "\n\n⚡ <b>Моментальные Robux!</b> После оплаты сразу напишем."

    text = (
        f"📋 <b>Подтверди заказ</b>\n\n"
        f"📦 {order['name']}\n"
        f"🎮 {gname}\n"
        f"💰 <b>{fmt(price)} сум</b>"
        f"{creds}{coins_line}"
        f"{cards_txt}\n"
        f"1. Переведи <b>{fmt(price)} сум</b> на любую карту\n"
        f"2. Нажми «Оплатил картой»\n"
        f"3. Введи сумму из истории банка"
        f"{fast_note}"
    )

    if edit or not hasattr(event, "answer"):
        await event.edit_text(text, reply_markup=confirm_kb(order["id"]))
    else:
        await event.answer(text, reply_markup=confirm_kb(order["id"]))


# ════════════════════════════════════════════════════════════
#  Payment — card
# ════════════════════════════════════════════════════════════
@r.callback_query(F.data.startswith("paycard:"))
async def cb_paycard(cb: CallbackQuery, state: FSMContext):
    oid = cb.data[8:]
    o   = _pending.get(cb.from_user.id)
    if not o or o["id"] != oid:
        await cb.answer("Заказ не найден. Начни заново /start", show_alert=True)
        return

    await state.set_state(Order.card)
    await cb.message.edit_text(
        "💳 <b>Выбери карту на которую переводил:</b>",
        reply_markup=cards_kb(oid)
    )
    await cb.answer()


@r.callback_query(F.data.startswith("backconfirm:"))
async def cb_backconfirm(cb: CallbackQuery, state: FSMContext):
    oid = cb.data[12:]
    o   = _pending.get(cb.from_user.id)
    if o and o["id"] == oid:
        await cb.message.edit_text(
            "📋 Подтверди заказ:",
            reply_markup=confirm_kb(oid)
        )
    await cb.answer()


@r.callback_query(F.data.startswith("card:"))
async def cb_card(cb: CallbackQuery, state: FSMContext):
    parts = cb.data.split(":")
    oid, last4 = parts[1], parts[2]
    await state.update_data(card_last4=last4)
    await state.set_state(Order.amount)

    num = CARDS.get(last4, "****")
    await cb.message.edit_text(
        f"💳 Карта: <code>{num}</code>\n\n"
        f"✏️ <b>Введи точную сумму перевода</b>\n"
        f"(из истории банка)\n\n"
        f"Пример: <code>17500</code>",
        reply_markup=ik([btn("◀️ Назад", f"paycard:{oid}")])
    )
    await cb.answer()


@r.message(Order.amount)
async def msg_amount(msg: Message, state: FSMContext):
    raw = (msg.text or "").strip().replace(" ", "").replace(",", ".")
    try:
        amount = int(float(raw))
    except ValueError:
        await msg.answer("❌ Введи число, например: <code>17500</code>")
        return

    data  = await state.get_data()
    oid   = data.get("oid", "")
    last4 = data.get("card_last4", "")
    uid   = msg.from_user.id
    o     = _pending.get(uid)

    if not o or o["id"] != oid:
        await msg.answer("❌ Заказ не найден. Начни заново /start")
        await state.clear()
        return

    # Check amount
    expected = o.get("price", 0)
    if expected and abs(expected - amount) > 1000:
        await msg.answer(
            f"❌ <b>Сумма не совпадает!</b>\n\n"
            f"Ожидалось: <b>{fmt(expected)} сум</b>\n"
            f"Ты ввёл:   <b>{fmt(amount)} сум</b>\n\n"
            f"Проверь историю банка и введи точную сумму:"
        )
        return

    # Anti-duplicate
    key = f"{last4}_{amount}_{oid}"
    if receipt_seen(key):
        await msg.answer("❌ Этот чек уже использован")
        return

    # Update order
    o.update({
        "buyer_tg_id":    uid,
        "buyer_name":     f"{msg.from_user.first_name or ''} {msg.from_user.last_name or ''}".strip(),
        "buyer_username": msg.from_user.username,
    })
    await save_order(o)
    await set_status(oid, "paid",
        paid_amount = amount,
        paid_card   = CARDS.get(last4, ""),
        paid_method = "card"
    )
    await state.clear()
    _pending.pop(uid, None)

    short = sid(oid)
    await msg.answer(
        f"✅ <b>Оплата подтверждена!</b>\n\n"
        f"📦 {o['name']}\n"
        f"💰 {fmt(amount)} сум\n"
        f"🆔 #{short}\n\n"
        f"⚙️ Обрабатываем заказ...",
        reply_markup=ik(
            [btn("📋 Мои заказы", "myorders")],
            [btn("🏠 Меню",       "main_menu")],
        )
    )

    # Notify admin
    creds = "\n".join(
        f"  • {f['label']}: {f['value']}"
        for f in o.get("cred_fields", [])
    )
    await send(ADMIN_ID,
        f"💳 <b>Оплата подтверждена!</b>\n\n"
        f"📦 {o['name']}\n"
        f"💰 {fmt(amount)} сум → *{last4}\n"
        f"🆔 #{short}\n"
        f"👤 {o.get('buyer_name', '')}"
        + (f"\n\n{creds}" if creds else "")
        + f"\n\n✅ /done_{short.lower()}   ❌ /reject_{short.lower()}"
    )

    asyncio.create_task(fulfill(oid, send))


# ════════════════════════════════════════════════════════════
#  Payment — FrozenCoins
# ════════════════════════════════════════════════════════════
@r.callback_query(F.data.startswith("paycoins:"))
async def cb_paycoins(cb: CallbackQuery, state: FSMContext):
    oid = cb.data[9:]
    uid = cb.from_user.id
    o   = _pending.get(uid)

    if not o or o["id"] != oid:
        await cb.answer("Заказ не найден", show_alert=True)
        return

    w     = get_wallet(uid)
    bal   = w.get("balance", 0)
    price = o.get("price", 0)

    if bal < price:
        await cb.answer(
            f"❌ Нужно {fmt(price)} FC, у тебя {fmt(bal)} FC\n"
            f"Для пополнения напиши @frozenld1",
            show_alert=True
        )
        return

    ok = await wallet_sub(uid, price, f"Заказ #{sid(oid)}", oid)
    if not ok:
        await cb.answer("❌ Ошибка списания", show_alert=True)
        return

    o.update({
        "buyer_tg_id":    uid,
        "buyer_name":     f"{cb.from_user.first_name or ''} {cb.from_user.last_name or ''}".strip(),
        "buyer_username": cb.from_user.username,
    })
    await save_order(o)
    await set_status(oid, "paid", paid_method="coins", paid_amount=price)
    _pending.pop(uid, None)
    await state.clear()

    short = sid(oid)
    await cb.message.edit_text(
        f"🪙 <b>Оплачено FrozenCoins!</b>\n\n"
        f"📦 {o['name']}\n"
        f"💰 {fmt(price)} FC\n"
        f"🆔 #{short}\n\n"
        f"⚙️ Обрабатываем заказ...",
        reply_markup=ik([btn("📋 Мои заказы", "myorders")])
    )
    await cb.answer()

    await send(ADMIN_ID,
        f"🪙 <b>Оплата FC!</b>\n📦 {o['name']}\n"
        f"💰 {fmt(price)} FC\n🆔 #{short}"
    )
    asyncio.create_task(fulfill(oid, send))


# ════════════════════════════════════════════════════════════
#  My orders
# ════════════════════════════════════════════════════════════
@r.callback_query(F.data == "myorders")
async def cb_myorders(cb: CallbackQuery):
    uid    = cb.from_user.id
    orders = [o for o in all_orders() if o.get("buyer_tg_id") == uid]
    orders.sort(key=lambda x: x.get("created_at", ""), reverse=True)
    orders = orders[:8]

    if not orders:
        await cb.message.edit_text(
            "📋 Заказов пока нет.\n\nНажми «Сделать заказ»!",
            reply_markup=ik(
                [btn("🛍 Заказать", "shop")],
                [btn("◀️ Меню",    "main_menu")]
            )
        )
        await cb.answer()
        return

    status_e = {
        "done":       "✅",
        "pending":    "⏳",
        "paid":       "💳",
        "processing": "⚙️",
        "rejected":   "❌",
        "failed":     "🔴",
        "timeout":    "⏰",
    }
    status_t = {
        "done":       "выдан",
        "pending":    "ожидает",
        "paid":       "оплачен",
        "processing": "обрабатывается",
        "rejected":   "отклонён",
        "failed":     "ошибка",
        "timeout":    "таймаут",
    }
    lines = []
    for o in orders:
        e = status_e.get(o["status"], "❔")
        t = status_t.get(o["status"], o["status"])
        lines.append(
            f"{e} <b>{o['name']}</b> — <code>#{sid(o['id'])}</code>\n"
            f"   <i>{t}</i> · {fmt(o.get('price',0))} сум"
        )

    await cb.message.edit_text(
        "📋 <b>Твои последние заказы:</b>\n\n" + "\n\n".join(lines),
        reply_markup=ik(
            [btn("🛍 Новый заказ", "shop")],
            [btn("◀️ Меню",       "main_menu")]
        )
    )
    await cb.answer()


# ════════════════════════════════════════════════════════════
#  Wallet
# ════════════════════════════════════════════════════════════
@r.callback_query(F.data == "wallet")
@r.message(Command("wallet"))
async def cb_wallet(event, **_):
    uid = (
        event.from_user.id
        if hasattr(event, "from_user")
        else event.message.from_user.id
    )
    w   = get_wallet(uid)
    bal = w.get("balance", 0)
    txs = w.get("txs", [])[:5]

    tx_txt = ""
    if txs:
        tx_txt = "\n\n<b>Последние транзакции:</b>\n"
        for t in txs:
            sign = "+" if t["type"] == "in" else "−"
            tx_txt += f"  {sign}{fmt(t['amount'])} FC — {t['desc']}\n"

    text = (
        f"💰 <b>Кошелёк FrozenCoins</b>\n\n"
        f"🪙 Баланс: <b>{fmt(bal)} FC</b>"
        f"{tx_txt}\n\n"
        f"<i>Для пополнения переведи деньги на карту\n"
        f"и напиши @frozenld1</i>"
    )
    back = ik([btn("🛍 Потратить", "shop")], [btn("◀️ Меню", "main_menu")])

    if isinstance(event, Message):
        await event.answer(text, reply_markup=back)
    else:
        await event.message.edit_text(text, reply_markup=back)
        await event.answer()


# ════════════════════════════════════════════════════════════
#  Cancel
# ════════════════════════════════════════════════════════════
@r.callback_query(F.data == "cancel")
async def cb_cancel(cb: CallbackQuery, state: FSMContext):
    await state.clear()
    _pending.pop(cb.from_user.id, None)
    await cb.message.edit_text(
        "❌ Отменено.",
        reply_markup=ik([btn("🏠 Главное меню", "main_menu")])
    )
    await cb.answer()


# ════════════════════════════════════════════════════════════
#  Forward user messages to admin
# ════════════════════════════════════════════════════════════
@r.message(F.text & ~F.text.startswith("/"))
async def fwd_to_admin(msg: Message, state: FSMContext):
    cur = await state.get_state()
    # Don't forward FSM inputs
    if cur in (Order.uid, Order.server, Order.amount):
        return
    if msg.from_user.id == ADMIN_ID:
        return

    name = f"{msg.from_user.first_name or ''} {msg.from_user.last_name or ''}".strip()
    user = f"@{msg.from_user.username}" if msg.from_user.username else f"ID:{msg.from_user.id}"

    await send(ADMIN_ID,
        f"📨 <b>Сообщение от покупателя</b>\n"
        f"👤 <b>{name}</b> {user}\n"
        f"🆔 <code>{msg.from_user.id}</code>\n\n"
        f"💬 {msg.text}\n\n"
        f"<i>Ответить: {user}</i>"
    )
    await msg.answer(
        "✅ Сообщение получено! Ответим в течение 5–15 минут. 🕐"
    )


# ════════════════════════════════════════════════════════════
#  ADMIN COMMANDS (only for ADMIN_ID)
# ════════════════════════════════════════════════════════════
def is_admin(uid: int) -> bool:
    return uid == ADMIN_ID


@r.message(Command("admin"))
async def cmd_admin(msg: Message):
    if not is_admin(msg.from_user.id): return
    await msg.answer(
        "🔧 <b>Команды администратора:</b>\n\n"
        "/orders — последние 10 заказов\n"
        "/stats — статистика\n"
        "/done_XXXXXXXX — выдать заказ\n"
        "/reject_XXXXXXXX — отклонить заказ\n"
        "/topup USERID СУММА — начислить FC\n"
        "/syncproducts — синхронизировать Buypin\n"
        "/bpbalance — баланс Buypin кошелька"
    )


@r.message(Command("orders"))
async def cmd_orders(msg: Message):
    if not is_admin(msg.from_user.id): return
    orders = sorted(
        all_orders(),
        key=lambda x: x.get("created_at", ""),
        reverse=True
    )[:10]
    if not orders:
        await msg.answer("Заказов пока нет")
        return
    se = {"done":"✅","pending":"⏳","paid":"💳","processing":"⚙️",
          "rejected":"❌","failed":"🔴","timeout":"⏰"}
    lines = []
    for o in orders:
        lines.append(
            f"{se.get(o['status'],'❔')} <code>#{sid(o['id'])}</code> "
            f"<b>{o['name']}</b>\n"
            f"  👤 {o.get('buyer_name','')} · {fmt(o.get('price',0))} сум"
        )
    await msg.answer("📋 <b>Последние заказы:</b>\n\n" + "\n\n".join(lines))


@r.message(Command("stats"))
async def cmd_stats(msg: Message):
    if not is_admin(msg.from_user.id): return
    orders  = all_orders()
    done    = sum(1 for o in orders if o["status"] == "done")
    pending = sum(1 for o in orders if o["status"] in ("pending","paid","processing"))
    revenue = sum(o.get("price",0) for o in orders if o["status"] == "done")
    await msg.answer(
        f"📊 <b>Статистика FrozenShop</b>\n\n"
        f"📦 Всего заказов: <b>{len(orders)}</b>\n"
        f"✅ Выдано:        <b>{done}</b>\n"
        f"⏳ Ожидают:       <b>{pending}</b>\n"
        f"💰 Выручка:       <b>{fmt(revenue)} сум</b>"
    )


@r.message(lambda m: m.text and m.text.startswith("/done_"))
async def cmd_done(msg: Message):
    if not is_admin(msg.from_user.id): return
    short = msg.text[6:].upper()
    o = next((x for x in all_orders() if x["id"][:8].upper() == short), None)
    if not o:
        await msg.answer(f"❌ Заказ #{short} не найден")
        return
    await set_status(o["id"], "done")
    await msg.answer(f"✅ Заказ #{short} выдан")
    if o.get("buyer_tg_id"):
        await send(o["buyer_tg_id"],
            f"🎉 <b>Ваш заказ выдан!</b>\n"
            f"📦 {o['name']}\n"
            f"🆔 #{short}\n"
            f"✨ Спасибо! FrozenShop ❄️\n"
            f"Вопросы: @frozenld1"
        )


@r.message(lambda m: m.text and m.text.startswith("/reject_"))
async def cmd_reject(msg: Message):
    if not is_admin(msg.from_user.id): return
    short = msg.text[8:].upper()
    o = next((x for x in all_orders() if x["id"][:8].upper() == short), None)
    if not o:
        await msg.answer(f"❌ Заказ #{short} не найден")
        return
    await set_status(o["id"], "rejected", error="Отклонён")
    await msg.answer(f"❌ Заказ #{short} отклонён")
    if o.get("buyer_tg_id"):
        await send(o["buyer_tg_id"], "❌ Заказ отклонён. Вопросы: @frozenld1")


@r.message(Command("topup"))
async def cmd_topup(msg: Message):
    if not is_admin(msg.from_user.id): return
    parts = (msg.text or "").split()[1:]
    if len(parts) < 2:
        await msg.answer("Формат: /topup USERID СУММА\nПример: /topup 123456789 50000")
        return
    try:
        uid    = int(parts[0])
        amount = float(parts[1])
    except ValueError:
        await msg.answer("❌ Неверный формат")
        return
    bal = await wallet_add(uid, amount, "Пополнение администратором")
    await msg.answer(f"✅ Начислено {fmt(amount)} FC → {uid}\nБаланс: {fmt(bal)} FC")
    await send(uid,
        f"🪙 Тебе начислено <b>{fmt(amount)} FrozenCoins</b>!\n"
        f"Баланс: <b>{fmt(bal)} FC</b>"
    )


@r.message(Command("syncproducts"))
async def cmd_sync(msg: Message):
    if not is_admin(msg.from_user.id): return
    await msg.answer("🔄 Синхронизирую продукты Buypin...")
    try:
        result = await sync_products()
        await msg.answer(f"✅ Синхронизировано {len(result)} продуктов!")
    except Exception as e:
        await msg.answer(f"❌ Ошибка: {e}")


@r.message(Command("bpbalance"))
async def cmd_bpbalance(msg: Message):
    if not is_admin(msg.from_user.id): return
    try:
        bal = await bp_balance()
        await msg.answer(f"💰 Buypin баланс: <b>${bal}</b>")
    except Exception as e:
        await msg.answer(f"❌ {e}")
