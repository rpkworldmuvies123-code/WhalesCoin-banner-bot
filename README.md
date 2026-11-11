# WhalesCoin Market & Banner Telegram Bot

## Features
- Channel schedule: one post every 3 hours (8/day), rotating Market Update, Trading Analysis, Top Gainers and Top Trending.
- Top Gainers and Trending images are downloaded at posting time from the WhalesCoin website using its visible Share Top Coins -> Download Image flow. If the website flow fails, the bot skips that post and logs the error; it never substitutes a fake image.
- Group commands: /price (Top 50), /btc, /eth, /market, /analysis, /gainers, /trending.
- Group command and reply messages are scheduled for deletion after 5 seconds. The bot must be a group admin with Delete Messages permission to delete users' commands.
- Market data uses CoinPaprika's public API. No Gemini/OpenAI key is required.
- Shayari is selected from a built-in English pool.

## Important: where to run it
Playwright's bundled Chromium does not run on Android/Termux. The error `Unsupported platform: android` is expected there. Run the complete bot on a Linux VPS or a paid Render Background Worker.

## Render deployment
Create a Background Worker from branch `feature/auto-news-market-bot`.
- Build: `pip install -r requirements.txt && playwright install --with-deps chromium`
- Start: `python bot.py`
- Set `TELEGRAM_BOT_TOKEN`, `TARGET_CHANNEL`, and optionally `GROUP_ID`.
- Add the bot as a channel admin with Post Messages permission.
- Add the bot as a group admin with Delete Messages permission.

## Known limitations / honest status
- The Playwright routine follows the supplied UI labels Share Top Coins and Download Image. A live browser run is still required to confirm those exact controls and download behavior on the current WhalesCoin site. If the site changes its UI, the selector may need updating.
- Trading Analysis is a 24-hour market snapshot, not chart-indicator technical analysis or a trade signal.
- Scheduler starts 30 seconds after process startup, then every 3 hours. A process restart resets the rotation.
- CoinPaprika can rate-limit; failed data requests are logged and scheduled posts are skipped.
- Do not run two polling instances with the same Telegram bot token simultaneously; Telegram polling conflicts can occur.
