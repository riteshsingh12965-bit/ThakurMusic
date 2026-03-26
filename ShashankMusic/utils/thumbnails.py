import os
import aiohttp
import aiofiles
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from youtubesearchpython.__future__ import VideosSearch
from ShashankMusic import app

CACHE_DIR = "cache"
os.makedirs(CACHE_DIR, exist_ok=True)

FONT = os.path.join("ThakurMusic", "ShashankMusic", "assets", "font.ttf")


def trim(text, font, max_w):
    while font.getbbox(text)[2] > max_w:
        text = text[:-1]
    return text + "..."


async def get_thumb(videoid: str):
    path = f"{CACHE_DIR}/{videoid}.png"
    if os.path.exists(path):
        return path

    # 🔍 GET DATA (IMPORTANT)
    try:
        search = VideosSearch(videoid, limit=1)
        data = (await search.next())["result"][0]

        title = data["title"]
        duration = data["duration"]
        views = data["viewCount"]["short"]
        thumb_url = data["thumbnails"][0]["url"]

    except:
        title = "Unknown"
        duration = "0:00"
        views = "0"
        thumb_url = f"https://img.youtube.com/vi/{videoid}/maxresdefault.jpg"

    thumb_file = f"{CACHE_DIR}/{videoid}.jpg"

    # ⬇ download thumb
    async with aiohttp.ClientSession() as s:
        async with s.get(thumb_url) as r:
            if r.status == 200:
                async with aiofiles.open(thumb_file, "wb") as f:
                    await f.write(await r.read())

    # 🎨 BACKGROUND
    bg = Image.new("RGB", (1280, 720), (20, 10, 5))

    glow = Image.new("RGB", (1280, 720), (0, 0, 0))
    g = ImageDraw.Draw(glow)
    g.ellipse((200, 50, 1100, 700), fill=(255, 80, 60))
    glow = glow.filter(ImageFilter.GaussianBlur(180))
    bg = Image.blend(bg, glow, 0.5)

    draw = ImageDraw.Draw(bg)

    # 🖼 THUMB
    thumb = Image.open(thumb_file).resize((420, 420)).convert("RGBA")

    mask = Image.new("L", (420, 420), 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, 420, 420), 60, fill=255)
    thumb.putalpha(mask)

    bg.paste(thumb, (120, 150), thumb)

    # 🔥 BORDER
    border = Image.new("RGBA", (440, 440), (0, 0, 0, 0))
    bd = ImageDraw.Draw(border)
    bd.rounded_rectangle((0, 0, 440, 440), 60, outline=(255, 80, 60), width=6)

    glow = border.filter(ImageFilter.GaussianBlur(25))
    bg.paste(glow, (110, 140), glow)
    bg.paste(border, (110, 140), border)

    # 🅵🅾🅽🆃
    try:
        title_font = ImageFont.truetype(FONT, 48)
        meta_font = ImageFont.truetype(FONT, 34)
        small_font = ImageFont.truetype(FONT, 28)
    except:
        title_font = meta_font = small_font = ImageFont.load_default()

    # 🔴 NOW PLAYING
    draw.rounded_rectangle((600, 140, 860, 200), 30, fill=(255, 80, 60))
    draw.text((640, 155), "NOW PLAYING", fill="white", font=small_font)

    # 🎵 TITLE
    title = trim(title, title_font, 550)
    draw.text((600, 240), title, fill="white", font=title_font)

    draw.line((600, 300, 1100, 300), fill=(255, 80, 60), width=3)

    # 📊 META
    draw.text((600, 330), f"Duration: {duration}", fill="white", font=meta_font)
    draw.text((600, 380), f"Views: {views}", fill=(255, 100, 80), font=meta_font)

    # 🎚 BAR
    bar_x = 600
    bar_y = 470
    bar_w = 500

    draw.rounded_rectangle((bar_x, bar_y, bar_x + bar_w, bar_y + 10), 6, fill=(100, 100, 100))
    draw.rounded_rectangle((bar_x, bar_y, bar_x + bar_w // 2, bar_y + 10), 6, fill=(255, 80, 60))
    draw.ellipse((bar_x + bar_w // 2 - 8, bar_y - 5, bar_x + bar_w // 2 + 8, bar_y + 15), fill="white")

    draw.text((600, 510), "00:00", fill="white", font=small_font)
    draw.text((1080, 510), duration, fill="white", font=small_font)

    # SAVE
    bg.save(path)
    return path
