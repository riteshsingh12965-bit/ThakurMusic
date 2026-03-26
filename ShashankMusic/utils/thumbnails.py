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


def load_font(size):
    try:
        return ImageFont.truetype(FONT, size)
    except:
        return ImageFont.load_default()


def trim_text(text, font, max_width):
    text = safe_text(text)
    try:
        while font.getbbox(text)[2] > max_width and len(text) > 3:
            text = text[:-1]
        return text + "..." if len(text) > 3 else text
    except:
        return text


# =========================
# FETCH TITLE FROM YOUTUBE
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
# ICON DRAW FUNCTIONS
# =========================
def draw_prev(draw, x, y, color="white"):
    draw.polygon([(x+28, y), (x, y+20), (x+28, y+40)], fill=color)
    draw.rectangle((x+33, y, x+40, y+40), fill=color)


def draw_play(draw, x, y, color=(25, 25, 25)):
    draw.polygon([(x, y), (x, y+40), (x+34, y+20)], fill=color)


def draw_next(draw, x, y, color="white"):
    draw.polygon([(x, y), (x+28, y+20), (x, y+40)], fill=color)
    draw.rectangle((x+33, y, x+40, y+40), fill=color)


def draw_shuffle(draw, x, y, color="white", width=5):
    draw.arc((x, y, x+38, y+28), start=200, end=340, fill=color, width=width)
    draw.arc((x, y+18, x+38, y+46), start=20, end=160, fill=color, width=width)
    draw.polygon([(x+35, y+5), (x+48, y+7), (x+39, y+18)], fill=color)
    draw.polygon([(x+5, y+30), (x-7, y+40), (x+10, y+42)], fill=color)


def draw_repeat(draw, x, y, color="white", width=5):
    draw.arc((x, y, x+42, y+34), start=210, end=20, fill=color, width=width)
    draw.arc((x+5, y+10, x+47, y+44), start=30, end=200, fill=color, width=width)
    draw.polygon([(x+36, y+2), (x+52, y+4), (x+42, y+17)], fill=color)
    draw.polygon([(x+8, y+29), (x-4, y+40), (x+12, y+42)], fill=color)


# =========================
# MAIN THUMB FUNCTION
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

    # auto title fix
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
    # Load image
    # -------------------------
    try:
        if thumb_file and os.path.exists(thumb_file):
            original = Image.open(thumb_file).convert("RGB")
        else:
            raise Exception("No thumb")
    except:
        original = Image.new("RGB", (1280, 720), (30, 30, 30))

    original = ImageOps.fit(original, (1280, 720), method=Image.LANCZOS)

    # =========================
    # BACKGROUND = SAME IMAGE BLUR
    # =========================
    bg = original.resize((1280, 720)).filter(ImageFilter.GaussianBlur(28))
    bg = ImageEnhance.Brightness(bg).enhance(0.35)
    bg = ImageEnhance.Color(bg).enhance(0.95)
    bg = bg.convert("RGBA")

    dark = Image.new("RGBA", (1280, 720), (0, 0, 0, 95))
    bg = Image.alpha_composite(bg, dark)

    # =========================
    # GLASS CARD (NO WHITE JHAT)
    # =========================
    card_x, card_y = 85, 150
    card_w, card_h = 1110, 410

    # shadow
    shadow = Image.new("RGBA", (card_w + 80, card_h + 80), (0, 0, 0, 0))
    sd = ImageDraw.Draw(shadow)
    sd.rounded_rectangle((0, 0, card_w + 80, card_h + 80), 42, fill=(0, 0, 0, 110))
    shadow = shadow.filter(ImageFilter.GaussianBlur(28))
    bg.paste(shadow, (card_x - 40, card_y - 20), shadow)

    # blurred card region
    card_crop = bg.crop((card_x, card_y, card_x + card_w, card_y + card_h))
    card_crop = card_crop.filter(ImageFilter.GaussianBlur(8))

    # overlay
    glass = Image.new("RGBA", (card_w, card_h), (255, 255, 255, 18))
    card_crop = Image.alpha_composite(card_crop.convert("RGBA"), glass)

    # mask
    mask = Image.new("L", (card_w, card_h), 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, card_w, card_h), 34, fill=255)
    bg.paste(card_crop, (card_x, card_y), mask)

    # border
    outline = Image.new("RGBA", (card_w, card_h), (0, 0, 0, 0))
    od = ImageDraw.Draw(outline)
    od.rounded_rectangle((0, 0, card_w - 1, card_h - 1), 34, outline=(255, 255, 255, 60), width=2)
    bg.paste(outline, (card_x, card_y), outline)

    draw = ImageDraw.Draw(bg)

    # =========================
    # ROUND THUMB (BIG)
    # =========================
    thumb_size = 285
    album = ImageOps.fit(original.convert("RGBA"), (thumb_size, thumb_size), method=Image.LANCZOS)

    circle_mask = Image.new("L", (thumb_size, thumb_size), 0)
    ImageDraw.Draw(circle_mask).ellipse((0, 0, thumb_size, thumb_size), fill=255)
    album.putalpha(circle_mask)

    ring = Image.new("RGBA", (thumb_size + 18, thumb_size + 18), (0, 0, 0, 0))
    rd = ImageDraw.Draw(ring)
    rd.ellipse((0, 0, thumb_size + 17, thumb_size + 17), fill=(255, 255, 255, 255))

    glow = Image.new("RGBA", (thumb_size + 80, thumb_size + 80), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    gd.ellipse((20, 20, thumb_size + 60, thumb_size + 60), fill=(255, 255, 255, 55))
    glow = glow.filter(ImageFilter.GaussianBlur(18))
    bg.paste(glow, (118, 192), glow)

    thumb_x = 145
    thumb_y = 215
    bg.paste(ring, (thumb_x - 9, thumb_y - 9), ring)
    bg.paste(album, (thumb_x, thumb_y), album)

    # =========================
    # FONTS
    # =========================
    title_font = load_font(36)
    meta_font = load_font(22)
    time_font = load_font(19)

    # =========================
    # TEXT
    # =========================
    title = trim_text(title, title_font, 560)

    draw.text((575, 245), title, fill="white", font=title_font)
    draw.text((575, 315), f"YouTube | {views} views", fill=(220, 220, 220), font=meta_font)

    # =========================
    # PROGRESS BAR
    # =========================
    bar_x1 = 575
    bar_x2 = 1125
    bar_y = 375

    draw.rounded_rectangle((bar_x1, bar_y, bar_x2, bar_y + 8), 8, fill=(255, 255, 255))
    progress = 0.58
    prog_x = int(bar_x1 + (bar_x2 - bar_x1) * progress)

    draw.rounded_rectangle((bar_x1, bar_y, prog_x, bar_y + 8), 8, fill=(255, 0, 0))
    draw.ellipse((prog_x - 10, bar_y - 9, prog_x + 10, bar_y + 11), fill=(255, 0, 0))

    draw.text((575, 410), "00:00", fill="white", font=time_font)
    draw.text((1065, 410), duration, fill="white", font=time_font)

    # =========================
    # CONTROLS
    # =========================
    controls_y = 462

    draw_shuffle(draw, 585, controls_y, color="white")
    draw_prev(draw, 725, controls_y + 2, color="white")

    # center play button
    draw.ellipse((820, 438, 910, 528), fill=(255, 255, 255, 245))
    draw_play(draw, 855, 463, color=(20, 20, 20))

    draw_next(draw, 980, controls_y + 2, color="white")
    draw_repeat(draw, 1088, controls_y, color="white")

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
