import os
import aiohttp
import aiofiles
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance, ImageOps

CACHE_DIR = "cache"
os.makedirs(CACHE_DIR, exist_ok=True)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FONT = os.path.abspath(os.path.join(BASE_DIR, "..", "assets", "font.ttf"))


# =========================
# SAFE TEXT
# =========================
def safe_text(text, default="Unknown Song"):
    if text is None:
        return default
    text = str(text).strip()
    return text if text else default


def trim(text, font, max_w):
    text = safe_text(text)
    try:
        while font.getbbox(text)[2] > max_w and len(text) > 3:
            text = text[:-1]
        return text + "..." if len(text) > 3 else text
    except:
        return text


def load_font(size):
    try:
        return ImageFont.truetype(FONT, size)
    except:
        return ImageFont.load_default()


# =========================
# FETCH YT TITLE
# =========================
async def fetch_youtube_title(videoid: str):
    try:
        url = f"https://www.youtube.com/oembed?url=https://www.youtube.com/watch?v={videoid}&format=json"
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=10) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    title = data.get("title")
                    if title:
                        return title.strip()
    except:
        pass
    return None


# =========================
# ICONS
# =========================
def draw_shuffle(draw, x, y, color="white", width=5):
    draw.arc((x, y, x+36, y+26), start=200, end=340, fill=color, width=width)
    draw.arc((x, y+18, x+36, y+44), start=20, end=160, fill=color, width=width)
    draw.polygon([(x+33, y+4), (x+48, y+7), (x+39, y+18)], fill=color)
    draw.polygon([(x+5, y+29), (x-7, y+39), (x+10, y+41)], fill=color)


def draw_prev(draw, x, y, size=34, color="white"):
    draw.polygon([(x + size*0.55, y), (x, y + size/2), (x + size*0.55, y + size)], fill=color)
    draw.rectangle((x + size*0.62, y, x + size*0.72, y + size), fill=color)


def draw_play(draw, x, y, size=40, color="white"):
    draw.polygon([(x, y), (x, y+size), (x+size, y+size/2)], fill=color)


def draw_next(draw, x, y, size=34, color="white"):
    draw.polygon([(x, y), (x + size*0.55, y + size/2), (x, y + size)], fill=color)
    draw.rectangle((x + size*0.62, y, x + size*0.72, y + size), fill=color)


def draw_repeat(draw, x, y, color="white", width=5):
    draw.arc((x, y, x+42, y+34), start=210, end=20, fill=color, width=width)
    draw.arc((x+5, y+10, x+47, y+44), start=30, end=200, fill=color, width=width)
    draw.polygon([(x+36, y+2), (x+52, y+4), (x+42, y+17)], fill=color)
    draw.polygon([(x+8, y+29), (x-4, y+40), (x+12, y+42)], fill=color)


# =========================
# MAIN
# =========================
async def get_thumb(videoid: str, title="Unknown Song", duration="0:00", views="0"):
    title = safe_text(title, "Unknown Song")
    duration = safe_text(duration, "0:00")
    views = safe_text(views, "0")

    path = f"{CACHE_DIR}/{videoid}.png"
    thumb_file = f"{CACHE_DIR}/{videoid}.jpg"

    try:
        if os.path.exists(path):
            os.remove(path)
    except:
        pass

    # auto title
    if title.lower() in ["unknown song", "unknown", "none", ""]:
        yt_title = await fetch_youtube_title(videoid)
        if yt_title:
            title = yt_title

    # -------------------------
    # Download thumbnail
    # -------------------------
    thumb_url = f"https://img.youtube.com/vi/{videoid}/maxresdefault.jpg"
    try:
        async with aiohttp.ClientSession() as s:
            async with s.get(thumb_url) as r:
                if r.status == 200:
                    async with aiofiles.open(thumb_file, "wb") as f:
                        await f.write(await r.read())
                else:
                    thumb_url = f"https://img.youtube.com/vi/{videoid}/hqdefault.jpg"
                    async with s.get(thumb_url) as r2:
                        if r2.status == 200:
                            async with aiofiles.open(thumb_file, "wb") as f:
                                await f.write(await r2.read())
                        else:
                            thumb_file = None
    except:
        thumb_file = None

    # -------------------------
    # Load original image
    # -------------------------
    try:
        if thumb_file and os.path.exists(thumb_file):
            original = Image.open(thumb_file).convert("RGB")
        else:
            raise Exception("No thumbnail")
    except:
        original = Image.new("RGB", (1280, 720), (25, 25, 25))

    original = ImageOps.fit(original, (1280, 720), method=Image.LANCZOS)

    # =========================
    # BACKGROUND BLUR (SAME IMAGE)
    # =========================
    bg = original.resize((1280, 720)).filter(ImageFilter.GaussianBlur(28))
    bg = ImageEnhance.Brightness(bg).enhance(0.35)
    bg = ImageEnhance.Color(bg).enhance(0.9)
    bg = bg.convert("RGBA")

    dark = Image.new("RGBA", (1280, 720), (0, 0, 0, 95))
    bg = Image.alpha_composite(bg, dark)

    # subtle center glow
    glow = Image.new("RGBA", (1280, 720), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    gd.ellipse((250, 120, 1030, 650), fill=(255, 255, 255, 18))
    glow = glow.filter(ImageFilter.GaussianBlur(120))
    bg = Image.alpha_composite(bg, glow)

    # =========================
    # GLASS CARD
    # =========================
    card_x, card_y = 70, 165
    card_w, card_h = 1140, 390

    # shadow
    shadow = Image.new("RGBA", (card_w + 80, card_h + 80), (0, 0, 0, 0))
    sd = ImageDraw.Draw(shadow)
    sd.rounded_rectangle((0, 0, card_w + 80, card_h + 80), 40, fill=(0, 0, 0, 120))
    shadow = shadow.filter(ImageFilter.GaussianBlur(30))
    bg.paste(shadow, (card_x - 40, card_y - 20), shadow)

    # actual glass
    glass = Image.new("RGBA", (card_w, card_h), (255, 255, 255, 20))
    mask = Image.new("L", (card_w, card_h), 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, card_w, card_h), 34, fill=255)
    bg.paste(glass, (card_x, card_y), mask)

    # border
    outline = Image.new("RGBA", (card_w, card_h), (0, 0, 0, 0))
    od = ImageDraw.Draw(outline)
    od.rounded_rectangle((0, 0, card_w - 1, card_h - 1), 34, outline=(255, 255, 255, 55), width=2)
    bg.paste(outline, (card_x, card_y), outline)

    draw = ImageDraw.Draw(bg)

    # =========================
    # ROUND THUMB (BIG)
    # =========================
    circle_size = 300
    album = ImageOps.fit(original.convert("RGBA"), (circle_size, circle_size), method=Image.LANCZOS)

    circle_mask = Image.new("L", (circle_size, circle_size), 0)
    ImageDraw.Draw(circle_mask).ellipse((0, 0, circle_size, circle_size), fill=255)
    album.putalpha(circle_mask)

    ring = Image.new("RGBA", (circle_size + 20, circle_size + 20), (0, 0, 0, 0))
    rd = ImageDraw.Draw(ring)
    rd.ellipse((0, 0, circle_size + 19, circle_size + 19), fill=(255, 255, 255, 255))

    # outer glow
    ring_glow = Image.new("RGBA", (circle_size + 80, circle_size + 80), (0, 0, 0, 0))
    rg = ImageDraw.Draw(ring_glow)
    rg.ellipse((20, 20, circle_size + 60, circle_size + 60), fill=(255, 255, 255, 70))
    ring_glow = ring_glow.filter(ImageFilter.GaussianBlur(18))
    bg.paste(ring_glow, (105, 195), ring_glow)

    thumb_x = 130
    thumb_y = 210
    bg.paste(ring, (thumb_x - 10, thumb_y - 10), ring)
    bg.paste(album, (thumb_x, thumb_y), album)

    # =========================
    # FONTS
    # =========================
    title_font = load_font(34)
    meta_font = load_font(20)
    time_font = load_font(18)

    # =========================
    # TEXT
    # =========================
    title = trim(title, title_font, 560)

    draw.text((560, 245), title, fill="white", font=title_font)
    draw.text((560, 318), f"YouTube | {views} views", fill=(225, 225, 225), font=meta_font)

    # =========================
    # PROGRESS BAR
    # =========================
    bar_x1 = 560
    bar_x2 = 1120
    bar_y = 370

    draw.rounded_rectangle((bar_x1, bar_y, bar_x2, bar_y + 9), 8, fill=(255, 255, 255))
    progress = 0.58
    prog_x = int(bar_x1 + (bar_x2 - bar_x1) * progress)

    draw.rounded_rectangle((bar_x1, bar_y, prog_x, bar_y + 9), 8, fill=(255, 0, 0))
    draw.ellipse((prog_x - 10, bar_y - 8, prog_x + 10, bar_y + 11), fill=(255, 0, 0))

    draw.text((560, 410), "00:00", fill="white", font=time_font)
    draw.text((1065, 410), duration, fill="white", font=time_font)

    # =========================
    # CONTROLS (SAME STYLE)
    # =========================
    icon_y = 462

    draw_shuffle(draw, 565, icon_y, color="white")
    draw_prev(draw, 715, icon_y + 4, size=32, color="white")

    # center play circle
    draw.ellipse((810, 440, 900, 530), fill=(255, 255, 255, 245))
    draw_play(draw, 844, 465, size=28, color=(35, 35, 35))

    draw_next(draw, 970, icon_y + 4, size=32, color="white")
    draw_repeat(draw, 1080, icon_y, color="white")

    # =========================
    # SAVE
    # =========================
    bg = bg.convert("RGB")
    bg.save(path, quality=98)

    try:
        if thumb_file and os.path.exists(thumb_file):
            os.remove(thumb_file)
    except:
        pass

    return path
