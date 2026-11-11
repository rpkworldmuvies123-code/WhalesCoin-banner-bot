# WhalesCoin Market & Banner Telegram Bot

## Features
- One channel post every 3 hours: 8 posts/day. Rotates Market Update, Trading Analysis, Top Gainers and Top Trending twice per 8-post cycle.
- Gainers/Trending use the site's Share Top Coins -> Download Image flow with Playwright. UI changes/download failures skip the post; no fake banner is generated.
- Group commands: /price (Top 50), /btc, /eth, /market, /gainers, /trending.
- Bot replies and command messages are scheduled for deletion after 5 seconds. Bot must be group admin with Delete Messages permission to delete users' commands.
- Market feed: CoinPaprika public API. No Gemini/OpenAI key required.
- Shayari is selected from a built-in pool.

## Render deployment
Create a Background Worker from branch feature/auto-news-market-bot.
Build: pip install -r requirements.txt && playwright install chromium
Start: python bot.py
Set environment variables from .env.example. Add bot as channel admin with Post Messages permission and group admin with Delete Messages permission.

## Validation required
- Test the Playwright download on the live website before enabling production posts. Selectors are based on the visible button labels from the provided screenshots; website redesigns can break them.
- Chromium may exceed small instance memory. Use a Render instance with enough RAM if browser launch fails.
- Scheduler starts 30 seconds after worker startup, then every 3 hours. A worker restart resets the rotation; this is interval-based, not a fixed local-time schedule.
- Trading Analysis is a 24-hour market snapshot, not chart-indicator technical analysis.
- CoinPaprika may rate-limit. Failed data fetches are logged and posts are skipped, never fabricated.
