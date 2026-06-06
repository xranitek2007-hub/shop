"""
FrozenShop API — FastAPI backend
Payment system + Buypin integration + Admin panel
"""
import uuid
import asyncio
from fastapi import FastAPI, HTTPException, Header, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from typing import Optional

from config import CARDS, ADMIN_ID, SECRET, GAME_KEYS, PRODUCTS, GAME_NAMES, GAME_EMOJI
from db import (
    get_order, all_orders, save_order, set_status,
    get_wallet, wallet_add, wallet_sub,
    receipt_seen, sid, now, fmt
)
from buypin import (
    fulfill, sync_products, bp_validate,
    bp_balance, bp_products
)

app = FastAPI(title="FrozenShop API", version="2.0", docs_url="/docs")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)

# Telegram send function — set from bot.py
_notify = None

def set_notify(fn):
    global _notify
    _notify = fn

async def tg(chat_id, text: str):
    if _notify:
        await _notify(chat_id, text)

def _auth(s: str):
    if s != SECRET:
        raise HTTPException(403, detail="Неверный SECRET")


# ── Pydantic Models ───────────────────────────────────────────

class OrderIn(BaseModel):
    id:             Optional[str]  = None
    pid:            str
    gid:            str
    name:           str
    price:          int            = 0
    diamonds:       Optional[int]  = None
    buyer_tg_id:    Optional[int]  = None
    buyer_name:     Optional[str]  = "Покупатель"
    buyer_username: Optional[str]  = None
    cred_fields:    list           = []
    bp_uid:         Optional[str]  = None
    bp_server:      Optional[str]  = None

class PayIn(BaseModel):
    order_id:    str
    amount:      int
    card_last4:  Optional[str] = None
    buyer_tg_id: Optional[int] = None
    buyer_name:  Optional[str] = None
    method:      str = "card"  # card | coins

class ValidateIn(BaseModel):
    game_key:  str
    player_id: str
    server_id: Optional[str] = ""

class AdminAction(BaseModel):
    id:      Optional[str]   = None
    user_id: Optional[int]   = None
    amount:  Optional[float] = None
    desc:    Optional[str]   = None
    reason:  Optional[str]   = None


# ════════════════════════════════════════════════════════════
#  PUBLIC ENDPOINTS (called from Mini App / website)
# ════════════════════════════════════════════════════════════

@app.get("/")
async def health():
    return {
        "ok":      True,
        "service": "FrozenShop",
        "orders":  len(all_orders()),
        "bp_key":  "✅ set" if __import__("config").BUYPIN_KEY else "❌ not set",
    }


@app.get("/api/products")
async def api_products():
    """All products for website / Mini App"""
    return {
        "ok":       True,
        "products": PRODUCTS,
        "games":    GAME_NAMES,
        "emoji":    GAME_EMOJI,
    }


@app.post("/api/order")
async def api_create_order(data: OrderIn):
    """Create new order (from Mini App or website)"""
    oid = data.id or uuid.uuid4().hex[:16]

    order = {
        "id":             oid,
        "pid":            data.pid,
        "gid":            data.gid,
        "name":           data.name,
        "price":          data.price,
        "diamonds":       data.diamonds,
        "buyer_tg_id":    data.buyer_tg_id,
        "buyer_name":     data.buyer_name,
        "buyer_username": data.buyer_username,
        "cred_fields":    data.cred_fields,
        "bp_uid":         data.bp_uid,
        "bp_server":      data.bp_server,
        "bp_order_ids":   [],
        "status":         "pending",
        "created_at":     now(),
        "updated_at":     now(),
        "error":          None,
    }
    await save_order(order)

    # Notify admin
    creds = ""
    if data.cred_fields:
        lines = "\n".join(
            f"  • {f['label']}: <code>{f['value']}</code>"
            for f in data.cred_fields
        )
        creds = f"\n\n📋 <b>Данные:</b>\n{lines}"

    short = sid(oid)
    uname = f" (@{data.buyer_username})" if data.buyer_username else ""
    await tg(ADMIN_ID,
        f"🛒 <b>Новый заказ!</b>\n\n"
        f"📦 <b>{data.name}</b>\n"
        f"💰 {fmt(data.price)} сум\n"
        f"🆔 <code>#{short}</code>\n"
        f"👤 {data.buyer_name}{uname}"
        f"{creds}\n\n"
        f"✅ /done_{short.lower()}   ❌ /reject_{short.lower()}"
    )
    return {"ok": True, "order_id": oid}


@app.post("/api/pay")
async def api_pay(data: PayIn):
    """
    Confirm payment and trigger auto-fulfillment.

    Payment methods:
      card   — manual card transfer + receipt verification
      coins  — FrozenCoins wallet deduction
    """
    order = get_order(data.order_id)
    if not order:
        return {"ok": False, "error": "Заказ не найден"}
    if order["status"] == "done":
        return {"ok": False, "error": "Заказ уже выдан"}

    short = sid(data.order_id)

    # ── FrozenCoins payment ────────────────────────────────────
    if data.method == "coins":
        if not data.buyer_tg_id:
            return {"ok": False, "error": "Нужен Telegram ID для оплаты монетами"}

        ok = await wallet_sub(
            data.buyer_tg_id, order["price"],
            f"Заказ #{short}", data.order_id
        )
        if not ok:
            w = get_wallet(data.buyer_tg_id)
            bal = w.get("balance", 0)
            return {
                "ok": False,
                "error": (
                    f"Недостаточно FrozenCoins. "
                    f"Нужно: {fmt(order['price'])} FC, "
                    f"у вас: {fmt(bal)} FC"
                )
            }

        await set_status(data.order_id, "paid",
            paid_method="coins",
            buyer_tg_id=data.buyer_tg_id,
            buyer_name=data.buyer_name or order.get("buyer_name")
        )
        await tg(ADMIN_ID,
            f"🪙 <b>Оплата FrozenCoins!</b>\n"
            f"📦 {order['name']}\n"
            f"💰 {fmt(order['price'])} FC\n"
            f"🆔 #{short}"
        )
        asyncio.create_task(fulfill(data.order_id, tg))
        return {"ok": True, "message": "Оплачено! Заказ обрабатывается."}

    # ── Card payment ───────────────────────────────────────────
    if data.card_last4 and data.card_last4 not in CARDS:
        return {"ok": False, "error": "Карта не найдена. Проверь последние 4 цифры."}

    expected = order.get("price", 0)
    if expected and abs(expected - data.amount) > 1000:
        return {
            "ok": False,
            "error": (
                f"Сумма не совпадает.\n"
                f"Нужно: {fmt(expected)} сум\n"
                f"Ты указал: {fmt(data.amount)} сум"
            )
        }

    # Anti-duplicate check
    key = f"{data.card_last4}_{data.amount}_{data.order_id}"
    if receipt_seen(key):
        return {"ok": False, "error": "Этот чек уже использован"}

    # Update order
    buyer_tg  = data.buyer_tg_id or order.get("buyer_tg_id")
    buyer_nm  = data.buyer_name  or order.get("buyer_name", "Покупатель")
    await set_status(data.order_id, "paid",
        paid_amount  = data.amount,
        paid_card    = CARDS.get(data.card_last4 or "", ""),
        paid_method  = "card",
        buyer_tg_id  = buyer_tg,
        buyer_name   = buyer_nm,
    )
    order = get_order(data.order_id)

    # Notify admin
    await tg(ADMIN_ID,
        f"💳 <b>Оплата подтверждена!</b>\n"
        f"📦 {order['name']}\n"
        f"💰 {fmt(data.amount)} сум → карта *{data.card_last4}\n"
        f"🆔 #{short}\n"
        f"👤 {buyer_nm}"
    )
    if buyer_tg:
        await tg(buyer_tg,
            f"✅ <b>Оплата получена!</b>\n"
            f"📦 {order['name']}\n"
            f"⚙️ Обрабатываем заказ..."
        )

    asyncio.create_task(fulfill(data.order_id, tg))
    return {"ok": True, "message": "Оплата подтверждена! Заказ обрабатывается."}


@app.post("/api/status")
async def api_status(req: Request):
    """Poll order status (from Mini App)"""
    d = await req.json()
    order = get_order(d.get("id", ""))
    return {
        "status": order["status"] if order else "not_found",
        "error":  order.get("error") if order else None,
    }


@app.post("/api/validate")
async def api_validate(data: ValidateIn):
    """Validate game player via Buypin"""
    result = await bp_validate(data.game_key, data.player_id, data.server_id or "")
    return result


@app.get("/api/wallet/{user_id}")
async def api_wallet(user_id: int):
    """Get user wallet balance"""
    w = get_wallet(user_id)
    return {
        "ok":      True,
        "balance": w.get("balance", 0),
        "txs":     w.get("txs", [])[:30],
    }


# ════════════════════════════════════════════════════════════
#  ADMIN ENDPOINTS (Header: x-secret: frozen2006)
# ════════════════════════════════════════════════════════════

@app.get("/admin/orders")
async def adm_orders(x_secret: str = Header(default="")):
    """All orders sorted by date"""
    _auth(x_secret)
    orders = sorted(all_orders(), key=lambda x: x.get("created_at", ""), reverse=True)
    return {"ok": True, "orders": orders, "total": len(orders)}


@app.post("/admin/done")
async def adm_done(data: AdminAction, x_secret: str = Header(default="")):
    """Mark order as delivered"""
    _auth(x_secret)
    order = get_order(data.id or "")
    if not order:
        raise HTTPException(404, "Not found")
    await set_status(data.id, "done")
    if order.get("buyer_tg_id"):
        await tg(order["buyer_tg_id"],
            f"🎉 <b>Ваш заказ выдан!</b>\n"
            f"📦 {order['name']}\n"
            f"🆔 #{sid(data.id)}\n"
            f"✨ Спасибо! FrozenShop ❄️\n"
            f"Вопросы: @frozenld1"
        )
    return {"ok": True}


@app.post("/admin/reject")
async def adm_reject(data: AdminAction, x_secret: str = Header(default="")):
    """Reject order"""
    _auth(x_secret)
    order = get_order(data.id or "")
    if not order:
        raise HTTPException(404, "Not found")
    await set_status(data.id, "rejected", error=data.reason or "Отклонён")
    if order.get("buyer_tg_id"):
        await tg(order["buyer_tg_id"], "❌ Заказ отклонён. Вопросы: @frozenld1")
    return {"ok": True}


@app.post("/admin/topup")
async def adm_topup(data: AdminAction, x_secret: str = Header(default="")):
    """Add FrozenCoins to user wallet"""
    _auth(x_secret)
    if not data.user_id or not data.amount:
        raise HTTPException(400, "user_id и amount обязательны")
    bal = await wallet_add(data.user_id, data.amount, data.desc or "Пополнение")
    await tg(data.user_id,
        f"🪙 Начислено <b>{fmt(data.amount)} FrozenCoins</b>!\n"
        f"Баланс: <b>{fmt(bal)} FC</b>"
    )
    return {"ok": True, "balance": bal}


@app.get("/admin/balance")
async def adm_balance(x_secret: str = Header(default="")):
    """Buypin wallet balance"""
    _auth(x_secret)
    try:
        bal = await bp_balance()
        return {"ok": True, "balance": bal, "currency": "USD"}
    except Exception as e:
        return {"ok": False, "error": str(e)}


@app.post("/admin/sync")
async def adm_sync(x_secret: str = Header(default="")):
    """Sync all Buypin product IDs"""
    _auth(x_secret)
    try:
        result = await sync_products()
        return {"ok": True, "synced": len(result)}
    except Exception as e:
        return {"ok": False, "error": str(e)}


@app.get("/admin/bp-products/{game}")
async def adm_bp_products(game: str, x_secret: str = Header(default="")):
    """List Buypin products for a game (to fill product map)"""
    _auth(x_secret)
    try:
        key = GAME_KEYS.get(game, game)
        prods = await bp_products(key)
        return {
            "ok":       True,
            "game":     game,
            "bp_key":   key,
            "count":    len(prods) if isinstance(prods, list) else 0,
            "products": prods,
        }
    except Exception as e:
        return {"ok": False, "error": str(e)}


# ── Website ────────────────────────────────────────────────────

@app.get("/shop", response_class=HTMLResponse)
async def shop_website():
    from web import render
    return render()
