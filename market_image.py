"""Generate branded WhalesCoin-style market cards from live CoinPaprika data."""
from datetime import datetime
from zoneinfo import ZoneInfo
from PIL import Image, ImageDraw, ImageFont
import os
import tempfile

W, H = 1600, 900
BG = (7, 10, 20)
GOLD = (247, 190, 35)
WHITE = (245, 247, 252)
MUTED = (157, 166, 184)
GREEN = (48, 207, 137)
RED = (239, 91, 99)
PURPLE = (137, 91, 238)


def _font(size, bold=False):
    candidates = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf",
    ]
    for path in candidates:
        if os.path.exists(path):
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def _money(value):
    if value is None:
        return "N/A"
    if abs(value) >= 1:
        return f"${value:,.2f}"
    if abs(value) >= .01:
        return f"${value:.4f}"
    return f"${value:.8f}"


def select_top_five(kind, rows):
    valid = [r for r in rows if r.get("change") is not None]
    if kind == "gainers":
        return sorted(valid, key=lambda r: r["change"], reverse=True)[:5]
    return sorted(rows, key=lambda r: r.get("volume") or 0, reverse=True)[:5]


def render_highlight(kind, rows, timezone="Asia/Kolkata"):
    chosen = select_top_five(kind, rows)
    if not chosen:
        raise ValueError("No market rows available to render")
    image = Image.new("RGB", (W, H), BG)
    px = image.load()
    # Subtle navy gradient and diagonal accent bands.
    for y in range(H):
        c = int(7 + 10 * y / H)
        for x in range(W):
            px[x, y] = (7, c, 20 + int(12 * x / W))
    draw = ImageDraw.Draw(image, "RGBA")
    for offset in (-500, 100, 700, 1300):
        draw.polygon([(offset, H), (offset + 500, H), (offset + 1250, 0), (offset + 750, 0)],
                     fill=(110, 43, 68, 24))
    draw.line((70, 790, 1530, 790), fill=(100, 110, 130, 100), width=2)

    title_font = _font(76, True)
    brand_font = _font(31, True)
    date_font = _font(27)
    name_font = _font(29, True)
    pct_font = _font(34, True)
    rank_font = _font(20, True)
    footer_font = _font(22)

    draw.rounded_rectangle((70, 55, 250, 125), radius=18, fill=(13, 30, 57, 255), outline=(46, 132, 244, 220), width=2)
    draw.text((91, 72), "WHALES", font=brand_font, fill=WHITE)
    draw.text((92, 103), "COIN", font=_font(19, True), fill=(70, 165, 255))
    heading = "TOP GAINERS" if kind == "gainers" else "TRENDING TOP 5"
    bbox = draw.textbbox((0, 0), heading, font=title_font)
    draw.text(((W - (bbox[2] - bbox[0])) / 2, 155), heading, font=title_font, fill=WHITE)
    date = datetime.now(ZoneInfo(timezone)).strftime("%Y.%m.%d")
    date_box = draw.textbbox((0, 0), date, font=date_font)
    draw.text(((W - (date_box[2] - date_box[0])) / 2, 250), date, font=date_font, fill=MUTED)

    margin, gap = 70, 22
    card_w = (W - 2 * margin - 4 * gap) // 5
    card_top, card_bottom = 390, 735
    for i, row in enumerate(chosen):
        x0 = margin + i * (card_w + gap)
        x1 = x0 + card_w
        center = (x0 + x1) // 2
        draw.rounded_rectangle((x0, card_top, x1, card_bottom), radius=25,
                               fill=(13, 17, 29, 230), outline=(117, 103, 157, 190), width=2)
        draw.ellipse((center - 62, card_top - 62, center + 62, card_top + 62),
                     fill=(20, 24, 40, 255), outline=PURPLE, width=8)
        symbol = str(row.get("symbol", "?")).upper()[:5]
        sb = draw.textbbox((0, 0), symbol, font=_font(34, True))
        draw.text((center - (sb[2] - sb[0]) / 2, card_top - 18), symbol,
                  font=_font(34, True), fill=GOLD)
        name = str(row.get("name", "Unknown"))
        while len(name) > 17:
            name = name[:16] + "…"
            break
        nb = draw.textbbox((0, 0), name, font=name_font)
        draw.text((center - (nb[2] - nb[0]) / 2, card_top + 100), name, font=name_font, fill=WHITE)
        change = row.get("change")
        if change is None:
            pct = "N/A"
            color = MUTED
        else:
            pct = f"{change:+.2f}%"
            color = GREEN if change >= 0 else RED
        pb = draw.textbbox((0, 0), pct, font=pct_font)
        draw.text((center - (pb[2] - pb[0]) / 2, card_top + 185), pct, font=pct_font, fill=color)
        price = _money(row.get("price"))
        prb = draw.textbbox((0, 0), price, font=footer_font)
        draw.text((center - (prb[2] - prb[0]) / 2, card_top + 250), price, font=footer_font, fill=MUTED)
        rank_label = f"NO. {i + 1}"
        rb = draw.textbbox((0, 0), rank_label, font=rank_font)
        draw.rounded_rectangle((center - 53, card_bottom - 48, center + 53, card_bottom - 15),
                               radius=15, fill=(65, 67, 82, 220))
        draw.text((center - (rb[2] - rb[0]) / 2, card_bottom - 44), rank_label, font=rank_font, fill=WHITE)

    draw.text((70, 825), "whalescoin.io", font=brand_font, fill=WHITE)
    draw.text((1180, 830), "LIVE MARKET DATA · 24H", font=footer_font, fill=MUTED)
    fd, path = tempfile.mkstemp(prefix=f"whalescoin-{kind}-", suffix=".png")
    os.close(fd)
    image.save(path, format="PNG", optimize=True)
    return path


def build_caption(kind, rows, timezone="Asia/Kolkata"):
    chosen = select_top_five(kind, rows)
    title = "Top Gainers" if kind == "gainers" else "Trending Top 5 by 24h trading volume"
    medal = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣"]
    lines = [f"🔥 WhalesCoin {title} | {datetime.now(ZoneInfo(timezone)).strftime('%B %d, %Y')}", "",
             "🚀 Live market snapshot from CoinPaprika.", "", "🏆 Today's Rankings:"]
    for i, row in enumerate(chosen):
        change = row.get("change")
        pct = "N/A" if change is None else f"{change:+.2f}%"
        lines.append(f"{medal[i]} {row.get('name')} — {pct}")
    if chosen:
        best = max((r for r in chosen if r.get("change") is not None), key=lambda r: r["change"], default=None)
        if best:
            lines += ["", f"📊 Market Insight: {best.get('name')} leads this Top 5 list with {best['change']:+.2f}% over 24 hours."]
    lines += ["", "💡 Stay informed. Track the trends. Discover opportunities.",
              "", "🌐 Powered by Whales Coin", "🐳 whalescoin.io",
              "", "⚠️ Market data changes rapidly. Informational purposes only; not financial advice.",
              "", "#WhalesCoin #CryptoTrends #TrendingCrypto #CryptoMarket"]
    return "\n".join(lines)[:1024]
