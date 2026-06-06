"""
Database layer — JSON files in data/ folder
Simple, no external dependencies, works on any host
"""
import json
import asyncio
from pathlib import Path
from datetime import datetime

DATA = Path("data")
DATA.mkdir(exist_ok=True)

_lock = asyncio.Lock()


def _read(name: str) -> dict:
    f = DATA / f"{name}.json"
    try:
        return json.loads(f.read_text(encoding="utf-8")) if f.exists() else {}
    except Exception:
        return {}


def _write(name: str, data: dict):
    (DATA / f"{name}.json").write_text(
        json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
    )


# ── Utils ─────────────────────────────────────────────────────
def now() -> str:
    return datetime.now().isoformat()

def sid(order_id: str) -> str:
    """Short order ID for display"""
    return (order_id or "")[:8].upper()

def fmt(n) -> str:
    """Format number: 17500 → '17 500'"""
    return f"{int(n):,}".replace(",", " ")


# ── Orders ────────────────────────────────────────────────────
def get_order(oid: str) -> dict | None:
    return _read("orders").get(oid)

def all_orders() -> list:
    return list(_read("orders").values())

async def save_order(order: dict):
    async with _lock:
        d = _read("orders")
        d[order["id"]] = order
        _write("orders", d)

async def set_status(oid: str, status: str, **kw) -> dict | None:
    async with _lock:
        d = _read("orders")
        if oid not in d:
            return None
        d[oid].update({"status": status, "updated_at": now(), **kw})
        _write("orders", d)
        return d[oid]


# ── Wallets ───────────────────────────────────────────────────
def get_wallet(uid) -> dict:
    return _read("wallets").get(str(uid), {"balance": 0, "txs": []})

async def wallet_add(uid, amount: float, desc: str) -> float:
    async with _lock:
        d = _read("wallets")
        k = str(uid)
        d.setdefault(k, {"balance": 0, "txs": []})
        d[k]["balance"] = round((d[k].get("balance") or 0) + amount, 2)
        d[k].setdefault("txs", []).insert(0, {
            "type": "in", "amount": amount, "desc": desc, "date": now()
        })
        d[k]["txs"] = d[k]["txs"][:500]
        _write("wallets", d)
        return d[k]["balance"]

async def wallet_sub(uid, amount: float, desc: str, oid: str = "") -> bool:
    async with _lock:
        d = _read("wallets")
        k = str(uid)
        if k not in d or (d[k].get("balance") or 0) < amount:
            return False
        d[k]["balance"] = round(d[k]["balance"] - amount, 2)
        d[k].setdefault("txs", []).insert(0, {
            "type": "out", "amount": amount,
            "desc": desc, "order_id": oid, "date": now()
        })
        d[k]["txs"] = d[k]["txs"][:500]
        _write("wallets", d)
        return True


# ── Anti-duplicate receipts ───────────────────────────────────
def receipt_seen(key: str) -> bool:
    r = _read("receipts")
    if key in r:
        return True
    r[key] = now()
    _write("receipts", r)
    return False


# ── Buypin product map ────────────────────────────────────────
def get_bp() -> dict:
    return _read("bp_products")

def save_bp(d: dict):
    _write("bp_products", d)
