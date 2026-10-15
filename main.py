"""Entry point: starts the admin panel (port 8080 by default) and the Telegram bot in one process."""
import asyncio
import logging
import os

import aiohttp
from aiohttp import web

from bot import BotManager
from db import DB
from web import build_app


async def main():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    default_db = "/data/bot.db" if os.path.isdir("/data") else os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "bot.db")
    db = DB(os.getenv("DB_PATH") or default_db)
    session = aiohttp.ClientSession(
        connector=aiohttp.TCPConnector(limit=300, ttl_dns_cache=300, keepalive_timeout=60),
        cookie_jar=aiohttp.DummyCookieJar())
    bm = BotManager(db, session)
    app = build_app(db, bm, session)
    runner = web.AppRunner(app, access_log=None)
    await runner.setup()
    port = int(os.getenv("PORT", "8080"))
    await web.TCPSite(runner, "0.0.0.0", port).start()
    logging.info("admin panel listening on port %s", port)
    if db.get("token") and db.get("bot_enabled"):
        await bm.start()
    bm.start_background()
    try:
        await asyncio.Event().wait()
    finally:
        await bm.stop()
        await session.close()


if __name__ == "__main__":
    try:
        import uvloop  # optional speed-up
        uvloop.install()
    except ImportError:
        pass
    asyncio.run(main())
