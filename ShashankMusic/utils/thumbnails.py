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
# MAIN FUNCTION
# =========================
async def get_thumb(videoid: str, title="Unknown Song", duration="0:00", views="0"):
    title = safe_text(title, "Unknown Song")
    duration = safe_text(duration, "0:00")
    views = safe_text(views, "0")

    path = f"{CACHE_DIR}/{videoid}.png"
    thumb_file = f"{CACHE_DIR}/{videoid}.jpg"

    # ALWAYS regenerate fresh thumbnail
    try:
        if os.path.exists(path):
            os.remove(path)
    except:
        pass

    # Better thumbnail source
    thumb_url = f"https://img.youtube.com/vi/{videoid}/maxresdefault.jpg"

    # -------------------------
    # Download thumbnail
    # -------------------------
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
        original = Image.new("RGB", (1280, 720), (35, 35, 35))

    # =========================
    # BACKGROUND
    # =========================
    bg = original.resize((1280, 720)).filter(ImageFilter.GaussianBlur(26))
    bg = bg.convert("RGBA")

    dark_overlay = Image.new("RGBA", (1280, 720), (0, 0, 0, 155))
    bg = Image.alpha_composite(bg, dark_overlay)

    glow = Image.new("RGBA", (1280, 720), (0, 0, 0, 0))
    glow_draw = ImageDraw.Draw(glow)
    glow_draw.ellipse((140, 70, 1140, 700), fill=(255, 170, 90, 40))
    glow = glow.filter(ImageFilter.GaussianBlur(140))
    bg = Image.alpha_composite(bg, glow)

    draw = ImageDraw.Draw(bg)

    # =========================
    # BIG CENTER CARD
    # =========================
    card_x, card_y = 220, 55
    card_w, card_h = 840, 610

    shadow = Image.new("RGBA", (card_w + 50, card_h + 50), (0, 0, 0, 0))
    sd = ImageDraw.Draw(shadow)
    sd.rounded_rectangle((0, 0, card_w + 50, card_h + 50), 70, fill=(0, 0, 0, 160))
    shadow = shadow.filter(ImageFilter.GaussianBlur(32))
    bg.paste(shadow, (card_x - 25, card_y - 10), shadow)

    card = Image.new("RGBA", (card_w, card_h), (16, 16, 18, 242))
    card_mask = Image.new("L", (card_w, card_h), 0)
    ImageDraw.Draw(card_mask).rounded_rectangle((0, 0, card_w, card_h), 60, fill=255)
    bg.paste(card, (card_x, card_y), card_mask)

    # =========================
    # TOP PREVIEW IMAGE
    # =========================
    preview = original.convert("RGBA").resize((670, 250))
    preview_mask = Image.new("L", (670, 250), 0)
    ImageDraw.Draw(preview_mask).rounded_rectangle((0, 0, 670, 250), 35, fill=255)
    preview.putalpha(preview_mask)

    border = Image.new("RGBA", (678, 258), (0, 0, 0, 0))
    bd = ImageDraw.Draw(border)
    bd.rounded_rectangle((0, 0, 678, 258), 38, outline=(225, 185, 120), width=4)

    bg.paste(border, (301, 91), border)
    bg.paste(preview, (305, 95), preview)

    # =========================
    # FONTS
    # =========================
    try:
        small_font = ImageFont.truetype(FONT, 28)
        med_font = ImageFont.truetype(FONT, 36)
        title_font = ImageFont.truetype(FONT, 56)
        time_font = ImageFont.truetype(FONT, 28)
        button_font = ImageFont.truetype(FONT, 52)
    except:
        small_font = ImageFont.load_default()
        med_font = ImageFont.load_default()
        title_font = ImageFont.load_default()
        time_font = ImageFont.load_default()
        button_font = ImageFont.load_default()

    # =========================
    # TEXT
    # =========================
    title = trim(title, title_font, 620)

    draw.text((640, 395), "Now Playing", fill=(210, 210, 210), font=med_font, anchor="mm")
    draw.text((640, 470), title, fill="white", font=title_font, anchor="mm")

    # =========================
    # PROGRESS BAR
    # =========================
    bar_x1 = 360
    bar_x2 = 920
    bar_y = 545

    draw.rounded_rectangle((bar_x1, bar_y, bar_x2, bar_y + 10), 10, fill=(95, 95, 95))

    progress = 0.40
    prog_x = int(bar_x1 + (bar_x2 - bar_x1) * progress)
    draw.rounded_rectangle((bar_x1, bar_y, prog_x, bar_y + 10), 10, fill=(225, 185, 120))

    draw.ellipse((prog_x - 11, bar_y - 9, prog_x + 11, bar_y + 13), fill="white")

    draw.text((360, 585), "1:24", fill=(170, 170, 170), font=time_font)
    draw.text((875, 585), duration, fill=(170, 170, 170), font=time_font)

    # =========================
    # BUTTONS
    # =========================
    draw.text((500, 635), "<<", fill="white", font=button_font, anchor="mm")

    draw.rounded_rectangle((585, 585, 695, 685), 28, fill=(55, 55, 60))
    draw.text((640, 635), "II", fill="white", font=button_font, anchor="mm")

    draw.text((780, 635), ">>", fill="white", font=button_font, anchor="mm")

    # =========================
    # SAVE
    # =========================
    bg = bg.convert("RGB")
    bg.save(path, quality=96)

    try:
        if thumb_file and os.path.exists(thumb_file):
            os.remove(thumb_file)
    except:
        pass

    return path
