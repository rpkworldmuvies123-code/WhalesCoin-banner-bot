# WhalesCoin Banner Studio (Telegram Bot)

A command-driven Telegram bot that uses Gemini to plan and generate 2–3 distinct WhalesCoin banners in English for a Bangladesh-facing audience. It sends previews to the administrator first. It **never publishes unless `/post` is explicitly issued**.

## Commands

- `/generate` — generate 3 banners (default)
- `/generate 2` or `/generate 3` — choose count
- `/preview` — resend pending previews
- `/post` — publish pending banners to `@WhalesCoinTalks` and `@WhalesCoinGlobal`
- `/cancel` — discard pending drafts
- `/status` — show model, targets, and draft count
- `/help` — show commands

## 1. Create credentials

1. In Telegram, open `@BotFather`, create a bot with `/newbot`, and copy its token.
2. Open Google AI Studio and create a Gemini API key. The configured image model is `gemini-3.1-flash-image`; availability, quota, and billing depend on your Google account/project.
3. Add the bot to both channels and promote it to administrator with permission to **Post Messages**.
4. The configured admin username is `DesignerPlusDev`. For stronger access control, add your numeric Telegram user ID to `ADMIN_USER_IDS` in `.env`. Do not share API keys or bot tokens in chat.

## 2. Run locally

Python 3.11+ recommended.

```bash
python -m venv .venv
# Windows: .venv\\Scripts\\activate
# Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env and fill in TELEGRAM_BOT_TOKEN and GEMINI_API_KEY
python bot.py
```

On Android, this can be run in Termux, but a VPS/worker is more reliable for long image-generation requests.

## 3. Deploy as a worker

Use a persistent Python worker (VPS, Render Background Worker, or equivalent). Set the environment variables from `.env.example` in the hosting dashboard and use:

- Build command: `pip install -r requirements.txt`
- Start command: `python bot.py`

Do not run two copies with the same Telegram bot token at the same time; polling conflicts can occur. A Bangladesh server region is optional—the bot's content is English and its displayed timezone is Asia/Dhaka.

## Important behavior and limitations

- `/generate` makes separate image-generation requests, so generation takes time and consumes Gemini API quota/credits according to current Google pricing and access.
- Gemini may occasionally fail to return an image or may render text imperfectly. Review every preview before `/post`.
- The bot requests a 16:9 2K image and normalizes it to 1920×1080 PNG.
- The supplied WhalesCoin logo is passed as a reference image. AI image models may still imperfectly reproduce small logo details; inspect previews.
- Drafts are held in memory and are cleared if the process restarts. Generate again if that happens.
- Content instructions prohibit invented exchange listings, partnerships, endorsements, token prices, returns, dates, events, and unsupported product claims.
- Telegram posting succeeds only if the bot is an administrator in each destination channel with posting permission.
