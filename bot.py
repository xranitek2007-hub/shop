"""
FrozenShop Bot — Полная автоматизация
Токен уже вставлен. Замени только ADMIN_ID и WEBHOOK_URL.
"""
import asyncio, json, os, logging, uuid
from datetime import datetime
from typing import Optional

from aiogram import Bot, Dispatcher, F
from aiogram.types import (
    Message, CallbackQuery,
    InlineKeyboardMarkup, InlineKeyboardButton,
    ReplyKeyboardMarkup, KeyboardButton
)
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage

from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)

# ══════════════════════════════════════════════
#  🔧 НАСТРОЙКИ
# ══════════════════════════════════════════════
BOT_TOKEN   = os.getenv("BOT_TOKEN",   "8165503899:AAGlY0wz8vMqtWftiOXIDPTh95Gppk06FPs")
ADMIN_ID    = int(os.getenv("ADMIN_ID", "123456789"))   # ← ЗАМЕНИ на свой TG ID
WEBHOOK_URL = os.getenv("WEBHOOK_URL", "https://YOUR-APP.railway.app")  # ← после деплоя
PORT        = int(os.getenv("PORT", 8000))
SITE_URL    = os.getenv("SITE_URL",    "https://YOUR-SITE.vercel.app")  # ← твой сайт

CARDS = [
    {"bank": "HUMO", "number": "9860 1606 3787 3359", "raw": "9860160637873359", "owner": "Бухарбаев Бердах"},
    {"bank": "HUMO", "number": "9860 3501 4482 3951", "raw": "9860350144823951", "owner": "Бухарбаев Бердах"},
]

BONUSES: list[dict] = []   # добавляй через бота кнопкой "Управление бонусами"
# ══════════════════════════════════════════════

bot = Bot(token=BOT_TOKEN, parse_mode="HTML")
dp  = Dispatcher(storage=MemoryStorage())
app = FastAPI(title="FrozenShop API")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

orders: dict[str, dict] = {}
buyer_orders: dict[str, list] = {}


class BonusState(StatesGroup):
    title = State(); desc = State(); code = State()

class BroadcastState(StatesGroup):
    text = State()


# ── клавиатуры ──────────────────────────────
def admin_kb():
    return ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text="📋 Все заказы"),    KeyboardButton(text="⏳ Ожидающие")],
        [KeyboardButton(text="🎁 Бонусы"),        KeyboardButton(text="📊 Статистика")],
        [KeyboardButton(text="📢 Рассылка")],
    ], resize_keyboard=True)

def buyer_kb():
    return ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text="🛒 Мои заказы"),  KeyboardButton(text="🎁 Бонусы")],
        [KeyboardButton(text="💬 Поддержка"),   KeyboardButton(text="🌐 Магазин")],
    ], resize_keyboard=True)

def order_admin_kb(oid: str, buyer_id):
    rows = [[
        InlineKeyboardButton(text="✅ Выдан",    callback_data=f"done:{oid}"),
        InlineKeyboardButton(text="❌ Отклонён", callback_data=f"reject:{oid}"),
    ]]
    if buyer_id:
        rows.append([InlineKeyboardButton(text="💬 Написать покупателю", url=f"tg://user?id={buyer_id}")])
    return InlineKeyboardMarkup(inline_keyboard=rows)

def order_buyer_kb(oid: str):
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="💳 Получить реквизиты", callback_data=f"card:{oid}"),
        InlineKeyboardButton(text="🔄 Проверить статус",   callback_data=f"chk:{oid}"),
    ]])


# ── форматирование ──────────────────────────
def fmt(n): return f"{int(n):,}".replace(",", "\u202f")
def rub(s):  return fmt(max(1, round(int(s) / 150)))

def order_admin_text(o):
    ts = datetime.fromisoformat(o["date"]).strftime("%d.%m.%Y %H:%M")
    st = {"pending":"⏳ Ожидает","done":"✅ Выдан","rejected":"❌ Отклонён"}.get(o.get("status","pending"),"⏳")
    uid = o.get("buyer_id","?"); uname = ("@"+o["buyer_username"]) if o.get("buyer_username") else "—"
    return (
        f"🛒 <b>ЗАКАЗ #{o['id'][:8].upper()}</b>  {st}\n\n"
        f"🎮 <b>{o.get('gameName','—')}</b>  •  {o.get('name','—')}\n"
        f"💰 <b>{fmt(o.get('price',0))} сум</b>  (~{rub(o.get('price',0))} ₽)\n\n"
        f"👤 {o.get('buyer_name','?')}  {uname}\n"
        f"🆔 <code>{uid}</code>  •  🕐 {ts}"
        + (f"\n📝 {o['note']}" if o.get("note") else "")
    )

def order_buyer_text(o):
    st = {"pending":"⏳ Ожидает подтверждения","done":"✅ Выдан!","rejected":"❌ Отклонён"}.get(o.get("status","pending"),"⏳")
    return (
        f"📦 <b>{o.get('name','—')}</b>\n"
        f"🎮 {o.get('gameName','—')}  •  💰 {fmt(o.get('price',0))} сум\n"
        f"Статус: {st}  •  ID: <code>{o['id'][:8].upper()}</code>"
    )

def cards_msg(price=None):
    lines = ["💳 <b>Реквизиты для оплаты:</b>\n"]
    if price:
        lines.append(f"💰 <b>Сумма: {fmt(price)} сум</b>  (~{rub(price)} ₽)\n")
    for c in CARDS:
        lines += [f"<b>{c['bank']}</b>", f"<code>{c['number']}</code>", f"👤 {c['owner']}", ""]
    lines.append("📸 После оплаты пришли скриншот сюда — выдадим в течение 5 минут ⚡")
    return "\n".join(lines)


# ══════════════════════════════════════════════
#  REST API
# ══════════════════════════════════════════════
@app.post("/api/order")
async def api_order(request: Request):
    try:
        data = await request.json()
    except:
        raise HTTPException(400, "bad json")

    oid = data.get("id") or str(uuid.uuid4())
    data.update({"id": oid, "status": "pending", "date": data.get("date") or datetime.now().isoformat()})
    orders[oid] = data
    buyer_orders.setdefault(str(data.get("buyer_id","anon")), []).append(oid)

    # Уведомить тебя
    try:
        await bot.send_message(ADMIN_ID, order_admin_text(data),
                               reply_markup=order_admin_kb(oid, data.get("buyer_id")))
    except Exception as e:
        log.error(f"admin notify: {e}")

    # Уведомить покупателя + карты
    bid = data.get("buyer_id")
    if bid:
        try:
            await bot.send_message(bid,
                f"✅ <b>Заказ принят!</b>\n\n{order_buyer_text(data)}\n\n"
                "Оплати по реквизитам ниже и пришли скриншот ⬇️",
                reply_markup=order_buyer_kb(oid))
            await bot.send_message(bid, cards_msg(data.get("price")))
        except Exception as e:
            log.warning(f"buyer notify: {e}")

    return {"ok": True, "order_id": oid}


@app.post("/api/status")
async def api_status(request: Request):
    d = await request.json()
    o = orders.get(d.get("id",""))
    return {"status": o["status"] if o else "not_found"}


@app.get("/api/orders/{buyer_id}")
async def api_buyer_orders(buyer_id: str):
    ids = buyer_orders.get(buyer_id, [])
    return {"orders": [orders[i] for i in ids if i in orders]}


@app.post("/webhook")
async def tg_webhook(request: Request):
    from aiogram.types import Update
    update = Update.model_validate(await request.json())
    await dp.feed_update(bot, update)
    return {"ok": True}


@app.get("/health")
async def health():
    return {"ok": True, "orders": len(orders)}


# ══════════════════════════════════════════════
#  BOT HANDLERS
# ══════════════════════════════════════════════
@dp.message(CommandStart())
async def start(msg: Message):
    if msg.from_user.id == ADMIN_ID:
        await msg.answer("👋 <b>FrozenShop Admin</b>\nЗаказы приходят автоматически 🚀", reply_markup=admin_kb())
    else:
        await msg.answer(
            "👋 <b>Добро пожаловать в FrozenShop!</b>\n\n"
            "🎮 Алмазы, валюта, пропуска для игр\n"
            "⚡ Доставка от 5 минут • 24/7\n\n"
            "Используй кнопки ниже 👇",
            reply_markup=buyer_kb())


# ПОКУПАТЕЛЬ
@dp.message(F.text == "🛒 Мои заказы")
async def my_orders(msg: Message):
    uid = str(msg.from_user.id)
    ids = buyer_orders.get(uid, [])
    if not ids:
        await msg.answer("У вас пока нет заказов 😊\n\nПерейди в магазин и сделай первый заказ!",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[[
                InlineKeyboardButton(text="🛒 Открыть магазин", url=SITE_URL)]])); return
    await msg.answer(f"📋 <b>Ваши заказы ({len(ids)}):</b>")
    for oid in reversed(ids[-8:]):
        o = orders.get(oid)
        if not o: continue
        kb = order_buyer_kb(oid) if o.get("status") == "pending" else None
        await msg.answer(order_buyer_text(o), reply_markup=kb)


@dp.message(F.text == "🎁 Бонусы")
async def bonuses(msg: Message):
    if not BONUSES:
        await msg.answer("🎁 <b>Бонусы</b>\n\nСкоро появятся спецпредложения! Следи за обновлениями 👀"); return
    text = "🎁 <b>Активные бонусы:</b>\n\n"
    for b in BONUSES:
        text += f"<b>{b['title']}</b>\n{b['desc']}\n"
        if b.get("code"): text += f"Промокод: <code>{b['code']}</code>\n"
        text += "\n"
    await msg.answer(text)


@dp.message(F.text == "💬 Поддержка")
async def support(msg: Message):
    await msg.answer("💬 <b>Поддержка</b>\n\nПишите по любым вопросам:\n👤 @frozenld1\n\n"
        "Если есть проблема с заказом — пришли скриншот чека прямо сюда или напрямую @frozenld1")


@dp.message(F.text == "🌐 Магазин")
async def open_shop(msg: Message):
    await msg.answer("🛒 Переходи в магазин:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[[
            InlineKeyboardButton(text="🛒 FrozenShop", url=SITE_URL)]]))


# АДМИН
@dp.message(F.text == "📋 Все заказы")
async def all_orders(msg: Message):
    if msg.from_user.id != ADMIN_ID: return
    if not orders:
        await msg.answer("Заказов пока нет"); return
    recent = sorted(orders.values(), key=lambda x: x.get("date",""), reverse=True)[:10]
    for o in recent:
        kb = order_admin_kb(o["id"], o.get("buyer_id")) if o["status"]=="pending" else None
        await msg.answer(order_admin_text(o), reply_markup=kb)


@dp.message(F.text == "⏳ Ожидающие")
async def pending_orders(msg: Message):
    if msg.from_user.id != ADMIN_ID: return
    p = [o for o in orders.values() if o.get("status")=="pending"]
    if not p:
        await msg.answer("✅ Нет ожидающих заказов!"); return
    await msg.answer(f"⏳ <b>Ожидают подтверждения: {len(p)}</b>")
    for o in sorted(p, key=lambda x: x.get("date",""))[:10]:
        await msg.answer(order_admin_text(o), reply_markup=order_admin_kb(o["id"], o.get("buyer_id")))


@dp.message(F.text == "📊 Статистика")
async def stats(msg: Message):
    if msg.from_user.id != ADMIN_ID: return
    total = len(orders)
    done_list = [o for o in orders.values() if o.get("status")=="done"]
    revenue = sum(o.get("price",0) for o in done_list)
    await msg.answer(
        f"📊 <b>Статистика FrozenShop</b>\n\n"
        f"📦 Всего заказов: <b>{total}</b>\n"
        f"⏳ Ожидают: <b>{sum(1 for o in orders.values() if o.get('status')=='pending')}</b>\n"
        f"✅ Выдано: <b>{len(done_list)}</b>\n"
        f"❌ Отклонено: <b>{sum(1 for o in orders.values() if o.get('status')=='rejected')}</b>\n\n"
        f"💰 Выручка: <b>{fmt(revenue)} сум</b>\n"
        f"   ≈ <b>{rub(revenue)} ₽</b>\n\n"
        f"👥 Покупателей: <b>{len(buyer_orders)}</b>"
    )


@dp.message(F.text == "🎁 Бонусы", F.from_user.func(lambda u: True))
async def admin_bonuses_btn(msg: Message):
    if msg.from_user.id != ADMIN_ID:
        await bonuses(msg); return
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Добавить",    callback_data="bn:add")],
        [InlineKeyboardButton(text="📋 Все бонусы",  callback_data="bn:list")],
        [InlineKeyboardButton(text="🗑 Удалить",     callback_data="bn:del")],
    ])
    await msg.answer("🎁 <b>Управление бонусами</b>", reply_markup=kb)


@dp.message(F.text == "📢 Рассылка")
async def broadcast_start(msg: Message, state: FSMContext):
    if msg.from_user.id != ADMIN_ID: return
    await state.set_state(BroadcastState.text)
    await msg.answer("📢 Напиши сообщение для рассылки всем покупателям.\n/cancel — отменить")


@dp.message(BroadcastState.text)
async def broadcast_send(msg: Message, state: FSMContext):
    if msg.from_user.id != ADMIN_ID: return
    await state.clear()
    sent = fail = 0
    uids = {int(uid) for uid in buyer_orders if uid.isdigit() and int(uid) != ADMIN_ID}
    for uid in uids:
        try:
            await bot.send_message(uid, msg.html_text or msg.text or "")
            sent += 1; await asyncio.sleep(0.05)
        except: fail += 1
    await msg.answer(f"📢 Рассылка завершена!\n✅ {sent} доставлено\n❌ {fail} не доставлено")


# Приём скриншота/чека
@dp.message(F.photo | F.document)
async def receipt(msg: Message):
    if msg.from_user.id == ADMIN_ID: return
    uid = str(msg.from_user.id)
    pending = [orders[i] for i in buyer_orders.get(uid,[]) if orders.get(i,{}).get("status")=="pending"]
    uname = f"@{msg.from_user.username}" if msg.from_user.username else msg.from_user.full_name
    header = f"📸 <b>ЧЕК от {uname}</b> (<code>{msg.from_user.id}</code>)"
    if pending:
        o = pending[-1]
        header += f"\n📦 {o.get('name','—')} — {fmt(o.get('price',0))} сум"
    try:
        await bot.send_message(ADMIN_ID, header)
        await bot.forward_message(ADMIN_ID, msg.chat.id, msg.message_id)
        if pending:
            await bot.send_message(ADMIN_ID, "Подтвердить?",
                reply_markup=order_admin_kb(pending[-1]["id"], msg.from_user.id))
    except Exception as e:
        log.error(f"receipt: {e}")
    await msg.answer("✅ <b>Чек получен!</b>\nПроверяем оплату — выдадим в течение 5 минут ⚡")


# ══════════════════════════════════════════════
#  CALLBACKS
# ══════════════════════════════════════════════
@dp.callback_query(F.data.startswith("done:"))
async def cb_done(cb: CallbackQuery):
    if cb.from_user.id != ADMIN_ID:
        await cb.answer("Нет доступа"); return
    oid = cb.data.split(":",1)[1]
    o = orders.get(oid)
    if not o: await cb.answer("Не найден"); return
    o["status"] = "done"
    await cb.message.edit_text(order_admin_text(o) + "\n\n✅ <b>ВЫДАН</b>")
    await cb.answer("✅ Выдан!")
    bid = o.get("buyer_id")
    if bid:
        try:
            await bot.send_message(bid,
                f"🎉 <b>Ваш заказ выдан!</b>\n\n{order_buyer_text(o)}\n\n"
                f"Спасибо за покупку в <b>FrozenShop</b>! 🛒\n"
                f"По вопросам: @frozenld1",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[[
                    InlineKeyboardButton(text="🛒 Купить ещё", url=SITE_URL)]]))
        except Exception as e:
            await cb.message.answer(f"⚠️ Не удалось уведомить покупателя (ID {bid}): {e}")


@dp.callback_query(F.data.startswith("reject:"))
async def cb_reject(cb: CallbackQuery):
    if cb.from_user.id != ADMIN_ID:
        await cb.answer("Нет доступа"); return
    oid = cb.data.split(":",1)[1]
    o = orders.get(oid)
    if not o: await cb.answer("Не найден"); return
    o["status"] = "rejected"
    await cb.message.edit_text(order_admin_text(o) + "\n\n❌ <b>ОТКЛОНЁН</b>")
    await cb.answer("❌ Отклонён")
    bid = o.get("buyer_id")
    if bid:
        try:
            await bot.send_message(bid,
                f"❌ <b>Заказ отклонён</b>\n\n{order_buyer_text(o)}\n\nПо вопросам: @frozenld1")
        except: pass


@dp.callback_query(F.data.startswith("card:"))
async def cb_card(cb: CallbackQuery):
    oid = cb.data.split(":",1)[1]
    o = orders.get(oid)
    if not o: await cb.answer("Заказ не найден", show_alert=True); return
    if o["status"] != "pending": await cb.answer("Заказ уже обработан", show_alert=True); return
    await cb.message.answer(cards_msg(o.get("price")))
    await cb.answer()


@dp.callback_query(F.data.startswith("chk:"))
async def cb_check(cb: CallbackQuery):
    oid = cb.data.split(":",1)[1]
    o = orders.get(oid)
    if not o: await cb.answer("Не найден", show_alert=True); return
    st = {"pending":"⏳ Ожидает подтверждения","done":"✅ Выдан!","rejected":"❌ Отклонён"}.get(o["status"],"⏳")
    await cb.answer(st, show_alert=True)


@dp.callback_query(F.data == "bn:list")
async def cb_bn_list(cb: CallbackQuery):
    if cb.from_user.id != ADMIN_ID: return
    if not BONUSES: await cb.answer("Бонусов нет", show_alert=True); return
    text = "📋 <b>Бонусы:</b>\n\n" + "\n".join(
        f"• {b['title']} — {b['desc']}" + (f" [{b['code']}]" if b.get("code") else "")
        for b in BONUSES)
    await cb.message.answer(text); await cb.answer()


@dp.callback_query(F.data == "bn:add")
async def cb_bn_add(cb: CallbackQuery, state: FSMContext):
    if cb.from_user.id != ADMIN_ID: return
    await state.set_state(BonusState.title)
    await cb.message.answer("Название бонуса (напр: 🔥 Скидка 10%):"); await cb.answer()


@dp.message(BonusState.title)
async def bn_title(msg: Message, state: FSMContext):
    await state.update_data(title=msg.text); await state.set_state(BonusState.desc)
    await msg.answer("Описание:")

@dp.message(BonusState.desc)
async def bn_desc(msg: Message, state: FSMContext):
    await state.update_data(desc=msg.text); await state.set_state(BonusState.code)
    await msg.answer("Промокод (или 'нет'):")

@dp.message(BonusState.code)
async def bn_code(msg: Message, state: FSMContext):
    d = await state.get_data(); await state.clear()
    b = {"id": str(uuid.uuid4())[:6], "title": d["title"], "desc": d["desc"],
         "code": None if msg.text.lower()=="нет" else msg.text}
    BONUSES.append(b)
    await msg.answer(f"✅ Бонус добавлен!\n{b['title']}\n{b['desc']}")


@dp.message(Command("cancel"))
async def cancel(msg: Message, state: FSMContext):
    await state.clear(); await msg.answer("Отменено.")


# ══════════════════════════════════════════════
#  STARTUP
# ══════════════════════════════════════════════
async def on_startup():
    wh = f"{WEBHOOK_URL}/webhook"
    await bot.set_webhook(wh)
    log.info(f"Webhook: {wh}")
    try:
        await bot.send_message(ADMIN_ID, "🚀 <b>FrozenShop Bot запущен!</b>\nЖду заказов...")
    except: pass

async def on_shutdown():
    await bot.delete_webhook()

app.add_event_handler("startup",  on_startup)
app.add_event_handler("shutdown", on_shutdown)

if __name__ == "__main__":
    uvicorn.run("bot:app", host="0.0.0.0", port=PORT)
