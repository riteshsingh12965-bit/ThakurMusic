import os
import re
import aiofiles
import aiohttp
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont
from py_yt import VideosSearch
from config import YOUTUBE_IMG_URL

CACHE_DIR = "cache"
os.makedirs(CACHE_DIR, exist_ok=True)

PANEL_W, PANEL_H = 763, 545
PANEL_X = (1280 - PANEL_W) // 2
PANEL_Y = 88
TRANSPARENCY = 170
INNER_OFFSET = 36

THUMB_W, THUMB_H = 542, 273
THUMB_X = PANEL_X + (PANEL_W - THUMB_W) // 2
THUMB_Y = PANEL_Y + INNER_OFFSET

TITLE_X = 377
META_X = 377

# 🔥 UPDATED POSITIONS
TITLE_Y = THUMB_Y + THUMB_H + 20
META_Y = TITLE_Y + 55

BAR_X, BAR_Y = 388, META_Y + 60
BAR_RED_LEN = 280
BAR_TOTAL_LEN = 480

ICONS_W, ICONS_H = 415, 45
ICONS_X = PANEL_X + (PANEL_W - ICONS_W) // 2
ICONS_Y = BAR_Y + 50

MAX_TITLE_WIDTH = 580


def trim_to_width(text, font, max_w):
    ellipsis = "..."
    if font.getlength(text) <= max_w:
        return text
    for i in range(len(text) - 1, 0, -1):
        if font.getlength(text[:i] + ellipsis) <= max_w:
            return text[:i] + ellipsis
    return ellipsis


async def get_thumb(videoid: str):
    cache_path = os.path.join(CACHE_DIR, f"{videoid}_v4.png")
    if os.path.exists(cache_path):
        return cache_path

    results = VideosSearch(f"https://www.youtube.com/watch?v={videoid}", limit=1)

    try:
        data = (await results.next())["result"][0]
        title = re.sub(r"\W+", " ", data.get("title", "Title")).title()
        thumbnail = data.get("thumbnails", [{}])[0].get("url", YOUTUBE_IMG_URL)
        duration = data.get("duration")
        views = data.get("viewCount", {}).get("short", "Views")
    except:
        title, thumbnail, duration, views = "Shashank Music", YOUTUBE_IMG_URL, "3:00", "0"

    is_live = not duration or str(duration).lower() in ["live", ""]
    duration_text = "Live" if is_live else duration

    thumb_path = os.path.join(CACHE_DIR, f"thumb{videoid}.png")

    async with aiohttp.ClientSession() as session:
        async with session.get(thumbnail) as resp:
            if resp.status == 200:
                async with aiofiles.open(thumb_path, "wb") as f:
                    await f.write(await resp.read())

    base = Image.open(thumb_path).resize((1280, 720)).convert("RGBA")
    bg = ImageEnhance.Brightness(base.filter(ImageFilter.BoxBlur(10))).enhance(0.6)

    panel = Image.new("RGBA", (PANEL_W, PANEL_H), (255, 255, 255, TRANSPARENCY))
    mask = Image.new("L", (PANEL_W, PANEL_H), 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, PANEL_W, PANEL_H), 50, fill=255)
    bg.paste(panel, (PANEL_X, PANEL_Y), mask)

    draw = ImageDraw.Draw(bg)

    # 🔥 BIG FONT
    try:
        title_font = ImageFont.truetype("ShashankMusic/assets/assets/font2.ttf", 40)
        regular_font = ImageFont.truetype("ShashankMusic/assets/assets/font.ttf", 24)
    except:
        title_font = regular_font = ImageFont.load_default()

    thumb = base.resize((THUMB_W, THUMB_H))
    tmask = Image.new("L", thumb.size, 0)
    ImageDraw.Draw(tmask).rounded_rectangle((0, 0, THUMB_W, THUMB_H), 20, fill=255)
    bg.paste(thumb, (THUMB_X, THUMB_Y), tmask)

    text = trim_to_width(title, title_font, MAX_TITLE_WIDTH)

    # 🔥 SHADOW TEXT
    draw.text((TITLE_X+2, TITLE_Y+2), text, fill="white", font=title_font)
    draw.text((TITLE_X, TITLE_Y), text, fill="black", font=title_font)

    draw.text((META_X, META_Y), f"YouTube | {views}", fill="black", font=regular_font)

    # 🎚️ BAR
    draw.line([(BAR_X, BAR_Y), (BAR_X+BAR_RED_LEN, BAR_Y)], fill="red", width=6)
    draw.line([(BAR_X+BAR_RED_LEN, BAR_Y), (BAR_X+BAR_TOTAL_LEN, BAR_Y)], fill="gray", width=5)

    draw.ellipse([(BAR_X+BAR_RED_LEN-7, BAR_Y-7),
                  (BAR_X+BAR_RED_LEN+7, BAR_Y+7)], fill="red")

    draw.text((BAR_X, BAR_Y+20), "00:00", fill="black", font=regular_font)
    draw.text((BAR_X+BAR_TOTAL_LEN-70, BAR_Y+20), duration_text,
              fill="red" if is_live else "black", font=regular_font)

    # ICONS
    icons_path = "ShashankMusic/assets/assets/play_icons.png"
    if os.path.isfile(icons_path):
        ic = Image.open(icons_path).resize((ICONS_W, ICONS_H)).convert("RGBA")
        bg.paste(ic, (ICONS_X, ICONS_Y), ic)

    os.remove(thumb_path)
    bg.save(cache_path)

    return cache_path
