import asyncio
from datetime import datetime, timezone
import os

from telegram.ext import Application
import bot

KINDS = ["market", "analysis", "gainers", "trending"]

async def main():
    token = (os.getenv("TELEGRAM_BOT_TOKEN") or "").strip()
    if not token:
        raise SystemExit("Missing TELEGRAM_BOT_TOKEN repository secret")
    if not bot.CHANNEL:
        raise SystemExit("Missing TARGET_CHANNEL repository secret")
    # GitHub schedule runs at 00, 03, 06, ... UTC. This yields the same
    # four-category rotation twice per day, i.e. eight posts per day.
    slot = datetime.now(timezone.utc).hour // 3
    kind = KINDS[slot % len(KINDS)]
    app = Application.builder().token(token).build()
    await app.initialize()
    try:
        await bot.publish(app, kind)
        print(f"Published scheduled category: {kind}")
    finally:
        await app.shutdown()

if __name__ == "__main__":
    asyncio.run(main())
