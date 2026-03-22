import os
import aiohttp
import aiofiles
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter, ImageFont
from youtubesearchpython import VideosSearch

CACHE_DIR = Path("cache")
CACHE_DIR.mkdir(exist_ok=True)

W, H = 1280, 720


def clean(text):
    return text.encode("ascii", "ignore").decode()


async def get_thumb(videoid: str):

    # 🎯 DIRECT THUMB (NO FAIL)
    thumburl = f"https://img.youtube.com/vi/{videoid}/hqdefault.jpg"

    # 🎧 GET DATA
    try:
        res = VideosSearch(videoid, limit=1)
        data = (await res.next())["result"][0]

        title = clean(data.get("title", "Unknown Song"))
        duration = data.get("duration", "3:00")
        views = clean(data.get("viewCount", {}).get("short", "0"))
        channel = clean(data.get("channel", {}).get("name", "Unknown"))

    except:
        title = "Unknown Song"
        duration = "3:00"
        views = "0"
        channel = "Shashank"

    thumb_path = CACHE_DIR / f"{videoid}.jpg"

    # 🌐 DOWNLOAD THUMB
    try:
        async with aiohttp.ClientSession() as s:
            async with s.get(thumburl) as r:
                if r.status == 200:
                    async with aiofiles.open(thumb_path, "wb") as f:
                        await f.write(await r.read())
    except:
        pass

    # 🖼️ LOAD BG
    if thumb_path.exists():
        bg = Image.open(thumb_path).resize((W, H)).convert("RGB")
    else:
        bg = Image.new("RGB", (W, H), (10, 15, 25))

    bg = bg.filter(ImageFilter.GaussianBlur(35))
    canvas = bg.copy()
    draw = ImageDraw.Draw(canvas)

    # 🔵 BLUE GLOW OVERLAY
    overlay = Image.new("RGBA", (W, H), (0, 120, 255, 60))
    canvas = Image.alpha_composite(canvas.convert("RGBA"), overlay)

    draw = ImageDraw.Draw(canvas)

    # 🎵 ALBUM CARD
    size = 380
    album = Image.open(thumb_path).resize((size, size)) if thumb_path.exists() else Image.new("RGB", (size, size), (40, 40, 40))

    mask = Image.new("L", (size, size), 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, size, size), 30, fill=255)
    album.putalpha(mask)

    canvas.paste(album, (100, 170), album)

    # 🔤 FONT SAFE
    title_font = ImageFont.load_default()
    small_font = ImageFont.load_default()

    # 🟢 NOW PLAYING
    draw.rounded_rectangle((550, 120, 780, 170), radius=25, fill=(80, 80, 80))
    draw.text((580, 130), "NOW PLAYING", fill="white", font=small_font)

    # 🎶 TITLE BIG
    draw.text((550, 200), title[:35], fill="white", font=title_font)

    # 📊 INFO
    draw.text((550, 260), f"Duration: {duration}", fill="white", font=small_font)
    draw.text((550, 300), f"Views: {views}", fill=(100, 180, 255), font=small_font)
    draw.text((550, 340), f"Player: @{channel}", fill=(100, 180, 255), font=small_font)

    # 🎚️ PROGRESS BAR
    x1, y = 550, 420
    x2 = 1100

    draw.line((x1, y, x2, y), fill=(180, 180, 180), width=8)
    draw.line((x1, y, x1 + 350, y), fill=(80, 180, 255), width=8)

    draw.ellipse((x1 + 340, y - 10, x1 + 360, y + 10), fill="white")

    # ⏱️ TIME
    draw.text((550, 450), "00:00", fill="white", font=small_font)
    draw.text((1050, 450), duration, fill="white", font=small_font)

    # 👑 CREDIT
    draw.text((900, 650), "Powered by Shashank", fill=(100, 180, 255), font=small_font)

    out = CACHE_DIR / f"{videoid}.png"
    canvas.convert("RGB").save(out)

    return str(out)
