import os
import aiohttp
import aiofiles
from PIL import Image, ImageDraw, ImageFont, ImageFilter

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
# MAIN FUNCTION
# =========================
async def get_thumb(videoid: str, title="Unknown Song", duration="0:00", views="0"):
    title = safe_text(title, "Unknown Song")
    duration = safe_text(duration, "0:00")
    views = safe_text(views, "0")

    path = f"{CACHE_DIR}/{videoid}.png"
    thumb_file = f"{CACHE_DIR}/{videoid}.jpg"

    # Always regenerate fresh thumbnail
    try:
        if os.path.exists(path):
            os.remove(path)
    except:
        pass

    # -------------------------
    # AUTO FIX TITLE
    # -------------------------
    if title.lower() in ["unknown song", "unknown", "none", ""]:
        yt_title = await fetch_youtube_title(videoid)
        if yt_title:
            title = yt_title

    # -------------------------
    # Download best thumbnail
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
            raise Exception("No thumb")
    except:
        original = Image.new("RGB", (1600, 900), (30, 30, 30))

    original = original.resize((1600, 900))

    # =========================
    # BACKGROUND
    # =========================
    bg = original.resize((1600, 900)).filter(ImageFilter.GaussianBlur(24))
    bg = bg.convert("RGBA")

    dark = Image.new("RGBA", (1600, 900), (0, 0, 0, 160))
    bg = Image.alpha_composite(bg, dark)

    glow = Image.new("RGBA", (1600, 900), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    gd.ellipse((180, 80, 1420, 860), fill=(255, 180, 90, 35))
    glow = glow.filter(ImageFilter.GaussianBlur(140))
    bg = Image.alpha_composite(bg, glow)

    draw = ImageDraw.Draw(bg)

    # =========================
    # MAIN CARD
    # =========================
    card_x, card_y = 260, 70
    card_w, card_h = 1080, 760

    shadow = Image.new("RGBA", (card_w + 60, card_h + 60), (0, 0, 0, 0))
    sd = ImageDraw.Draw(shadow)
    sd.rounded_rectangle((0, 0, card_w + 60, card_h + 60), 70, fill=(0, 0, 0, 180))
    shadow = shadow.filter(ImageFilter.GaussianBlur(40))
    bg.paste(shadow, (card_x - 30, card_y - 10), shadow)

    card = Image.new("RGBA", (card_w, card_h), (22, 22, 24, 242))
    card_mask = Image.new("L", (card_w, card_h), 0)
    ImageDraw.Draw(card_mask).rounded_rectangle((0, 0, card_w, card_h), 60, fill=255)
    bg.paste(card, (card_x, card_y), card_mask)

    # =========================
    # TOP PREVIEW IMAGE
    # =========================
    preview = original.convert("RGBA").resize((860, 320))
    preview_mask = Image.new("L", (860, 320), 0)
    ImageDraw.Draw(preview_mask).rounded_rectangle((0, 0, 860, 320), 34, fill=255)
    preview.putalpha(preview_mask)

    border = Image.new("RGBA", (868, 328), (0, 0, 0, 0))
    bd = ImageDraw.Draw(border)
    bd.rounded_rectangle((0, 0, 868, 328), 36, outline=(220, 185, 120), width=4)

    preview_x = 370
    preview_y = 110
    bg.paste(border, (preview_x - 4, preview_y - 4), border)
    bg.paste(preview, (preview_x, preview_y), preview)

    # =========================
    # FONTS
    # =========================
    try:
        now_font = ImageFont.truetype(FONT, 42)
        title_font = ImageFont.truetype(FONT, 72)
        time_font = ImageFont.truetype(FONT, 32)
        btn_font = ImageFont.truetype(FONT, 66)
    except:
        now_font = ImageFont.load_default()
        title_font = ImageFont.load_default()
        time_font = ImageFont.load_default()
        btn_font = ImageFont.load_default()

    # =========================
    # TEXT
    # =========================
    title = trim(title, title_font, 820)

    draw.text((800, 495), "Now Playing", fill=(210, 210, 210), font=now_font, anchor="mm")
    draw.text((800, 585), title, fill="white", font=title_font, anchor="mm")

    # =========================
    # PROGRESS BAR
    # =========================
    bar_x1 = 420
    bar_x2 = 1180
    bar_y = 675

    draw.rounded_rectangle((bar_x1, bar_y, bar_x2, bar_y + 12), 12, fill=(105, 105, 105))

    progress = 0.40
    prog_x = int(bar_x1 + (bar_x2 - bar_x1) * progress)
    draw.rounded_rectangle((bar_x1, bar_y, prog_x, bar_y + 12), 12, fill=(225, 185, 120))

    draw.ellipse((prog_x - 13, bar_y - 10, prog_x + 13, bar_y + 16), fill="white")

    draw.text((420, 725), "1:24", fill=(180, 180, 180), font=time_font)
    draw.text((1120, 725), duration, fill=(180, 180, 180), font=time_font)

    # =========================
    # BUTTONS
    # =========================
    draw.text((620, 790), "<<", fill="white", font=btn_font, anchor="mm")

    draw.rounded_rectangle((735, 735, 865, 850), 34, fill=(58, 58, 64))
    draw.text((800, 793), "II", fill="white", font=btn_font, anchor="mm")

    draw.text((980, 790), ">>", fill="white", font=btn_font, anchor="mm")

    # =========================
    # SAVE
    # =========================
    bg = bg.convert("RGB")
    bg.save(path, quality=96)

    # cleanup
    try:
        if thumb_file and os.path.exists(thumb_file):
            os.remove(thumb_file)
    except:
        pass

    return path
