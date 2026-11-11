# WhalesCoin Market & Banner Telegram Bot

## Features
- GitHub Actions publishes one channel post every 3 hours (8/day): Market Update, Trading Analysis, Top Gainers and Top Trending, each twice daily.
- Gainers/Trending images are downloaded at posting time from WhalesCoin's own Share Top Coins -> Download Image UI using Playwright. If the website export fails, the workflow fails visibly; no fake image is sent.
- Group commands: /price (Top 50), /btc, /eth, /market, /analysis, /gainers, /trending.
- Group command and reply messages are scheduled for deletion after 5 seconds. Bot must be group admin with Delete Messages permission.
- CoinPaprika public API; no Gemini/OpenAI key required.
- Built-in English shayari pool.

## Free scheduled posting with GitHub Actions
After merging this branch into `main`:
1. Open repository Settings -> Secrets and variables -> Actions -> New repository secret.
2. Add `TELEGRAM_BOT_TOKEN` with your BotFather token.
3. Add `TARGET_CHANNEL` with the channel username (for example `@yourchannel`) or numeric channel ID.
4. Add the bot as channel admin with Post Messages permission.
5. Open Actions -> WhalesCoin scheduled channel posts -> Run workflow to test one post manually. Automatic schedule is every 3 hours.

GitHub scheduled jobs can start late under GitHub load; this is not a guaranteed exact-to-the-minute scheduler. Workflow sends exactly one post per successful run. Check Actions logs if a post is skipped or fails.

## Group commands
Run `python bot.py` on a machine that stays online and add `TELEGRAM_BOT_TOKEN`, `TARGET_CHANNEL`, and optionally `GROUP_ID` to its environment. By default, in-process scheduled posting is disabled so it will not duplicate GitHub Actions posts. The bot must be a group admin with Delete Messages permission if it should delete users' commands. Keep this process running for commands to respond immediately.

## Android / Termux limitation
Playwright's bundled Chromium does not run on Android/Termux. The error `Unsupported platform: android` is expected. GitHub Actions runs Chromium on Linux for scheduled posts. Termux can still run the command bot without browser automation, but it cannot download the site's image itself.

## Optional Render Background Worker
If using a paid always-on Render worker instead of GitHub scheduled posting, set `ENABLE_SCHEDULER=true` in its environment and disable the GitHub scheduled workflow to avoid duplicate posts. Build command: `pip install -r requirements.txt && playwright install --with-deps chromium`; start command: `python bot.py`.

## Accuracy and operational notes
- Trading Analysis is a 24-hour market snapshot, not chart-indicator technical analysis or a trade signal.
- CoinPaprika can rate-limit; failures are logged and no fabricated market data is posted.
- Do not run two polling bot processes with the same token simultaneously; Telegram polling conflicts can occur.
