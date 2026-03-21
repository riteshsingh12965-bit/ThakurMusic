import os
import re
import aiofiles
import aiohttp
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont
from youtubesearchpython import VideosSearch

CACHE_DIR = "cache"
os.makedirs(CACHE_DIR, exist_ok=True)

def trim(text, font, max_w):
    try:
        while font.getlength(text) > max_w:
            text = text[:-1]
        return text
    except:
        return text

async def get_thumb(videoid: str):

    videoid = str(videoid).split("v=")[-1].strip()

    path = f"{CACHE_DIR}/{videoid}.png"
    if os.path.exists(path):
        return path

    # 🔍 YT FETCH (SAFE)
    try:
        search = VideosSearch(videoid, limit=1)
        res = await search.next()
        data = res.get("result", [{}])[0]

        title = data.get("title") or "Unknown Song"
        title = re.sub(r"\W+", " ", title).title()

        thumbs = data.get("thumbnails") or []
        thumb_url = thumbs[0]["url"] if thumbs else None

        duration = data.get("duration") or "3:00"
        views = data.get("viewCount", {}).get("short", "Unknown")

    except Exception:
        title, thumb_url, duration, views = "Unknown Song", None, "3:00", "Unknown"

    # ⬇️ DOWNLOAD SAFE
    thumb_path = f"{CACHE_DIR}/{videoid}_raw.png"
    try:
        if thumb_url:
            async with aiohttp.ClientSession() as s:
                async with s.get(thumb_url) as r:
                    if r.status == 200:
                        async with aiofiles.open(thumb_path, "wb") as f:
                            await f.write(await r.read())
        else:
            raise Exception
    except:
        # fallback blank image
        img = Image.new("RGB", (1280, 720), (30, 30, 30))
        img.save(path)
        return path

    # 🖼 BASE
    base = Image.open(thumb_path).resize((1280, 720)).convert("RGBA")
    bg = base.filter(ImageFilter.GaussianBlur(25))
    bg = ImageEnhance.Brightness(bg).enhance(0.6)

    # 🧊 GLASS PANEL
    panel = Image.new("RGBA", (800, 500), (255, 255, 255, 160))
    mask = Image.new("L", (800, 500), 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, 800, 500), 40, fill=255)
    bg.paste(panel, (240, 110), mask)

    draw = ImageDraw.Draw(bg)

    # 🖼 THUMB
    thumb = base.resize((600, 280))
    tmask = Image.new("L", thumb.size, 0)
    ImageDraw.Draw(tmask).rounded_rectangle((0, 0, 600, 280), 30, fill=255)
    bg.paste(thumb, (340, 130), tmask)

    # 🔤 FONT
    try:
        title_font = ImageFont.truetype("ShashankMusic/assets/font.ttf", 38)
        small_font = ImageFont.truetype("ShashankMusic/assets/font.ttf", 22)
    except:
        title_font = small_font = ImageFont.load_default()

    # 🎵 TITLE
    title = trim(title, title_font, 600)
    draw.text((360, 430), title, fill="black", font=title_font)

    # 📊 META
    draw.text((360, 470), f"YouTube | {views}", fill="black", font=small_font)

    # 🎚 BAR
    bar_x, bar_y = 360, 520
    draw.line((bar_x, bar_y, bar_x+300, bar_y), fill="red", width=6)
    draw.line((bar_x+300, bar_y, bar_x+500, bar_y), fill="gray", width=5)
    draw.ellipse((bar_x+290, bar_y-8, bar_x+310, bar_y+8), fill="red")

    draw.text((360, 540), "00:00", fill="black", font=small_font)
    draw.text((820, 540), duration, fill="black", font=small_font)

    # 🧹 CLEAN
    try:
        os.remove(thumb_path)
    except:
        pass

    bg.save(path)
    return path
