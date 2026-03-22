import os
import random
import aiohttp
import aiofiles
import traceback
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter, ImageFont
from youtubesearchpython import VideosSearch
from ShashankMusic import app
import math

CACHE_DIR = Path("cache")
CACHE_DIR.mkdir(exist_ok=True)

CANVAS_W, CANVAS_H = 1320, 760

FONT_REGULAR_PATH = "ShashankMusic/assets/font2.ttf"
FONT_BOLD_PATH = "ShashankMusic/assets/font3.ttf"
DEFAULT_THUMB = "ShashankMusic/assets/ShashankBots.jpg"


def create_shape_mask(size):
    mask = Image.new("L", (size, size), 0)
    draw = ImageDraw.Draw(mask)
    draw.ellipse([0, 0, size, size], fill=255)
    return mask


def random_gradient():
    colors = [
        [(15, 12, 41), (48, 43, 99), (36, 36, 62)],
        [(10, 10, 10), (35, 35, 40), (20, 20, 25)],
        [(26, 26, 46), (56, 56, 86), (40, 40, 60)],
    ]
    return random.choice(colors)


def apply_gradient(canvas, colors):
    overlay = Image.new('RGBA', canvas.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    for y in range(CANVAS_H):
        progress = y / CANVAS_H
        r = int(colors[0][0] * (1-progress) + colors[1][0] * progress)
        g = int(colors[0][1] * (1-progress) + colors[1][1] * progress)
        b = int(colors[0][2] * (1-progress) + colors[1][2] * progress)

        draw.line([(0, y), (CANVAS_W, y)], fill=(r, g, b, 255))

    return Image.alpha_composite(canvas, overlay)


async def get_thumb(videoid: str):
    url = f"https://www.youtube.com/watch?v={videoid}"
    thumb_path = None

    # 🎧 FETCH DATA
    try:
        results = VideosSearch(url, limit=1)
        result = (await results.next())["result"][0]

        title = result.get("title", "Unknown")
        duration = result.get("duration", "Unknown")
        thumburl = result["thumbnails"][0]["url"].split("?")[0]
        views = result.get("viewCount", {}).get("short", "Unknown")
        channel = result.get("channel", {}).get("name", "Unknown")

    except Exception as e:
        print(f"[YT ERROR] {e}")
        title = "ShashankMusic"
        duration = "Unknown"
        views = "Unknown Views"
        channel = "ShashankBots"
        thumburl = None

    # 🌐 DOWNLOAD IMAGE
    try:
        if thumburl:
            async with aiohttp.ClientSession() as session:
                async with session.get(thumburl) as resp:
                    if resp.status == 200:
                        thumb_path = CACHE_DIR / f"{videoid}.png"
                        async with aiofiles.open(thumb_path, "wb") as f:
                            await f.write(await resp.read())
    except:
        thumb_path = None

    # 🖼️ LOAD IMAGE
    if thumb_path and thumb_path.exists():
        base_img = Image.open(thumb_path).convert("RGBA")
    else:
        base_img = Image.open(DEFAULT_THUMB).convert("RGBA")

    try:
        canvas = Image.new("RGBA", (CANVAS_W, CANVAS_H))
        canvas = apply_gradient(canvas, random_gradient())

        art_size = 450
        art = base_img.resize((art_size, art_size))
        mask = create_shape_mask(art_size)
        art.putalpha(mask)

        canvas.paste(art, (80, 150), art)

        draw = ImageDraw.Draw(canvas)

        # BRAND
        brand_font = ImageFont.truetype(FONT_BOLD_PATH, 42)
        draw.text((40, 30), app.username, fill="white", font=brand_font)

        # NOW PLAYING
        np_font = ImageFont.truetype(FONT_BOLD_PATH, 60)
        draw.text((600, 150), "NOW PLAYING", fill=(120, 180, 255), font=np_font)

        # TITLE
        title_font = ImageFont.truetype(FONT_BOLD_PATH, 40)
        draw.text((600, 260), title[:40], fill="white", font=title_font)

        # META
        meta_font = ImageFont.truetype(FONT_REGULAR_PATH, 30)
        draw.text((600, 350), f"Views: {views}", fill="white", font=meta_font)
        draw.text((600, 400), f"Duration: {duration}", fill="white", font=meta_font)
        draw.text((600, 450), f"Channel: {channel}", fill="white", font=meta_font)

        out = CACHE_DIR / f"{videoid}_final.png"
        canvas.save(out)

        if thumb_path and thumb_path.exists():
            os.remove(thumb_path)

        return str(out)

    except Exception as e:
        print(e)
        traceback.print_exc()
        return None
