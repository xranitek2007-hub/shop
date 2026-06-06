"""
Buypin API — complete integration
Auto-fulfillment with MLBB combo support
"""
import asyncio
import re
import aiohttp

from config import BUYPIN_KEY, BUYPIN_URL, GAME_KEYS, MLBB_COMBOS, MANUAL_GAMES, ADMIN_ID
from db import get_order, set_status, get_bp, save_bp, sid


class BuypinError(Exception):
    pass


# ── Core request ──────────────────────────────────────────────
async def _req(path: str, method: str = "GET", body: dict = None):
    if not BUYPIN_KEY:
        raise BuypinError("BUYPIN_KEY не задан в .env !")
    headers = {
        "Accept":       "application/json",
        "Content-Type": "application/json",
        "X-API-Key":    BUYPIN_KEY,
    }
    async with aiohttp.ClientSession() as s:
        async with s.request(
            method, BUYPIN_URL + path,
            headers=headers, json=body,
            timeout=aiohttp.ClientTimeout(total=30)
        ) as r:
            data = await r.json()
            if not data.get("success"):
                raise BuypinError(
                    data.get("message") or data.get("error") or f"HTTP {r.status}"
                )
            return data["data"]


# ── API methods ───────────────────────────────────────────────
async def bp_balance() -> float:
    """Get Buypin wallet balance in USD"""
    d = await _req("/me")
    return d.get("wallet", {}).get("balance", 0)

async def bp_games() -> list:
    return await _req("/games")

async def bp_products(game_key: str) -> list:
    try:
        return await _req(f"/games/{game_key}/products")
    except BuypinError:
        return []

async def bp_validate(game_key: str, player_id: str, server_id: str = "") -> dict:
    """Validate player exists. Returns {"ok": bool, "username": str}"""
    try:
        body = {"player_id": str(player_id)}
        if server_id:
            body["server_id"] = str(server_id)
        d = await _req(f"/games/{game_key}/validate-player", "POST", body)
        return {"ok": True, "username": d.get("username") or d.get("name") or ""}
    except BuypinError as e:
        return {"ok": False, "error": str(e)}

async def bp_create_order(game_key: str, product_id: str,
                          user_id: str, server_id: str = "") -> str:
    """Create Buypin order. Returns bp_order_id."""
    body = {"product_id": str(product_id), "user_id": str(user_id)}
    if server_id:
        body["server_id"] = str(server_id)
    d = await _req(f"/games/{game_key}/order", "POST", body)
    return d.get("order_id") or d.get("id") or ""

async def bp_order_status(game_key: str, bp_oid: str) -> str:
    """Check Buypin order status"""
    d = await _req(f"/games/{game_key}/order/status", "POST", {"order_id": bp_oid})
    return (d.get("status") or "").lower()


# ── Product sync ──────────────────────────────────────────────
async def sync_products() -> dict:
    """
    Sync all Buypin product IDs to data/bp_products.json
    Call once after deploy, then when products change
    """
    result = {}
    for gid, bp_key in GAME_KEYS.items():
        try:
            products = await bp_products(bp_key)
            if isinstance(products, list):
                for p in products:
                    pid = p.get("id") or p.get("sku") or ""
                    amt = p.get("amount") or p.get("qty") or 0
                    if pid:
                        result[f"{gid}_pid_{pid}"] = pid
                    if amt:
                        result[f"{gid}_amt_{int(amt)}"] = pid
                print(f"  ✅ {bp_key}: {len(products)} products")
        except Exception as e:
            print(f"  ❌ {bp_key}: {e}")

    save_bp(result)
    print(f"Saved {len(result)} entries to data/bp_products.json")
    return result


def _find_product(gid: str, amount: int = None, pid: str = None) -> str | None:
    """Find Buypin product_id by amount or pid"""
    bp = get_bp()
    if amount is not None:
        v = bp.get(f"{gid}_amt_{amount}")
        if v:
            return v
    if pid:
        v = bp.get(f"{gid}_pid_{pid}")
        if v:
            return v
    return None


def _parse_diamonds(name: str) -> int | None:
    """Extract diamond count from product name: '86 💎' → 86"""
    m = re.match(r"^(\d+)", str(name or ""))
    return int(m.group(1)) if m else None


# ── Auto-fulfillment ──────────────────────────────────────────
async def fulfill(order_id: str, notify=None):
    """
    Auto-fulfill order via Buypin API.
    notify: async func(chat_id, text) for Telegram messages
    """
    order = get_order(order_id)
    if not order:
        return

    gid    = order.get("gid", "")
    bpgame = GAME_KEYS.get(gid)
    bp_uid = order.get("bp_uid")
    short  = sid(order_id)

    async def msg(cid, text):
        if notify:
            await notify(cid, text)

    # ── Manual games (roblox, brawl etc.) ─────────────────────
    if gid in MANUAL_GAMES or not bpgame or not bp_uid:
        reason = (
            "ручная выдача" if gid in MANUAL_GAMES
            else "нет игрового ID"
        )
        # For robux_fast — direct link to seller
        extra = ""
        if gid == "roblox":
            prod = order.get("pid", "")
            # Check if fast category
            from config import PRODUCTS
            p = next((x for x in PRODUCTS.get("roblox", []) if x["id"] == prod), None)
            if p and p.get("cat") == "robux_fast":
                extra = "\n⚡ Моментальные — напиши покупателю немедленно!"

        await msg(ADMIN_ID,
            f"🔶 <b>Нужна ручная выдача!</b>\n"
            f"📦 {order.get('name')}\n"
            f"🆔 #{short}\n"
            f"Причина: {reason}{extra}\n\n"
            f"/done_{short.lower()}"
        )
        return

    # ── Build Buypin product list ──────────────────────────────
    bp_pids = []

    if gid == "mlbb":
        diamonds = order.get("diamonds") or _parse_diamonds(order.get("name", ""))
        combo = MLBB_COMBOS.get(diamonds) if diamonds else None

        if not combo:
            await msg(ADMIN_ID,
                f"⚠️ Нет комбо для {diamonds} алмазов\n"
                f"#{short}\n/done_{short.lower()}")
            return

        for amt in combo:
            pid = _find_product(gid, amount=amt)
            if not pid:
                await msg(ADMIN_ID,
                    f"⚠️ mlbb_{amt} не найден в Buypin!\n"
                    f"Отправь /syncproducts\n"
                    f"/done_{short.lower()}")
                await set_status(order_id, "failed", error=f"mlbb_{amt} not mapped")
                return
            bp_pids.append(pid)
    else:
        pid = _find_product(gid, pid=order.get("pid"))
        if not pid:
            await msg(ADMIN_ID,
                f"⚠️ {gid}/{order.get('pid')} не найден в Buypin!\n"
                f"Отправь /syncproducts")
            return
        bp_pids = [pid]

    # ── Create orders in Buypin ────────────────────────────────
    await set_status(order_id, "processing", bp_order_ids=[])
    bp_oids = []

    try:
        for bp_pid in bp_pids:
            bp_oid = await bp_create_order(
                bpgame, bp_pid, str(bp_uid),
                order.get("bp_server", "")
            )
            bp_oids.append(bp_oid)
            await set_status(order_id, "processing", bp_order_ids=bp_oids)
            print(f"✅ Buypin order: {bp_oid}")

        if order.get("buyer_tg_id"):
            await msg(order["buyer_tg_id"],
                f"⚙️ <b>Заказ обрабатывается!</b>\n"
                f"📦 {order.get('name')}\n"
                f"🆔 #{short}\n⏳ 1–5 минут")

        asyncio.create_task(
            _watch_orders(order_id, bpgame, bp_oids, notify)
        )

    except BuypinError as e:
        await set_status(order_id, "failed", error=str(e))
        await msg(ADMIN_ID,
            f"❌ <b>Buypin ошибка!</b>\n"
            f"📦 {order.get('name')}\n🆔 #{short}\n"
            f"{e}\n\n/done_{short.lower()}")
        if order.get("buyer_tg_id"):
            await msg(order["buyer_tg_id"],
                "⚠️ Небольшая задержка. Разбираемся. @frozenld1")


async def _watch_orders(order_id: str, game_key: str,
                        bp_oids: list, notify=None):
    """Watch Buypin order status. Max 6 minutes."""
    total = len(bp_oids)
    done  = set()
    short = sid(order_id)

    async def msg(cid, text):
        if notify:
            await notify(cid, text)

    for attempt in range(24):  # 24 × 15s = 6 min
        await asyncio.sleep(15)

        for bp_oid in bp_oids:
            if bp_oid in done:
                continue
            try:
                st = await bp_order_status(game_key, bp_oid)
                if st in ("delivered", "success", "completed"):
                    done.add(bp_oid)
                elif st in ("failed", "error", "cancelled"):
                    done.add(bp_oid)
                    await set_status(order_id, "failed", error=st)
                    await msg(ADMIN_ID,
                        f"❌ Buypin failed!\n#{short}\n/done_{short.lower()}")
                    return
            except Exception as e:
                print(f"watch {short}: {e}")

        if len(done) >= total:
            await set_status(order_id, "done")
            order = get_order(order_id)
            if order and order.get("buyer_tg_id"):
                await msg(order["buyer_tg_id"],
                    f"🎉 <b>Ваш заказ выдан!</b>\n\n"
                    f"📦 {order.get('name')}\n"
                    f"🆔 #{short}\n\n"
                    f"✨ Спасибо! FrozenShop ❄️\n"
                    f"Вопросы: @frozenld1")
            await msg(ADMIN_ID,
                f"✅ Авто-выдан: {order.get('name')} #{short}")
            return

    # Timeout
    order = get_order(order_id)
    if order and order.get("status") == "processing":
        await set_status(order_id, "timeout")
        await msg(ADMIN_ID,
            f"⏰ Таймаут #{short} — проверь в buypin.net")
