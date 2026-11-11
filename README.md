# WhalesCoin Market & Banner Telegram Bot

## Implemented
- Group commands: /price (Top 50), /btc, /eth, /market, /analysis, /gainers, /trending.
- Replies and command messages are scheduled for deletion after 5 seconds. The bot must be group admin with Delete Messages permission.
- CoinPaprika public market data; no Gemini/OpenAI key required.
- Built-in Hindi shayari pool.
- Playwright code attempts the WhalesCoin website's own Share Top Coins -> Download Image flow for Gainers and Trending. It sends no fake/local placeholder image.
- Automated unit tests cover Top 50 sorting, coin lookup, gainers ranking, volume ranking, and Hindi shayari.

## Important blockers verified during testing
- Android/Termux cannot run Playwright Chromium. The `Unsupported platform: android` error is expected.
- GitHub-hosted Ubuntu runner reached the WhalesCoin page but received HTTP 403 and a Cloudflare "Just a moment..." page. The Share Top Coins control was therefore not accessible to automation. This means live website image downloading is NOT yet verified and scheduled image publishing must not be enabled on that runner.
- A Linux VPS/worker may work only if WhalesCoin allows requests from that server's IP. Test the website export flow before enabling scheduled posts. Do not assume Render will bypass the 403.

## Run the command bot
Install Python 3.11+, then:
```bash
pip install -r requirements.txt
export TELEGRAM_BOT_TOKEN="your_bot_token"
export TARGET_CHANNEL="@your_channel"
python bot.py
```
Optional: set `GROUP_ID` to restrict commands to one group. Keep the process running for commands to respond immediately. The bot's in-process channel scheduler is disabled by default to avoid duplicate posts.

## Optional scheduler
On a Linux host where the WhalesCoin Playwright export has been verified, set `ENABLE_SCHEDULER=true`. It starts 30 seconds after startup and posts every 3 hours. If image download fails, the scheduled post is skipped and logged. Do not enable this until the export test succeeds.

## Accuracy and operations
- Trading Analysis is a 24-hour market snapshot, not chart-indicator technical analysis or a trade signal. Top Trending is ranked by 24-hour traded volume from CoinPaprika; it is not a proprietary WhalesCoin trending score.
- CoinPaprika may rate-limit; failures are logged.
- Do not run two polling processes with the same Telegram bot token simultaneously.
- Channel posting requires bot admin permission; deleting group commands requires Delete Messages permission.
