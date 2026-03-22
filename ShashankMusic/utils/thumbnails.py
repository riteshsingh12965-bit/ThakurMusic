import os
import re
import aiofiles
import aiohttp
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont
from unidecode import unidecode
from py_yt import VideosSearch
from config import YOUTUBE_IMG_URL

CACHE_DIR = "cache"
os.makedirs(CACHE_DIR, exist_ok=True)


def clean(text):
    return unidecode(str(text))


def trim(text, font, max_w):
    if font.getlength(text) <= max_w:
        return text
    while font.getlength(text + "...") > max_w:
        text = text[:-1]
    return text + "..."


async def get_thumb(videoid):

    final_path = f"{CACHE_DIR}/{videoid}_final.png"
    if os.path.exists(final_path):
        return final_path

    # 🔍 FETCH DATA
    try:
        data = (await VideosSearch(f"https://www.youtube.com/watch?v={videoid}", limit=1).next())["result"][0]

        title = clean(data.get("title", "Song"))
        title = re.sub(r"\W+", " ", title).title()

        duration = data.get("duration", "3:00")
        views = data.get("viewCount", {}).get("short", "0")
        channel = data.get("channel", {}).get("name", "Channel")

        thumbnail = data["thumbnails"][0]["url"].split("?")[0]

    except:
        title, duration, views, channel = "Shashank Music", "3:00", "0", "Channel"
        thumbnail = YOUTUBE_IMG_URL

    # 📥 DOWNLOAD THUMB
    thumb_path = f"{CACHE_DIR}/{videoid}.jpg"

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(thumbnail) as r:
                if r.status == 200:
                    async with aiofiles.open(thumb_path, "wb") as f:
                        await f.write(await r.read())
    except:
        return YOUTUBE_IMG_URL

    try:
        base = Image.open(thumb_path).resize((1280, 720)).convert("RGBA")
    except:
        return YOUTUBE_IMG_URL

    # 🌌 BACKGROUND
    bg = base.filter(ImageFilter.GaussianBlur(30))
    bg = ImageEnhance.Brightness(bg).enhance(0.4)

    draw = ImageDraw.Draw(bg)

    # 🎵 LEFT IMAGE (BIG)
    thumb = base.resize((550, 330))
    mask = Image.new("L", thumb.size, 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, 550, 330), 35, fill=255)
    bg.paste(thumb, (80, 200), mask)

    # 🔤 BIG FONTS
    try:
        title_font = ImageFont.truetype("ShashankMusic/assets/font3.ttf", 85)
        meta_font = ImageFont.truetype("ShashankMusic/assets/font2.ttf", 42)
        small_font = ImageFont.truetype("ShashankMusic/assets/font2.ttf", 34)
    except:
        title_font = meta_font = small_font = ImageFont.load_default()

    x = 660

    title = trim(title, title_font, 520)

    # ✨ TITLE WITH SHADOW
    draw.text((x+4, 224), title, fill="black", font=title_font)
    draw.text((x, 220), title, fill="white", font=title_font)

    # 📊 META INFO
    draw.text((x, 340), f"Duration: {duration}", fill=(255,140,0), font=meta_font)
    draw.text((x, 400), f"Views: {views}", fill=(255,140,0), font=meta_font)
    draw.text((x, 460), f"Channel: {channel}", fill=(255,140,0), font=meta_font)

    # ▶️ NOW PLAYING
    draw.text((x, 160), "NOW PLAYING", fill=(255,140,0), font=small_font)

    # 🎚️ PROGRESS BAR
    total = 500
    done = int(total * 0.5)
    bar_y = 560

    draw.line((x, bar_y, x + total, bar_y), fill=(120,120,120), width=8)
    draw.line((x, bar_y, x + done, bar_y), fill=(255,140,0), width=10)

    draw.ellipse((x + done - 10, bar_y - 10, x + done + 10, bar_y + 10), fill="white")

    draw.text((x, bar_y + 25), "0:00", fill="white", font=small_font)
    draw.text((x + total - 90, bar_y + 25), duration, fill="white", font=small_font)

    # 🎮 ICONS
    try:
        icons = Image.open("ShashankMusic/assets/play_icons.png").resize((450, 70))
        bg.paste(icons, (x, 610), icons)
    except:
        pass

    # 🧹 CLEANUP
    try:
        os.remove(thumb_path)
    except:
        pass

    bg.save(final_path)
    return final_path
