import os, random, asyncio, logging
from zoneinfo import ZoneInfo
import requests
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

load_dotenv()
logging.basicConfig(level=os.getenv("LOG_LEVEL","INFO"),format="%(asctime)s %(levelname)s %(name)s: %(message)s")
log=logging.getLogger("whalescoin-auto")
TZ=ZoneInfo(os.getenv("TIMEZONE","Asia/Kolkata"))
TOKEN=(os.getenv("BOT_TOKEN") or os.getenv("TELEGRAM_BOT_TOKEN","")).strip()
CHANNEL=(os.getenv("CHANNEL_ID") or os.getenv("TARGET_CHANNEL","")).strip()
GROUP_ID=os.getenv("GROUP_ID","").strip() or None
GAINERS_URL=os.getenv("GAINERS_URL","https://whalescoin.io/market-highlights/gainers")
TRENDING_URL=os.getenv("TRENDING_URL","https://whalescoin.io/market-highlights/trending")
DELETE_SECONDS=int(os.getenv("DELETE_SECONDS","5"))
POST_INTERVAL_HOURS=int(os.getenv("POST_INTERVAL_HOURS","3"))
HTTP=requests.Session()
HTTP.headers.update({"User-Agent":"WhalesCoinTelegramBot/1.0"})
SHAYARI=[
"Markets may rise and markets may fall; patience and research matter most of all.",
"Read the trend, manage the risk, and never let excitement make the decision.",
"Green candles bring hope, red candles test your plan; discipline matters more than a lucky span.",
"Every coin has a story to show; check the facts before you go.",
"Do not chase every shining name; protect your capital, stay in the game.",
"Prices move fast, but wisdom takes time; make each decision with reason in mind.",
"Let data guide your way, not fear or greed that fades away.",
"Big moves attract the crowd; a clear plan speaks louder than the noise."
]
CATEGORIES=["market","analysis","gainers","trending"]

def shayari(): return random.choice(SHAYARI)
def api_get(path,params=None,timeout=35):
    r=HTTP.get("https://api.coinpaprika.com/v1"+path,params=params,timeout=timeout); r.raise_for_status(); return r.json()
def get_tickers():
    data=api_get("/tickers",{"quotes":"USD"})
    rows=[]
    for x in data:
        q=(x.get("quotes") or {}).get("USD") or {}
        if not x.get("rank") or not q.get("price"): continue
        rows.append({"rank":x["rank"],"name":x.get("name","?"),"symbol":x.get("symbol","?"),"price":q.get("price"),
          "change":q.get("percent_change_24h"),"market_cap":q.get("market_cap"),"volume":q.get("volume_24h")})
    return sorted(rows,key=lambda x:x["rank"])[:50]
def money(v):
    if v is None:return "N/A"
    if abs(v)>=1:return f"${v:,.2f}"
    if abs(v)>=.01:return f"${v:.4f}"
    return f"${v:.8f}"
def compact(v):
    if v is None:return "N/A"
    for n,s in ((1e12,"T"),(1e9,"B"),(1e6,"M"),(1e3,"K")):
        if abs(v)>=n:return f"${v/n:.2f}{s}"
    return f"${v:,.0f}"
def price_text(rows):
    lines=["🐋 WHALESCOIN · TOP 50 CRYPTOCURRENCIES · USD","Rank  Coin       Price           24h"]
    for x in rows:
        ch=x["change"]; pct="N/A" if ch is None else f"{ch:+.2f}%"
        lines.append(f'{x["rank"]:>2}. {x["symbol"][:8]:<8} {money(x["price"]):>13} {pct:>9}')
    lines.append("\n"+shayari()+"\nNot financial advice.")
    return "\n".join(lines)
def coin_detail(symbol,rows):
    x=next((z for z in rows if z["symbol"].lower()==symbol.lower()),None)
    if not x:return None
    ch=x["change"]; pct="N/A" if ch is None else f"{ch:+.2f}%"
    return (f'{x["name"]} ({x["symbol"]})\nRank: #{x["rank"]}\nPrice: {money(x["price"])}\n24h change: {pct}\n'
      f'Market cap: {compact(x["market_cap"])}\n24h volume: {compact(x["volume"])}\nNot financial advice.')
async def get_rows(): return await asyncio.to_thread(get_tickers)
async def delete_later(bot,chat_id,message_id):
    await asyncio.sleep(DELETE_SECONDS)
    try: await bot.delete_message(chat_id=chat_id,message_id=message_id)
    except Exception as e: log.info("Deletion failed (check bot admin permissions): %s",e)
async def temp_reply(update,context,text):
    msg=update.effective_message
    sent=await msg.reply_text(text)
    context.application.create_task(delete_later(context.bot,sent.chat_id,sent.message_id))
    context.application.create_task(delete_later(context.bot,msg.chat_id,msg.message_id))
def in_group(update):
    m=update.effective_message
    return bool(m and m.chat.type in ("group","supergroup") and (not GROUP_ID or str(m.chat_id)==GROUP_ID))
async def price_cmd(u,c):
    if not in_group(u):return
    try:
        body=price_text(await get_rows())
        for chunk in [body[i:i+3500] for i in range(0,len(body),3500)]:
            await temp_reply(u,c,chunk)
    except Exception:
        log.exception("Top 50 failed"); await temp_reply(u,c,"Market data temporarily unavailable. Please try again.")
async def coin_cmd(u,c,symbol):
    if not in_group(u):return
    try:
        detail=coin_detail(symbol,await get_rows()) or f"{symbol} is not in the current Top 50 feed."
        await temp_reply(u,c,detail+"\n\n"+shayari())
    except Exception:
        log.exception("Coin lookup failed"); await temp_reply(u,c,"Coin data temporarily unavailable.")
async def btc_cmd(u,c): await coin_cmd(u,c,"BTC")
async def eth_cmd(u,c): await coin_cmd(u,c,"ETH")
async def analysis_cmd(u,c):
    if not in_group(u):return
    try: await temp_reply(u,c,await commentary("analysis"))
    except Exception:
        log.exception("Analysis command failed"); await temp_reply(u,c,"Trading analysis data temporarily unavailable.")
async def market_cmd(u,c):
    if not in_group(u):return
    try:
        g=await asyncio.to_thread(api_get,"/global")
        text=(f"🐋 WHALESCOIN · CRYPTO MARKET OVERVIEW\nMarket cap: {compact(g.get('market_cap_usd'))}\n"
          f"24h volume: {compact(g.get('volume_24h_usd'))}\nBTC dominance: {g.get('bitcoin_dominance_percentage','N/A')}%\n"
          f"Active cryptocurrencies: {g.get('cryptocurrencies_number','N/A')}\n\n{shayari()}\n"
          "Snapshot · Not financial advice.")
        await temp_reply(u,c,text)
    except Exception:
        log.exception("Global market failed"); await temp_reply(u,c,"Global market data temporarily unavailable.")
def highlight_text(kind, rows):
    valid=[x for x in rows if x["change"] is not None]
    if kind=="gainers":
        chosen=sorted(valid,key=lambda x:x["change"],reverse=True)[:10]
        heading="🐋 WHALESCOIN · TOP GAINERS · 24H"
    else:
        chosen=sorted(rows,key=lambda x:(x["volume"] or 0),reverse=True)[:10]
        heading="🐋 WHALESCOIN · TOP TRENDING"
    lines=[heading]
    for i,x in enumerate(chosen,1):
        change="N/A" if x["change"] is None else f'{x["change"]:+.2f}%'
        lines.append(f'{i}. {x["name"]} ({x["symbol"]}) · {money(x["price"])} · 24h {change}')
    lines.extend(["",shayari(),"Not financial advice."])
    return "\n".join(lines)
async def commentary(kind):
    rows=await get_rows()
    movers=sorted([x for x in rows if x["change"] is not None],key=lambda x:x["change"],reverse=True)
    up=sum(x["change"]>0 for x in rows if x["change"] is not None)
    down=sum(x["change"]<0 for x in rows if x["change"] is not None)
    if kind=="market":
        body=(f"🐋 WHALESCOIN · MARKET UPDATE\nTop 50 snapshot: {up} assets positive, {down} negative over 24h.\n"
          f"Strongest mover: {movers[0]['name']} ({movers[0]['change']:+.2f}%).\n"
          f"Weakest mover: {movers[-1]['name']} ({movers[-1]['change']:+.2f}%).")
    else:
        body=(f"🐋 WHALESCOIN · TRADING ANALYSIS\nTop 50: {up} assets positive and {down} negative over 24h.\n"
          f"Top positive mover: {movers[0]['name']} ({movers[0]['change']:+.2f}%).\n"
          f"Top negative mover: {movers[-1]['name']} ({movers[-1]['change']:+.2f}%).\n"
          "24-hour market snapshot only; not chart-based technical analysis or a trade signal.")
    return body+"\n\n"+shayari()+"\n\nData snapshot · Not financial advice."
async def publish(app,kind):
    if kind in ("gainers","trending"):
        body=highlight_text(kind,await get_rows())
        image_name = "gainers.jpg" if kind == "gainers" else "trending.jpg"
        image_path = os.path.join(os.path.dirname(__file__), image_name)
        if os.path.isfile(image_path):
            with open(image_path, "rb") as photo:
                await app.bot.send_photo(chat_id=CHANNEL, photo=photo,
                    caption=("🐋 WHALESCOIN · " + ("TOP GAINERS" if kind == "gainers" else "TRENDING TOP 5")
                             + "\\n\\n" + shayari() + "\\n\\nTemporary test image · Not live refreshed."),
                    )
            log.info("Published %s image from %s", kind, image_name)
        else:
            await app.bot.send_message(chat_id=CHANNEL,
                text=body[:4000] + "\\n\\nImage file missing: " + image_name,
                disable_web_page_preview=True)
    else:
        await app.bot.send_message(chat_id=CHANNEL,text=(await commentary(kind))[:4000],disable_web_page_preview=True)
async def scheduled(context):
    index=context.job.data["index"]
    kind=CATEGORIES[index%4]
    try:
        await publish(context.application,kind)
        log.info("Published scheduled category %s",kind)
    except Exception: log.exception("Scheduled %s failed; skipped safely",kind)
    context.job.data["index"]=(index+1)%8
async def group_banner(u,c,kind):
    if not in_group(u):return
    try:
        body=highlight_text(kind,await get_rows())
        image_name = "gainers.jpg" if kind == "gainers" else "trending.jpg"
        image_path = os.path.join(os.path.dirname(__file__), image_name)
        if os.path.isfile(image_path):
            msg = await u.effective_message.reply_photo(photo=open(image_path, "rb"),
                caption="🐋 WHALESCOIN · " + ("TOP GAINERS" if kind == "gainers" else "TRENDING TOP 5") + "\\n" + shayari())
            c.application.create_task(delete_later(c.bot, msg.chat_id, msg.message_id))
            c.application.create_task(delete_later(c.bot, u.effective_message.chat_id, u.effective_message.message_id))
        else:
            await temp_reply(u,c,body + "\\n\\nImage file missing: " + image_name)
    except Exception:
        log.exception("%s highlights failed",kind)
        await temp_reply(u,c,"Market highlights are temporarily unavailable.")
async def gainers_cmd(u,c): await group_banner(u,c,"gainers")
async def trending_cmd(u,c): await group_banner(u,c,"trending")
async def start_cmd(u,c):
    if in_group(u): await temp_reply(u,c,"WhalesCoin Market Bot ready.\n/price /btc /eth /market /gainers /trending")
async def post_init(app):
    app.job_queue.run_repeating(scheduled,interval=POST_INTERVAL_HOURS*3600,first=30,
      data={"index":0},name="whalescoin-3-hour-cycle")
def main():
    if not TOKEN:raise SystemExit("Missing TELEGRAM_BOT_TOKEN")
    if not CHANNEL:raise SystemExit("Missing TARGET_CHANNEL")
    app=Application.builder().token(TOKEN).post_init(post_init).build()
    for name,fn in [("start",start_cmd),("price",price_cmd),("btc",btc_cmd),("eth",eth_cmd),("market",market_cmd),
      ("analysis",analysis_cmd),("gainers",gainers_cmd),("trending",trending_cmd)]:
        app.add_handler(CommandHandler(name,fn))
    log.info("WhalesCoin bot starting. One post every %s hours.",POST_INTERVAL_HOURS)
    app.run_polling(allowed_updates=Update.ALL_TYPES)
if __name__=="__main__":main()
