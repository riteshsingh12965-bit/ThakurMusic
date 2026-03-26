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
# FETCH TITLE
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
# MAIN FUNCTION
# =========================
async def get_thumb(videoid: str, title="Unknown Song", duration="0:00", views="YouTube"):
    title = safe_text(title, "Unknown Song")
    duration = safe_text(duration, "0:00")
    views = safe_text(views, "YouTube")

    path = f"{CACHE_DIR}/{videoid}.png"
    thumb_file = f"{CACHE_DIR}/{videoid}.jpg"

    # Always fresh
    try:
        if os.path.exists(path):
            os.remove(path)
    except:
        pass

    # Auto title fix
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

    # Load image
    try:
        if thumb_file and os.path.exists(thumb_file):
            original = Image.open(thumb_file).convert("RGB")
        else:
            raise Exception("No thumb")
    except:
        original = Image.new("RGB", (1280, 720), (30, 30, 30))

    original = ImageOps.fit(original, (1280, 720), method=Image.LANCZOS)

    # =========================
    # BACKGROUND
    # =========================
    bg = original.copy().filter(ImageFilter.GaussianBlur(26))
    bg = ImageEnhance.Brightness(bg).enhance(0.28)
    bg = ImageEnhance.Color(bg).enhance(0.9)
    bg = bg.convert("RGBA")

    dark = Image.new("RGBA", (1280, 720), (0, 0, 0, 135))
    bg = Image.alpha_composite(bg, dark)

    # Cinematic glow
    glow = Image.new("RGBA", (1280, 720), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    gd.ellipse((260, 80, 1020, 650), fill=(230, 190, 120, 25))
    glow = glow.filter(ImageFilter.GaussianBlur(120))
    bg = Image.alpha_composite(bg, glow)

    draw = ImageDraw.Draw(bg)

    # =========================
    # MAIN CARD (AADAT STYLE)
    # =========================
    card_x, card_y = 305, 42
    card_w, card_h = 670, 635

    # Shadow
    shadow = Image.new("RGBA", (card_w + 80, card_h + 80), (0, 0, 0, 0))
    sd = ImageDraw.Draw(shadow)
    sd.rounded_rectangle((0, 0, card_w + 80, card_h + 80), 58, fill=(0, 0, 0, 185))
    shadow = shadow.filter(ImageFilter.GaussianBlur(32))
    bg.paste(shadow, (card_x - 40, card_y + 28), shadow)

    # Card
    card = Image.new("RGBA", (card_w, card_h), (17, 17, 20, 245))
    card_mask = Image.new("L", (card_w, card_h), 0)
    ImageDraw.Draw(card_mask).rounded_rectangle((0, 0, card_w, card_h), 48, fill=255)
    bg.paste(card, (card_x, card_y), card_mask)

    # =========================
    # TOP IMAGE (BIG SAME STYLE)
    # =========================
    preview = ImageOps.fit(original.convert("RGBA"), (560, 245), method=Image.LANCZOS)

    preview_mask = Image.new("L", (560, 245), 0)
    ImageDraw.Draw(preview_mask).rounded_rectangle((0, 0, 560, 245), 34, fill=255)
    preview.putalpha(preview_mask)

    preview_x = 360
    preview_y = 78
    bg.paste(preview, (preview_x, preview_y), preview)

    # Gold border
    border = Image.new("RGBA", (568, 253), (0, 0, 0, 0))
    bd = ImageDraw.Draw(border)
    bd.rounded_rectangle((0, 0, 568, 253), 36, outline=(226, 191, 123), width=4)
    bg.paste(border, (preview_x - 4, preview_y - 4), border)

    # 4k text
    tag_font = load_font(30)
    draw.text((378, 292), "4k", fill="white", font=tag_font)

    # =========================
    # FONTS
    # =========================
    top_font = load_font(17)
    now_font = load_font(36)
    title_font = load_font(52)
    meta_font = load_font(23)
    time_font = load_font(24)
    side_btn_font = load_font(56)
    pause_font = load_font(78)

    # =========================
    # TEXT
    # =========================
    draw.text((640, 62), "NOW PLAYING • PREMIUM PLAYER", fill=(175, 175, 175), font=top_font, anchor="mm")

    clean_title = trim(title.upper(), title_font, 570)

    draw.text((640, 362), "Now Playing", fill=(205, 205, 205), font=now_font, anchor="mm")
    draw.text((640, 438), clean_title, fill="white", font=title_font, anchor="mm")
    draw.text((640, 485), views, fill=(155, 155, 155), font=meta_font, anchor="mm")

    # =========================
    # PROGRESS BAR
    # =========================
    bar_x1 = 405
    bar_x2 = 875
    bar_y = 532

    draw.rounded_rectangle((bar_x1, bar_y, bar_x2, bar_y + 10), 10, fill=(95, 95, 95))

    progress = 0.40
    prog_x = int(bar_x1 + (bar_x2 - bar_x1) * progress)

    draw.rounded_rectangle((bar_x1, bar_y, prog_x, bar_y + 10), 10, fill=(226, 191, 123))
    draw.ellipse((prog_x - 11, bar_y - 7, prog_x + 11, bar_y + 15), fill="white")

    draw.text((405, 570), "1:24", fill=(188, 188, 188), font=time_font)
    draw.text((820, 570), duration, fill=(188, 188, 188), font=time_font)

    # =========================
    # BUTTONS (AADAT STYLE)
    # =========================
    draw.text((520, 640), "◀◀", fill="white", font=side_btn_font, anchor="mm")
    draw.text((760, 640), "▶▶", fill="white", font=side_btn_font, anchor="mm")

    pause_bg = Image.new("RGBA", (115, 115), (0, 0, 0, 0))
    pbd = ImageDraw.Draw(pause_bg)
    pbd.rounded_rectangle((0, 0, 115, 115), 32, fill=(55, 55, 60, 255))
    bg.paste(pause_bg, (582, 582), pause_bg)

    draw.text((640, 640), "II", fill="white", font=pause_font, anchor="mm")

    # =========================
    # SAVE
    # =========================
    bg = bg.convert("RGB")
    bg.save(path, quality=98)

    # Cleanup
    try:
        if thumb_file and os.path.exists(thumb_file):
            os.remove(thumb_file)
    except:
        pass

    return path
