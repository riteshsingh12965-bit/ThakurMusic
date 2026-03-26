import os
import aiohttp
import aiofiles
from PIL import Image, ImageDraw, ImageFont, ImageFilter

CACHE_DIR = "cache"
os.makedirs(CACHE_DIR, exist_ok=True)

FONT = os.path.join("ThakurMusic", "ShashankMusic", "assets", "font.ttf")


def trim(text, font, max_w):
    try:
        while font.getbbox(text)[2] > max_w and len(text) > 3:
            text = text[:-1]
        return text + "..." if len(text) > 3 else text
    except:
        return text


async def get_thumb(videoid: str, title="Unknown Song", duration="0:00", views="0"):
    path = f"{CACHE_DIR}/{videoid}.png"
    if os.path.exists(path) and os.path.getsize(path) > 0:
        return path

    thumb_url = f"https://img.youtube.com/vi/{videoid}/hqdefault.jpg"
    thumb_file = f"{CACHE_DIR}/{videoid}.jpg"

    # Download thumbnail
    try:
        async with aiohttp.ClientSession() as s:
            async with s.get(thumb_url) as r:
                if r.status == 200:
                    async with aiofiles.open(thumb_file, "wb") as f:
                        await f.write(await r.read())
    except:
        thumb_file = None

    # Background
    bg = Image.new("RGB", (1280, 720), (18, 10, 8))
    glow = Image.new("RGB", (1280, 720), (0, 0, 0))
    g = ImageDraw.Draw(glow)
    g.ellipse((180, 30, 1120, 700), fill=(255, 90, 70))
    glow = glow.filter(ImageFilter.GaussianBlur(170))
    bg = Image.blend(bg, glow, 0.48)

    draw = ImageDraw.Draw(bg)

    # Thumb image
    try:
        thumb = Image.open(thumb_file).resize((430, 430)).convert("RGBA")
    except:
        thumb = Image.new("RGBA", (430, 430), (40, 40, 40, 255))

    mask = Image.new("L", (430, 430), 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, 430, 430), 55, fill=255)
    thumb.putalpha(mask)

    bg.paste(thumb, (120, 145), thumb)

    # Border
    border = Image.new("RGBA", (450, 450), (0, 0, 0, 0))
    bd = ImageDraw.Draw(border)
    bd.rounded_rectangle((0, 0, 450, 450), 60, outline=(255, 90, 70), width=7)

    glow_border = border.filter(ImageFilter.GaussianBlur(22))
    bg.paste(glow_border, (110, 135), glow_border)
    bg.paste(border, (110, 135), border)

    # Fonts (BIGGER)
    try:
        badge_font = ImageFont.truetype(FONT, 30)
        title_font = ImageFont.truetype(FONT, 62)
        meta_font = ImageFont.truetype(FONT, 44)
        small_font = ImageFont.truetype(FONT, 34)
    except:
        badge_font = ImageFont.load_default()
        title_font = ImageFont.load_default()
        meta_font = ImageFont.load_default()
        small_font = ImageFont.load_default()

    # NOW PLAYING badge
    draw.rounded_rectangle((620, 145, 960, 220), 35, fill=(255, 90, 70))
    draw.text((695, 164), "NOW PLAYING", fill="black", font=badge_font)

    # Title
    title = trim(title, title_font, 540)
    draw.text((620, 265), title, fill="white", font=title_font)

    # Underline
    draw.line((620, 345, 1120, 345), fill=(255, 90, 70), width=5)

    # Meta section
    draw.text((620, 400), "Duration:", fill="white", font=meta_font)
    draw.text((860, 400), duration, fill=(255, 110, 90), font=meta_font)

    draw.text((620, 490), "Views:", fill="white", font=meta_font)
    draw.text((790, 490), views, fill=(255, 110, 90), font=meta_font)

    # Progress bar (BIG)
    bar_x = 620
    bar_y = 590
    bar_w = 500

    draw.rounded_rectangle((bar_x, bar_y, bar_x + bar_w, bar_y + 12), 8, fill=(180, 180, 180))
    draw.rounded_rectangle((bar_x, bar_y, bar_x + bar_w // 2, bar_y + 12), 8, fill=(255, 90, 70))
    draw.ellipse((bar_x + bar_w // 2 - 12, bar_y - 8, bar_x + bar_w // 2 + 12, bar_y + 16), fill="white")

    draw.text((620, 620), "00:00", fill="white", font=small_font)
    draw.text((1060, 620), duration, fill="white", font=small_font)

    bg.save(path)
    return path
