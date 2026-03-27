import os
import re
import aiofiles
import aiohttp
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont
from py_yt import VideosSearch
from config import YOUTUBE_IMG_URL

# =========================
# CONFIG
# =========================
CACHE_DIR = "cache"
os.makedirs(CACHE_DIR, exist_ok=True)

WIDTH, HEIGHT = 1280, 720

# Left thumbnail box
THUMB_X = 105
THUMB_Y = 140
THUMB_W = 450
THUMB_H = 450
THUMB_RADIUS = 35
BORDER_WIDTH = 10

# Right content area
BADGE_X = 620
BADGE_Y = 125

TITLE_X = 620
TITLE_Y = 215

META_X = 620
META_Y = 370

BAR_X = 620
BAR_Y = 535
BAR_TOTAL = 500
BAR_RED = 250

FOOTER_X = 910
FOOTER_Y = 650

MAX_TITLE_WIDTH = 520

# =========================
# HELPERS
# =========================
def safe_text(text):
    """Remove unsupported unicode safely."""
    return str(text).encode("ascii", "ignore").decode("ascii")

def trim_to_width(text: str, font, max_w: int) -> str:
    ellipsis = "..."
    if font.getlength(text) <= max_w:
        return text
    for i in range(len(text) - 1, 0, -1):
        if font.getlength(text[:i] + ellipsis) <= max_w:
            return text[:i] + ellipsis
    return ellipsis

# =========================
# MAIN THUMB FUNCTION
# =========================
async def get_thumb(videoid: str) -> str:
    cache_path = os.path.join(CACHE_DIR, f"{videoid}_premium.png")
    if os.path.exists(cache_path):
        return cache_path

    # -------------------------
    # FETCH YOUTUBE DATA
    # -------------------------
    try:
        results = VideosSearch(f"https://www.youtube.com/watch?v={videoid}", limit=1)
        results_data = await results.next()
        result_items = results_data.get("result", [])

        if not result_items:
            raise ValueError("No results found.")

        data = result_items[0]

        raw_title = data.get("title", "Unknown Title")
        title = safe_text(raw_title)

        thumbnail = data.get("thumbnails", [{}])[0].get("url", f"https://i.ytimg.com/vi/{videoid}/hqdefault.jpg")
        duration = data.get("duration", "4:00")
        views = data.get("viewCount", {}).get("short", "Unknown Views")

        title = trim_to_width(title, ImageFont.load_default(), 45)

    except Exception:
        title = "Unknown Song"
        thumbnail = f"https://i.ytimg.com/vi/{videoid}/hqdefault.jpg"
        duration = "4:00"
        views = "Unknown Views"

    # -------------------------
    # DOWNLOAD THUMBNAIL
    # -------------------------
    thumb_path = os.path.join(CACHE_DIR, f"{videoid}_thumb.jpg")

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(thumbnail) as resp:
                if resp.status == 200:
                    async with aiofiles.open(thumb_path, "wb") as f:
                        await f.write(await resp.read())
                else:
                    raise Exception("Thumbnail download failed")
    except Exception:
        return None

    # -------------------------
    # OPEN BASE IMAGE
    # -------------------------
    base = Image.open(thumb_path).convert("RGBA").resize((WIDTH, HEIGHT))
    bg = ImageEnhance.Brightness(base.filter(ImageFilter.GaussianBlur(18))).enhance(0.30)

    draw = ImageDraw.Draw(bg)

    # -------------------------
    # LOAD FONTS
    # -------------------------
    try:
        badge_font = ImageFont.truetype("Shashank/assets/assets/font2.ttf", 30)
        title_font = ImageFont.truetype("Shashank/assets/assets/font.ttf", 56)
        regular_font = ImageFont.truetype("Shashank/assets/assets/font2.ttf", 40)
        small_font = ImageFont.truetype("Shashank/assets/assets/font2.ttf", 30)
        footer_font = ImageFont.truetype("Shashank/assets/assets/font2.ttf", 24)
    except OSError:
        badge_font = title_font = regular_font = small_font = footer_font = ImageFont.load_default()

    # -------------------------
    # LEFT THUMB IMAGE
    # -------------------------
    thumb = Image.open(thumb_path).convert("RGBA").resize((THUMB_W, THUMB_H))

    mask = Image.new("L", (THUMB_W, THUMB_H), 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, THUMB_W, THUMB_H), THUMB_RADIUS, fill=255)

    border_img = Image.new("RGBA", (THUMB_W + BORDER_WIDTH*2, THUMB_H + BORDER_WIDTH*2), (0, 0, 0, 0))
    border_draw = ImageDraw.Draw(border_img)
    border_draw.rounded_rectangle(
        (0, 0, THUMB_W + BORDER_WIDTH*2 - 1, THUMB_H + BORDER_WIDTH*2 - 1),
        THUMB_RADIUS + 8,
        outline=(255, 59, 59, 255),
        width=BORDER_WIDTH
    )

    bg.paste(border_img, (THUMB_X - BORDER_WIDTH, THUMB_Y - BORDER_WIDTH), border_img)
    bg.paste(thumb, (THUMB_X, THUMB_Y), mask)

    # -------------------------
    # NOW PLAYING BADGE
    # -------------------------
    badge_w, badge_h = 230, 65
    badge = Image.new("RGBA", (badge_w, badge_h), (0, 0, 0, 0))
    badge_draw = ImageDraw.Draw(badge)
    badge_draw.rounded_rectangle((0, 0, badge_w, badge_h), 32, fill=(255, 59, 59, 255))
    bg.paste(badge, (BADGE_X, BADGE_Y), badge)

    draw.text((BADGE_X + 38, BADGE_Y + 15), "NOW PLAYING", fill="white", font=badge_font)

    # -------------------------
    # TITLE
    # -------------------------
    title = trim_to_width(title, title_font, MAX_TITLE_WIDTH)
    draw.text((TITLE_X, TITLE_Y), title, fill="white", font=title_font)

    # underline
    title_w = int(draw.textlength(title, font=title_font))
    draw.line((TITLE_X, TITLE_Y + 78, TITLE_X + min(title_w, 430), TITLE_Y + 78), fill=(255, 59, 59), width=5)

    # -------------------------
    # META TEXT
    # -------------------------
    draw.text((META_X, META_Y), f"Duration: {safe_text(duration)}", fill="white", font=regular_font)
    draw.text((META_X, META_Y + 58), f"Views: {safe_text(views)}", fill=(255, 90, 90), font=regular_font)
    draw.text((META_X, META_Y + 116), "Player: @sunumusicbot", fill=(255, 90, 90), font=regular_font)

    # -------------------------
    # PROGRESS BAR
    # -------------------------
    draw.line((BAR_X, BAR_Y, BAR_X + BAR_TOTAL, BAR_Y), fill=(240, 240, 240), width=16)
    draw.line((BAR_X, BAR_Y, BAR_X + BAR_RED, BAR_Y), fill=(255, 59, 59), width=16)

    knob_x = BAR_X + BAR_RED
    draw.ellipse((knob_x - 16, BAR_Y - 16, knob_x + 16, BAR_Y + 16), fill="white")

    draw.text((BAR_X, BAR_Y + 28), "00:00", fill="white", font=small_font)
    draw.text((BAR_X + BAR_TOTAL - 70, BAR_Y + 28), safe_text(duration), fill="white", font=small_font)

    # -------------------------
    # FOOTER
    # -------------------------
    draw.text((FOOTER_X, FOOTER_Y), "Powered by Mr Thakur", fill=(190, 190, 190), font=footer_font)

    # -------------------------
    # SAVE
    # -------------------------
    bg.save(cache_path)

    try:
        os.remove(thumb_path)
    except:
        pass

    return cache_path
