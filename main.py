"""
FrozenShop — Main entry point
Runs Telegram bot + FastAPI server together
"""
import asyncio
import sys

import uvicorn
from aiogram import Bot

from config import BOT_TOKEN, BUYPIN_KEY, ADMIN_ID, PORT
from db import get_bp
from bot import bot, dp, send
from api import app, set_notify
from buypin import sync_products


async def on_startup():
    """Called once when everything starts"""
    from config import GAME_NAMES

    print("\n" + "═" * 50)
    print("  FrozenShop Backend — Starting up")
    print("═" * 50)
    print(f"  BOT_TOKEN  : {'✅ set' if BOT_TOKEN else '❌ NOT SET'}")
    print(f"  ADMIN_ID   : {ADMIN_ID}")
    print(f"  BUYPIN_KEY : {'✅ set' if BUYPIN_KEY else '❌ NOT SET — auto-fulfillment disabled'}")
    print(f"  PORT       : {8000}")
    print(f"  Games      : {', '.join(GAME_NAMES.keys())}")
    print("═" * 50 + "\n")

    if not BOT_TOKEN:
        print("❌ BOT_TOKEN не задан. Укажи в .env файле!")
        sys.exit(1)

    # Auto-sync Buypin products if key is set and map is empty
    if BUYPIN_KEY and not get_bp():
        print("⚡ Buypin products not synced — running auto-sync...")
        try:
            result = await sync_products()
            print(f"✅ Synced {len(result)} product entries\n")
        except Exception as e:
            print(f"⚠️  Auto-sync failed: {e}")
            print("   Run /syncproducts in bot to sync manually\n")

    # Connect bot to API for Telegram notifications
    set_notify(send)

    # Notify admin on startup
    try:
        await bot.send_message(
            ADMIN_ID,
            "🚀 <b>FrozenShop запущен!</b>\n\n"
            f"🔑 Buypin: {'✅ подключён' if BUYPIN_KEY else '❌ не задан'}\n"
            "📦 Готов принимать заказы\n\n"
            "/admin — список команд"
        )
    except Exception as e:
        print(f"⚠️  Could not notify admin: {e}")


async def on_shutdown():
    """Called on graceful shutdown"""
    print("\n⏹  Shutting down...")
    try:
        await bot.send_message(ADMIN_ID, "⏹ FrozenShop остановлен")
    except Exception:
        pass
    await bot.session.close()
    print("✅ Done")


async def run_bot():
    """Run aiogram polling"""
    await dp.start_polling(bot, skip_updates=True)


async def run_api():
    """Run FastAPI with uvicorn"""
    config = uvicorn.Config(
        app,
        host="0.0.0.0",
        port=PORT,
        log_level="warning",
        access_log=False,
    )
    server = uvicorn.Server(config)
    await server.serve()


async def main():
    await on_startup()
    try:
        # Run bot and API server concurrently
        await asyncio.gather(
            run_bot(),
            run_api(),
        )
    except (KeyboardInterrupt, SystemExit):
        pass
    finally:
        await on_shutdown()


if __name__ == "__main__":
    asyncio.run(main())
