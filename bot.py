import os, json, base64, logging, asyncio, re
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo

import requests
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from PIL import Image

load_dotenv()
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
log = logging.getLogger("whalescoin-bot")

ROOT = Path(__file__).parent
ASSETS = ROOT / "assets"
OUT = ROOT / "generated"
OUT.mkdir(exist_ok=True)
LOGO = ASSETS / "whalescoin_logo.jpg"
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
TEXT_MODEL = os.getenv("GEMINI_TEXT_MODEL", "gemini-2.5-flash")
IMAGE_MODEL = os.getenv("GEMINI_IMAGE_MODEL", "gemini-3.1-flash-image")
IMAGE_SIZE = os.getenv("IMAGE_SIZE", "2K")
ADMIN_IDS = {int(x.strip()) for x in os.getenv("ADMIN_USER_IDS", "").split(",") if x.strip().isdigit()}
ADMIN_NAMES = {x.strip().lstrip("@").lower() for x in os.getenv("ADMIN_USERNAMES", "DesignerPlusDev").split(",") if x.strip()}
CHANNELS = [x.strip() for x in os.getenv("TARGET_CHANNELS", "@WhalesCoinTalks,@WhalesCoinGlobal").split(",") if x.strip()]
TZ = ZoneInfo("Asia/Dhaka")

# In-memory drafts are intentionally cleared on restart; publish only after an explicit /post.
drafts = []


def is_admin(update: Update) -> bool:
    user = update.effective_user
    if not user:
        return False
    return user.id in ADMIN_IDS or (user.username or "").lower() in ADMIN_NAMES

async def guard(update: Update) -> bool:
    if not is_admin(update):
        if update.effective_message:
            await update.effective_message.reply_text("Access denied. This bot is restricted to its configured administrators.")
        return False
    return True


def gemini_text(prompt: str) -> str:
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{TEXT_MODEL}:generateContent?key={GEMINI_API_KEY}"
    payload = {"contents": [{"parts": [{"text": prompt}]}], "generationConfig": {"temperature": 0.9, "responseMimeType": "application/json"}}
    r = requests.post(url, json=payload, timeout=120)
    r.raise_for_status()
    data = r.json()
    return data["candidates"][0]["content"]["parts"][0]["text"]


def make_content(count: int):
    prompt = f'''You are the creative director for WhalesCoin, a crypto/blockchain brand targeting an English-speaking Bangladesh audience. Create exactly {count} DISTINCT evergreen promotional banner concepts.
Return ONLY valid JSON: {{"banners":[{{"headline":"...","supporting_text":"...","caption":"...","hashtags":["..."] ,"visual_direction":"..."}}]}}.
Rules: English only; concise, polished global crypto-brand voice; themes may include blockchain community, digital ocean, education, technology, community participation, brand awareness. Do NOT invent exchange listings, partnerships, endorsements, token prices, returns, dates, events, product features, regulatory status, or other factual claims. No investment promises, guaranteed profit, or financial advice. Avoid repeating concepts. Each visual_direction must describe a clearly different composition and palette while retaining WhalesCoin identity (deep navy/black, electric blue/cyan, restrained silver/white).'''
    raw = gemini_text(prompt)
    # tolerate accidental markdown fences
    raw = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw.strip(), flags=re.I)
    obj = json.loads(raw)
    banners = obj.get("banners", [])
    if len(banners) < count:
        raise RuntimeError(f"Gemini returned {len(banners)} concepts; expected {count}. Try /generate again.")
    return banners[:count]


def generate_image(concept: dict, index: int) -> Path:
    logo_bytes = LOGO.read_bytes()
    prompt = f'''Create ONE premium, polished, original cryptocurrency brand marketing banner for WhalesCoin.
Canvas: exact 16:9 landscape, designed for Telegram channel publishing. Generate a 2K image.
Brand identity: use the supplied WhalesCoin logo image as the exact brand mark; preserve its icon and wordmark, do not redraw, distort, misspell, or invent a replacement logo. Integrate it cleanly and legibly.
Exact headline text to render: {concept['headline']}
Exact supporting text to render: {concept['supporting_text']}
Visual direction: {concept['visual_direction']}
Art direction: sophisticated agency-level art direction, cinematic 3D blockchain/ocean visual language where appropriate, strong typography hierarchy, high contrast, precise spacing, clean composition, premium lighting, no clutter, no fake exchange logos, no extra brand names, no fabricated statistics, no watermarks, no UI mockups. English text only. Make all text readable and spell it exactly. Avoid any investment/price/return claims.'''
    url = "https://generativelanguage.googleapis.com/v1beta/interactions"
    payload = {
        "model": IMAGE_MODEL,
        "input": [
            {"type": "text", "text": prompt},
            {"type": "image", "data": base64.b64encode(logo_bytes).decode("ascii"), "mime_type": "image/jpeg"},
        ],
        "response_format": {"type": "image", "aspect_ratio": "16:9", "image_size": IMAGE_SIZE},
    }
    r = requests.post(url, headers={"x-goog-api-key": GEMINI_API_KEY, "Content-Type": "application/json"}, json=payload, timeout=300)
    r.raise_for_status()
    data = r.json()
    image_data = None
    # Interactions responses contain output_image or image blocks in output/steps.
    if isinstance(data.get("output_image"), dict):
        image_data = data["output_image"].get("data")
    if not image_data:
        for step in data.get("steps", []):
            block = step.get("image") or step.get("output_image")
            if isinstance(block, dict) and block.get("data"):
                image_data = block["data"]
                break
            for part in step.get("content", []) if isinstance(step.get("content"), list) else []:
                if isinstance(part, dict) and part.get("type") == "image" and part.get("data"):
                    image_data = part["data"]
                    break
            if image_data:
                break
    if not image_data:
        raise RuntimeError("Gemini returned no image. Check API access/model availability and try again.")
    path = OUT / f"whalescoin_{datetime.now(TZ).strftime('%Y%m%d_%H%M%S')}_{index}.png"
    path.write_bytes(base64.b64decode(image_data))
    # Normalize to an exact 16:9 canvas; keep the generated art centered.
    with Image.open(path) as im:
        im = im.convert("RGB")
        target_ratio = 16 / 9
        w, h = im.size
        if w / h > target_ratio:
            nw = int(h * target_ratio); left = (w - nw) // 2
            im = im.crop((left, 0, left + nw, h))
        else:
            nh = int(w / target_ratio); top = (h - nh) // 2
            im = im.crop((0, top, w, top + nh))
        im = im.resize((1920, 1080), Image.Resampling.LANCZOS)
        im.save(path, "PNG", optimize=True)
    return path


def caption_for(item: dict) -> str:
    tags = " ".join("#" + re.sub(r"[^A-Za-z0-9_]", "", str(t)).lstrip("#") for t in item.get("hashtags", [])[:8])
    caption = f"{item.get('headline','WhalesCoin')}\n\n{item.get('caption','')}\n\n{tags}".strip()
    return caption[:1024]

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await guard(update): return
    await update.message.reply_text("WhalesCoin Banner Studio is ready.\n\n/generate [2|3] — create banners\n/preview — resend current previews\n/post — publish approved drafts to both channels\n/cancel — discard drafts\n/status — configuration status\n/help — command list\n\nPublishing is never automatic; use /post when you approve the previews.")

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await start(update, context)

async def generate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global drafts
    if not await guard(update): return
    if not GEMINI_API_KEY:
        await update.message.reply_text("GEMINI_API_KEY is missing. Add it to the .env file and restart the bot."); return
    count = 3
    if context.args:
        try: count = int(context.args[0])
        except ValueError: count = 0
    if count not in (2, 3):
        await update.message.reply_text("Usage: /generate or /generate 2 or /generate 3"); return
    await update.message.reply_text(f"Creating {count} WhalesCoin banner concepts and images. This may take a few minutes…")
    try:
        concepts = await asyncio.to_thread(make_content, count)
        new_drafts = []
        for i, concept in enumerate(concepts, 1):
            await update.message.reply_text(f"Generating banner {i}/{count}…")
            path = await asyncio.to_thread(generate_image, concept, i)
            new_drafts.append({"path": str(path), "caption": caption_for(concept)})
        drafts = new_drafts
        await update.message.reply_text(f"Done. {len(drafts)} banner(s) are ready. Review them below; nothing has been published.")
        for i, item in enumerate(drafts, 1):
            with open(item["path"], "rb") as photo:
                await update.message.reply_photo(photo=photo, caption=f"PREVIEW {i}/{len(drafts)}\n\n{item['caption']}")
        await update.message.reply_text("If approved, send /post. To discard these drafts, send /cancel.")
    except Exception as e:
        log.exception("Generation failed")
        await update.message.reply_text(f"Generation failed: {str(e)[:700]}\nCheck API key, billing/quota, and model access. No channel post was made.")

async def preview(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await guard(update): return
    if not drafts:
        await update.message.reply_text("No drafts available. Use /generate first."); return
    for i, item in enumerate(drafts, 1):
        with open(item["path"], "rb") as photo:
            await update.message.reply_photo(photo=photo, caption=f"PREVIEW {i}/{len(drafts)}\n\n{item['caption']}")

async def post(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await guard(update): return
    if not drafts:
        await update.message.reply_text("No drafts to publish. Use /generate first."); return
    if not CHANNELS:
        await update.message.reply_text("No target channels configured in TARGET_CHANNELS."); return
    await update.message.reply_text("Publishing approved banners to configured channels…")
    successes, failures = [], []
    for channel in CHANNELS:
        for i, item in enumerate(drafts, 1):
            try:
                with open(item["path"], "rb") as photo:
                    await context.bot.send_photo(chat_id=channel, photo=photo, caption=item["caption"])
                successes.append(f"{channel}: banner {i}")
            except Exception as e:
                log.exception("Post failed for %s", channel)
                failures.append(f"{channel}, banner {i}: {str(e)[:180]}")
    msg = "Publish finished.\n\nSuccessful:\n" + ("\n".join(successes) if successes else "None")
    if failures: msg += "\n\nFailed:\n" + "\n".join(failures)
    await update.message.reply_text(msg[:4000])
    if not failures:
        drafts.clear()

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await guard(update): return
    drafts.clear()
    await update.message.reply_text("All pending drafts have been discarded. Nothing was published.")

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await guard(update): return
    await update.message.reply_text(
        "WhalesCoin Banner Studio\n"
        f"Text model: {TEXT_MODEL}\nImage model: {IMAGE_MODEL}\nImage size: {IMAGE_SIZE}\n"
        f"Audience language: English | Target timezone: Asia/Dhaka\n"
        f"Pending drafts: {len(drafts)}\nTargets: {', '.join(CHANNELS)}\n"
        "Publishing mode: manual approval only"
    )

async def post_init(app: Application):
    await app.bot.set_my_commands([
        ("start", "Open WhalesCoin Banner Studio"),
        ("generate", "Generate 2 or 3 banner previews"),
        ("preview", "Show pending banner previews"),
        ("post", "Publish approved banners to channels"),
        ("cancel", "Discard pending banners"),
        ("status", "Show bot configuration"),
        ("help", "Show commands"),
    ])

def main():
    if not TELEGRAM_BOT_TOKEN:
        raise SystemExit("TELEGRAM_BOT_TOKEN is missing. Copy .env.example to .env and configure it.")
    if not LOGO.exists():
        raise SystemExit("Brand logo missing: assets/whalescoin_logo.jpg")
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).post_init(post_init).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("generate", generate))
    app.add_handler(CommandHandler("preview", preview))
    app.add_handler(CommandHandler("post", post))
    app.add_handler(CommandHandler("cancel", cancel))
    app.add_handler(CommandHandler("status", status))
    log.info("WhalesCoin Banner Studio starting")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
