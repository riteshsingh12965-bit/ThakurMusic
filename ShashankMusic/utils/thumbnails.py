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
def draw_prev(draw, x, y, size=38, color="white"):
    draw.polygon([(x + size*0.55, y), (x, y + size/2), (x + size*0.55, y + size)], fill=color)
    draw.polygon([(x + size*1.1, y), (x + size*0.55, y + size/2), (x + size*1.1, y + size)], fill=color)


def draw_next(draw, x, y, size=38, color="white"):
    draw.polygon([(x, y), (x + size*0.55, y + size/2), (x, y + size)], fill=color)
    draw.polygon([(x + size*0.55, y), (x + size*1.1, y + size/2), (x + size*0.55, y + size)], fill=color)


def draw_pause(draw, x, y, w=14, h=48, gap=14, color="white"):
    draw.rounded_rectangle((x, y, x + w, y + h), radius=4, fill=color)
    draw.rounded_rectangle((x + w + gap, y, x + w + gap + w, y + h), radius=4, fill=color)


# =========================
# MAIN
# =========================
async def get_thumb(videoid: str, title="Unknown Song", duration="0:00", views="YouTube"):
    title = safe_text(title, "Unknown Song")
    duration = safe_text(duration, "0:00")
    views = safe_text(views, "YouTube")

    path = f"{CACHE_DIR}/{videoid}.png"
    thumb_file = f"{CACHE_DIR}/{videoid}.jpg"

    try:
        if os.path.exists(path):
            os.remove(path)
    except:
        pass

    if title.lower() in ["unknown song", "unknown", "none", ""]:
        yt_title = await fetch_youtube_title(videoid)
        if yt_title:
            title = yt_title

    # Download thumbnail
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

    # Load original
    try:
        if thumb_file and os.path.exists(thumb_file):
            original = Image.open(thumb_file).convert("RGB")
        else:
            raise Exception("No thumbnail")
    except:
        original = Image.new("RGB", (1280, 720), (25, 25, 25))

    original = ImageOps.fit(original, (1280, 720), method=Image.LANCZOS)

    # =========================
    # BACKGROUND (AADAT STYLE)
    # =========================
    bg = original.copy().filter(ImageFilter.GaussianBlur(34))
    bg = ImageEnhance.Brightness(bg).enhance(0.28)
    bg = ImageEnhance.Color(bg).enhance(1.0)
    bg = bg.convert("RGBA")

    dark = Image.new("RGBA", (1280, 720), (0, 0, 0, 150))
    bg = Image.alpha_composite(bg, dark)

    # side blur dark
    side = Image.new("RGBA", (1280, 720), (0, 0, 0, 0))
    sd = ImageDraw.Draw(side)
    sd.rectangle((0, 0, 220, 720), fill=(0, 0, 0, 80))
    sd.rectangle((1060, 0, 1280, 720), fill=(0, 0, 0, 80))
    side = side.filter(ImageFilter.GaussianBlur(80))
    bg = Image.alpha_composite(bg, side)

    # center cinematic glow
    glow = Image.new("RGBA", (1280, 720), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    gd.ellipse((250, 80, 1030, 680), fill=(255, 220, 150, 26))
    glow = glow.filter(ImageFilter.GaussianBlur(100))
    bg = Image.alpha_composite(bg, glow)

    draw = ImageDraw.Draw(bg)

    # =========================
    # BIG CARD
    # =========================
    card_x, card_y = 300, 25
    card_w, card_h = 680, 670

    shadow = Image.new("RGBA", (card_w + 120, card_h + 120), (0, 0, 0, 0))
    shd = ImageDraw.Draw(shadow)
    shd.rounded_rectangle((0, 0, card_w + 120, card_h + 120), 60, fill=(0, 0, 0, 210))
    shadow = shadow.filter(ImageFilter.GaussianBlur(45))
    bg.paste(shadow, (card_x - 60, card_y + 20), shadow)

    card = Image.new("RGBA", (card_w, card_h), (20, 20, 24, 242))
    card_mask = Image.new("L", (card_w, card_h), 0)
    ImageDraw.Draw(card_mask).rounded_rectangle((0, 0, card_w, card_h), 50, fill=255)
    bg.paste(card, (card_x, card_y), card_mask)

    # top gloss
    gloss = Image.new("RGBA", (card_w, card_h), (0, 0, 0, 0))
    gld = ImageDraw.Draw(gloss)
    gld.rounded_rectangle((10, 10, card_w - 10, 100), 40, fill=(255, 255, 255, 8))
    bg.paste(gloss, (card_x, card_y), gloss)

    # =========================
    # BIG TOP IMAGE
    # =========================
    preview = ImageOps.fit(original.convert("RGBA"), (560, 260), method=Image.LANCZOS)

    preview_mask = Image.new("L", (560, 260), 0)
    ImageDraw.Draw(preview_mask).rounded_rectangle((0, 0, 560, 260), 34, fill=255)
    preview.putalpha(preview_mask)

    preview_x = 360
    preview_y = 60
    bg.paste(preview, (preview_x, preview_y), preview)

    # golden border
    border = Image.new("RGBA", (568, 268), (0, 0, 0, 0))
    bd = ImageDraw.Draw(border)
    bd.rounded_rectangle((0, 0, 568, 268), 36, outline=(224, 191, 120), width=4)
    bg.paste(border, (preview_x - 4, preview_y - 4), border)

    # 4k
    tag_font = load_font(30)
    draw.text((372, 295), "4k", fill="white", font=tag_font)

    # =========================
    # FONTS
    # =========================
    top_font = load_font(16)
    now_font = load_font(30)
    title_font = load_font(42)
    meta_font = load_font(22)
    time_font = load_font(24)

    # =========================
    # TEXT
    # =========================
    draw.text((640, 40), "NOW PLAYING • PREMIUM PLAYER", fill=(175, 175, 175), font=top_font, anchor="mm")

    clean_title = trim(title.upper(), title_font, 560)

    draw.text((640, 365), "Now Playing", fill=(210, 210, 210), font=now_font, anchor="mm")
    draw.text((640, 430), clean_title, fill="white", font=title_font, anchor="mm")
    draw.text((640, 470), views, fill=(155, 155, 155), font=meta_font, anchor="mm")

    # =========================
    # PROGRESS BAR
    # =========================
    bar_x1 = 395
    bar_x2 = 885
    bar_y = 525

    draw.rounded_rectangle((bar_x1, bar_y, bar_x2, bar_y + 12), 12, fill=(100, 100, 100))

    progress = 0.40
    prog_x = int(bar_x1 + (bar_x2 - bar_x1) * progress)

    draw.rounded_rectangle((bar_x1, bar_y, prog_x, bar_y + 12), 12, fill=(224, 191, 120))
    draw.ellipse((prog_x - 12, bar_y - 8, prog_x + 12, bar_y + 16), fill="white")

    draw.text((395, 565), "1:24", fill=(190, 190, 190), font=time_font)
    draw.text((845, 565), duration, fill=(190, 190, 190), font=time_font)

    # =========================
    # BUTTONS
    # =========================
    draw_prev(draw, 470, 620, size=42, color="white")
    draw_next(draw, 760, 620, size=42, color="white")

    pause_bg = Image.new("RGBA", (120, 120), (0, 0, 0, 0))
    pbd = ImageDraw.Draw(pause_bg)
    pbd.rounded_rectangle((0, 0, 120, 120), 34, fill=(58, 58, 64, 255))
    bg.paste(pause_bg, (580, 590), pause_bg)

    draw_pause(draw, 620, 625, w=14, h=50, gap=14, color="white")

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
